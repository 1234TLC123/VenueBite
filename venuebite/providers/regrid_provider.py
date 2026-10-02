"""Server-only Regrid point adapter, verified against official v2 docs/schema."""

from dataclasses import fields, replace
from datetime import date
import json
import logging
from math import isfinite
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID

from venuebite.providers.location_provider import LocationError, validate_coordinates
from venuebite.providers.site_provider import ParcelRecord, SiteError, parcel_geometry, safe_source_url


REGRID_BASE_URL = "https://app.regrid.com/api/v2"
POINT_ENDPOINT = REGRID_BASE_URL + "/parcels/point"
PARCEL_RESULT_LIMIT = 2
MAX_RESPONSE_BYTES = 1024 * 1024
DEFAULT_TIMEOUT = 8
DEFAULT_FALLBACK_RADIUS_METERS = 25
logger = logging.getLogger(__name__)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_timeout(value):
    try:
        timeout = float(value)
        return timeout if not isinstance(value, bool) and isfinite(timeout) and 0 < timeout <= 30 else DEFAULT_TIMEOUT
    except (TypeError, ValueError, OverflowError):
        return DEFAULT_TIMEOUT


def fallback_radius(value):
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]{1,2}", str(value)):
        return DEFAULT_FALLBACK_RADIUS_METERS
    radius = int(value)
    return radius if 0 <= radius <= 30 else DEFAULT_FALLBACK_RADIUS_METERS


def _text(value):
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split())[:300]
    return "" if text.lower() in {"null", "none", "n/a"} else text


def _number(value, *, integer=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    try:
        number = float(value)
        if not isfinite(number) or not 0 <= number <= 1e15 or (integer and not number.is_integer()):
            return None
        return int(number) if integer else number
    except (ValueError, OverflowError):
        return None


def _date(value):
    try:
        return date.fromisoformat(value) if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) else None
    except ValueError:
        return None


def _uuid(value):
    try:
        return str(UUID(value)) if isinstance(value, str) else ""
    except ValueError:
        return ""


def normalize_parcel(feature):
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise SiteError("invalid_response")
    properties = feature.get("properties")
    data = properties.get("fields") if isinstance(properties, dict) else None
    if not isinstance(data, dict):
        raise SiteError("invalid_response")
    year = _number(data.get("yearbuilt"), integer=True)
    year = year if year is not None and 1000 <= year <= date.today().year else None
    county = _text(data.get("geoid"))
    parcel = ParcelRecord(
        regrid_id=_uuid(data.get("ll_uuid")) or _uuid(properties.get("ll_uuid")),
        parcel_number=_text(data.get("parcelnumb")), display_address=_text(data.get("address")),
        parcel_area_acres=_number(data.get("ll_gisacre")), parcel_area_sqft=_number(data.get("ll_gissqft")),
        land_use_code=_text(data.get("usecode")), land_use_description=_text(data.get("usedesc")),
        zoning_code=_text(data.get("zoning")), zoning_description=_text(data.get("zoning_description")), zoning_type=_text(data.get("zoning_type")),
        building_count=_number(data.get("ll_bldg_count"), integer=True), assessor_structure_count=_number(data.get("structno"), integer=True),
        building_area_sqft=_number(data.get("area_building")), building_area_definition=_text(data.get("area_building_definition")),
        building_footprint_sqft=_number(data.get("ll_bldg_footprint_sqft")), year_built=year,
        land_value=_number(data.get("landval")), improvement_value=_number(data.get("improvval")), value_type=_text(data.get("parvaltype")),
        last_sale_price=_number(data.get("saleprice")), last_sale_date=_date(data.get("saledate")),
        county_fips=county if re.fullmatch(r"\d{5}", county) else "",
        geometry=parcel_geometry(feature.get("geometry")), provider_refresh_date=_date(data.get("ll_last_refresh")),
        source_url=safe_source_url(data.get("sourceurl")),
    )
    if not parcel.regrid_id and not parcel.parcel_number and parcel.geometry is None:
        raise SiteError("invalid_response")
    availability = tuple((field.name, getattr(parcel, field.name) is not None and getattr(parcel, field.name) != "")
                         for field in fields(parcel) if field.name != "field_availability")
    return replace(parcel, field_availability=availability)


class RegridProvider:
    def __init__(self, token, *, timeout=DEFAULT_TIMEOUT):
        self._token = token.strip() if isinstance(token, str) else ""
        self.enabled = bool(self._token) and len(self._token) <= 4096 and "your_" not in self._token.lower() and not any(c.isspace() or ord(c) < 32 for c in self._token)
        self.timeout = request_timeout(timeout)
        self._opener = build_opener(NoRedirect())

    def lookup(self, latitude, longitude, *, radius_meters=0):
        if not self.enabled:
            raise SiteError("not_configured")
        try:
            latitude, longitude = validate_coordinates(latitude, longitude)
        except LocationError:
            raise SiteError("invalid_coordinates") from None
        if isinstance(radius_meters, bool) or not isinstance(radius_meters, int) or not 0 <= radius_meters <= 30:
            raise SiteError("invalid_radius")
        params = {"lat": latitude, "lon": longitude, "radius": radius_meters, "limit": PARCEL_RESULT_LIMIT,
                  "return_geometry": "true", "return_stacked": "true", "return_custom": "false",
                  "return_matched_buildings": "false", "return_matched_addresses": "false", "return_enhanced_ownership": "false", "return_zoning": "false"}
        request = Request(POINT_ENDPOINT + "?" + urlencode(params), headers={
            "Authorization": "Bearer " + self._token, "Accept": "application/json", "User-Agent": "VenueBite/6",
        })
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ValueError
                payload = json.loads(raw)
        except HTTPError as error:
            logger.warning("Regrid request failed: endpoint=point status=%s", error.code)
            code = "authorization" if error.code == 401 else "restricted" if error.code == 403 else "rate_limit" if error.code == 429 else "http_error"
            raise SiteError(code) from None
        except (URLError, TimeoutError, OSError):
            raise SiteError("network") from None
        except (ValueError, UnicodeDecodeError, RecursionError):
            raise SiteError("invalid_response") from None
        return self.parse(payload)

    @staticmethod
    def parse(payload):
        collection = payload.get("parcels") if isinstance(payload, dict) else None
        if not isinstance(collection, dict) or collection.get("type") != "FeatureCollection":
            raise SiteError("invalid_response")
        features = collection.get("features")
        if not isinstance(features, list) or len(features) > PARCEL_RESULT_LIMIT:
            raise SiteError("invalid_response")
        # Do not discard a malformed second record and accidentally turn ambiguity into an exact match.
        return tuple(normalize_parcel(feature) for feature in features)
