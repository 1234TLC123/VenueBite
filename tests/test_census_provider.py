from io import BytesIO
import json
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

from venuebite.providers.census_provider import (
    CensusClient, CensusDemographicProvider, CensusGeoProvider, MAX_RESPONSE_BYTES, NoRedirect,
)
from venuebite.providers.demographic_provider import (
    ACS_VARIABLES, ACS_YEAR, CENSUS_BENCHMARK, CENSUS_VINTAGE, CensusError, CensusTract, DemographicData,
)


TRACT = CensusTract("08", "031", "002000", "Census Tract 20", "Colorado", "Denver County")
HEADERS = ["NAME", *ACS_VARIABLES, "state", "county", "tract"]
ROW = ["Census Tract 20; Denver County; Colorado", "3200", "160", None, None,
       "87000", "5000", None, None, "08", "031", "002000"]


def response(population="3200", income="87000"):
    row = ROW.copy()
    row[1], row[5] = population, income
    return [HEADERS.copy(), row]


def install_response(client, payload, *, failure=None, raw=None):
    calls = []
    def open_request(request, timeout):
        calls.append((request, timeout))
        if failure:
            raise failure
        return BytesIO(raw if raw is not None else json.dumps(payload).encode())
    client._opener = SimpleNamespace(open=open_request)
    return calls


def geographic_payload():
    return {"result": {"geographies": {
        "Census Tracts": [{"STATE": "08", "COUNTY": "031", "TRACT": "002000", "GEOID": TRACT.geoid, "NAME": TRACT.name}],
        "States": [{"NAME": "Colorado"}], "Counties": [{"NAME": "Denver County"}],
    }}}


def test_documented_coordinate_parameters_and_normalization():
    provider = CensusGeoProvider()
    calls = install_response(provider, geographic_payload())
    assert provider.lookup(39.7392, -104.9903) == TRACT
    request, timeout = calls[0]
    assert urlsplit(request.full_url).path.endswith("/geographies/coordinates")
    assert parse_qs(urlsplit(request.full_url).query) == {
        "x": ["-104.9903"], "y": ["39.7392"], "benchmark": [CENSUS_BENCHMARK],
        "vintage": [CENSUS_VINTAGE], "format": ["json"],
    }
    assert timeout == 8


def test_optional_geography_names_are_not_required():
    provider = CensusGeoProvider()
    payload = geographic_payload()
    payload["result"]["geographies"].pop("States")
    payload["result"]["geographies"]["Counties"] = None
    install_response(provider, payload)
    result = provider.lookup(39, -104)
    assert result.geoid == TRACT.geoid
    assert result.state_name == result.county_name == ""


@pytest.mark.parametrize("latitude,longitude", [(91, 0), (0, 181), (float("nan"), 0), (0, float("inf")), (True, 0), (None, 0), ("bad", 0)])
def test_invalid_coordinates_make_no_request(latitude, longitude):
    provider = CensusGeoProvider()
    calls = install_response(provider, geographic_payload())
    with pytest.raises(CensusError):
        provider.lookup(latitude, longitude)
    assert not calls


@pytest.mark.parametrize("payload", [None, [], {}, {"result": {}}, {"result": {"geographies": None}},
    {"result": {"geographies": {"Census Tracts": []}}},
    {"result": {"geographies": {"Census Tracts": [None]}}},
    {"result": {"geographies": {"Census Tracts": [{"STATE": "08"}]}}},
])
def test_geography_schema_errors_are_sanitized(payload):
    provider = CensusGeoProvider()
    install_response(provider, payload)
    with pytest.raises(CensusError):
        provider.lookup(39, -104)


def test_geoid_mismatch_rejected():
    provider = CensusGeoProvider()
    payload = geographic_payload()
    payload["result"]["geographies"]["Census Tracts"][0]["GEOID"] = "99999999999"
    install_response(provider, payload)
    with pytest.raises(CensusError, match="Census data is unavailable"):
        provider.lookup(39, -104)


def test_multiple_tracts_are_explicitly_ambiguous_not_arbitrarily_selected():
    provider = CensusGeoProvider()
    payload = geographic_payload()
    payload["result"]["geographies"]["Census Tracts"].append({"STATE": "08", "COUNTY": "031", "TRACT": "002100", "GEOID": "08031002100"})
    install_response(provider, payload)
    with pytest.raises(CensusError) as error:
        provider.lookup(39, -104)
    assert error.value.code == "ambiguous_geography"


def test_fips_leading_zeros_and_derived_geoid():
    assert CensusTract(8, 31, 2000).geoid == TRACT.geoid
    assert CensusTract("8", "31", "2000").geoid == TRACT.geoid


@pytest.mark.parametrize("state,county,tract", [(None, "031", "002000"), (True, "031", "002000"),
    ("008", "031", "002000"), ("08", "3.1", "002000"), ("08", "", "002000"),
    ("08", "031", "2000.00"), ("08", "031", "-1"), ("99", "031", "002000"), ("72", "001", "000100")])
def test_invalid_or_unsupported_fips(state, county, tract):
    with pytest.raises(CensusError):
        CensusTract(state, county, tract)


def test_one_acs_request_all_variables_exact_tract_and_server_key():
    provider = CensusDemographicProvider("test-key", timeout=7)
    calls = install_response(provider, response())
    result = provider.fetch(TRACT)
    request, timeout = calls[0]
    assert request.full_url.startswith(f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5?")
    assert parse_qs(urlsplit(request.full_url).query) == {
        "get": [",".join(("NAME", *ACS_VARIABLES))], "for": ["tract:002000"],
        "in": ["state:08 county:031"], "key": ["test-key"],
    }
    assert timeout == 7 and len(calls) == 1
    assert result.population == 3200 and result.median_household_income == 87000
    assert result.population_moe == 160 and result.income_moe == 5000
    assert result.status == "available" and result.geography == TRACT
    assert "test-key" not in repr(result)


def test_header_order_and_extra_fields_do_not_matter():
    headers, row = response()
    values = dict(zip(headers, row))
    values["extra"] = "ignored"
    headers = sorted(values)
    result = CensusDemographicProvider.parse([headers, [values[key] for key in headers]], TRACT)
    assert result.population == 3200 and result.median_household_income == 87000


@pytest.mark.parametrize("bad", [None, "", "null", "N", "(X)", "-666666666", "-999999999", "-888888888",
    "-222222222", "-333333333", "-555555555", "-1", "NaN", "inf", "2.5", "1,000", True, {}, []])
def test_bad_population_keeps_independent_income(bad):
    result = CensusDemographicProvider.parse(response(bad), TRACT)
    assert result.population is None and result.population_moe is None
    assert result.median_household_income == 87000 and result.status == "partial"


@pytest.mark.parametrize("bad", [None, "", "-666666666", "NaN", "bad", False])
def test_bad_income_keeps_independent_population(bad):
    result = CensusDemographicProvider.parse(response(income=bad), TRACT)
    assert result.median_household_income is None and result.income_moe is None
    assert result.population == 3200 and result.status == "partial"


def test_zero_is_real_not_missing():
    result = CensusDemographicProvider.parse(response("0", "0"), TRACT)
    assert result.population == result.median_household_income == 0
    assert result.status == "available"


def test_missing_estimate_and_moe_variables_do_not_invent_values():
    headers = ["NAME", "B01003_001E", "state", "county", "tract"]
    result = CensusDemographicProvider.parse([headers, [ROW[0], "3200", "08", "031", "002000"]], TRACT)
    assert result.population == 3200
    assert result.population_moe is None and result.median_household_income is None
    assert result.status == "partial"
    result = CensusDemographicProvider.parse([headers[:1] + headers[2:], [ROW[0], "08", "031", "002000"]], TRACT)
    assert result.status == "unavailable"


@pytest.mark.parametrize("annotation", ["(X)", "-", "N", "250,000+", "2,500-"])
def test_estimate_annotations_are_not_exact_medians(annotation):
    payload = response()
    payload[1][7] = annotation
    result = CensusDemographicProvider.parse(payload, TRACT)
    assert result.median_household_income is None
    assert result.income_annotation == annotation
    assert result.population == 3200


def test_missing_or_annotated_moe_does_not_discard_estimate():
    payload = response()
    payload[1][2] = "-555555555"
    payload[1][4] = "*****"
    payload[1][6] = "-333333333"
    payload[1][8] = "***"
    result = CensusDemographicProvider.parse(payload, TRACT)
    assert result.status == "available"
    assert result.population_moe is None and result.income_moe is None
    assert result.population_moe_annotation == "*****"


@pytest.mark.parametrize("payload", [[], None, {}, [HEADERS], [None, ROW], [HEADERS, None],
    [HEADERS, ROW[:-1]], [HEADERS, ROW, ROW], [["NAME", "NAME"], ["A", "A"]],
    [[True], ["A"]], [["B01003_001E"], ["3200"]]])
def test_bad_acs_structure(payload):
    with pytest.raises(CensusError):
        CensusDemographicProvider.parse(payload, TRACT)


@pytest.mark.parametrize("part,value", [(0, None), (-3, "8"), (-2, "999"), (-1, "999999")])
def test_acs_name_and_geography_must_match(part, value):
    payload = response()
    payload[1][part] = value
    with pytest.raises(CensusError):
        CensusDemographicProvider.parse(payload, TRACT)


@pytest.mark.parametrize("failure", [URLError("test-key"), TimeoutError("test-key"), OSError("test-key")])
def test_network_failures_do_not_reveal_provider_errors(failure, caplog):
    provider = CensusDemographicProvider("test-key")
    install_response(provider, None, failure=failure)
    with pytest.raises(CensusError) as error:
        provider.fetch(TRACT)
    assert error.value.code == "network"
    assert "test-key" not in str(error.value) + caplog.text


@pytest.mark.parametrize("status", [302, 400, 401, 403, 429, 500, 503])
def test_http_errors_log_only_family_and_status(status, caplog):
    provider = CensusDemographicProvider("test-key")
    failure = HTTPError("https://api.census.gov/?key=test-key", status, "test-key", {}, BytesIO(b"test-key"))
    install_response(provider, None, failure=failure)
    with pytest.raises(CensusError) as error:
        provider.fetch(TRACT)
    assert f"endpoint=acs5 status={status}" in caplog.text
    assert "test-key" not in caplog.text + str(error.value)


@pytest.mark.parametrize("raw", [b"", b"<html>invalid key test-key</html>", b"\xff", b"x" * (MAX_RESPONSE_BYTES + 1)], ids=["empty", "html", "nonutf8", "oversized"])
def test_unreadable_and_oversized_response(raw):
    provider = CensusDemographicProvider("test-key")
    install_response(provider, None, raw=raw)
    with pytest.raises(CensusError) as error:
        provider.fetch(TRACT)
    assert error.value.code == "invalid_response" and "test-key" not in str(error.value)


@pytest.mark.parametrize("key", [None, "", "  ", "your_census_api_key_here", "key with space"])
def test_missing_key_makes_no_request(key):
    provider = CensusDemographicProvider(key)
    calls = install_response(provider, response())
    assert not provider.enabled
    with pytest.raises(CensusError):
        provider.fetch(TRACT)
    assert not calls


@pytest.mark.parametrize("timeout", [None, "bad", 0, -1, 31, float("nan"), float("inf")])
def test_invalid_timeouts_fall_back(timeout):
    assert CensusClient(timeout).timeout == 8


def test_redirects_never_forward_secret_query():
    assert NoRedirect().redirect_request(None, None, 302, "", {}, "https://elsewhere.invalid") is None


@pytest.mark.parametrize("value", [-1, True, "3200", float("nan")])
def test_normalized_record_rejects_non_real_estimates(value):
    with pytest.raises(CensusError):
        DemographicData(geography=TRACT, population=value)
