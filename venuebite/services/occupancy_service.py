"""Request-scoped candidate terms, conservative completeness and provenance."""

from dataclasses import dataclass, replace
from decimal import Decimal
import re
from types import MappingProxyType

from venuebite.occupancy import (
    CandidateProperty, OccupancyRate, OccupancyCosts, BudgetFit, LEASE_STRUCTURES, RENT_BASES,
    calculate_costs, calculate_budget_fit, currency,
)
from venuebite.providers.site_provider import safe_source_url


TEXT_LIMITS = {"property_address": 300, "source_label": 120, "source_url": 2000, "occupancy_notes": 1000}
NUMBER_LIMITS = {"space_size_sqft": Decimal("10000000"), "asking_rent": Decimal("100000000"),
                 "additional_occupancy_rate": Decimal("100000000"), "monthly_occupancy_budget": Decimal("100000000")}
ENUM_OPTIONS = {"asking_rent_basis": RENT_BASES, "additional_occupancy_basis": RENT_BASES,
                "lease_structure": LEASE_STRUCTURES}
ENUM_DEFAULTS = {"asking_rent_basis": "per_sqft_per_year", "additional_occupancy_basis": "per_sqft_per_year", "lease_structure": "unknown"}
FIELD_NAMES = tuple((*TEXT_LIMITS, *NUMBER_LIMITS, *ENUM_OPTIONS))
NUMBER_PATTERN = re.compile(r"-?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]{1,6})?")
EVIDENCE_CAUTION = "Commercial occupancy terms are user-supplied and have not been independently verified."
LIMITATION = "Budget fit is relative to your stated USD occupancy budget, not submarket rent, fair market value, restaurant revenue or profitability."
BASE_ONLY_WARNING = "Base rent only. Total occupancy cost may be higher; additional NNN/CAM or operating charges were not supplied."
LEASE_CAUTIONS = {
    "nnn": "NNN base rent may exclude property taxes, insurance, maintenance/CAM and other pass-throughs. Confirm the quoted additional charges and exclusions.",
    "gross": "Gross lease inclusions vary. No operating expense is assumed included unless explicitly supplied; confirm the lease with the source.",
    "modified_gross": "Modified Gross expense responsibility depends on the lease; confirm all inclusions and exclusions.",
    "unknown": "Lease structure was not stated. Expense responsibility is unknown; no inclusions are assumed.",
}


@dataclass(frozen=True)
class OccupancyInput:
    candidate: CandidateProperty
    values: MappingProxyType
    errors: MappingProxyType

    @property
    def status(self):
        return "invalid" if self.errors else "partial" if self.candidate.provided else "not_provided"


def normalize_candidate_input(form):
    values, errors, numbers = {}, {}, {}
    for field in FIELD_NAMES:
        raw = form.get(field, ENUM_DEFAULTS.get(field, ""))
        value = raw.strip() if isinstance(raw, str) else ""
        limit = TEXT_LIMITS.get(field, 48)
        values[field] = value[:limit]
        if hasattr(form, "getlist") and len(form.getlist(field)) > 1:
            errors[field] = "Submit one value for this field."
        elif not isinstance(raw, str) or len(value) > limit:
            errors[field] = f"Keep this field to {limit} characters or fewer."
        elif any(ord(char) < 32 and char not in "\n\r\t" for char in value) or "\x7f" in value:
            errors[field] = "Remove unsupported control characters."
        elif field != "occupancy_notes" and any(ord(char) < 32 for char in value):
            errors[field] = "Remove unsupported control characters."
        elif field in ENUM_OPTIONS and value not in ENUM_OPTIONS[field]:
            errors[field] = "Choose one of the listed options."
        elif field == "source_url" and value and not safe_source_url(value):
            errors[field] = "Enter a valid HTTP or HTTPS source URL without credentials."
        if field in NUMBER_LIMITS:
            numbers[field] = None
            if not value or field in errors:
                continue
            numeric = value.removeprefix("$").strip() if field != "space_size_sqft" else value
            if not NUMBER_PATTERN.fullmatch(numeric):
                errors[field] = "Enter a finite number with up to six decimal places (USD for money)."
                continue
            number = Decimal(numeric.replace(",", ""))
            minimum_is_positive = field in {"space_size_sqft", "monthly_occupancy_budget"}
            if number < 0 or (minimum_is_positive and number == 0):
                errors[field] = "Enter an amount greater than zero." if minimum_is_positive else "Enter a nonnegative amount."
            elif number > NUMBER_LIMITS[field]:
                errors[field] = f"Enter an amount no greater than {NUMBER_LIMITS[field]:,}."
            else:
                numbers[field] = number
    provided = any(values.get(field) for field in (*TEXT_LIMITS, *NUMBER_LIMITS)) or any(
        values[field] != default for field, default in ENUM_DEFAULTS.items())
    def rate(field, basis):
        return OccupancyRate(numbers[field], values[basis]) if numbers[field] is not None and basis not in errors else None
    candidate = CandidateProperty(
        source_label=values["source_label"] or "Commercial listing / user entry", source_url=values["source_url"] if "source_url" not in errors else "",
        property_address=values["property_address"], space_size_sqft=numbers["space_size_sqft"],
        asking_rent=rate("asking_rent", "asking_rent_basis"), lease_structure=values["lease_structure"] if "lease_structure" not in errors else "unknown",
        additional_occupancy_rate=rate("additional_occupancy_rate", "additional_occupancy_basis"),
        monthly_occupancy_budget=numbers["monthly_occupancy_budget"], notes=values["occupancy_notes"], provided=provided,
    )
    return OccupancyInput(candidate, MappingProxyType(values), MappingProxyType(errors))


@dataclass(frozen=True)
class OccupancyFact:
    label: str
    value: str
    detail: str = ""


@dataclass(frozen=True)
class OccupancyAnalysis:
    status: str
    candidate: CandidateProperty
    costs: OccupancyCosts
    model: BudgetFit | None
    fallback_reason: str
    summary: str
    warnings: tuple[str, ...]
    facts: tuple[OccupancyFact, ...]

    @property
    def supported(self):
        return self.model is not None

    @property
    def budget_statement(self):
        if not self.model:
            return ""
        return ("Estimated occupancy cost exceeds the stated monthly occupancy budget."
                if self.model.above_budget else "Candidate occupancy cost is within the stated monthly occupancy budget.")


def _address_key(value):
    return " ".join(re.sub(r"[^\w\s]", " ", value.casefold()).split())


class OccupancyService:
    def analyze(self, candidate=None, *, selected_address=""):
        candidate = candidate or CandidateProperty()
        if candidate.provided and not candidate.property_address:
            candidate = replace(candidate, property_address=selected_address)
        costs = calculate_costs(candidate)
        complete = costs.total is not None and candidate.space_size_sqft is not None
        status = "not_provided" if not candidate.provided else "complete" if complete else "partial"
        model = None
        reason = ""
        if not complete:
            reason = "Demo fallback - insufficient lease terms: size, base rent and explicit additional charges are required."
        elif candidate.monthly_occupancy_budget is None:
            reason = "Demo fallback - occupancy budget not supplied."
        else:
            model = calculate_budget_fit(costs.total.monthly, candidate.monthly_occupancy_budget)
        warnings = [EVIDENCE_CAUTION, LEASE_CAUTIONS[candidate.lease_structure]] if candidate.provided else []
        if candidate.asking_rent is not None and costs.base is None:
            warnings.append("Available space is required to calculate a per-SF asking rent; no space size has been inferred.")
        if costs.base is not None and costs.total is None:
            warnings.append(BASE_ONLY_WARNING if candidate.additional_occupancy_rate is None else
                            "Base rent only. Total occupancy cost may be higher; supplied additional charges could not be calculated without available space.")
        if candidate.additional_occupancy_rate is not None and costs.additional is None:
            warnings.append("Available space is required to calculate per-SF additional charges.")
        address_key, selected_key = _address_key(candidate.property_address), _address_key(selected_address)
        if address_key and selected_key and address_key != selected_key:
            warnings.append("Property address differs from the selected analysis location. Verify the candidate site.")
        if costs.total is not None:
            warnings.append("Estimate includes only supplied base and additional charges; utilities, buildout, deposits, fees and future escalations are not inferred.")
            summary = f"Supplied terms yield estimated occupancy cost of {costs.total.label} ({costs.total.annual_label})."
            if candidate.monthly_occupancy_budget is not None:
                ratio = costs.total.monthly / candidate.monthly_occupancy_budget
                summary += f" This is {ratio * 100:.1f}% of the stated {currency(candidate.monthly_occupancy_budget)} monthly occupancy budget."
        elif costs.base is not None:
            summary = f"Estimated base rent is {costs.base.label} ({costs.base.annual_label}). Additional charges were not supplied or cannot be calculated, so total occupancy cost is not known."
        else:
            summary = "Supplied terms are incomplete; no base rent or total occupancy cost has been inferred."
        if model is None and candidate.provided:
            summary += f" {reason}"
        facts = [OccupancyFact("Property / space address", candidate.property_address or "Not supplied", "Context only; analysis location is not changed"),
                 OccupancyFact("Available space", f"{candidate.space_size_sqft:,.2f} SF" if candidate.space_size_sqft is not None else "Not supplied"),
                 OccupancyFact("Asking rent (USD)", candidate.asking_rent.label if candidate.asking_rent else "Not supplied"),
                 OccupancyFact("Lease structure", LEASE_STRUCTURES[candidate.lease_structure]),
                 OccupancyFact("Additional charges (USD)", candidate.additional_occupancy_rate.label if candidate.additional_occupancy_rate else "Not supplied")]
        for label, cost in (("Estimated base rent", costs.base), ("Estimated additional charges", costs.additional), ("Estimated occupancy cost", costs.total)):
            if cost is not None:
                facts.append(OccupancyFact(label, cost.label, cost.annual_label))
        facts.append(OccupancyFact("Monthly occupancy budget (USD)", currency(candidate.monthly_occupancy_budget) if candidate.monthly_occupancy_budget is not None else "Not supplied", "User's own threshold; not market data"))
        if model:
            facts.append(OccupancyFact("Budget utilization", model.utilization_label, model.level))
        return OccupancyAnalysis(status, candidate, costs, model, reason, summary, tuple(warnings), tuple(facts))
