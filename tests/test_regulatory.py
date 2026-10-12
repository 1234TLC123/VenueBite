from dataclasses import replace
import json

import pytest
from werkzeug.datastructures import MultiDict

from venuebite.providers.zoning_provider import ZoningLookup, ZoningRecord
from venuebite.regulatory import PROJECT_FIELDS, PROJECT_TYPES, PROJECT_QUESTIONS, SOURCE_URLS, normalize_project, official_url, validate_regulatory
from venuebite.services.regulatory_service import RegulatoryService
from test_site_intelligence import LOCATION


STAMP = "2026-10-08T12:00:00+00:00"


class Zoning:
    enabled = True
    def __init__(self, result=None):
        self.result = result or ZoningLookup("identified", STAMP, "City and County of Denver", "08031", ZoningRecord("D-CV", code_family=2010))
        self.calls = []
    def lookup(self, latitude, longitude):
        self.calls.append((latitude, longitude))
        if isinstance(self.result, Exception): raise self.result
        return self.result


def review(result=None, values=None):
    return RegulatoryService(Zoning(result)).analyze(LOCATION, "Indian Restaurant", values)


@pytest.mark.parametrize("version,framework", [(2010, "Denver Zoning Code"), (1959, "Former Chapter 59"), (2020, "Unknown - official framework confirmation required"), (None, "Unknown - official framework confirmation required")])
def test_code_framework_is_not_legal_permission(version, framework):
    result = review(ZoningLookup("identified", STAMP, "City and County of Denver", "08031", ZoningRecord("PUD-123" if version == 1959 else "D-CV", code_family=version)))
    assert result["framework"] == framework and result["use_status"] == "Restaurant-use permission not yet verified"
    assert result["effective_date"] == "" and result["status"] == "use_review_required"
    if version == 1959: assert "PUD" in " ".join(result["unresolved"])
    assert result["evidence_status"] == "verified_official_fact"


@pytest.mark.parametrize("status", ["unsupported", "ambiguous", "no_match", "unavailable", "unknown"])
def test_missing_district_never_means_negative_permission(status):
    result = review(ZoningLookup(status, STAMP))
    assert result["status"] == status and result["district"] == "" and result["framework"] == "Unknown"
    assert result["checklist"] == [] and result["use_status"] == "Restaurant-use permission not yet verified"
    assert "bad zoning" not in json.dumps(result).lower()
    assert result["agency"] == ""


@pytest.mark.parametrize("country", ["fr", "ca", "mx"])
def test_unsupported_country_does_not_contact_denver(country):
    provider = Zoning()
    result = RegulatoryService(provider).analyze(replace(LOCATION, country_code=country), "Cafe")
    assert result["status"] == "unsupported" and provider.calls == []


def test_location_name_is_not_a_jurisdiction_selector():
    provider = Zoning(ZoningLookup("unsupported", STAMP, "Arapahoe County"))
    result = RegulatoryService(provider).analyze(replace(LOCATION, display_name="Denver mailing address"), "Indian")
    assert result["status"] == "unsupported" and provider.calls == [(LOCATION.latitude, LOCATION.longitude)]


def test_unresolved_location_is_not_a_fabricated_live_lookup():
    provider = Zoning()
    assert RegulatoryService(provider).analyze(None, "Cafe")["status"] == "unknown"
    assert not provider.calls


@pytest.mark.parametrize("failure", [RuntimeError("synthetic-private"), None, {"raw": "synthetic-private"}, ZoningLookup("identified", record=object())])
def test_unexpected_provider_errors_do_not_break_core_analysis(failure, caplog):
    provider = Zoning()
    provider.result = failure
    result = RegulatoryService(provider).analyze(LOCATION, "Indian")
    assert result["status"] == "unavailable"
    assert "synthetic-private" not in json.dumps(result) + caplog.text


@pytest.mark.parametrize("field", PROJECT_FIELDS)
def test_project_option_validation_and_duplicate_rejection(field):
    values, errors = normalize_project(MultiDict([(field, "yes"), (field, "no")]))
    assert field in errors and values[field] == "unknown"
    values, errors = normalize_project({field: "<script>"})
    assert field in errors and values[field] == "unknown"


@pytest.mark.parametrize("kind", list(PROJECT_TYPES))
def test_concept_and_project_type_remain_separate_from_statutory_use(kind):
    result = review(values={"regulatory_type": kind})
    assert result["project"]["type"] == kind and result["project_concept"] == "Indian Restaurant"
    assert result["use_status"] == "Restaurant-use permission not yet verified"


@pytest.mark.parametrize("answer", ["yes", "no", "unknown"])
def test_project_specific_checklist_and_deterministic_next_steps(answer):
    values = {field: answer for field in PROJECT_FIELDS if field != "regulatory_type"}
    first, second = review(values=values), review(values=values)
    assert first == second
    assert len(first["checklist"]) == 16 and all(official_url(item["source_url"]) for item in first["checklist"])
    alcohol = next(item for item in first["checklist"] if item["topic"] == "Alcohol licensing")
    assert alcohol["status"] == {"yes": "Requires official confirmation", "no": "Not proposed - user supplied; not an exemption", "unknown": "Not evaluated - project details missing"}[answer]
    assert alcohol["evidence"] == {"yes": "interpretation_requires_confirmation", "no": "user_supplied", "unknown": "unknown"}[answer]
    assert ("Confirm alcohol service requirements" in " ".join(first["next_steps"])) == (answer == "yes")
    assert first["retention_note"].startswith("Normalized by VenueBite")


def test_source_traceability_and_unknown_fields():
    result = review()
    assert result["retrieved_at"] == STAMP
    assert all(item["agency"] and item["type"] and official_url(item["url"]) for item in result["sources"])
    assert all(item["source_url"] for item in result["findings"])
    assert result["overlay"] == result["waivers"] == result["conditions"] == ""
    assert "not legally evaluated" in " ".join(result["unresolved"])
    assert "approval probability" not in json.dumps(result).lower()


@pytest.mark.parametrize("url", ["javascript:alert(1)", "http://denvergov.org/", "https://denvergov.org.evil.example/", "https://evil.example/",
    "https://denvergov.org@evil.example/", "https://denvergov.org/private?token=secret", "https://services1.arcgis.com/other-org/", "/../file", None])
def test_only_exact_reviewed_official_urls_are_renderable(url):
    assert official_url(url) == ""


@pytest.mark.parametrize("url", list(SOURCE_URLS))
def test_official_sources_are_https_and_allowlisted(url):
    assert official_url(url) == url


@pytest.mark.parametrize("mutate", [lambda r: r.update(coordinates=[1,2]), lambda r: r.update(regulatory_score=99),
    lambda r: r.update(use_status="Restaurant approved"), lambda r: r.update(status="approved"), lambda r: r["project"].update(alcohol=True),
    lambda r: r["sources"][0].update(url="https://evil.example/"), lambda r: r.update(retrieved_at="2026-01-01"),
    lambda r: r["checklist"][0].update(raw_payload={}), lambda r: r["findings"][0].update(evidence="probably"),
    lambda r: r.update(missing=[None])])
def test_persisted_regulatory_whitelist_rejects_unsafe_data(mutate):
    value = review()
    mutate(value)
    with pytest.raises(ValueError): validate_regulatory(value)
