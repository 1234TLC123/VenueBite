from copy import deepcopy
from datetime import date
from io import BytesIO
import json
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest
from shapely.geometry import Point

from venuebite.providers.regrid_provider import (
    MAX_RESPONSE_BYTES, NoRedirect, POINT_ENDPOINT, RegridProvider, fallback_radius,
    normalize_parcel, request_timeout,
)
from venuebite.providers.site_provider import SiteError, parcel_geometry, safe_source_url


UUID = "12345678-1234-4234-8234-123456789abc"
POLYGON = {"type": "Polygon", "coordinates": [[[-105, 39], [-104, 39], [-104, 40], [-105, 40], [-105, 39]]]}


def feature(**attributes):
    return {"type": "Feature", "geometry": deepcopy(POLYGON), "properties": {"fields": {
        "ll_uuid": UUID, "parcelnumb": "APN-01", "address": "123 Sample St", **attributes,
    }}}


def payload(*features):
    return {"parcels": {"type": "FeatureCollection", "features": list(features)}}


def install_response(provider, value=None, *, failure=None, raw=None):
    calls = []
    def open_request(request, timeout):
        calls.append((request, timeout))
        if failure:
            raise failure
        return BytesIO(raw if raw is not None else json.dumps(value).encode())
    provider._opener = SimpleNamespace(open=open_request)
    return calls


def test_verified_endpoint_header_parameters_and_small_record_limit():
    provider = RegridProvider("synthetic-private-token")
    calls = install_response(provider, payload(feature()))
    record, = provider.lookup(39.5, -104.5)
    request, timeout = calls[0]
    assert request.full_url.startswith(POINT_ENDPOINT + "?")
    assert parse_qs(urlsplit(request.full_url).query) == {
        "lat": ["39.5"], "lon": ["-104.5"], "radius": ["0"], "limit": ["2"],
        "return_geometry": ["true"], "return_stacked": ["true"], "return_custom": ["false"],
        "return_matched_buildings": ["false"], "return_matched_addresses": ["false"],
        "return_enhanced_ownership": ["false"], "return_zoning": ["false"],
    }
    assert request.get_header("Authorization") == "Bearer synthetic-private-token"
    assert "synthetic-private-token" not in request.full_url
    assert timeout == 8 and record.regrid_id == UUID
    assert record.geometry.covers(Point(-104.5, 39.5))


def test_documented_field_semantics_and_no_personal_owner_attributes():
    record = normalize_parcel(feature(
        ll_gisacre="1.25", ll_gissqft=54450, usecode="C", usedesc="Commercial",
        zoning="MU", zoning_description="Mixed use", zoning_type="Mixed",
        ll_bldg_count="2", structno="3", area_building="8000", area_building_definition="Gross floor area",
        ll_bldg_footprint_sqft=4000, yearbuilt="1980", landval=200000, improvval="300000",
        parvaltype="Assessed", saleprice=550000, saledate="2018-06-01", geoid="08031",
        ll_last_refresh="2025-06-02", sourceurl="https://county.example/parcel/01",
        owner="Private owner", mailadd="Private mailing address",
    ))
    assert record.parcel_area_acres == 1.25 and record.parcel_area_sqft == 54450
    assert record.building_count == 2 and record.assessor_structure_count == 3
    assert record.building_area_sqft == 8000 and record.building_footprint_sqft == 4000
    assert record.building_area_definition == "Gross floor area" and record.year_built == 1980
    assert record.land_value == 200000 and record.improvement_value == 300000
    assert record.value_type == "Assessed" and record.last_sale_price == 550000
    assert record.last_sale_date == date(2018, 6, 1) and record.provider_refresh_date == date(2025, 6, 2)
    assert record.county_fips == "08031" and record.zoning_description == "Mixed use"
    assert "Private owner" not in repr(record) and "Private mailing" not in repr(record)
    assert dict(record.field_availability)["building_count"]
    assert record.geojson()["type"] == "Polygon"


def test_properties_level_documented_uuid_and_missing_optional_attributes():
    data = feature()
    del data["properties"]["fields"]["ll_uuid"]
    data["properties"]["ll_uuid"] = UUID
    record = normalize_parcel(data)
    assert record.regrid_id == UUID and record.building_count is None
    assert record.zoning_code == "" and record.land_value is None
    assert not dict(record.field_availability)["building_count"]


@pytest.mark.parametrize("value", [None, "", "n/a", "bad", -1, True, float("nan"), float("inf"), "-999999999", {}, 1e20])
def test_invalid_numeric_fields_are_unknown_not_zero(value):
    record = normalize_parcel(feature(ll_gisacre=value, landval=value, area_building=value, ll_bldg_count=value))
    assert record.parcel_area_acres is record.land_value is record.building_area_sqft is record.building_count is None


def test_real_zeros_preserved_and_fractional_count_rejected():
    record = normalize_parcel(feature(ll_bldg_count=0, structno=1.5, landval=0, improvval="0"))
    assert record.building_count == record.land_value == record.improvement_value == 0
    assert record.assessor_structure_count is None


@pytest.mark.parametrize("value", ["2025-02-30", "2025/01/01", "2025-01-01T00:00:00Z", 2025, None])
def test_malformed_dates_omitted(value):
    record = normalize_parcel(feature(saledate=value, ll_last_refresh=value))
    assert record.last_sale_date is record.provider_refresh_date is None


@pytest.mark.parametrize("year", [0, 999, 9999, True, "unknown", 1980.5])
def test_invalid_build_years_omitted(year):
    assert normalize_parcel(feature(yearbuilt=year)).year_built is None


@pytest.mark.parametrize("value", [None, [], {}, {"features": []}, {"parcels": {}},
    {"parcels": {"type": "FeatureCollection", "features": None}}, payload(None), payload({}),
    payload(feature(), feature(), feature()), payload({"type": "Feature", "properties": {"fields": {}}, "geometry": None}),
])
def test_malformed_response_not_silently_interpreted_as_empty(value):
    with pytest.raises(SiteError, match="Parcel provider"):
        RegridProvider.parse(value)


def test_empty_response_and_ambiguity_are_preserved():
    assert RegridProvider.parse(payload()) == ()
    assert len(RegridProvider.parse(payload(feature(), feature(parcelnumb="APN-02")))) == 2
    with pytest.raises(SiteError):
        RegridProvider.parse(payload(feature(), None))


@pytest.mark.parametrize("geometry", [None, {}, {"type": "Point", "coordinates": [-104, 39]},
    {"type": "Polygon", "coordinates": []}, {"type": "Polygon", "coordinates": [[[-104, 39]]]},
    {"type": "MultiPolygon", "coordinates": "bad"},
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [0, 1], [1, 0], [0, 0]]]},
    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [2, 0], [0, 0]]]},
])
def test_bad_geometry_removed_while_attributes_remain(geometry):
    data = feature(landval=12)
    data["geometry"] = geometry
    record = normalize_parcel(data)
    assert record.geometry is None and record.land_value == 12 and record.parcel_number == "APN-01"


@pytest.mark.parametrize("point", [[181, 0], [0, 91], [True, 0], [float("nan"), 0], [float("inf"), 0], ["1", 0], [1, 0, 2], None])
def test_invalid_geometry_coordinate_removed(point):
    geometry = deepcopy(POLYGON)
    geometry["coordinates"][0][1] = point
    assert parcel_geometry(geometry) is None


def test_unclosed_and_oversized_rings_rejected():
    geometry = deepcopy(POLYGON)
    geometry["coordinates"][0][-1] = [-105, 39.1]
    assert parcel_geometry(geometry) is None
    assert parcel_geometry({"type": "Polygon", "coordinates": [[[-105, 39]] * 10001]}) is None


def test_valid_multipolygon_and_holes_preserve_topology():
    geometry = deepcopy(POLYGON)
    geometry["coordinates"].append([[-104.8, 39.2], [-104.2, 39.2], [-104.2, 39.8], [-104.8, 39.8], [-104.8, 39.2]])
    parcel = parcel_geometry(geometry)
    assert parcel.is_valid and not parcel.covers(Point(-104.5, 39.5))
    multi = parcel_geometry({"type": "MultiPolygon", "coordinates": [geometry["coordinates"]]})
    assert multi.is_valid and multi.geom_type == "MultiPolygon"


@pytest.mark.parametrize("url", [None, "javascript:alert(1)", "data:text/html,x", "//evil.example", "https://u:p@example.com", "https://example.com:bad", "https://localhost/a", "https://example.com/\nx", "https://[bad/a", "https://example.com/?token=synthetic-private"])
def test_unsafe_source_urls_not_displayed(url):
    assert safe_source_url(url) == ""


@pytest.mark.parametrize("status,code", [(401, "authorization"), (403, "restricted"), (429, "rate_limit"), (500, "http_error"), (302, "http_error")])
def test_http_failures_have_safe_messages_logs_and_no_retry(status, code, caplog):
    provider = RegridProvider("synthetic-secret")
    error = HTTPError("https://example.com/?token=synthetic-secret", status, "synthetic-secret", {}, BytesIO(b"synthetic-secret"))
    calls = install_response(provider, failure=error)
    with pytest.raises(SiteError) as raised:
        provider.lookup(39, -104)
    assert raised.value.code == code and "synthetic-secret" not in str(raised.value)
    assert "synthetic-secret" not in caplog.text and len(calls) == 1
    assert f"status={status}" in caplog.text


@pytest.mark.parametrize("failure", [URLError("synthetic-secret"), TimeoutError("synthetic-secret"), OSError("synthetic-secret")])
def test_network_failures_sanitized(failure):
    provider = RegridProvider("synthetic-secret")
    install_response(provider, failure=failure)
    with pytest.raises(SiteError) as raised:
        provider.lookup(39, -104)
    assert raised.value.code == "network" and "synthetic-secret" not in str(raised.value)


@pytest.mark.parametrize("raw", [b"not JSON synthetic-secret", b"\xff", b"x" * (MAX_RESPONSE_BYTES + 1)], ids=["not-json", "invalid-encoding", "oversized"])
def test_invalid_and_oversized_body_sanitized(raw):
    provider = RegridProvider("synthetic-secret")
    install_response(provider, raw=raw)
    with pytest.raises(SiteError) as raised:
        provider.lookup(39, -104)
    assert raised.value.code == "invalid_response" and "synthetic-secret" not in str(raised.value)


@pytest.mark.parametrize("token", [None, "", "your_regrid_api_token_here", "two words", "bad\nheader"])
def test_missing_or_invalid_token_makes_no_request(token):
    provider = RegridProvider(token)
    calls = install_response(provider, payload())
    with pytest.raises(SiteError) as raised:
        provider.lookup(39, -104)
    assert raised.value.code == "not_configured" and not calls


@pytest.mark.parametrize("lat,lon", [(91, 0), (0, 181), (True, 0), (float("nan"), 0), (None, 0)])
def test_invalid_coordinates_make_no_request(lat, lon):
    provider = RegridProvider("synthetic-secret")
    calls = install_response(provider, payload())
    with pytest.raises(SiteError):
        provider.lookup(lat, lon)
    assert not calls


@pytest.mark.parametrize("radius", [True, -1, 31, 1000, "25", 25.5])
def test_invalid_radius_makes_no_request(radius):
    provider = RegridProvider("synthetic-secret")
    calls = install_response(provider, payload())
    with pytest.raises(SiteError):
        provider.lookup(39, -104, radius_meters=radius)
    assert not calls


@pytest.mark.parametrize("value", [None, "bad", 0, -1, 31, True, float("nan"), float("inf")])
def test_timeout_is_bounded(value):
    assert request_timeout(value) == 8


@pytest.mark.parametrize("value", [None, "bad", -1, 31, True, "25.5"])
def test_fallback_configuration_is_bounded(value):
    assert fallback_radius(value) == 25


def test_supported_config_and_redirect_header_protection():
    assert request_timeout("10.5") == 10.5 and fallback_radius("0") == 0 and fallback_radius(30) == 30
    assert NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example") is None
