import io
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

from venuebite.concepts import resolve_concept
from venuebite.distance import METERS_PER_MILE
from venuebite.providers import mapbox_provider
from venuebite.providers.location_provider import GeographicLocation
from venuebite.providers.mapbox_poi_provider import MapboxPoiProvider
from venuebite.providers.poi_provider import PoiError

LOCATION = GeographicLocation("Denver", 39.7392, -104.9903, "place", "mapbox", "test.denver")
TOKEN = "pk.test-placeholder"


def feature(coordinates=None, **properties):
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": coordinates if coordinates is not None else [-104.9903, 39.74]}, "properties": {"name": "Kitchen", "feature_type": "poi", **properties}}


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


def search(provider, concept="Indian restaurant"):
    return provider.search(LOCATION, resolve_concept(concept), 3 * METERS_PER_MILE)


def test_two_bounded_queries_use_selected_coordinates_radius_and_timeout(response_stub):
    calls = response_stub({"type": "FeatureCollection", "features": [feature()], "attribution": "Mapbox"})
    result = search(MapboxPoiProvider(TOKEN, countries="us", request_origin="https://venue.example", timeout=4))
    assert result.query_count == len(calls) == 2
    assert result.attribution == "Mapbox"
    assert [urlsplit(call[0].full_url).path.rsplit("/", 1)[-1] for call in calls] == ["restaurant", "indian_restaurant"]
    for request, timeout in calls:
        params = parse_qs(urlsplit(request.full_url).query)
        assert params["proximity"] == ["-104.9903,39.7392"]
        assert params["limit"] == ["25"]
        assert "types" not in params
        assert params["country"] == ["us"]
        assert params["show_closed_pois"] == ["false"]
        assert len(params["bbox"][0].split(",")) == 4
        assert timeout == 4
        assert request.get_header("Referer") == "https://venue.example"


def test_optional_fields_and_malformed_categories_are_safe(response_stub):
    response_stub({"type": "FeatureCollection", "features": [feature(poi_category_ids="wrong", poi_category=[None, {}, "Restaurant"], operational_status={})]})
    poi = search(MapboxPoiProvider(TOKEN)).pois[0]
    assert poi.name == "Kitchen"
    assert poi.provider_id is None
    assert poi.address == ""
    assert poi.category_ids == ()
    assert poi.categories == ("Restaurant",)
    assert poi.status is None
    assert poi.search_categories == ("restaurant",)


def test_reliable_fields_are_normalized_without_provider_distance(response_stub):
    response_stub({"type": "FeatureCollection", "features": [feature(name_preferred=" Preferred  name ", mapbox_id="id", full_address="1 Main", poi_category_ids=["indian_restaurant", "indian_restaurant", 5], poi_category=["Indian Restaurant"], operational_status="closed", distance=1)]})
    poi = search(MapboxPoiProvider(TOKEN)).pois[0]
    assert poi.name == "Preferred name"
    assert poi.provider_id == "id"
    assert poi.address == "1 Main"
    assert poi.category_ids == ("indian_restaurant",)
    assert poi.status == "closed"
    assert not hasattr(poi, "distance")


def test_unknown_concept_uses_safe_text_search_with_restaurant_filter(response_stub):
    calls = response_stub({"type": "FeatureCollection", "features": []})
    result = search(MapboxPoiProvider(TOKEN), "Congolese restaurant")
    assert result.pois == ()
    params = parse_qs(urlsplit(calls[1][0].full_url).query)
    assert urlsplit(calls[1][0].full_url).path.endswith("/forward")
    assert params["q"] == ["Congolese restaurant"]
    assert params["poi_category"] == ["restaurant"]
    assert params["types"] == ["poi"]
    assert params["limit"] == ["10"]
    assert "congolese_restaurant" not in calls[1][0].full_url


def test_broad_restaurant_concept_does_not_make_duplicate_call(response_stub):
    calls = response_stub({"type": "FeatureCollection", "features": []})
    assert search(MapboxPoiProvider(TOKEN), "Restaurant").query_count == len(calls) == 1


@pytest.mark.parametrize("coordinates", [[181, 0], [0, 91], [False, 0], ["1", 0], [None, 0], [0], [0, 0, 0], [float("nan"), 0]])
def test_malformed_coordinates_do_not_become_zero_results(response_stub, coordinates):
    response_stub({"type": "FeatureCollection", "features": [feature(coordinates)]})
    with pytest.raises(PoiError, match="unusable"):
        search(MapboxPoiProvider(TOKEN))


@pytest.mark.parametrize("payload", [{}, {"type": "FeatureCollection", "features": {}}, {"type": "FeatureCollection", "features": [None]}, {"type": "FeatureCollection", "features": [feature(name=None)]}, {"type": "FeatureCollection", "features": [feature(feature_type="place")]}])
def test_malformed_schema_is_unavailable_not_high_score(response_stub, payload):
    response_stub(payload)
    with pytest.raises(PoiError):
        search(MapboxPoiProvider(TOKEN))


def test_valid_results_survive_partial_bad_features_with_coverage_note(response_stub):
    response_stub({"type": "FeatureCollection", "features": [None, feature()]})
    result = search(MapboxPoiProvider(TOKEN))
    assert len(result.pois) == 2
    assert result.discarded_count == 2


def test_result_cap_is_detected_and_processing_is_bounded(response_stub):
    response_stub({"type": "FeatureCollection", "features": [feature()] * 100})
    result = search(MapboxPoiProvider(TOKEN))
    assert result.limit_reached
    assert len(result.pois) == 50


@pytest.mark.parametrize("raw", [b"not-json", b"[]", b"\xff", b"x" * (1024 * 1024 + 1)], ids=["bad-json", "wrong-root", "bad-encoding", "oversized"])
def test_bad_json_and_oversized_bodies_have_sanitized_errors(response_stub, raw):
    response_stub(raw)
    with pytest.raises(PoiError, match="unreadable"):
        search(MapboxPoiProvider(TOKEN))


@pytest.mark.parametrize("error", [URLError("access_token=private"), TimeoutError("private"), HTTPError("private", 401, "private", None, None), HTTPError("private", 403, "private", None, None), HTTPError("private", 429, "private", None, None), HTTPError("private", 500, "private", None, None)])
def test_http_and_network_failures_do_not_expose_tokens(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(mapbox_provider, "urlopen", fail)
    with pytest.raises(PoiError) as caught:
        search(MapboxPoiProvider(TOKEN))
    assert "private" not in str(caught.value)
    assert TOKEN not in str(caught.value)
    assert caught.value.__suppress_context__


@pytest.mark.parametrize("token", ["", None, "sk.test-placeholder", "pk.invalid whitespace"])
def test_unconfigured_provider_never_calls_network(monkeypatch, token):
    monkeypatch.setattr(mapbox_provider, "urlopen", lambda *args, **kwargs: pytest.fail("Unexpected network call"))
    with pytest.raises(PoiError, match="not configured"):
        search(MapboxPoiProvider(token))


@pytest.mark.parametrize("timeout", [None, "bad", 0, -1, 31, float("nan"), float("inf")])
def test_invalid_timeout_uses_central_default(timeout):
    assert MapboxPoiProvider(TOKEN, timeout=timeout).timeout == 6


def test_partial_query_failure_does_not_mislabel_incomplete_analysis(monkeypatch):
    calls = []

    def open_request(request, timeout):
        calls.append(request)
        if len(calls) == 2:
            raise TimeoutError("private")
        return io.BytesIO(json.dumps({"type": "FeatureCollection", "features": [feature()]}).encode())

    monkeypatch.setattr(mapbox_provider, "urlopen", open_request)
    with pytest.raises(PoiError):
        search(MapboxPoiProvider(TOKEN))
    assert len(calls) == 2


def test_category_endpoint_rejects_types_regression(monkeypatch):
    def open_request(request, timeout):
        parsed = urlsplit(request.full_url)
        if "/category/" in parsed.path and "types" in parse_qs(parsed.query):
            raise HTTPError("private", 400, "unknown field types", None, None)
        return io.BytesIO(json.dumps({"type": "FeatureCollection", "features": [feature()]}).encode())

    monkeypatch.setattr(mapbox_provider, "urlopen", open_request)
    assert len(search(MapboxPoiProvider(TOKEN)).pois) == 2


def test_failure_logs_only_endpoint_and_status(monkeypatch, caplog):
    def fail(*args, **kwargs):
        raise HTTPError(f"https://private?access_token={TOKEN}", 400, "secret body", None, None)

    monkeypatch.setattr(mapbox_provider, "urlopen", fail)
    with pytest.raises(PoiError, match="rejected the search request"):
        search(MapboxPoiProvider(TOKEN))
    assert "endpoint=category status=400" in caplog.text
    assert TOKEN not in caplog.text
    assert "secret body" not in caplog.text
    assert "access_token=" not in caplog.text
