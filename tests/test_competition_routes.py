from dataclasses import replace
from pathlib import Path
import re

import pytest
from werkzeug.datastructures import MultiDict

from venuebite import create_app
from venuebite.providers.location_provider import GeographicLocation
from venuebite.providers.poi_provider import PoiError, PoiSearchResult, RestaurantPoi

LOCATION = GeographicLocation("Denver, Colorado", 39.7392, -104.9903, "place", "mapbox", "test.denver")


class Geography:
    enabled = True
    configuration_message = ""

    def __init__(self):
        self.location = LOCATION
        self.calls = []

    def forward(self, query):
        self.calls.append(query)
        return self.location


class Pois:
    enabled = True

    def __init__(self):
        self.calls = []
        self.failure = None
        self.pois = (RestaurantPoi("Real observed kitchen", 39.74, -104.9903, category_ids=("indian_restaurant",)),)

    def search(self, location, concept, radius):
        self.calls.append((location, concept, radius))
        if self.failure:
            raise self.failure
        return PoiSearchResult(self.pois, attribution="Search by Mapbox")


@pytest.fixture
def workspace():
    geography, pois = Geography(), Pois()
    app = create_app({"TESTING": True}, location_provider=geography, poi_provider=pois)
    return app, app.test_client(), geography, pois


def test_hybrid_route_labels_factors_and_removes_fictional_list(workspace):
    _, client, _, pois = workspace
    response = client.post("/", data={"location": "Denver", "concept": "Indian restaurant", "radius_miles": "3"})
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Hybrid analysis" in html
    assert html.count('class="factor-source "') == 3
    assert "Real observed data" in html
    assert "Real observed kitchen" in html
    assert "Sample Kitchen" not in html
    assert "data-competition=" in html
    assert "85" in html and "80" in html and "55" in html
    assert "76.5" in html
    assert pois.calls[0][0] == LOCATION
    assert response.headers["Cache-Control"] == "no-store"
    assert "Set-Cookie" not in response.headers


def test_signed_coordinates_are_reused_without_second_geocode(workspace):
    app, client, geography, pois = workspace
    signed = app.extensions["geography_service"].sign(LOCATION)
    response = client.post("/", data={"location": LOCATION.display_name, "concept": "Indian", "selection_token": signed, "latitude": LOCATION.latitude, "longitude": LOCATION.longitude})
    assert response.status_code == 200
    assert not geography.calls
    assert pois.calls[0][0] == LOCATION


@pytest.mark.parametrize("radius", ["", "0", "2", "10", "3.0", "NaN", ["1", "3"]])
def test_radius_is_validated_before_external_calls(workspace, radius):
    _, client, geography, pois = workspace
    data = MultiDict([("location", "Denver"), ("concept", "Indian")])
    for value in radius if isinstance(radius, list) else [radius]:
        data.add("radius_miles", value)
    response = client.post("/", data=data)
    assert response.status_code == 400
    assert b"Choose a 1, 3, or 5 mile radius" in response.data
    assert not geography.calls and not pois.calls


def test_failure_keeps_real_geography_and_explicit_demo_score(workspace):
    _, client, _, pois = workspace
    pois.failure = PoiError("Nearby search is busy. Try again.")
    response = client.post("/", data={"location": "Denver", "concept": "Indian"})
    assert response.status_code == 200
    assert b"72.5" in response.data
    assert b"live competition unavailable" in response.data
    assert b"Real location data" in response.data
    assert b"data-initial-location=" in response.data
    assert b"data-competition=" not in response.data
    assert b"Sample Kitchen" not in response.data
    assert b"Real observed data" not in response.data


def test_empty_success_is_hybrid_with_coverage_not_existence_claim(workspace):
    _, client, _, pois = workspace
    pois.pois = ()
    response = client.post("/", data={"location": "Denver", "concept": "Indian"})
    assert b"Hybrid analysis" in response.data
    assert b"No nearby restaurant results were returned" in response.data
    assert b"not a complete restaurant census" in response.data
    assert b"80.5" in response.data


def test_explicit_demo_bypasses_competition_even_if_selection_signed(workspace):
    app, client, geography, pois = workspace
    response = client.post("/", data={"location": LOCATION.display_name, "concept": "Indian", "selection_token": app.extensions["geography_service"].sign(LOCATION), "demo_only": "1"})
    assert response.status_code == 200
    assert b"72.5" in response.data
    assert b"Sample Kitchen" in response.data
    assert not geography.calls and not pois.calls


def test_changing_candidate_does_not_reuse_previous_pois(workspace):
    _, client, geography, pois = workspace
    first = client.post("/", data={"location": "Denver", "concept": "Indian"})
    assert b"Real observed kitchen" in first.data
    geography.location = replace(LOCATION, display_name="Miami, Florida", latitude=25.7617, longitude=-80.1918, provider_id="test.miami")
    pois.pois = (RestaurantPoi("Miami kitchen", 25.762, -80.1918, category_ids=("cuban_restaurant",)),)
    second = client.post("/", data={"location": "Miami", "concept": "Cuban", "radius_miles": "1"})
    assert b"Miami kitchen" in second.data
    assert b"Real observed kitchen" not in second.data
    assert b"Denver, Colorado" not in second.data
    assert pois.calls[-1][0] == geography.location
    assert pois.calls[-1][1].category == "cuban_restaurant"


def test_tampered_coordinates_are_rejected_before_competition(workspace):
    app, client, _, pois = workspace
    response = client.post("/", data={"location": LOCATION.display_name, "concept": "Indian", "selection_token": app.extensions["geography_service"].sign(LOCATION), "latitude": "0", "longitude": "0"})
    assert response.status_code == 400
    assert not pois.calls


def test_external_names_addresses_attribution_are_escaped(workspace):
    _, client, _, pois = workspace
    pois.pois = (RestaurantPoi("<script>alert('xss')</script>", 39.74, -104.9903, address='<img src=x onerror="bad()">'),)
    response = client.post("/", data={"location": "Denver", "concept": "Indian"})
    assert b"<script>alert" not in response.data
    assert b"<img src=x" not in response.data
    assert b"&lt;script&gt;" in response.data
    assert b"\\u003cscript\\u003e" in response.data


@pytest.mark.parametrize("setting,expected", [("1", 1), ("5", 5), ("2", 3), (None, 3), ("bad", 3)])
def test_configurable_default_radius_is_sanitized(setting, expected):
    app = create_app({"TESTING": True, "COMPETITION_RADIUS_MILES": setting})
    assert app.config["COMPETITION_RADIUS_MILES"] == expected
    assert f'value="{expected}" selected'.encode() in app.test_client().get("/").data


def test_frontend_stale_guards_and_safe_popup_rendering_are_present():
    root = Path(__file__).resolve().parents[1] / "static" / "js"
    state = (root / "analysis-state.js").read_text()
    markers = (root / "competition-markers.js").read_text()
    assert "venuebite:location-cleared" in state and "venuebite:location-selected" in state
    assert 'querySelector("#concept").addEventListener("input"' in state
    assert 'querySelector("#radius-miles").addEventListener("change"' in state
    assert "delete frame.dataset.competition" in state
    assert "payload.latitude !== location.latitude" in markers
    assert "payload.concept !==" in markers
    assert "String(payload.radius_miles)" in markers
    assert "textContent = poi.name" in markers
    assert not re.search(r"innerHTML\s*=", markers)
