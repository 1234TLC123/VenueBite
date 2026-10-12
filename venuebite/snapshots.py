"""Versioned normalized facts, not raw provider responses or Python pickles."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from math import isfinite
import re

from venuebite.providers.site_provider import safe_source_url
from venuebite.regulatory import validate_regulatory


SNAPSHOT_VERSION = 2
REGULATORY_SNAPSHOT_VERSION = 3
COMPETITION_SOURCE_NOTE = "Live analysis source: Mapbox Search Box. Business records and geography are not retained."
MAX_SNAPSHOT_BYTES = 64 * 1024
FACTOR_KEYS = ("population", "income", "rent", "competition")
EVIDENCE_STATUSES = frozenset({"real", "partial", "demo", "fallback", "unavailable"})
SECTIONS = {
    "location": ("label", "provider", "city", "region", "country", "coordinate_status"),
    "analysis": ("id", "timestamp", "concept", "radius_miles"),
    "score": ("value", "classification", "classification_key", "model_version", "model_label", "raw_sum"),
    "coverage": ("percent", "label", "warning"),
    "demographics": ("status", "provider", "population", "population_moe", "income", "income_moe", "geoid", "vintage", "dataset", "tract_name", "county", "region", "boundary_vintage", "reason"),
    "competition": ("status", "provider", "observed_count", "direct_count", "nearest_direct_meters", "nearest_restaurant_meters", "model_version", "pressure", "level", "coverage_note", "matching_note", "attribution", "reason"),
    "site": ("status", "provider", "message", "match_quality", "parcel_id", "parcel_number", "area_acres", "area_sqft", "building_area_sqft", "land_use_code", "land_use_description", "zoning_code", "refresh_date", "source_url", "considerations"),
    "occupancy": ("provided", "status", "evidence_status", "model_version", "property_address", "space_size_sqft", "asking_rent", "asking_rent_basis", "lease_structure", "additional_rate", "additional_basis", "monthly_base", "monthly_additional", "monthly_known_total", "monthly_budget", "budget_utilization", "budget_level", "source_label", "source_url", "notes", "fallback_reason", "warnings"),
    "explanations": ("summary", "assumptions", "quality_notes", "strengths", "risks"),
}
FACTOR_FIELDS = {"key", "label", "score", "weight", "contribution", "status", "provider", "source_label", "model_version", "vintage", "geoid", "reason", "description", "coverage_credit", "coverage_points"}


class SnapshotError(ValueError):
    def __init__(self, message="This saved snapshot is unreadable or uses an unsupported version."):
        super().__init__(message)


def utc_timestamp(value):
    try:
        timestamp = datetime.fromisoformat(value)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError
        return timestamp
    except (TypeError, ValueError):
        raise SnapshotError() from None


def number(value, *, minimum=0, maximum=None, optional=False):
    if value is None and optional:
        return
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise SnapshotError()
    if not isfinite(value) or value < minimum or maximum is not None and value > maximum:
        raise SnapshotError()


def _decimal(value):
    if value is None:
        return
    try:
        if not isinstance(value, str) or len(value) > 80:
            raise ValueError
        amount = Decimal(value)
        if not amount.is_finite() or amount < 0:
            raise ValueError
    except (ValueError, InvalidOperation):
        raise SnapshotError() from None


def _safe_tree(value, depth=0):
    if depth > 8:
        raise SnapshotError()
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise SnapshotError()
        for item in value.values():
            _safe_tree(item, depth + 1)
    elif isinstance(value, list):
        if len(value) > 50:
            raise SnapshotError()
        for item in value:
            _safe_tree(item, depth + 1)
    elif isinstance(value, str):
        if len(value) > 5000 or any(ord(char) < 32 and char not in "\n\r\t" for char in value):
            raise SnapshotError()
    elif value is not None and not isinstance(value, (bool, int, float)):
        raise SnapshotError()
    elif isinstance(value, (int, float)) and not isfinite(value):
        raise SnapshotError()


def _validate_snapshot(snapshot):
    if not isinstance(snapshot, dict):
        raise SnapshotError()
    version = snapshot.get("snapshot_version")
    if type(version) is not int or version not in (SNAPSHOT_VERSION, REGULATORY_SNAPSHOT_VERSION):
        raise SnapshotError()
    extra = {"regulatory"} if version == REGULATORY_SNAPSHOT_VERSION else set()
    if set(snapshot) != {"snapshot_version", "factors", *SECTIONS, *extra}:
        raise SnapshotError()
    if extra:
        validate_regulatory(snapshot["regulatory"])
    for section, fields in SECTIONS.items():
        if not isinstance(snapshot[section], dict) or set(snapshot[section]) != set(fields):
            raise SnapshotError()
    numeric_fields = {
        "analysis": {"radius_miles"},
        "score": {"value", "raw_sum"}, "coverage": {"percent"},
        "demographics": {"population", "population_moe", "income", "income_moe", "vintage"},
        "competition": {"observed_count", "direct_count", "nearest_direct_meters", "nearest_restaurant_meters", "pressure"},
        "site": {"area_acres", "area_sqft", "building_area_sqft"}, "occupancy": {"provided"},
    }
    list_fields = {"site": {"considerations"}, "occupancy": {"warnings"}, "explanations": {"quality_notes", "strengths", "risks"}}
    optional_decimals = {"space_size_sqft", "asking_rent", "additional_rate", "monthly_base", "monthly_additional", "monthly_known_total", "monthly_budget", "budget_utilization"}
    for section, fields in SECTIONS.items():
        for key in fields:
            value = snapshot[section][key]
            if key in numeric_fields.get(section, set()):
                continue
            if section == "occupancy" and key in optional_decimals:
                _decimal(value)
            elif key in list_fields.get(section, set()):
                if not isinstance(value, list) or key not in {"strengths", "risks"} and any(not isinstance(item, str) for item in value):
                    raise SnapshotError()
            elif not isinstance(value, str):
                raise SnapshotError()
    _safe_tree(snapshot)
    location, analysis, score, coverage = (snapshot[key] for key in ("location", "analysis", "score", "coverage"))
    for value, limit in ((location["label"], 200), (analysis["concept"], 120), (score["model_version"], 80)):
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise SnapshotError()
    if not re.fullmatch(r"[a-f0-9]{32}", str(analysis["id"])):
        raise SnapshotError()
    utc_timestamp(analysis["timestamp"])
    if location["provider"] != "User supplied" or location["coordinate_status"] != "not_retained":
        raise SnapshotError()
    if type(analysis["radius_miles"]) is not int or analysis["radius_miles"] not in (1, 3, 5):
        raise SnapshotError()
    number(score["value"], maximum=100)
    number(score["raw_sum"], maximum=100)
    number(coverage["percent"], maximum=100)
    if score["classification_key"] not in {"strong", "promising", "mixed", "challenging"}:
        raise SnapshotError()
    factors = snapshot["factors"]
    if not isinstance(factors, list) or len(factors) != 4 or any(not isinstance(f, dict) for f in factors) or [f["key"] for f in factors] != list(FACTOR_KEYS):
        raise SnapshotError()
    for factor in factors:
        if set(factor) != FACTOR_FIELDS or factor["status"] not in EVIDENCE_STATUSES:
            raise SnapshotError()
        for key, maximum in (("score", 100), ("weight", 1), ("contribution", 100), ("coverage_credit", 1), ("coverage_points", 100)):
            number(factor[key], maximum=maximum)
        for key in FACTOR_FIELDS - {"score", "weight", "contribution", "coverage_credit", "coverage_points", "vintage"}:
            if not isinstance(factor[key], str):
                raise SnapshotError()
        number(factor["vintage"], optional=True)
    demo = snapshot["demographics"]
    if demo["status"] not in {"available", "partial", "unavailable"}:
        raise SnapshotError()
    for key in ("population", "population_moe", "income", "income_moe", "vintage"):
        number(demo[key], optional=True)
    if demo["geoid"] and not re.fullmatch(r"[0-9]{11}", demo["geoid"]):
        raise SnapshotError()
    competition, site, occupancy = (snapshot[key] for key in ("competition", "site", "occupancy"))
    if competition["attribution"] != COMPETITION_SOURCE_NOTE:
        raise SnapshotError()
    if competition["status"] not in {"available", "unavailable"} or site["status"] not in {"exact", "nearby", "not_found", "ambiguous", "restricted", "unavailable"}:
        raise SnapshotError()
    for key in ("observed_count", "direct_count", "nearest_direct_meters", "nearest_restaurant_meters", "pressure"):
        number(competition[key], optional=True)
    for key in ("area_acres", "area_sqft", "building_area_sqft"):
        number(site[key], optional=True)
    if occupancy["status"] not in {"not_provided", "partial", "complete"} or occupancy["evidence_status"] not in EVIDENCE_STATUSES or type(occupancy["provided"]) is not bool:
        raise SnapshotError()
    for key in ("space_size_sqft", "asking_rent", "additional_rate", "monthly_base", "monthly_additional", "monthly_known_total", "monthly_budget", "budget_utilization"):
        _decimal(occupancy[key])
    for section in (site, occupancy):
        url = section["source_url"]
        if url and safe_source_url(url) != url:
            raise SnapshotError()
    for key in ("strengths", "risks"):
        items = snapshot["explanations"][key]
        if not isinstance(items, list):
            raise SnapshotError()
        for item in items:
            if not isinstance(item, dict) or set(item) != {"key", "label", "score", "status", "explanation"} or item["status"] not in EVIDENCE_STATUSES:
                raise SnapshotError()
            number(item["score"], maximum=100)
            if any(not isinstance(item[key], str) for key in ("key", "label", "status", "explanation")):
                raise SnapshotError()
    return snapshot


def validate_snapshot(snapshot):
    try:
        return _validate_snapshot(snapshot)
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        raise SnapshotError() from None


def encode_snapshot(snapshot):
    validate_snapshot(snapshot)
    value = json.dumps(snapshot, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    if len(value.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
        raise SnapshotError()
    return value


def parse_snapshot_json(value):
    try:
        if not isinstance(value, str) or len(value.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
            raise SnapshotError()
        def reject_constant(value):
            raise SnapshotError()
        def unique_object(pairs):
            result = {}
            for key, item in pairs:
                if key in result:
                    raise SnapshotError()
                result[key] = item
            return result
        return json.loads(value, parse_constant=reject_constant, object_pairs_hook=unique_object)
    except (ValueError, TypeError, RecursionError):
        raise SnapshotError() from None


def decode_snapshot(value):
    return validate_snapshot(parse_snapshot_json(value))


def migrate_source_note(value):
    try:
        snapshot = parse_snapshot_json(value)
        snapshot["competition"]["attribution"] = COMPETITION_SOURCE_NOTE
        return validate_snapshot(snapshot)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise SnapshotError() from None


def migrate_legacy_snapshot(value):
    """Remove prototype Search Box geography without recalculating model outputs."""
    try:
        snapshot = parse_snapshot_json(value)
        old = snapshot["location"]
        if snapshot["snapshot_version"] != 1 or set(old) != {"label", "latitude", "longitude", "provider", "place_type", "city", "region", "country"}:
            raise SnapshotError()
        if not isinstance(old["provider"], str) or not isinstance(old["label"], str):
            raise SnapshotError()
        label = "Saved candidate" if old["provider"].casefold() == "mapbox" else old["label"]
        if snapshot["occupancy"]["property_address"] == old["label"]:
            snapshot["occupancy"]["property_address"] = ""
        snapshot["location"] = {"label": label, "provider": "User supplied", "city": "", "region": snapshot["demographics"]["region"],
                                "country": "us" if snapshot["demographics"]["geoid"] else "", "coordinate_status": "not_retained"}
        snapshot["snapshot_version"] = SNAPSHOT_VERSION
        snapshot["competition"]["attribution"] = COMPETITION_SOURCE_NOTE
        return validate_snapshot(snapshot)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise SnapshotError() from None


@dataclass(frozen=True)
class SavedSite:
    id: int
    display_name: str
    created_at: str
    snapshot: dict


@dataclass(frozen=True)
class SavedSiteList:
    sites: tuple[SavedSite, ...]
    unreadable_count: int = 0
