import io
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest

from venuebite.providers import mapbox_provider
from venuebite.providers.location_provider import (
    LocationError, validate_coordinates, validate_identifier, validate_query, validate_session,
)
from venuebite.providers.mapbox_provider import MapboxLocationProvider


SESSION = str(uuid4())
IDENTIFIER = "example.location-id"
PUBLIC_TOKEN = "pk.test-placeholder"


def feature(**overrides):
    properties = {
        "name": "Chicago", "place_formatted": "Illinois, United States",
        "mapbox_id": IDENTIFIER, "feature_type": "place",
        "bbox": [-87.95, 41.64, -87.52, 42.03],
    }
    properties.update(overrides)
    return {
        "type": "Feature", "properties": properties,
        "geometry": {"type": "Point", "coordinates": [-87.6298, 41.8781]},
    }


@pytest.fixture
def response_stub(monkeypatch):
    calls = []

    def respond(payload):
        raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()

        def open_request(request, timeout):
            calls.append((request, timeout))
            return io.BytesIO(raw)

        monkeypatch.setattr(mapbox_provider, "urlopen", open_request)
        return calls

    return respond


def test_suggestions_are_normalized_without_provider_payload(response_stub):
    calls = response_stub({"suggestions": [feature()["properties"]], "attribution": "Mapbox"})
    results, attribution = MapboxLocationProvider(PUBLIC_TOKEN).suggest("  Chicago  ", SESSION)
    assert results[0].to_dict() == {
        "display_name": "Chicago, Illinois, United States", "provider_id": IDENTIFIER,
        "place_type": "place", "provider": "mapbox",
    }
    assert attribution == "Mapbox"
    request, timeout = calls[0]
    query = parse_qs(urlsplit(request.full_url).query)
    assert query["q"] == ["Chicago"]
    assert query["session_token"] == [SESSION]
    assert "country" not in query
    assert timeout == 6


def test_retrieve_normalizes_coordinates_and_bounds(response_stub):
    calls = response_stub({"type": "FeatureCollection", "features": [feature()]})
    location = MapboxLocationProvider(PUBLIC_TOKEN, countries="us", request_origin="https://venue.example").retrieve(IDENTIFIER, SESSION)
    assert (location.latitude, location.longitude) == (41.8781, -87.6298)
    assert location.bbox == (-87.95, 41.64, -87.52, 42.03)
    assert location.provider == "mapbox"
    request = calls[0][0]
    assert request.get_header("Referer") == "https://venue.example"
    assert "country" not in parse_qs(urlsplit(request.full_url).query)
    assert f"/retrieve/{IDENTIFIER}" in request.full_url


@pytest.mark.parametrize("query", ["Miami, FL", "Dallas, TX", "10001", "Times Square", "Paris, France", "1 Main Street"])
def test_forward_accepts_broad_queries_without_region_bias(response_stub, query):
    calls = response_stub({"type": "FeatureCollection", "features": [feature()]})
    location = MapboxLocationProvider(PUBLIC_TOKEN).forward(query)
    assert location.display_name == "Chicago, Illinois, United States"
    params = parse_qs(urlsplit(calls[0][0].full_url).query)
    assert params["q"] == [query]
    assert "country" not in params


def test_optional_country_filter(response_stub):
    calls = response_stub({"suggestions": []})
    MapboxLocationProvider(PUBLIC_TOKEN, countries="us,ca").suggest("Main", SESSION)
    assert parse_qs(urlsplit(calls[0][0].full_url).query)["country"] == ["us,ca"]


def test_landmark_name_and_address_are_preserved(response_stub):
    response_stub({"type": "FeatureCollection", "features": [feature(name="Landmark", feature_type="poi", full_address="1 Main Street")]})
    assert MapboxLocationProvider(PUBLIC_TOKEN).forward("Landmark").display_name == "Landmark, 1 Main Street"


@pytest.mark.parametrize("payload", [{}, {"suggestions": {}}, {"suggestions": [None]}, {"suggestions": [{"name": "Broken"}]}])
def test_invalid_suggestions_have_safe_errors(response_stub, payload):
    response_stub(payload)
    with pytest.raises(LocationError) as caught:
        MapboxLocationProvider(PUBLIC_TOKEN).suggest("Chicago", SESSION)
    assert caught.value.status == 502
    assert caught.value.code == "invalid_response"


def test_one_malformed_suggestion_does_not_hide_valid_results(response_stub):
    response_stub({"suggestions": [None, {}, feature()["properties"]]})
    assert len(MapboxLocationProvider(PUBLIC_TOKEN).suggest("Chicago", SESSION)[0]) == 1


def test_zero_suggestions_is_not_an_api_failure(response_stub):
    response_stub({"suggestions": []})
    assert MapboxLocationProvider(PUBLIC_TOKEN).suggest("Unmatched", SESSION)[0] == []


@pytest.mark.parametrize("coordinates", [[181, 0], [0, 91], [False, 0], ["1", 2], [None, 0], [0], [0, 0, 0], [float("nan"), 0]])
def test_malformed_provider_coordinates_are_rejected(response_stub, coordinates):
    data = feature()
    data["geometry"]["coordinates"] = coordinates
    response_stub({"type": "FeatureCollection", "features": [data]})
    with pytest.raises(LocationError, match="unusable") as caught:
        MapboxLocationProvider(PUBLIC_TOKEN).forward("Chicago")
    assert caught.value.status == 502


@pytest.mark.parametrize("payload", [{}, {"type": "FeatureCollection", "features": {}}, {"type": "FeatureCollection", "features": [None]}, {"type": "FeatureCollection", "features": [feature(feature_type="category")]}])
def test_malformed_location_response_is_rejected(response_stub, payload):
    response_stub(payload)
    with pytest.raises(LocationError) as caught:
        MapboxLocationProvider(PUBLIC_TOKEN).forward("Chicago")
    assert caught.value.status == 502


def test_no_resolved_location_is_a_useful_error(response_stub):
    response_stub({"type": "FeatureCollection", "features": []})
    with pytest.raises(LocationError) as caught:
        MapboxLocationProvider(PUBLIC_TOKEN).forward("Unmatched")
    assert caught.value.status == 404
    assert caught.value.code == "no_results"


def test_retrieve_cannot_silently_return_another_location(response_stub):
    response_stub({"type": "FeatureCollection", "features": [feature(mapbox_id="different-id")]})
    with pytest.raises(LocationError, match="different location"):
        MapboxLocationProvider(PUBLIC_TOKEN).retrieve(IDENTIFIER, SESSION)


def test_invalid_optional_bounds_do_not_destroy_valid_coordinates(response_stub):
    response_stub({"type": "FeatureCollection", "features": [feature(bbox=[-200, 0, 100, 90])]})
    assert MapboxLocationProvider(PUBLIC_TOKEN).forward("Chicago").bbox is None


@pytest.mark.parametrize("raw", [b"not json", b"[]", b"\xff", b"x" * (1024 * 1024 + 1), b"[" * 1500 + b"0" + b"]" * 1500], ids=["invalid-json", "wrong-root", "bad-encoding", "oversized", "too-deep"])
def test_unreadable_responses_are_sanitized(response_stub, raw):
    response_stub(raw)
    with pytest.raises(LocationError) as caught:
        MapboxLocationProvider(PUBLIC_TOKEN).suggest("Chicago", SESSION)
    assert caught.value.code == "invalid_response"


@pytest.mark.parametrize("error", [URLError("private-url?access_token=secret"), TimeoutError("private token"), HTTPError("private-url", 401, "secret", None, None), HTTPError("private-url", 403, "secret", None, None), HTTPError("private-url", 429, "secret", None, None), HTTPError("private-url", 500, "secret", None, None)])
def test_upstream_errors_never_expose_credentials(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(mapbox_provider, "urlopen", fail)
    with pytest.raises(LocationError) as caught:
        MapboxLocationProvider(PUBLIC_TOKEN).suggest("Chicago", SESSION)
    assert caught.value.status == 503
    assert "secret" not in str(caught.value)
    assert "private" not in str(caught.value)
    assert PUBLIC_TOKEN not in str(caught.value)
    assert caught.value.__suppress_context__


@pytest.mark.parametrize("token", ["", None, "sk.test-placeholder", "your_mapbox_access_token_here", "pk.invalid whitespace"])
def test_missing_or_secret_token_never_calls_network(monkeypatch, token):
    def unexpected(*args, **kwargs):
        pytest.fail("Unconfigured providers must not call Mapbox")

    monkeypatch.setattr(mapbox_provider, "urlopen", unexpected)
    provider = MapboxLocationProvider(token)
    assert not provider.enabled
    with pytest.raises(LocationError) as caught:
        provider.forward("Chicago")
    assert caught.value.code == "not_configured"


@pytest.mark.parametrize("latitude,longitude", [(90, 180), (-90, -180), ("41.5", "-87.5")])
def test_valid_coordinate_bounds(latitude, longitude):
    assert validate_coordinates(latitude, longitude) == (float(latitude), float(longitude))


@pytest.mark.parametrize("latitude,longitude", [(91, 0), (0, 181), (True, 0), (0, False), ("nan", 0), (0, "inf"), ("", 0), (None, 0)])
def test_invalid_coordinate_bounds(latitude, longitude):
    with pytest.raises(LocationError) as caught:
        validate_coordinates(latitude, longitude)
    assert caught.value.status == 400


@pytest.mark.parametrize("query", [None, "", "x", "x" * 201, "bad\x00query"])
def test_invalid_search_query(query):
    with pytest.raises(LocationError):
        validate_query(query)


@pytest.mark.parametrize("identifier", [None, "", "../../secret", "id?token=secret", "x" * 513])
def test_invalid_provider_identifiers(identifier):
    with pytest.raises(LocationError):
        validate_identifier(identifier)


@pytest.mark.parametrize("session", [None, "", "not-a-uuid", "00000000-0000-1000-8000-000000000000"])
def test_invalid_sessions(session):
    with pytest.raises(LocationError):
        validate_session(session)
