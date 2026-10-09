from dataclasses import replace
from math import fsum
from html.parser import HTMLParser
from pathlib import Path

import pytest
from werkzeug.datastructures import MultiDict

from venuebite import create_app
from venuebite.providers.demographic_provider import CensusError
from venuebite.providers.poi_provider import PoiError
from venuebite.providers.site_provider import SiteError
from venuebite.scoring import WEIGHTS
from venuebite.services.analysis_service import AnalysisService
from venuebite.services.occupancy_service import FIELD_NAMES
from test_demographic_integration import Census, CensusGeography, Geography, Pois
from test_occupancy import TERMS, candidate
from test_site_intelligence import LOCATION, PARCEL, Parcels


@pytest.fixture
def workspace():
    geo, tract, census, pois, parcels = Geography(), CensusGeography(), Census(), Pois(), Parcels()
    geo.location = LOCATION
    app = create_app({"TESTING": True}, location_provider=geo, poi_provider=pois, census_geo_provider=tract,
                     demographic_provider=census, site_provider=parcels)
    return app, app.test_client(), geo, tract, census, pois, parcels


def analyze(workspace, property_terms=None, location=LOCATION):
    app = workspace[0]
    return AnalysisService(app.extensions["location_data_provider"], app.extensions["competition_service"],
        app.extensions["demographic_service"], app.extensions["site_intelligence_service"]).analyze(
        location.display_name, "Indian", geographic_location=location, candidate_property=property_terms)


def submit(workspace, **terms):
    app, client = workspace[:2]
    return client.post("/", data={"location": LOCATION.display_name, "concept": "Indian", "radius_miles": "3",
                                 "selection_token": app.extensions["geography_service"].sign(LOCATION), **terms})


def test_no_occupancy_preserves_entire_baseline_score_provenance_and_coverage(workspace):
    report = analyze(workspace)
    assert report.occupancy is None and report.provenance["rent"].status == "demo"
    assert report.data.factor_scores["rent"] == 55 and report.coverage.percent == 80


def test_supported_rent_only_changes_its_own_contribution_not_other_models_or_site(workspace):
    workspace[-1].results = [(PARCEL,), (PARCEL,)]
    before, after = analyze(workspace), analyze(workspace, candidate(source_label="Broker quote"))
    assert dict(WEIGHTS) == {"population": .30, "income": .30, "rent": .20, "competition": .20}
    assert after.score.model_version == before.score.model_version == "2.0"
    for key in ("population", "income", "competition"):
        assert after.data.factor_scores[key] == before.data.factor_scores[key]
        assert after.provenance[key] == before.provenance[key]
        assert next(f for f in before.score.factors if f.key == key) == next(f for f in after.score.factors if f.key == key)
    assert after.demographics == before.demographics and after.competition == before.competition and after.site == before.site
    assert after.data.factor_scores["rent"] == 66 and before.data.factor_scores["rent"] == 55
    assert after.score.raw_weighted_sum == pytest.approx(before.score.raw_weighted_sum + 2.2)
    assert after.score.raw_weighted_sum == fsum(f.weighted_points for f in after.score.factors)
    assert after.score.overall_score == round(after.score.raw_weighted_sum, 1)
    assert before.coverage.percent == 80 and after.coverage.percent == 90
    source = after.provenance["rent"]
    assert source.status == "partial" and source.provider == "user_supplied" and not source.real
    assert source.model_version == "commercial-occupancy-v1" and source.reason == "Broker quote"
    rent = next(f for f in after.scoring_trace.factors if f.key == "rent")
    assert rent.coverage_credit == .5 and rent.coverage_points == 10 and rent.weighted_points == pytest.approx(13.2)
    assert not any(item.key == "commercial_rent" for item in after.data.area_insights)


@pytest.mark.parametrize("changes", [{"additional_occupancy_rate": ""}, {"monthly_occupancy_budget": ""}, {"space_size_sqft": ""}, {"asking_rent": ""}])
def test_insufficient_terms_or_budget_preserve_rent_demo_and_80_coverage(workspace, changes):
    report = analyze(workspace, candidate(**changes))
    assert report.data.factor_scores["rent"] == 55 and report.provenance["rent"].status == "demo"
    assert report.coverage.percent == 80 and report.occupancy.model is None
    assert "Demo fallback" in report.provenance["rent"].reason


@pytest.mark.parametrize("census_fails,competition_fails,expected", [(False, False, 90), (True, False, 30), (False, True, 70), (True, True, 10)])
def test_partial_rent_coverage_uses_existing_credit_with_provider_failures(workspace, census_fails, competition_fails, expected):
    if census_fails:
        workspace[4].failure = CensusError("network")
    if competition_fails:
        workspace[5].failure = PoiError("Network unavailable")
    report = analyze(workspace, candidate())
    assert report.coverage.percent == expected and report.coverage.percent != 100
    assert report.coverage.percent == sum(f.coverage_points for f in report.coverage.factors)


@pytest.mark.parametrize("population,income,expected", [(None, 87000, 60), (3200, None, 60), (0, 0, 90)])
def test_individual_missing_census_factor_and_real_zero_preserved(workspace, population, income, expected):
    workspace[4].population, workspace[4].income = population, income
    assert analyze(workspace, candidate()).coverage.percent == expected


@pytest.mark.parametrize("changes,expected", [({}, "within the stated monthly occupancy budget"),
    ({"monthly_occupancy_budget": "8000"}, "exceeds the stated monthly occupancy budget")])
def test_deterministic_budget_explanations_keep_evidence_risk_and_no_market_advice(workspace, changes, expected):
    report = analyze(workspace, candidate(**changes))
    rent = next(item for item in report.explanations.risks if item.key == "rent")
    assert expected in rent.explanation and "have not been independently verified" in rent.explanation
    assert "rent" not in [item.key for item in report.explanations.strengths]
    text = " ".join((report.explanations.summary, rent.explanation, report.occupancy.summary, *report.explanations.quality_notes))
    for prohibited in ("below market", "good lease", "bad lease", "you should sign", "profitable location", "rent-to-sales"):
        assert prohibited not in text.lower()
    if changes:
        assert report.occupancy.model.score < 66


def test_base_only_and_no_budget_explanations_explain_demo_reason(workspace):
    workspace[-1].results = [(PARCEL,), (PARCEL,)]
    base = analyze(workspace, candidate(additional_occupancy_rate=""))
    no_budget = analyze(workspace, candidate(monthly_occupancy_budget=""))
    assert "additional NNN/CAM" in " ".join(base.explanations.quality_notes)
    assert "insufficient lease terms" in next(i for i in base.explanations.risks if i.key == "rent").explanation
    assert "budget not supplied" in next(i for i in no_budget.explanations.risks if i.key == "rent").explanation


def test_route_complete_preserves_signed_map_parcel_census_and_competitors(workspace):
    response = submit(workspace, **TERMS, property_address="Different address", source_label="Broker quote", source_url="https://example.com/quote")
    html = response.get_data(as_text=True)
    assert response.status_code == 200 and response.headers["Cache-Control"] == "no-store"
    for text in ('data-parcel=', 'data-competition=', 'data-initial-location=', 'data-site-status="exact"', 'data-census-status="available"',
                 'data-occupancy-status="complete"', 'PARTIAL EVIDENCE', '90%', '$9,450.00', '94.5%', '13.20 points',
                 'Commercial Occupancy Model v1', 'Property address differs', 'rel="noopener noreferrer"'):
        assert text in html
    assert "Commercial rent remains demo" not in html
    assert not workspace[2].calls and workspace[3].calls == [(LOCATION.latitude, LOCATION.longitude)]
    assert workspace[-1].calls == [(LOCATION.latitude, LOCATION.longitude, 0)]


@pytest.mark.parametrize("changes", [{"monthly_occupancy_budget": ""}, {"additional_occupancy_rate": ""}, {"asking_rent": ""}, {"space_size_sqft": ""}])
def test_route_incomplete_keeps_demo_label_and_retains_supplied_terms(workspace, changes):
    response = submit(workspace, **{**TERMS, **changes})
    html = response.get_data(as_text=True)
    assert response.status_code == 200 and "80%" in html and "Commercial rent remains demo" in html
    assert "Commercial occupancy" in html and 'class="occupancy-inputs" open' in html


@pytest.mark.parametrize("field,value", [("space_size_sqft", "-2800"), ("asking_rent", "NaN"), ("monthly_occupancy_budget", "0"),
    ("source_url", "javascript:alert(1)"), ("lease_structure", "invalid"), ("asking_rent_basis", "unknown"), ("occupancy_notes", "x" * 1001)])
def test_invalid_terms_show_specific_errors_and_keep_location_without_live_requests(workspace, field, value):
    response = submit(workspace, **{**TERMS, field: value})
    html = response.get_data(as_text=True)
    assert response.status_code == 400 and f'id="{field}-error"' in html and 'aria-invalid="true"' in html
    assert 'data-initial-location=' in html and 'selection-token' in html
    assert not workspace[2].calls and not workspace[3].calls and not workspace[4].calls and not workspace[5].calls and not workspace[-1].calls
    assert 'data-occupancy-status=' not in html and 'class="score-value"' not in html


def test_duplicate_occupancy_route_rejected(workspace):
    app, client = workspace[:2]
    form = MultiDict({"location": LOCATION.display_name, "concept": "Indian", **TERMS})
    form.add("asking_rent", "0")
    assert client.post("/", data=form).status_code == 400


def test_html_text_notes_and_source_labels_escaped_and_cannot_upgrade_provenance(workspace):
    response = submit(workspace, **TERMS, source_label='<script>alert("x")</script>', occupancy_notes='<img src=x onerror="alert(1)">',
                      property_address='<b>Other address</b>', source_url="https://example.com/?a=1&b=2", source_type="verified_provider", status="real")
    html = response.get_data(as_text=True)
    assert response.status_code == 200 and "&lt;script&gt;" in html and "&lt;img" in html and "&lt;b&gt;" in html
    assert '<script>alert("x")</script>' not in html and '<img src=x onerror=' not in html
    assert 'href="https://example.com/?a=1&amp;b=2"' in html and 'user_supplied' in html and 'PARTIAL EVIDENCE' in html and '90%' in html


def test_no_persistence_next_request_cannot_reuse_terms(workspace):
    workspace[-1].results = [(PARCEL,), (PARCEL,)]
    assert submit(workspace, **TERMS).status_code == 200
    second = submit(workspace).get_data(as_text=True)
    assert 'data-occupancy-status=' not in second and '$9,450.00' not in second
    assert '80%' in second and "Commercial rent remains demo" in second
    assert 'value="10000"' not in workspace[1].get("/").get_data(as_text=True)


@pytest.mark.parametrize("budget,coverage", [("10000", "10%"), ("", "0%")])
def test_explicit_demo_geography_never_calls_providers_but_keeps_user_cost_evidence(workspace, budget, coverage):
    response = submit(workspace, **{**TERMS, "monthly_occupancy_budget": budget}, demo_only="1")
    html = response.get_data(as_text=True)
    assert response.status_code == 200 and "$9,450.00" in html and coverage in html
    assert not workspace[2].calls and not workspace[3].calls and not workspace[4].calls and not workspace[5].calls and not workspace[-1].calls
    assert 'data-parcel=' not in html and 'data-competition=' not in html
    assert "Fictional restaurant records and sample distances" in html
    if budget:
        assert "PARTIAL EVIDENCE" in html and "No fully real-data factor" in html
    else:
        assert "Commercial rent remains demo" in html


def test_non_us_terms_are_explicit_usd_without_currency_inference(workspace):
    non_us = replace(LOCATION, country_code="fr", display_name="Paris, France")
    report = analyze(workspace, candidate(), non_us)
    assert report.occupancy.supported and report.coverage.percent == 30 and not workspace[3].calls and not workspace[4].calls
    assert report.site.status == "restricted"


@pytest.mark.parametrize("result,state", [(SiteError("restricted"), "restricted"), (SiteError("network"), "unavailable"), ((PARCEL, PARCEL), "ambiguous"), ((), "not_found")])
def test_parcel_failure_does_not_change_supported_rent_or_evidence(workspace, result, state):
    workspace[-1].results = [result, ()]
    report = analyze(workspace, candidate())
    assert report.site.status == state and report.occupancy.model.score == 66 and report.coverage.percent == 90


def test_assessor_values_and_building_size_cannot_fill_missing_lease_terms(workspace):
    workspace[-1].results = [(replace(PARCEL, land_value=10_000_000, improvement_value=50_000_000, building_area_sqft=2800),)]
    report = analyze(workspace, candidate(space_size_sqft=""))
    assert report.occupancy.candidate.space_size_sqft is None and not report.occupancy.supported
    assert report.data.factor_scores["rent"] == 55 and report.coverage.percent == 80


def test_every_occupancy_form_field_is_bound_to_stale_state_contract(workspace):
    class FormFields(HTMLParser):
        def __init__(self):
            super().__init__()
            self.names = set()

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if "data-occupancy-input" in attrs:
                self.names.add(attrs["name"])

    fields = FormFields()
    fields.feed(workspace[1].get("/").get_data(as_text=True))
    assert fields.names == set(FIELD_NAMES)
    state = (Path(__file__).resolve().parents[1] / "static/js/analysis-state.js").read_text()
    assert 'document.querySelectorAll("[data-occupancy-input]")' in state
    assert 'for (const event of ["input", "change"])' in state
    assert 'context.dataset.occupancyStatus = "stale"' in state
    assert 'document.querySelectorAll("[data-analysis-output]")' in state
