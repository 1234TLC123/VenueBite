"""Normalized parcel contracts; missing evidence is not a negative property fact."""

from dataclasses import dataclass
from datetime import date
from math import isfinite
from numbers import Real
from typing import Protocol
from urllib.parse import parse_qsl, urlsplit

from shapely.errors import ShapelyError
from shapely.geometry import mapping, shape


MAX_GEOMETRY_POINTS = 10_000


class SiteError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__("Parcel provider request could not be completed.")


def parcel_geometry(value):
    """Bound structure and coordinates before GEOS validates polygon topology."""
    try:
        if not isinstance(value, dict) or value.get("type") not in {"Polygon", "MultiPolygon"}:
            return None
        coordinates = value["coordinates"]
        polygons = [coordinates] if value["type"] == "Polygon" else coordinates
        if not isinstance(polygons, (list, tuple)) or not polygons:
            return None
        count = 0
        for polygon in polygons:
            if not isinstance(polygon, (list, tuple)) or not polygon:
                return None
            for ring in polygon:
                if not isinstance(ring, (list, tuple)) or len(ring) < 4 or ring[0] != ring[-1]:
                    return None
                count += len(ring)
                if count > MAX_GEOMETRY_POINTS:
                    return None
                for point in ring:
                    if not isinstance(point, (list, tuple)) or len(point) != 2:
                        return None
                    lon, lat = point
                    if any(isinstance(v, bool) or not isinstance(v, Real) or not isfinite(v) for v in point):
                        return None
                    if not -180 <= lon <= 180 or not -90 <= lat <= 90:
                        return None
        geometry = shape({"type": value["type"], "coordinates": coordinates})
        return geometry if geometry.is_valid and not geometry.is_empty and geometry.area > 0 else None
    except (KeyError, TypeError, ValueError, OverflowError, ShapelyError):
        return None


def safe_source_url(value):
    if not isinstance(value, str) or len(value) > 2000 or any(c.isspace() or ord(c) < 32 for c in value):
        return ""
    try:
        url = urlsplit(value)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
            return ""
        if url.hostname.lower() in {"localhost", "127.0.0.1", "::1"}:
            return ""
        if any(key.lower() in {"token", "access_token", "api_token", "key", "api_key", "authorization", "password", "secret"}
               for key, _ in parse_qsl(url.query, max_num_fields=50)):
            return ""
        _ = url.port
        return value
    except ValueError:
        return ""


@dataclass(frozen=True)
class ParcelRecord:
    regrid_id: str = ""
    parcel_number: str = ""
    display_address: str = ""
    parcel_area_acres: float | None = None
    parcel_area_sqft: float | None = None
    land_use_code: str = ""
    land_use_description: str = ""
    zoning_code: str = ""
    zoning_description: str = ""
    zoning_type: str = ""
    building_count: int | None = None
    assessor_structure_count: int | None = None
    building_area_sqft: float | None = None
    building_area_definition: str = ""
    building_footprint_sqft: float | None = None
    year_built: int | None = None
    land_value: float | None = None
    improvement_value: float | None = None
    value_type: str = ""
    last_sale_price: float | None = None
    last_sale_date: date | None = None
    county_fips: str = ""
    geometry: object | None = None
    provider_refresh_date: date | None = None
    source_url: str = ""
    field_availability: tuple[tuple[str, bool], ...] = ()

    def geojson(self):
        return mapping(self.geometry) if self.geometry is not None else None


class SiteProvider(Protocol):
    enabled: bool

    def lookup(self, latitude: float, longitude: float, *, radius_meters: int = 0) -> tuple[ParcelRecord, ...]:
        ...
