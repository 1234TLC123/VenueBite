"""Commercial Occupancy Model v1: supplied USD costs and personal budget fit."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from types import MappingProxyType


MODEL_VERSION = "commercial-occupancy-v1"
MODEL_LABEL = "Commercial Occupancy Model v1"
MODEL_DESCRIPTION = "Fit relative to the user's stated monthly USD occupancy budget, not market rent or profitability."
RENT_BASES = MappingProxyType({
    "per_sqft_per_year": "USD / SF / year",
    "per_sqft_per_month": "USD / SF / month",
    "total_monthly": "USD total / month",
    "total_annual": "USD total / year",
})
LEASE_STRUCTURES = MappingProxyType({
    "unknown": "Unknown / Not stated", "nnn": "NNN", "gross": "Gross", "modified_gross": "Modified Gross",
})
# Linear interpolation; <=70% caps at 100, >=150% floors at 0.
BUDGET_ANCHORS = tuple((Decimal(ratio), Decimal(score)) for ratio, score in (
    ("0.70", "100"), ("0.85", "85"), ("1.00", "55"), ("1.15", "25"), ("1.50", "0"),
))
BUDGET_BANDS = ((Decimal("0.70"), "Well within stated budget"),
                (Decimal("0.85"), "Within stated budget"),
                (Decimal("1.00"), "Near stated budget"),
                (Decimal("1.15"), "Above stated budget"))


def currency(value):
    return f"${value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"


@dataclass(frozen=True)
class OccupancyRate:
    value: Decimal
    basis: str

    @property
    def label(self):
        return f"{currency(self.value)} {RENT_BASES[self.basis].removeprefix('USD ')}"


@dataclass(frozen=True)
class CandidateProperty:
    source_type: str = "user_supplied"
    source_label: str = "Commercial listing / user entry"
    source_url: str = ""
    property_address: str = ""
    space_size_sqft: Decimal | None = None
    asking_rent: OccupancyRate | None = None
    lease_structure: str = "unknown"
    additional_occupancy_rate: OccupancyRate | None = None
    monthly_occupancy_budget: Decimal | None = None
    notes: str = ""
    provided: bool = False


@dataclass(frozen=True)
class PeriodCost:
    monthly: Decimal
    annual: Decimal

    @property
    def label(self):
        return f"{currency(self.monthly)} / month"

    @property
    def annual_label(self):
        return f"{currency(self.annual)} / year"


@dataclass(frozen=True)
class OccupancyCosts:
    base: PeriodCost | None
    additional: PeriodCost | None
    total: PeriodCost | None
    completeness: str


@dataclass(frozen=True)
class BudgetFit:
    ratio: Decimal
    score: float
    level: str
    version: str = MODEL_VERSION

    @property
    def utilization_label(self):
        return f"{self.ratio * 100:.1f}%"

    @property
    def above_budget(self):
        return self.ratio > 1


def normalize_cost(rate, space_size_sqft):
    if rate is None:
        return None
    if rate.basis not in RENT_BASES:
        raise ValueError("Unsupported occupancy cost basis.")
    if not rate.value.is_finite() or rate.value < 0:
        raise ValueError("Occupancy costs must be finite and nonnegative.")
    amount = rate.value
    if rate.basis.startswith("per_sqft"):
        if space_size_sqft is None:
            return None
        if not space_size_sqft.is_finite() or space_size_sqft <= 0:
            raise ValueError("Space size must be finite and positive.")
        amount *= space_size_sqft
    if rate.basis in {"per_sqft_per_year", "total_annual"}:
        return PeriodCost(amount / 12, amount)
    return PeriodCost(amount, amount * 12)


def calculate_costs(candidate):
    base = normalize_cost(candidate.asking_rent, candidate.space_size_sqft)
    additional = normalize_cost(candidate.additional_occupancy_rate, candidate.space_size_sqft)
    total = None
    if base is not None and additional is not None:
        total = PeriodCost(base.monthly + additional.monthly, base.annual + additional.annual)
    return OccupancyCosts(base, additional, total,
                          "base_plus_additional" if total else "base_only" if base else "unknown_expenses")


def calculate_budget_fit(monthly_cost, monthly_budget):
    if any(not isinstance(value, Decimal) or not value.is_finite() for value in (monthly_cost, monthly_budget)):
        raise ValueError("Cost and budget must be finite Decimal values.")
    if monthly_cost < 0 or monthly_budget <= 0:
        raise ValueError("Cost must be nonnegative and budget must be positive.")
    ratio = monthly_cost / monthly_budget
    if ratio <= BUDGET_ANCHORS[0][0]:
        score = Decimal(100)
    elif ratio >= BUDGET_ANCHORS[-1][0]:
        score = Decimal(0)
    else:
        for (low, low_score), (high, high_score) in zip(BUDGET_ANCHORS, BUDGET_ANCHORS[1:]):
            if ratio <= high:
                score = low_score + (ratio - low) / (high - low) * (high_score - low_score)
                break
    level = next((label for maximum, label in BUDGET_BANDS if ratio <= maximum), "Materially above stated budget")
    return BudgetFit(ratio, float(score.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)), level)
