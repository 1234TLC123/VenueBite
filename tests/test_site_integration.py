from dataclasses import replace
from pathlib import Path

import pytest

from venuebite import create_app
from venuebite.providers.site_provider import SiteError
from venuebite.services.analysis_service import AnalysisService
from venuebite.services.competition_service import CompetitionService
from venuebite.services.demographic_service import DemographicService
from venuebite.services.mock_data_service import MockLocationDataService
from venuebite.services.site_intelligence_service import SiteIntelligenceService
from test_demographic_integration import Census, CensusGeography, Geography, Pois
from test_site_intelligence import LOCATION, PARCEL, Parcels


@pytest.fixture
def workspace():
    geo, census_geo, census, pois, parcels = Geography(), CensusGeography(), Census(), Pois(), Parcels()
    geo.location = LOCATION
    app = create_app({"TESTING": True}, location_provider=geo, poi_provider=pois,
                     census_geo_provider=census_geo, demographic_provider=census, site_provider=parcels)
    return app, app.test_client(), geo, census_geo, census, pois, parcels


def test_signed_point_shared_by_all_providers_no_regeocoding(workspace):
    app, client, geo, census_geo, census, pois, parcels = workspace
    html = client.post("/", data={"location": LOCATION.display_name, "concept": "Indian",
        "selection_token": app.extensions["geography_service"].sign(LOCATION)}).get_data(as_text=True)
    assert not geo.calls
    assert census_geo.calls == [(LOCATION.latitude, LOCATION.longitude)]
    assert parcels.calls == [(LOCATION.latitude, LOCATION.longitude, 0)]
    assert len(pois.calls) == len(census.calls) == 1
    for text in ('data-parcel=', 'data-competition=', 'data-initial-location=', 'data-site-status="exact"', 'data-census-status="available"',
                 'Site intelligence', 'Opportunity score', 'Data Coverage', '80%', 'Commercial rent remains demo'):
        assert text in html


@pytest.mark.parametrize("state", ["exact", "nearby", "ambiguous", "not_found", "restricted", "unavailable", "exception"])
def test_site_never_changes_four_factor_scores_explanations_trace_or_coverage(workspace, state):
    app, _, _, census_geo, census, pois, parcels = workspace
    results = {"exact": [(PARCEL,)], "nearby": [(), (PARCEL,)], "ambiguous": [(PARCEL, PARCEL)],
               "not_found": [(), ()], "restricted": [SiteError("restricted")], "unavailable": [SiteError("network")],
               "exception": [RuntimeError("synthetic-private")]}[state]
    parcels.results = results
    args = (MockLocationDataService(), CompetitionService(pois), DemographicService(census_geo, census))
    before = AnalysisService(*args).analyze(LOCATION.display_name, "Indian", geographic_location=LOCATION)
    after = AnalysisService(*args, site_service=app.extensions["site_intelligence_service"]).analyze(LOCATION.display_name, "Indian", geographic_location=LOCATION)
    assert after.site.status == ("unavailable" if state == "exception" else state)
    assert after.score == before.score and after.scoring_trace == before.scoring_trace
    assert after.coverage == before.coverage and after.coverage.percent == 80
    assert after.explanations == before.explanations and after.provenance == before.provenance
    assert after.data == before.data and after.provenance["rent"].status == "demo"
    assert [(factor.key, factor.weight_percent) for factor in after.score.factors] == [("population", 30), ("income", 30), ("rent", 20), ("competition", 20)]


@pytest.mark.parametrize("result,state", [((PARCEL, PARCEL), "ambiguous"), (SiteError("restricted"), "restricted"),
    (SiteError("authorization"), "unavailable"), (RuntimeError("synthetic-secret"), "unavailable")])
def test_site_failure_route_preserves_map_census_competition(workspace, result, state):
    _, client, _, _, _, _, parcels = workspace
    parcels.results = [result]
    response = client.post("/", data={"location": "123 Sample St", "concept": "Indian"})
    html = response.get_data(as_text=True)
    assert response.status_code == 200 and f'data-site-status="{state}"' in html
    assert 'data-parcel=' not in html and 'data-competition=' in html and 'data-census-status="available"' in html
    assert '80%' in html and 'synthetic-secret' not in html


def test_get_suggestions_retrieve_validation_and_demo_never_call_regrid(workspace):
    app, client, _, _, _, _, parcels = workspace
    for path in ("/", "/api/map-config", "/api/locations/suggestions", "/api/locations/retrieve"):
        client.get(path)
    assert client.post("/", data={"location": "123 Sample St", "concept": ""}).status_code == 400
    token = app.extensions["geography_service"].sign(LOCATION)
    assert client.post("/", data={"location": LOCATION.display_name, "concept": "Indian", "selection_token": token, "latitude": "0", "longitude": "0"}).status_code == 400
    response = client.post("/", data={"location": LOCATION.display_name, "concept": "Indian", "selection_token": token, "demo_only": "1"})
    assert response.status_code == 200 and b"Demo market analysis" in response.data
    assert not parcels.calls and b'data-parcel=' not in response.data


def test_private_token_never_in_html_map_config_csp_or_logs(workspace, caplog):
    app, client, _, _, _, _, _ = workspace
    app.config["REGRID_API_TOKEN"] = "synthetic-private-server-token"
    for response in (client.get("/"), client.get("/api/map-config"), client.post("/", data={"location": "123 Sample St", "concept": "Indian"})):
        assert b"synthetic-private-server-token" not in response.data
        assert "app.regrid.com" not in response.headers["Content-Security-Policy"]
    assert "synthetic-private-server-token" not in caplog.text


def test_test_mode_does_not_use_real_environment_and_missing_token_starts(monkeypatch):
    monkeypatch.setenv("REGRID_API_TOKEN", "synthetic-environment-secret")
    app = create_app({"TESTING": True})
    assert app.config["REGRID_API_TOKEN"] == ""
    assert not app.extensions["site_intelligence_service"].provider.enabled
    assert app.test_client().get("/").status_code == 200
    assert app.test_client().post("/", data={"location": "Denver", "concept": "Indian"}).status_code == 200


def test_site_provider_text_escaped_and_unsafe_source_omitted(workspace):
    _, client, _, _, _, _, parcels = workspace
    parcels.results = [(replace(PARCEL, display_address='<script>alert("xss")</script>', land_use_description='<img src=x onerror="bad()">'),)]
    html = client.post("/", data={"location": "123 Sample St", "concept": "Indian"}).get_data(as_text=True)
    assert '<script>alert("xss")</script>' not in html and '<img src=x' not in html
    assert "&lt;script&gt;" in html and "&lt;img" in html


def test_next_analysis_cannot_reuse_prior_parcel(workspace):
    _, client, geo, _, _, _, parcels = workspace
    first = client.post("/", data={"location": "123 Sample St", "concept": "Indian"})
    assert PARCEL.regrid_id.encode() in first.data
    geo.location = replace(LOCATION, display_name="Next site", latitude=39.6)
    parcels.results = [SiteError("restricted")]
    second = client.post("/", data={"location": "Next site", "concept": "Indian"})
    assert PARCEL.regrid_id.encode() not in second.data and b'data-parcel=' not in second.data


def test_frontend_snapshot_invalidation_and_style_reload_contract():
    root = Path(__file__).resolve().parents[1]
    state = (root / "static/js/analysis-state.js").read_text()
    layer = (root / "static/js/parcel-layer.js").read_text()
    viewer = (root / "static/js/map-viewer.js").read_text()
    template = (root / "templates/_site_intelligence.html").read_text()
    assert 'data-analysis-output data-site-status=' in template
    assert 'delete frame.dataset.parcel' in state and 'delete context.dataset.siteId' in state
    assert 'context.dataset.siteStatus = "stale"' in state
    assert 'payload.concept !==' in layer and 'payload.radius_miles' in layer
    assert 'payload.latitude !== location.latitude' in layer and 'payload.longitude !== location.longitude' in layer
    assert '"Polygon", "MultiPolygon"' in layer and 'map.addSource' in layer and 'map.addLayer' in layer
    assert 'this.parcel.update(this.styleReady ? this.map : null, location)' in viewer and 'this.parcel.clear(this.map)' in viewer
    assert 'this.styleReady = true' in viewer and 'map.isStyleLoaded()' not in layer
    assert 'this.map.on("style.load"' in viewer and 'this.updateLocation(this.location)' in viewer
    assert 'fetch(' not in layer and 'localStorage' not in layer
    assert 'this.parcel.focus(this.map, this.location, this.reduceMotion.matches)' in viewer
