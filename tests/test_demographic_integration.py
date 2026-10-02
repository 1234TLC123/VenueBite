from dataclasses import replace
from pathlib import Path

import pytest

from venuebite import create_app
from venuebite.demographic_scoring import income_score, population_score
from venuebite.providers.demographic_provider import CensusError, CensusTract, DemographicData
from venuebite.providers.location_provider import GeographicLocation, LocationError
from venuebite.providers.mapbox_provider import MapboxLocationProvider
from venuebite.providers.poi_provider import PoiError, PoiSearchResult, RestaurantPoi
from venuebite.services.analysis_service import AnalysisService
from venuebite.services.competition_service import CompetitionService
from venuebite.services.demographic_service import DemographicService
from venuebite.services.mock_data_service import MockLocationDataService


LOCATION = GeographicLocation("Denver, Colorado, United States", 39.7392, -104.9903, "place", "mapbox", "test.denver", country_code="us")
TRACT = CensusTract("08", "031", "002000", "Census Tract 20", "Colorado", "Denver County")


class Geography:
    enabled = True
    configuration_message = ""

    def __init__(self):
        self.calls = []
        self.location = LOCATION

    def forward(self, query):
        self.calls.append(query)
        return self.location


class CensusGeography:
    def __init__(self):
        self.calls = []
        self.tract = TRACT
        self.failure = None

    def lookup(self, latitude, longitude):
        self.calls.append((latitude, longitude))
        if self.failure:
            raise self.failure
        return self.tract


class Census:
    enabled = True

    def __init__(self):
        self.calls = []
        self.failure = None
        self.population = 3200
        self.income = 87000

    def fetch(self, geography):
        self.calls.append(geography)
        if self.failure:
            raise self.failure
        return DemographicData(
            geography=geography, population=self.population, median_household_income=self.income,
            population_moe=160 if self.population is not None else None,
            income_moe=5000 if self.income is not None else None,
            geography_name=f"{geography.name}; {geography.county_name}; {geography.state_name}",
            reason="Some ACS estimates are unavailable; their scores use demo fallback." if self.population is None or self.income is None else "",
        )


class Pois:
    enabled = True

    def __init__(self):
        self.calls = []
        self.failure = None

    def search(self, location, concept, radius):
        self.calls.append((location, concept, radius))
        if self.failure:
            raise self.failure
        return PoiSearchResult((RestaurantPoi("Live Indian kitchen", location.latitude, location.longitude, category_ids=("indian_restaurant",)),))


@pytest.fixture
def workspace():
    geography, census_geo, census, pois = Geography(), CensusGeography(), Census(), Pois()
    app = create_app({"TESTING": True}, location_provider=geography, poi_provider=pois,
                     census_geo_provider=census_geo, demographic_provider=census)
    return app, app.test_client(), geography, census_geo, census, pois


def report(census_geo, census, pois, location=LOCATION):
    return AnalysisService(MockLocationDataService(), CompetitionService(pois), DemographicService(census_geo, census)).analyze(
        location.display_name, "Indian restaurant", geographic_location=location,
    )


def test_independent_real_factors_and_structured_provenance(workspace):
    _, _, _, census_geo, census, pois = workspace
    result = report(census_geo, census, pois)
    assert result.data.factor_scores == {"population": population_score(3200), "income": income_score(87000), "rent": 55, "competition": 80}
    assert result.score.overall_score == round(population_score(3200) * .3 + income_score(87000) * .3 + 55 * .2 + 80 * .2, 1)
    assert result.data.source_label == "Hybrid analysis" and not result.data.is_demo
    assert result.demographics.data.status == "available"
    assert result.provenance["population"].provider == "U.S. Census Bureau"
    assert result.provenance["population"].vintage == 2024
    assert result.provenance["population"].geoid == TRACT.geoid
    assert result.provenance["population"].model_version == "population-v1"
    assert result.provenance["income"].model_version == "income-v1"
    assert result.provenance["rent"].status == "demo"
    assert result.provenance["competition"].real
    assert census_geo.calls == [(LOCATION.latitude, LOCATION.longitude)]
    assert census.calls == [TRACT]


@pytest.mark.parametrize("population,income", [(None, 87000), (3200, None), (None, None), (0, 0)])
def test_partial_results_replace_only_usable_factors(workspace, population, income):
    _, _, _, census_geo, census, pois = workspace
    census.population, census.income = population, income
    result = report(census_geo, census, pois)
    assert result.data.factor_scores["population"] == (85 if population is None else population_score(population))
    assert result.data.factor_scores["income"] == (80 if income is None else income_score(income))
    assert result.provenance["population"].status == ("fallback" if population is None else "real")
    assert result.provenance["income"].status == ("fallback" if income is None else "real")
    assert result.data.factor_scores["competition"] == 80 and result.data.factor_scores["rent"] == 55


@pytest.mark.parametrize("code", ["not_configured", "authorization", "rate_limit", "network", "no_tract", "invalid_response", "geography_mismatch", "unexpected-test-key"])
def test_failures_preserve_competition_and_use_sanitized_demo_factors(workspace, code):
    _, _, _, census_geo, census, pois = workspace
    census.failure = CensusError(code)
    result = report(census_geo, census, pois)
    assert result.data.factor_scores == {"population": 85, "income": 80, "rent": 55, "competition": 80}
    assert result.score.overall_score == 76.5
    assert result.demographics.data.status == "unavailable"
    assert "test-key" not in result.demographics.data.reason
    assert result.provenance["population"].status == "fallback"


def test_geography_failure_skips_acs(workspace):
    _, _, _, census_geo, census, pois = workspace
    census_geo.failure = CensusError("no_tract")
    result = report(census_geo, census, pois)
    assert not census.calls and result.demographics.data.geography is None
    assert result.competition.available


def test_missing_key_skips_both_census_requests(workspace):
    _, _, _, census_geo, census, pois = workspace
    census.enabled = False
    result = report(census_geo, census, pois)
    assert not census.calls and not census_geo.calls
    assert "not configured" in result.demographics.data.reason
    assert result.competition.available


def test_boundary_ambiguity_preserves_map_competition_and_suggests_specific_address(workspace):
    _, client, _, census_geo, census, _ = workspace
    census_geo.failure = CensusError("ambiguous_geography")
    html = client.post("/", data={"location": "Denver", "concept": "Indian"}).get_data(as_text=True)
    assert "multiple Census tracts" in html and "more specific address" in html
    assert 'data-competition=' in html and 'data-initial-location=' in html
    assert 'data-census-geoid=' not in html and not census.calls


def test_metric_provenance_does_not_depend_on_display_labels_or_icons(workspace):
    _, _, _, census_geo, census, pois = workspace
    class Market:
        def get_location_data(self, location, concept):
            data = MockLocationDataService().get_location_data(location, concept)
            return replace(data, area_insights=tuple(replace(item, label="Renamed metric", icon="info") for item in data.area_insights))
    result = AnalysisService(Market(), CompetitionService(pois), DemographicService(census_geo, census)).analyze(
        LOCATION.display_name, "Indian", geographic_location=LOCATION,
    )
    assert {item.key for item in result.data.area_insights} == {"population", "income", "population_growth", "commercial_rent", "restaurants", "schools"}
    assert all(item.status == "demo" for item in result.data.area_insights if item.key in {"commercial_rent", "schools"})


def test_competition_failure_does_not_discard_census(workspace):
    _, client, _, census_geo, census, pois = workspace
    pois.failure = PoiError("Competition unavailable")
    result = report(census_geo, census, pois)
    assert result.provenance["population"].real and result.provenance["income"].real
    assert result.provenance["competition"].status == "fallback"
    html = client.post("/", data={"location": "Denver", "concept": "Indian"}).get_data(as_text=True)
    assert "Hybrid analysis" in html and "Real Census estimate" in html
    assert "all four scores use fictional" not in html
    assert "Sample Kitchen" not in html


def test_successful_route_shows_real_metrics_moes_and_no_old_mock_leaks(workspace):
    _, client, _, census_geo, census, pois = workspace
    response = client.post("/", data={"location": "Denver", "concept": "Indian restaurant"})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    for text in ("3,200", "$87,000", "ACS 2024", "ACS 5-Year Detailed Tables", "U.S. Census Bureau", "08031002000", "Denver County", "Colorado", "2020&ndash;2024", "population-v1", "income-v1", "90% margins of error", "160", "$5,000", "Commercial rent remains demo", "Live Indian kitchen"):
        assert text in html
    for text in ("184,500", "$72,400", "+1.8%", "Sample Kitchen", "Sample business count"):
        assert text not in html
    assert html.count('class="factor-source real-source"') == 3
    assert html.count('class="factor-source "') == 1
    assert "Demo data" in html and "$28 / sq ft" in html
    assert 'data-census-status="available"' in html
    assert 'data-competition=' in html and 'data-initial-location=' in html
    assert response.headers["Cache-Control"] == "no-store"
    assert len(census_geo.calls) == len(census.calls) == len(pois.calls) == 1


def test_partial_route_marks_missing_metric_and_demo_factor(workspace):
    _, client, _, _, census, _ = workspace
    census.income = None
    html = client.post("/", data={"location": "Denver", "concept": "Indian"}).get_data(as_text=True)
    assert 'data-census-status="partial"' in html and "Demo data (fallback)" in html
    assert "$72,400" not in html
    assert html.count('class="factor-source real-source"') == 2
    assert "Income: Demo data" in html


def test_signed_coordinates_reused_and_key_not_sent_to_browser(workspace):
    app, client, geography, census_geo, census, _ = workspace
    app.config["CENSUS_API_KEY"] = "synthetic-private-test-key"
    response = client.post("/", data={"location": LOCATION.display_name, "concept": "Indian", "selection_token": app.extensions["geography_service"].sign(LOCATION)})
    assert not geography.calls and census_geo.calls == [(LOCATION.latitude, LOCATION.longitude)]
    for path in ("/", "/api/map-config"):
        assert b"synthetic-private-test-key" not in client.get(path).data
    assert b"synthetic-private-test-key" not in response.data
    assert "api.census.gov" not in response.headers["Content-Security-Policy"]


def test_get_and_explicit_demo_do_not_request_census(workspace):
    app, client, _, census_geo, census, pois = workspace
    client.get("/")
    response = client.post("/", data={"location": LOCATION.display_name, "concept": "Indian", "selection_token": app.extensions["geography_service"].sign(LOCATION), "demo_only": "1"})
    assert response.status_code == 200 and b"72.5" in response.data
    assert b"Sample Kitchen" in response.data
    assert not census_geo.calls and not census.calls and not pois.calls


def test_validation_before_census(workspace):
    app, client, _, census_geo, census, _ = workspace
    token = app.extensions["geography_service"].sign(LOCATION)
    response = client.post("/", data={"location": LOCATION.display_name, "concept": "Indian", "selection_token": token, "latitude": "0", "longitude": "0"})
    assert response.status_code == 400 and not census_geo.calls and not census.calls


def test_new_selected_point_cannot_reuse_previous_census_geo_or_metrics(workspace):
    _, client, geography, census_geo, census, _ = workspace
    first = client.post("/", data={"location": "Denver", "concept": "Indian"})
    assert TRACT.geoid.encode() in first.data
    geography.location = replace(LOCATION, display_name="Miami, Florida, United States", latitude=25.7617, longitude=-80.1918, provider_id="test.miami")
    census_geo.tract = CensusTract("12", "086", "006701", "Census Tract 67.01", "Florida", "Miami-Dade County")
    census.population, census.income = 2100, 43000
    second = client.post("/", data={"location": "Miami", "concept": "Cuban"})
    assert b"12086006701" in second.data and b"2,100" in second.data and b"$43,000" in second.data
    assert TRACT.geoid.encode() not in second.data and b"3,200" not in second.data and b"$87,000" not in second.data
    assert census_geo.calls[-1] == (25.7617, -80.1918)


def test_non_us_skips_census_but_preserves_real_map_and_competition(workspace):
    _, client, geography, census_geo, census, pois = workspace
    geography.location = replace(LOCATION, display_name="Paris, France", latitude=48.8566, longitude=2.3522, country_code="fr", provider_id="test.paris")
    html = client.post("/", data={"location": "Paris", "concept": "Indian"}).get_data(as_text=True)
    assert "50 U.S. states and DC only" in html
    assert "Real observed data" in html and 'data-initial-location=' in html and 'data-competition=' in html
    assert 'data-census-geoid=' not in html and "Demo data (fallback)" in html
    assert not census_geo.calls and not census.calls and len(pois.calls) == 1


def test_testing_ignores_environment_census_key(monkeypatch):
    monkeypatch.setenv("CENSUS_API_KEY", "environment-private-test-key")
    app = create_app({"TESTING": True})
    assert app.config["CENSUS_API_KEY"] == ""
    assert not app.extensions["demographic_service"].demographic_provider.enabled


def test_country_metadata_is_normalized_and_signed():
    provider = MapboxLocationProvider("pk.test")
    feature = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [2.3522, 48.8566]},
               "properties": {"name": "Paris", "feature_type": "place", "mapbox_id": "test.paris", "context": {"country": {"country_code": "FR"}}}}
    location = provider._normalize_feature(feature)
    assert location.country_code == "fr" and location.to_dict()["country_code"] == "fr"
    assert "country_code" not in replace(location, country_code=None).to_dict()
    app = create_app({"TESTING": True}, location_provider=Geography())
    service = app.extensions["geography_service"]
    assert service.read_selection(service.sign(location)).country_code == "fr"


@pytest.mark.parametrize("country", ["france", "123", True])
def test_invalid_country_metadata_is_rejected(country):
    with pytest.raises(LocationError):
        replace(LOCATION, country_code=country)


def test_all_census_ui_is_inside_invalidated_analysis_section():
    root = Path(__file__).resolve().parents[1]
    results = (root / "templates/results.html").read_text()
    state = (root / "static/js/analysis-state.js").read_text()
    assert 'aria-labelledby="insights-heading" data-analysis-output' in results
    assert "{% include '_demographics.html' %}" in results
    assert "delete context.dataset.censusGeoid" in state and 'context.dataset.censusStatus = "stale"' in state
    assert "venuebite:location-selected" in state and "venuebite:location-cleared" in state


def test_census_geography_names_are_escaped(workspace):
    _, client, _, census_geo, _, _ = workspace
    census_geo.tract = replace(TRACT, name='<script>alert("xss")</script>', county_name='<img src=x onerror="bad()">')
    html = client.post("/", data={"location": "Denver", "concept": "Indian"}).get_data(as_text=True)
    assert '<script>alert("xss")</script>' not in html and '<img src=x' not in html
    assert "&lt;script&gt;" in html and "&lt;img" in html


def test_score_v2_hybrid_trace_and_ui(workspace):
    _, client, _, census_geo, census, pois = workspace
    result = report(census_geo, census, pois)
    assert result.coverage.percent == 80 and result.coverage.label == "High data coverage"
    assert result.scoring_trace.model_version == "2.0"
    assert result.scoring_trace.final_score == result.score.overall_score
    assert result.scoring_trace.coverage == 80
    assert [item.status for item in result.scoring_trace.factors] == ["real", "real", "demo", "real"]
    html = client.post("/", data={"location": "Denver", "concept": "Indian"}).get_data(as_text=True)
    for text in ("Data Coverage", "80%", "High data coverage", "VenueBite Score Model v2", "Contribution", "competition-v1", "Evidence &amp; data quality", "not success probability", "Commercial rent remains demo"):
        assert text in html
    for factor in result.score.factors:
        assert f"{factor.weighted_points_label} points" in html
    assert "raw_weighted_sum" not in html and "scoring_trace" not in html


@pytest.mark.parametrize("failure,percent", [("census", 20), ("competition", 60), ("both", 0)])
def test_score_v2_independent_failure_coverage(workspace, failure, percent):
    _, client, _, census_geo, census, pois = workspace
    if failure in {"census", "both"}:
        census.failure = CensusError("network")
    if failure in {"competition", "both"}:
        pois.failure = PoiError("Competition unavailable")
    result = report(census_geo, census, pois)
    assert result.coverage.percent == percent and result.coverage.warning
    assert result.score.overall_score == round(sum(item.weighted_points for item in result.score.factors), 1)
    assert "rent" in [item.key for item in result.explanations.risks]
    html = client.post("/", data={"location": "Denver", "concept": "Indian"}).get_data(as_text=True)
    assert "Data gaps need verification" in html and f"{percent}%" in html
    assert 'data-initial-location=' in html


@pytest.mark.parametrize("population,income,percent", [(3200, None, 50), (None, 87000, 50), (None, None, 20), (0, 0, 80)])
def test_score_v2_partial_census_is_factor_specific(workspace, population, income, percent):
    _, _, _, census_geo, census, pois = workspace
    census.population, census.income = population, income
    result = report(census_geo, census, pois)
    assert result.coverage.percent == percent
    assert {item.status for item in result.coverage.factors} <= {"real", "demo", "fallback"}
    assert (result.provenance["population"].real) == (population is not None)
    assert (result.provenance["income"].real) == (income is not None)


def test_score_v2_non_us_and_explicit_demo(workspace):
    app, client, geography, census_geo, census, pois = workspace
    paris = replace(LOCATION, display_name="Paris, France", country_code="fr")
    result = report(census_geo, census, pois, paris)
    assert result.coverage.percent == 20
    assert not census.calls and not census_geo.calls
    assert "population" not in [item.key for item in result.explanations.strengths]
    html = client.post("/", data={"location": LOCATION.display_name, "concept": "Indian", "selection_token": app.extensions["geography_service"].sign(LOCATION), "demo_only": "1"}).get_data(as_text=True)
    assert "Very limited data coverage" in html and 'value="0.0" aria-label="Real usable model data coverage, percent"' in html
    assert "No fully real-data factors meet" in html and "verify data" in html


def test_score_v2_output_uses_existing_stale_report_guard():
    root = Path(__file__).resolve().parents[1]
    results = (root / "templates/results.html").read_text()
    score_section = results.split('aria-labelledby="score-heading" data-analysis-output>', 1)[1].split("</section>", 1)[0]
    assert 'id="coverage-heading"' in score_section
    assert "report.explanations.summary" in score_section and "factor.weighted_points_label" in score_section
    assert "report.explanations.strengths" in results.split('class="lower-grid" data-analysis-output>', 1)[1]
