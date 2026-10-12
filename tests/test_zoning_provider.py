from io import BytesIO
import json
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

from venuebite.providers.denver_zoning_provider import DenverZoningProvider, BOUNDARY_LAYER, ZONING_LAYER, OUT_FIELDS, MAX_BYTES, NoRedirect
from venuebite.providers.zoning_provider import ZoningError


LAT, LON = 39.7392, -104.9909
GEOMETRY = {"type": "Polygon", "coordinates": [[[-105, 39], [-104, 39], [-104, 40], [-105, 40], [-105, 39]]]}


def collection(properties=None, *, geometry=None):
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": properties or {}, "geometry": geometry or GEOMETRY}]}


def zone(version=2010):
    return collection({"ZONE_DISTRICT": "D-CV", "ZCODE_VERSION": version, "ZONE_DESCRIPTION": "Downtown Civic",
                       "OVERLAY_DISTRICT": None, "WAIVERS": None, "CONDITIONS": None, "PUD_NUM": None})


def installed(*results):
    provider = DenverZoningProvider()
    pending, calls = list(results), []
    def opened(request, timeout):
        calls.append((request, timeout))
        result = pending.pop(0)
        if isinstance(result, Exception):
            raise result
        return BytesIO(result if isinstance(result, bytes) else json.dumps(result).encode())
    provider.opener = SimpleNamespace(open=opened)
    return provider, calls


def test_verified_schema_and_point_query_normalization():
    provider, calls = installed(collection({"COUNTY": "Denver"}), zone())
    result = provider.lookup(LAT, LON)
    assert result.status == "identified" and result.jurisdiction_id == "08031"
    assert result.record.district == "D-CV" and result.record.code_family == 2010
    assert result.record.overlay == "" and result.record.pud_number == ""
    assert result.retrieved_at.endswith("+00:00")
    for index, layer in enumerate((BOUNDARY_LAYER, ZONING_LAYER)):
        request, timeout = calls[index]
        assert request.full_url.startswith(layer + "/query?") and timeout == 6
        params = parse_qs(urlsplit(request.full_url).query)
        assert params == {"f": ["geojson"], "geometry": [f"{LON},{LAT}"], "geometryType": ["esriGeometryPoint"],
                          "inSR": ["4326"], "outSR": ["4326"], "spatialRel": ["esriSpatialRelIntersects"],
                          "outFields": ["COUNTY" if index == 0 else OUT_FIELDS], "returnGeometry": ["true"], "resultRecordCount": ["2"]}
    assert "geometry" not in vars(result) and "coordinates" not in vars(result.record)


@pytest.mark.parametrize("version", [1959, None, 2030])
def test_code_family_is_reported_not_guessed(version):
    provider, _ = installed(collection({"COUNTY": "Denver"}), zone(version))
    assert provider.lookup(LAT, LON).record.code_family == version


@pytest.mark.parametrize("latitude,longitude", [(True, 0), (None, 0), (91, 0), (0, 181), (float("nan"), 0), (0, float("inf")), ("invalid", 0)])
def test_invalid_point_makes_no_request(latitude, longitude):
    provider, calls = installed()
    with pytest.raises(ZoningError):
        provider.lookup(latitude, longitude)
    assert not calls


@pytest.mark.parametrize("timeout", [None, "bad", 0, -1, 16, float("inf"), float("nan")])
def test_bounded_timeout(timeout):
    assert DenverZoningProvider(timeout=timeout).timeout == 6


def test_unconfigured_provider_and_endpoint_security():
    provider, calls = installed()
    provider.enabled = False
    assert provider.lookup(LAT, LON).status == "unavailable" and not calls
    for url in ("http://services1.arcgis.com", "https://evil.example/", "http://127.0.0.1/private", ZONING_LAYER + "/../query"):
        with pytest.raises(ZoningError): provider._query(url, LAT, LON, "COUNTY")
    assert not calls
    assert NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example/") is None


@pytest.mark.parametrize("county", ["Arapahoe", "Adams", "Jefferson"])
def test_authoritative_neighbor_jurisdiction_stops_zoning_request(county):
    provider, calls = installed(collection({"COUNTY": county}))
    result = provider.lookup(LAT, LON)
    assert result.status == "unsupported" and result.jurisdiction == county + " County" and len(calls) == 1


def test_no_boundary_match_is_unsupported_without_inventing_jurisdiction():
    provider, calls = installed({"type": "FeatureCollection", "features": []})
    result = provider.lookup(LAT, LON)
    assert result.status == "unsupported" and result.jurisdiction == "" and len(calls) == 1


def test_no_zone_match_preserves_confirmed_denver_and_missing_district():
    provider, calls = installed(collection({"COUNTY": "Denver"}), {"type": "FeatureCollection", "features": []})
    result = provider.lookup(LAT, LON)
    assert result.status == "no_match" and result.jurisdiction_id == "08031" and result.record is None
    assert len(calls) == 2


@pytest.mark.parametrize("stage", ["boundary", "zone"])
@pytest.mark.parametrize("condition", ["multiple", "capped", "edge"])
def test_ambiguity_never_selects_a_district(stage, condition):
    payload = collection({"COUNTY": "Denver"}) if stage == "boundary" else zone()
    if condition == "multiple": payload["features"] *= 2
    elif condition == "capped": payload["exceededTransferLimit"] = True
    else: payload["features"][0]["geometry"] = {"type": "Polygon", "coordinates": [[[LON, 39], [-104, 39], [-104, 40], [LON, 40], [LON, 39]]]}
    provider, _ = installed(*([collection({"COUNTY": "Denver"})] if stage == "zone" else []), payload)
    result = provider.lookup(LAT, LON)
    assert result.status == "ambiguous" and result.record is None


@pytest.mark.parametrize("payload", [None, [], {}, {"error": {"message": "synthetic-private"}}, {"type": "FeatureCollection"},
    {"type": "FeatureCollection", "features": [None]}, {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": []}]},
    b'{"type":"FeatureCollection","type":"FeatureCollection","features":[]}', b'{"features":NaN}', b'not JSON', b'x' * (MAX_BYTES + 1)],
    ids=["null", "array", "empty", "provider-error", "missing-features", "null-feature", "bad-properties", "duplicate", "nan", "not-json", "oversized"])
def test_bad_json_bounded_and_sanitized(payload, caplog):
    provider, _ = installed(payload)
    with pytest.raises(ZoningError) as error: provider.lookup(LAT, LON)
    assert "synthetic-private" not in str(error.value) + caplog.text


@pytest.mark.parametrize("field,bad", [("ZONE_DISTRICT", ""), ("ZONE_DISTRICT", {}), ("ZCODE_VERSION", True), ("ZCODE_VERSION", "2010"),
                                     ("ZONE_DESCRIPTION", []), ("WAIVERS", "x" * 201)])
def test_malformed_zone_fields_are_unavailable(field, bad):
    payload = zone()
    payload["features"][0]["properties"][field] = bad
    provider, _ = installed(collection({"COUNTY": "Denver"}), payload)
    with pytest.raises(ZoningError): provider.lookup(LAT, LON)


@pytest.mark.parametrize("change", ["missing_version", "wrong_crs", "wrong_geometry", "missing_geometry", "not_containing"])
def test_incomplete_or_untrustworthy_geometry_rejected(change):
    payload = zone()
    if change == "missing_version": del payload["features"][0]["properties"]["ZCODE_VERSION"]
    elif change == "wrong_crs": payload["crs"] = {"properties": {"name": "EPSG:2877"}}
    elif change == "wrong_geometry": payload["features"][0]["geometry"] = {"type": "Point", "coordinates": [LON, LAT]}
    elif change == "missing_geometry": payload["features"][0].pop("geometry")
    else: payload["features"][0]["geometry"] = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
    provider, _ = installed(collection({"COUNTY": "Denver"}), payload)
    with pytest.raises(ZoningError): provider.lookup(LAT, LON)


@pytest.mark.parametrize("error", [TimeoutError("synthetic-private"), URLError("synthetic-private"),
    HTTPError("https://example.test/token=synthetic-private", 429, "synthetic-private", {}, BytesIO()),
    HTTPError("https://example.test", 500, "synthetic-private", {}, BytesIO()), HTTPError("https://example.test", 302, "redirect", {}, BytesIO())])
def test_upstream_errors_do_not_leak_payloads(error, caplog):
    provider, _ = installed(error)
    with pytest.raises(ZoningError) as caught: provider.lookup(LAT, LON)
    assert "synthetic-private" not in str(caught.value) + caplog.text
