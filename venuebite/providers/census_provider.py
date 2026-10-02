"""Bounded, server-only Census transport and header-based ACS normalization."""

import json
import logging
from math import isfinite
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from venuebite.providers.demographic_provider import (
    ACS_VARIABLES, ACS_YEAR, CENSUS_BENCHMARK, CENSUS_VINTAGE,
    INCOME_ESTIMATE, INCOME_MOE, POPULATION_ESTIMATE, POPULATION_MOE,
    CensusError, CensusTract, DemographicData,
)
from venuebite.providers.location_provider import LocationError, validate_coordinates


logger = logging.getLogger(__name__)
MAX_RESPONSE_BYTES = 1024 * 1024
DEFAULT_TIMEOUT = 8


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # A rejected key can redirect to HTML. Never forward credentials elsewhere.
        return None


def request_timeout(value):
    try:
        timeout = float(value)
        return timeout if isfinite(timeout) and 0 < timeout <= 30 else DEFAULT_TIMEOUT
    except (TypeError, ValueError, OverflowError):
        return DEFAULT_TIMEOUT


class CensusClient:
    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.timeout = request_timeout(timeout)
        self._opener = build_opener(NoRedirect())

    def _request(self, endpoint, params, family):
        request = Request(endpoint + "?" + urlencode(params), headers={"Accept": "application/json", "User-Agent": "VenueBite/4"})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ValueError
                return json.loads(raw)
        except HTTPError as error:
            logger.warning("Census request failed: endpoint=%s status=%s", family, error.code)
            code = "authorization" if error.code in {301, 302, 303, 307, 308, 401, 403} else "rate_limit" if error.code == 429 else "http_error"
            raise CensusError(code) from None
        except (URLError, TimeoutError, OSError):
            raise CensusError("network") from None
        except (ValueError, UnicodeDecodeError, RecursionError):
            raise CensusError("invalid_response") from None


def _text(value):
    return " ".join(value.split())[:300] if isinstance(value, str) else ""


class CensusGeoProvider(CensusClient):
    endpoint = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"

    def lookup(self, latitude, longitude):
        try:
            latitude, longitude = validate_coordinates(latitude, longitude)
        except LocationError:
            raise CensusError("invalid_coordinates") from None
        payload = self._request(self.endpoint, {
            "x": longitude, "y": latitude, "benchmark": CENSUS_BENCHMARK,
            "vintage": CENSUS_VINTAGE, "format": "json",
        }, "geographies")
        try:
            geographies = payload["result"]["geographies"]
            tracts = geographies.get("Census Tracts", [])
            if not isinstance(tracts, list):
                raise CensusError("invalid_response")
            if not tracts:
                raise CensusError("no_tract")
            if len(tracts) != 1:
                raise CensusError("ambiguous_geography")
            item = tracts[0]
            def name(layer):
                rows = geographies.get(layer)
                return _text(rows[0].get("NAME")) if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict) else ""
            tract = CensusTract(item["STATE"], item["COUNTY"], item["TRACT"], _text(item.get("NAME")), name("States"), name("Counties"))
            if item.get("GEOID") != tract.geoid:
                raise CensusError("invalid_geography")
            return tract
        except (KeyError, TypeError, AttributeError, IndexError):
            raise CensusError("invalid_response") from None


def _annotation(value):
    text = _text(value)
    return "" if text.lower() == "null" else text


def _estimate(value, annotation=""):
    # All negative ACS codes are metadata, not measurements. Controlled MOEs
    # remain unavailable rather than claiming a literal zero sampling error.
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    text = str(value)
    if not re.fullmatch(r"[0-9]{1,15}", text) or annotation:
        return None
    return int(text)


class CensusDemographicProvider(CensusClient):
    endpoint = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"

    def __init__(self, key, *, timeout=DEFAULT_TIMEOUT):
        super().__init__(timeout)
        self._key = key.strip() if isinstance(key, str) else ""
        self.enabled = bool(self._key) and not any(c.isspace() for c in self._key) and "your_" not in self._key.lower()

    def fetch(self, geography):
        if not self.enabled:
            raise CensusError("not_configured")
        payload = self._request(self.endpoint, {
            "get": ",".join(("NAME", *ACS_VARIABLES)),
            "for": "tract:" + geography.tract_fips,
            "in": f"state:{geography.state_fips} county:{geography.county_fips}",
            "key": self._key,
        }, "acs5")
        return self.parse(payload, geography)

    @staticmethod
    def parse(payload, geography):
        if payload == [] or (isinstance(payload, list) and len(payload) == 1):
            raise CensusError("no_data")
        if not isinstance(payload, list) or len(payload) != 2:
            raise CensusError("invalid_response")
        headers, row = payload
        if not isinstance(headers, list) or not isinstance(row, list) or len(headers) != len(row):
            raise CensusError("invalid_response")
        if not all(isinstance(header, str) for header in headers) or len(set(headers)) != len(headers):
            raise CensusError("invalid_response")
        values = dict(zip(headers, row))
        if not {"NAME", "state", "county", "tract"} <= values.keys():
            raise CensusError("invalid_response")
        # Exact returned geography guards against stale/wrong rows and lost zeros.
        if [values[part] for part in ("state", "county", "tract")] != [geography.state_fips, geography.county_fips, geography.tract_fips]:
            raise CensusError("geography_mismatch")
        name = _text(values["NAME"])
        if not name:
            raise CensusError("invalid_response")
        pop_a, income_a = (_annotation(values.get(variable + "A")) for variable in (POPULATION_ESTIMATE, INCOME_ESTIMATE))
        pop_ma, income_ma = (_annotation(values.get(variable + "A")) for variable in (POPULATION_MOE, INCOME_MOE))
        population = _estimate(values.get(POPULATION_ESTIMATE), pop_a)
        income = _estimate(values.get(INCOME_ESTIMATE), income_a)
        return DemographicData(
            geography=geography, population=population, median_household_income=income,
            population_moe=_estimate(values.get(POPULATION_MOE), pop_ma) if population is not None else None,
            income_moe=_estimate(values.get(INCOME_MOE), income_ma) if income is not None else None,
            population_annotation=pop_a, income_annotation=income_a,
            population_moe_annotation=pop_ma, income_moe_annotation=income_ma,
            geography_name=name,
            reason="Some ACS estimates are unavailable or annotated; their scores use demo fallback." if population is None or income is None else "",
        )
