from dataclasses import replace
from uuid import uuid4

import pytest
from itsdangerous import SignatureExpired

from venuebite import create_app
from venuebite.providers.location_provider import GeographicLocation, LocationError, LocationSuggestion


SESSION = str(uuid4())
LOCATION = GeographicLocation("Chicago, Illinois, United States", 41.8781, -87.6298, "place", "mapbox", "test.chicago")


class FakeGeographicProvider:
    enabled = True
    configuration_message = ""

    def __init__(self):
        self.calls = []
        self.failure = None
        self.location = LOCATION
        self.suggestions = [LocationSuggestion(LOCATION.display_name, LOCATION.provider_id, "place", "mapbox")]

    def check(self):
        if self.failure:
            raise self.failure

    def suggest(self, query, session_token):
        self.check()
        self.calls.append(("suggest", query, session_token))
        return self.suggestions, "Mapbox"

    def retrieve(self, identifier, session_token):
        self.check()
        self.calls.append(("retrieve", identifier, session_token))
        return self.location

    def forward(self, query):
        self.check()
        self.calls.append(("forward", query))
        return self.location


@pytest.fixture
def explorer():
    provider = FakeGeographicProvider()
    app = create_app({"TESTING": True, "SECRET_KEY": "test-only-signing-key"}, location_provider=provider)
    return app, app.test_client(), provider


def selected_form(client, **overrides):
    response = client.post("/api/locations/retrieve", json={"provider_id": LOCATION.provider_id, "session_token": SESSION})
    assert response.status_code == 200
    form = {
        "location": LOCATION.display_name, "concept": "Cafe & Bakery",
        "selection_token": response.json["selection_token"],
        "latitude": str(LOCATION.latitude), "longitude": str(LOCATION.longitude),
    }
    form.update(overrides)
    return form


def test_suggestions_api_uses_normalized_provider_contract(explorer):
    _, client, provider = explorer
    response = client.get("/api/locations/suggestions", query_string={"q": "  Chicago  ", "session_token": SESSION})
    assert response.status_code == 200
    assert response.json["suggestions"][0]["provider_id"] == LOCATION.provider_id
    assert provider.calls == [("suggest", "Chicago", SESSION)]
    assert response.headers["Cache-Control"] == "no-store"


def test_selected_location_drives_map_and_keeps_original_demo_scoring(explorer):
    _, client, provider = explorer
    response = client.post("/", data=selected_form(client))
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Real location data" in html
    assert "Demo market analysis" in html
    assert "72.5" in html
    assert "Cafe &amp; Bakery" in html
    assert "41.87810, -87.62980" in html
    assert "data-initial-location=" in html
    assert [call[0] for call in provider.calls] == ["retrieve"]
    assert "Set-Cookie" not in response.headers


def test_no_javascript_form_resolves_location_server_side(explorer):
    _, client, provider = explorer
    response = client.post("/", data={"location": "Chicago", "concept": "Bistro"})
    assert response.status_code == 200
    assert provider.calls == [("forward", "Chicago")]
    assert LOCATION.display_name.encode() in response.data


def test_changing_location_does_not_reuse_old_coordinates_or_concept(explorer):
    _, client, provider = explorer
    client.post("/", data=selected_form(client))
    provider.location = replace(LOCATION, display_name="Miami, Florida, United States", latitude=25.7617, longitude=-80.1918, provider_id="test.miami")
    response = client.post("/", data={"location": "Miami", "concept": "Cafe & Bakery"})
    assert response.status_code == 200
    assert b"Miami, Florida" in response.data
    assert b"Chicago, Illinois" not in response.data
    assert b"25.76170, -80.19180" in response.data
    assert b"Cafe &amp; Bakery" in response.data


@pytest.mark.parametrize("changes", [
    {"latitude": "91"}, {"longitude": "-181"}, {"latitude": "NaN"},
    {"latitude": ""}, {"longitude": ""}, {"latitude": "0"},
    {"location": "Different place"}, {"selection_token": "tampered"},
    {"latitude": ["41", "42"]}, {"selection_token": ["one", "two"]},
])
def test_forged_or_invalid_hidden_geography_is_rejected(explorer, changes):
    _, client, _ = explorer
    response = client.post("/", data=selected_form(client, **changes))
    assert response.status_code == 400
    assert b"72.5" not in response.data
    assert b'value="Cafe &amp; Bakery"' in response.data
    assert b'aria-invalid="true"' in response.data
    assert b'id="selection-token" value=""' in response.data


def test_unsigned_coordinates_are_rejected_even_in_demo_mode(explorer):
    _, client, provider = explorer
    response = client.post("/", data={"location": "Chicago", "concept": "Cafe", "latitude": "41", "longitude": "-87", "demo_only": "1"})
    assert response.status_code == 400
    assert b"before submitting coordinates" in response.data
    assert not provider.calls


def test_signed_selection_still_validates_without_optional_coordinate_fields(explorer):
    _, client, _ = explorer
    form = selected_form(client)
    del form["latitude"], form["longitude"]
    assert client.post("/", data=form).status_code == 200


def test_expired_selection_requires_reselection(explorer, monkeypatch):
    app, client, _ = explorer
    form = selected_form(client)

    def expired(*args, **kwargs):
        raise SignatureExpired("private signature detail")

    monkeypatch.setattr(app.extensions["geography_service"].serializer, "loads", expired)
    response = client.post("/", data=form)
    assert response.status_code == 400
    assert b"expired or changed" in response.data
    assert b"private signature" not in response.data


def test_concept_validation_preserves_verified_selection(explorer):
    _, client, _ = explorer
    response = client.post("/", data=selected_form(client, concept=""))
    assert response.status_code == 400
    assert b"Enter a restaurant concept" in response.data
    assert b"data-initial-location=" in response.data
    assert b"Real location data selected" in response.data


def test_zero_suggestions_are_returned_for_no_results_state(explorer):
    _, client, provider = explorer
    provider.suggestions = []
    response = client.get("/api/locations/suggestions", query_string={"q": "Unmatched", "session_token": SESSION})
    assert response.status_code == 200
    assert response.json["suggestions"] == []


@pytest.mark.parametrize("query", [{}, {"q": "x", "session_token": SESSION}, {"q": "Chicago", "session_token": "invalid"}, {"q": ["Chicago", "Miami"], "session_token": SESSION}])
def test_search_api_validates_request_before_provider(explorer, query):
    _, client, provider = explorer
    assert client.get("/api/locations/suggestions", query_string=query).status_code == 400
    assert not provider.calls


@pytest.mark.parametrize("payload", [None, [], {}, {"provider_id": "../../secret", "session_token": SESSION}, {"provider_id": LOCATION.provider_id, "session_token": "invalid"}])
def test_retrieve_api_validates_request_before_provider(explorer, payload):
    _, client, provider = explorer
    response = client.post("/api/locations/retrieve", json=payload)
    assert response.status_code == 400
    assert not provider.calls


def test_provider_failure_offers_explicit_demo_fallback(explorer):
    _, client, provider = explorer
    provider.failure = LocationError("Location search is temporarily unavailable.")
    suggestions = client.get("/api/locations/suggestions", query_string={"q": "Chicago", "session_token": SESSION})
    assert suggestions.status_code == 503
    assert suggestions.json["code"] == "provider_unavailable"
    assert client.post("/api/locations/retrieve", json={"provider_id": LOCATION.provider_id, "session_token": SESSION}).status_code == 503
    response = client.post("/", data={"location": "Chicago", "concept": "Cafe"})
    assert response.status_code == 503
    assert b"Analyze demo only" in response.data
    assert b'type="submit" name="demo_only" value="1"' in response.data
    assert b'value="Cafe"' in response.data
    demo = client.post("/", data={"location": "Chicago", "concept": "Cafe", "demo_only": "1"})
    assert demo.status_code == 200
    assert b"72.5" in demo.data
    assert b"data-initial-location=" not in demo.data


def test_map_configuration_exposes_only_public_browser_tokens():
    for token, enabled in [("", False), ("sk.test-placeholder", False), ("pk.test-placeholder", True)]:
        app = create_app({"TESTING": True, "MAPBOX_ACCESS_TOKEN": token})
        client = app.test_client()
        response = client.get("/api/map-config")
        assert response.status_code == 200
        assert response.json["enabled"] is enabled
        assert response.json["access_token"] == (token if enabled else "")
        assert b"sk.test-placeholder" not in response.data
        assert b"sk.test-placeholder" not in client.get("/").data
        assert response.headers["Cache-Control"] == "no-store"


def test_missing_configuration_keeps_demo_functional(client):
    assert client.get("/api/map-config").json["enabled"] is False
    assert b"Mapbox is not configured" in client.get("/").data
    assert client.post("/", data={"location": "Dallas", "concept": "Cafe"}).status_code == 200
    response = client.get("/api/locations/suggestions", query_string={"q": "Dallas", "session_token": SESSION})
    assert response.status_code == 503
    assert response.json["code"] == "not_configured"


def test_tests_ignore_developer_token_and_never_load_local_env(monkeypatch):
    monkeypatch.setenv("MAPBOX_ACCESS_TOKEN", "pk.test-placeholder")

    def unexpected(*args, **kwargs):
        pytest.fail("Tests must not load local .env credentials")

    monkeypatch.setattr("venuebite.load_dotenv", unexpected)
    app = create_app({"TESTING": True})
    assert app.test_client().get("/api/map-config").json["enabled"] is False


def test_normal_startup_loads_env_without_overriding_environment(monkeypatch):
    calls = []
    monkeypatch.setattr("venuebite.load_dotenv", lambda path, **kwargs: calls.append((path.name, kwargs)))
    create_app({"MAPBOX_ACCESS_TOKEN": ""})
    assert calls == [(".env", {"override": False})]


def test_mapbox_security_policy_allows_official_resources_only(client):
    response = client.get("/")
    policy = response.headers["Content-Security-Policy"]
    assert "https://api.mapbox.com/mapbox-gl-js/" in policy
    assert "worker-src 'self' blob:" in policy
    assert "'unsafe-inline'" not in policy.split("script-src", 1)[1].split(";", 1)[0]
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_provider_names_are_escaped_in_html_and_initial_map_json(explorer):
    _, client, provider = explorer
    provider.location = replace(LOCATION, display_name="<script>alert('xss')</script>")
    response = client.post("/", data={"location": "Chicago", "concept": "Cafe"})
    assert response.status_code == 200
    assert b"<script>alert" not in response.data
    assert b"&lt;script&gt;" in response.data
    assert b"\\u003cscript\\u003e" in response.data
