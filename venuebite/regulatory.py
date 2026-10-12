"""Regulatory evidence and user project facts are independent of scoring."""

from datetime import date, datetime
from urllib.parse import urlsplit

from venuebite.providers.denver_zoning_provider import BOUNDARY_LAYER, ZONING_LAYER


MODEL_VERSION = "regulatory-review-v1"
GOV_ROOT = "https://denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/"
CPD = GOV_ROOT + "Community-Planning-and-Development/"
CODE_URL = CPD + "Denver-Zoning-Code"
RESTAURANT_URL = CPD + "Plan-Review-Permits-and-Inspections/Commercial-and-Multifamily-Projects/Restaurants-and-Commercial-Kitchen-Permits"
LICENSE_URL = GOV_ROOT + "Business-Licensing"
BUILDING_URL = "https://www.denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Community-Planning-and-Development/Building-Codes-Policies-and-Guides"
CATALOG_URL = "https://opendata-geospatialdenver.hub.arcgis.com/"
CATALOG_TERMS = "https://www.arcgis.com/sharing/rest/content/items/08ac95d2733c45059ec5a3c76faa770d/data?f=json"
PROJECT_TYPES = {"unknown": "Not specified", "full_service": "Full-service restaurant", "quick_service": "Quick-service restaurant",
                 "cafe": "Cafe / coffee shop", "takeout": "Takeout-focused restaurant", "commercial_kitchen": "Commercial kitchen"}
PROJECT_QUESTIONS = {"alcohol": "Alcohol service", "outdoor_seating": "Outdoor seating / patio", "drive_through": "Drive-through",
                     "renovation": "Major interior renovation", "change_of_use": "Change of use / occupancy"}
PROJECT_FIELDS = ("regulatory_type", *("regulatory_" + key for key in PROJECT_QUESTIONS))
ANSWERS = {"unknown": "Not specified", "yes": "Proposed", "no": "Not proposed"}
STATUS_LABELS = {"use_review_required": "Official use review required", "unsupported": "Unsupported jurisdiction",
                 "unavailable": "Provider unavailable", "ambiguous": "Ambiguous point match", "no_match": "No zoning polygon returned",
                 "unknown": "No resolved regulatory lookup"}
EVIDENCE_LABELS = {"verified_official_fact": "Verified official fact", "user_supplied": "User supplied",
                   "interpretation_requires_confirmation": "Needs official confirmation", "general_guidance": "Government guidance",
                   "unknown": "Unknown", "unsupported": "Unsupported"}
SOURCE_URLS = frozenset((BOUNDARY_LAYER, ZONING_LAYER, CODE_URL, RESTAURANT_URL, LICENSE_URL, BUILDING_URL, CATALOG_URL, CATALOG_TERMS))


def _timestamp(value):
    if value:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("Invalid regulatory timestamp")


def _date(value):
    if value:
        date.fromisoformat(value)


def official_url(value):
    if not isinstance(value, str) or value not in SOURCE_URLS:
        return ""
    url = urlsplit(value)
    return value if url.scheme == "https" and not url.username and not url.password else ""


def normalize_project(form):
    values, errors = {}, {}
    for field in PROJECT_FIELDS:
        options = PROJECT_TYPES if field == "regulatory_type" else ANSWERS
        value = form.get(field, "unknown")
        if value not in options or hasattr(form, "getlist") and len(form.getlist(field)) > 1:
            errors[field] = "Choose one supported project option."
            value = "unknown"
        values[field] = value
    return values, errors


def project_profile(values):
    return {field.removeprefix("regulatory_"): values.get(field, "unknown") for field in PROJECT_FIELDS}


REGULATORY_FIELDS = {"version", "status", "status_label", "message", "jurisdiction", "jurisdiction_id", "agency", "project_concept", "project",
                     "district", "description", "code_family", "framework", "neighborhood_context", "district_group", "use_form", "district_type",
                     "overlay", "waivers", "conditions", "pud_number", "use_status", "retrieved_at", "effective_date", "source_version",
                     "evidence_status", "findings", "unresolved", "missing", "checklist", "next_steps", "sources", "retention_note", "limitations"}


def validate_regulatory(value):
    """Strict persisted whitelist, with no geometry, arbitrary source links or legal approval state."""
    if not isinstance(value, dict) or set(value) != REGULATORY_FIELDS:
        raise ValueError("Invalid regulatory snapshot")
    if value["version"] != MODEL_VERSION or value["status"] not in STATUS_LABELS or value["status_label"] != STATUS_LABELS[value["status"]]:
        raise ValueError("Invalid regulatory status")
    if value["use_status"] != "Restaurant-use permission not yet verified" or value["evidence_status"] not in EVIDENCE_LABELS:
        raise ValueError("Unsupported regulatory conclusion")
    project = value["project"]
    if not isinstance(project, dict) or set(project) != {"type", *PROJECT_QUESTIONS}:
        raise ValueError("Invalid project profile")
    if project["type"] not in PROJECT_TYPES or any(project[key] not in ANSWERS for key in PROJECT_QUESTIONS):
        raise ValueError("Invalid project option")
    nested = {"project", "findings", "unresolved", "missing", "checklist", "next_steps", "sources"}
    if any(not isinstance(value[key], str) or len(value[key]) > 2000 for key in REGULATORY_FIELDS - nested):
        raise ValueError("Invalid regulatory field")
    _timestamp(value["retrieved_at"])
    _date(value["effective_date"])
    for key in ("unresolved", "missing", "next_steps"):
        if not isinstance(value[key], list) or len(value[key]) > 25 or any(not isinstance(v, str) or len(v) > 500 for v in value[key]):
            raise ValueError("Invalid regulatory list")
    for key, fields in (("findings", {"text", "evidence", "source_url"}), ("checklist", {"topic", "status", "evidence", "source_url"}),
                        ("sources", {"title", "url", "agency", "type", "retrieved_at", "verified_at", "version", "effective_date"})):
        items = value[key]
        if not isinstance(items, list) or len(items) > 25:
            raise ValueError("Invalid regulatory evidence")
        for item in items:
            if not isinstance(item, dict) or set(item) != fields or any(not isinstance(v, str) or len(v) > 1000 for v in item.values()):
                raise ValueError("Invalid regulatory evidence")
            if official_url(item["url" if key == "sources" else "source_url"]) == "":
                raise ValueError("Invalid official source URL")
            if key != "sources" and item["evidence"] not in EVIDENCE_LABELS:
                raise ValueError("Invalid regulatory evidence state")
            if key == "sources":
                _timestamp(item["retrieved_at"])
                _date(item["verified_at"])
                _date(item["effective_date"])
    return value
