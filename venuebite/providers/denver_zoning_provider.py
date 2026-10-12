"""Official Denver boundary and zoning point queries, never nearby district guessing."""

from datetime import datetime, timezone
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from shapely.geometry import Point

from venuebite.providers.location_provider import validate_coordinates, LocationError
from venuebite.providers.site_provider import parcel_geometry
from venuebite.providers.zoning_provider import ZoningError, ZoningLookup, ZoningRecord


HOST_ROOT = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/"
BOUNDARY_LAYER = HOST_ROOT + "ODC_ENG_SRVCCDBOUNDARY_A/FeatureServer/40"
ZONING_LAYER = HOST_ROOT + "ODC_ZONE_ZONING_A/FeatureServer/209"
FIELDS = {
    "description": "ZONE_DESCRIPTION", "neighborhood_context": "NBHD_CONTEXT",
    "district_group": "ZONE_DISTRICT_GROUP", "use_form": "ZONE_USE_FORM",
    "district_type": "ZONE_DIST_TYPE", "overlay": "OVERLAY_DISTRICT",
    "waivers": "WAIVERS", "conditions": "CONDITIONS", "pud_number": "PUD_NUM",
}
OUT_FIELDS = "ZONE_DISTRICT,ZCODE_VERSION," + ",".join(FIELDS.values())
MAX_BYTES = 1024 * 1024
logger = logging.getLogger(__name__)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError()
        result[key] = value
    return result


def _text(value):
    if value is None:
        return ""
    if not isinstance(value, str) or len(value) > 200 or any(ord(c) < 32 for c in value):
        raise ZoningError()
    return value.strip()


class DenverZoningProvider:
    def __init__(self, *, enabled=True, timeout=6):
        self.enabled = enabled
        try:
            value = float(timeout)
            self.timeout = value if 0 < value <= 15 else 6
        except (ValueError, TypeError, OverflowError):
            self.timeout = 6
        self.opener = build_opener(NoRedirect())

    def _query(self, layer, latitude, longitude, fields):
        # Even internal callers cannot turn this client into an arbitrary URL fetcher.
        if layer not in (BOUNDARY_LAYER, ZONING_LAYER):
            raise ZoningError()
        params = {"f": "geojson", "geometry": f"{longitude},{latitude}",
                  "geometryType": "esriGeometryPoint", "inSR": 4326, "outSR": 4326,
                  "spatialRel": "esriSpatialRelIntersects", "outFields": fields,
                  "returnGeometry": "true", "resultRecordCount": 2}
        request = Request(layer + "/query?" + urlencode(params), headers={"Accept": "application/geo+json, application/json"})
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError()
            data = json.loads(body, object_pairs_hook=_unique, parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
            if not isinstance(data, dict) or "error" in data or data.get("type") != "FeatureCollection":
                raise ValueError()
            features = data.get("features")
            if not isinstance(features, list) or len(features) > 2:
                raise ValueError()
            if data.get("exceededTransferLimit"):
                return None
            crs = data.get("crs")
            if crs and crs.get("properties", {}).get("name") not in ("urn:ogc:def:crs:OGC:1.3:CRS84", "urn:ogc:def:crs:EPSG::4326", "EPSG:4326"):
                raise ValueError()
            for feature in features:
                if not isinstance(feature, dict) or feature.get("type") != "Feature" or not isinstance(feature.get("properties"), dict):
                    raise ValueError()
            return features
        except (HTTPError, URLError, OSError, ValueError, TypeError, AttributeError, RecursionError):
            logger.warning("Denver regulatory query unavailable; no response details retained")
            raise ZoningError() from None

    def lookup(self, latitude, longitude):
        try:
            latitude, longitude = validate_coordinates(latitude, longitude)
        except LocationError:
            raise ZoningError() from None
        if not self.enabled:
            return ZoningLookup("unavailable")
        timestamp = datetime.now(timezone.utc).isoformat()
        point = Point(longitude, latitude)
        boundaries = self._query(BOUNDARY_LAYER, latitude, longitude, "COUNTY")
        if boundaries is None or len(boundaries) > 1:
            return ZoningLookup("ambiguous", timestamp)
        if not boundaries:
            return ZoningLookup("unsupported", timestamp)
        boundary = boundaries[0]
        county = _text(boundary["properties"].get("COUNTY"))
        if not county:
            raise ZoningError()
        geometry = parcel_geometry(boundary.get("geometry"))
        if geometry is None or not geometry.covers(point):
            raise ZoningError()
        if not geometry.contains(point):
            return ZoningLookup("ambiguous", timestamp)
        if county != "Denver":
            return ZoningLookup("unsupported", timestamp, county + " County")
        context = {"retrieved_at": timestamp, "jurisdiction": "City and County of Denver", "jurisdiction_id": "08031"}
        zones = self._query(ZONING_LAYER, latitude, longitude, OUT_FIELDS)
        if zones is None or len(zones) > 1:
            return ZoningLookup("ambiguous", **context)
        if not zones:
            return ZoningLookup("no_match", **context)
        feature = zones[0]
        geometry = parcel_geometry(feature.get("geometry"))
        if geometry is None or not geometry.covers(point):
            raise ZoningError()
        if not geometry.contains(point):
            return ZoningLookup("ambiguous", **context)
        properties = feature["properties"]
        if "ZONE_DISTRICT" not in properties or "ZCODE_VERSION" not in properties:
            raise ZoningError()
        district = _text(properties["ZONE_DISTRICT"])
        version = properties["ZCODE_VERSION"]
        if not district or version is not None and (type(version) is not int or not 0 < version < 10000):
            raise ZoningError()
        record = ZoningRecord(district, code_family=version, **{name: _text(properties.get(field)) for name, field in FIELDS.items()})
        return ZoningLookup("identified", record=record, **context)
