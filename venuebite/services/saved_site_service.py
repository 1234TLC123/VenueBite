"""Completed-analysis snapshots, freshness validation and explicit user saving."""

from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
import re
from uuid import uuid4

from itsdangerous import BadData, URLSafeTimedSerializer

from venuebite.occupancy import MODEL_VERSION as OCCUPANCY_VERSION
from venuebite.providers.site_provider import safe_source_url
from venuebite.services.occupancy_service import FIELD_NAMES, ENUM_DEFAULTS
from venuebite.snapshots import SNAPSHOT_VERSION, COMPETITION_SOURCE_NOTE, SnapshotError, encode_snapshot, validate_snapshot


NAME_LIMIT = 140
SAVE_TOKEN_AGE_SECONDS = 7200
FORM_FIELDS = ("location", "concept", "radius_miles", "selection_token", "latitude", "longitude", *FIELD_NAMES)


class SaveError(ValueError):
    pass


def validated_id(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not re.fullmatch(r"[1-9][0-9]{0,18}", str(value)):
        raise SaveError("Choose a valid saved site.")
    value = int(value)
    if value > 9223372036854775807:
        raise SaveError("Choose a valid saved site.")
    return value


def form_context(values):
    context = {}
    for field in FORM_FIELDS:
        value = values.get(field, ENUM_DEFAULTS.get(field, "3" if field == "radius_miles" else ""))
        context[field] = str(value).strip()
    for field in ("location", "concept"):
        context[field] = " ".join(context[field].split())
    return context


def form_fingerprint(values):
    return sha256(json.dumps(form_context(values), sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _decimal(value):
    return str(value) if value is not None else None


def _explanation_items(items):
    return [{"key": item.key, "label": item.label, "score": item.score, "status": item.status, "explanation": item.explanation} for item in items]


def build_snapshot(report, location, values, *, timestamp=None):
    if location is None or location.display_name != report.data.location:
        raise SaveError("Save requires a completed analysis with a resolved candidate location.")
    if not report.provenance or not report.coverage or not report.explanations:
        raise SaveError("Complete an analysis before saving a site.")
    census = report.demographics.data if report.demographics else None
    tract = census.geography if census else None
    competition, site, occupancy = report.competition, report.site, report.occupancy
    parcel = site.parcel if site and site.available else None
    candidate = occupancy.candidate if occupancy else None
    credit = {item.key: item for item in report.coverage.factors}
    factors = []
    for factor in report.score.factors:
        source = report.provenance[factor.key]
        factors.append({
            "key": factor.key, "label": factor.label, "score": factor.score, "weight": factor.weight,
            "contribution": factor.weighted_points, "status": source.status, "provider": source.provider,
            "source_label": source.label, "model_version": source.model_version, "vintage": source.vintage,
            "geoid": source.geoid, "reason": source.reason, "description": source.description or factor.description,
            "coverage_credit": credit[factor.key].credit, "coverage_points": credit[factor.key].coverage_points,
        })
    snapshot = {
        "snapshot_version": SNAPSHOT_VERSION,
        "location": {"label": "Candidate analysis", "provider": "User supplied", "city": "",
                     "region": tract.state_name if tract else "", "country": "us" if tract else "", "coordinate_status": "not_retained"},
        "analysis": {"id": uuid4().hex, "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
                     "concept": report.data.concept, "radius_miles": int(values.get("radius_miles", 3))},
        "score": {"value": report.score.overall_score, "classification": report.score.classification,
                  "classification_key": report.score.classification_key, "model_version": report.score.model_version,
                  "model_label": report.score.model_label, "raw_sum": report.score.raw_weighted_sum},
        "coverage": {"percent": report.coverage.percent, "label": report.coverage.label, "warning": report.coverage.warning},
        "factors": factors,
        "demographics": {
            "status": census.status if census else "unavailable", "provider": census.provider if census else "U.S. Census Bureau",
            "population": census.population if census else None, "population_moe": census.population_moe if census else None,
            "income": census.median_household_income if census else None, "income_moe": census.income_moe if census else None,
            "geoid": tract.geoid if tract else "", "vintage": census.year if census else None,
            "dataset": census.dataset if census else "", "tract_name": (census.geography_name or tract.name) if tract else "",
            "county": tract.county_name if tract else "", "region": tract.state_name if tract else "",
            "boundary_vintage": tract.geography_vintage if tract else "", "reason": census.reason if census else "Not available in saved analysis.",
        },
        "competition": {
            "status": "available" if competition and competition.available else "unavailable", "provider": "Mapbox",
            "observed_count": len(competition.rows) if competition and competition.available else None,
            "direct_count": competition.direct_count if competition and competition.available else None,
            "nearest_direct_meters": competition.nearest_direct_meters if competition and competition.available else None,
            "nearest_restaurant_meters": competition.nearest_restaurant_meters if competition and competition.available else None,
            "model_version": competition.model.version if competition and competition.model else "",
            "pressure": competition.model.pressure if competition and competition.model else None,
            "level": competition.model.level if competition and competition.model else "",
            "coverage_note": competition.coverage_note if competition else "No observed provider summary available.",
            "matching_note": competition.matching_note if competition else "", "attribution": COMPETITION_SOURCE_NOTE,
            "reason": competition.error if competition else "Not available in saved analysis.",
        },
        "site": {
            "status": site.status if site else "unavailable", "provider": "Regrid", "message": site.message if site else "Not available in saved analysis.",
            "match_quality": site.provenance.match_quality if site and site.provenance else "unavailable",
            "parcel_id": parcel.regrid_id if parcel else "", "parcel_number": parcel.parcel_number if parcel else "",
            "area_acres": parcel.parcel_area_acres if parcel else None, "area_sqft": parcel.parcel_area_sqft if parcel else None,
            "building_area_sqft": parcel.building_area_sqft if parcel else None, "land_use_code": parcel.land_use_code if parcel else "",
            "land_use_description": parcel.land_use_description if parcel else "", "zoning_code": parcel.zoning_code if parcel else "",
            "refresh_date": parcel.provider_refresh_date.isoformat() if parcel and parcel.provider_refresh_date else "",
            "source_url": safe_source_url(parcel.source_url) if parcel else "", "considerations": list(site.considerations) if site else [],
        },
        "occupancy": {
            "provided": bool(candidate and candidate.provided), "status": occupancy.status if occupancy else "not_provided",
            "evidence_status": report.provenance["rent"].status, "model_version": OCCUPANCY_VERSION if occupancy else "",
            "property_address": str(values.get("property_address", "")).strip(), "space_size_sqft": _decimal(candidate.space_size_sqft) if candidate else None,
            "asking_rent": _decimal(candidate.asking_rent.value) if candidate and candidate.asking_rent else None,
            "asking_rent_basis": candidate.asking_rent.basis if candidate and candidate.asking_rent else "",
            "lease_structure": candidate.lease_structure if candidate else "unknown",
            "additional_rate": _decimal(candidate.additional_occupancy_rate.value) if candidate and candidate.additional_occupancy_rate else None,
            "additional_basis": candidate.additional_occupancy_rate.basis if candidate and candidate.additional_occupancy_rate else "",
            "monthly_base": _decimal(occupancy.costs.base.monthly) if occupancy and occupancy.costs.base else None,
            "monthly_additional": _decimal(occupancy.costs.additional.monthly) if occupancy and occupancy.costs.additional else None,
            "monthly_known_total": _decimal(occupancy.costs.total.monthly) if occupancy and occupancy.costs.total else None,
            "monthly_budget": _decimal(candidate.monthly_occupancy_budget) if candidate else None,
            "budget_utilization": _decimal(occupancy.model.ratio * 100) if occupancy and occupancy.model else None,
            "budget_level": occupancy.model.level if occupancy and occupancy.model else "",
            "source_label": candidate.source_label if candidate else "", "source_url": safe_source_url(candidate.source_url) if candidate else "",
            "notes": candidate.notes if candidate else "", "fallback_reason": occupancy.fallback_reason if occupancy else "Commercial rent remains demo.",
            "warnings": list(occupancy.warnings) if occupancy else [],
        },
        "explanations": {"summary": report.explanations.summary, "assumptions": report.explanations.assumptions,
                         "quality_notes": list(report.explanations.quality_notes), "strengths": _explanation_items(report.explanations.strengths),
                         "risks": _explanation_items(report.explanations.risks)},
    }
    validate_snapshot(snapshot)
    return snapshot


class SavedSiteService:
    def __init__(self, repository, secret_key, *, sensitive_values=()):
        self.repository = repository
        self.serializer = URLSafeTimedSerializer(secret_key, salt="venuebite-completed-snapshot-v1")
        self.sensitive_values = tuple(value for value in sensitive_values if isinstance(value, str) and value)

    def _check_sensitive(self, text):
        if any(value in text for value in self.sensitive_values) or re.search(r"\b(?:pk|sk)\.[A-Za-z0-9._-]{12,}", text):
            raise SaveError("Remove credential-like content before saving this analysis.")

    def prepare(self, report, location, values):
        snapshot = build_snapshot(report, location, values)
        self._check_sensitive(encode_snapshot(snapshot))
        return self.serializer.dumps({"snapshot": snapshot, "fingerprint": form_fingerprint(values)})

    def save(self, token, display_name, current_values, *, location_label):
        if not isinstance(display_name, str):
            raise SaveError("Enter a saved site name.")
        name = display_name.strip()
        if not name:
            raise SaveError("Enter a saved site name.")
        if len(name) > NAME_LIMIT:
            raise SaveError(f"Keep the saved site name to {NAME_LIMIT} characters or fewer.")
        if any(ord(char) < 32 or ord(char) == 127 for char in name):
            raise SaveError("Remove unsupported control characters from the saved site name.")
        self._check_sensitive(name)
        if not isinstance(location_label, str) or not location_label.strip() or len(location_label.strip()) > 200:
            raise SaveError("Enter your own location label, up to 200 characters.")
        if any(ord(char) < 32 or ord(char) == 127 for char in location_label):
            raise SaveError("Remove unsupported control characters from the location label.")
        self._check_sensitive(location_label)
        try:
            if not isinstance(token, str) or len(token) > 12000:
                raise SaveError("Unable to save stale analysis. Analyze the current inputs again.")
            payload = self.serializer.loads(token, max_age=SAVE_TOKEN_AGE_SECONDS)
            if not isinstance(payload, dict) or set(payload) != {"snapshot", "fingerprint"}:
                raise SnapshotError()
            if not isinstance(payload["fingerprint"], str) or not hmac.compare_digest(payload["fingerprint"], form_fingerprint(current_values)):
                raise SaveError("Unable to save stale analysis. Analyze the current inputs again.")
            snapshot = validate_snapshot(payload["snapshot"])
        except (BadData, SnapshotError, TypeError, ValueError) as error:
            if isinstance(error, SaveError):
                raise
            raise SaveError("Unable to save stale analysis. Analyze the current inputs again.") from None
        snapshot["location"]["label"] = location_label.strip()
        self._check_sensitive(encode_snapshot(snapshot))
        return self.repository.insert(name, snapshot)

    def list(self):
        return self.repository.list()

    def get(self, site_id):
        return self.repository.get(validated_id(site_id))

    def delete(self, site_id):
        return self.repository.delete(validated_id(site_id))

    def prefill(self, site):
        snapshot, occupancy = site.snapshot, site.snapshot["occupancy"]
        location = snapshot["location"]
        values = {"location": location["label"], "concept": snapshot["analysis"]["concept"], "radius_miles": str(snapshot["analysis"]["radius_miles"]),
                  "occupancy_provided": occupancy["provided"]}
        for field, saved in (("property_address", "property_address"), ("space_size_sqft", "space_size_sqft"), ("asking_rent", "asking_rent"),
                             ("asking_rent_basis", "asking_rent_basis"), ("lease_structure", "lease_structure"),
                             ("additional_occupancy_rate", "additional_rate"), ("additional_occupancy_basis", "additional_basis"),
                             ("monthly_occupancy_budget", "monthly_budget"), ("source_label", "source_label"), ("source_url", "source_url"), ("occupancy_notes", "notes")):
            values[field] = occupancy[saved] if occupancy[saved] not in (None, "") else ENUM_DEFAULTS.get(field, "")
        return values
