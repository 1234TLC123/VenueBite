"""Straight-line spherical distances, not driving distances or travel times."""

import math

EARTH_RADIUS_METERS = 6_371_008.8
METERS_PER_MILE = 1609.344
ALLOWED_RADIUS_MILES = (1, 3, 5)
DEFAULT_RADIUS_MILES = 3


def haversine_meters(latitude, longitude, other_latitude, other_longitude):
    lat1, lat2 = math.radians(latitude), math.radians(other_latitude)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(other_longitude - longitude)
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * math.asin(math.sqrt(min(1, max(0, a))))


def miles_label(meters):
    return f"{meters / METERS_PER_MILE:.2f} mi" if meters is not None else "Not returned"


def search_bounds(latitude, longitude, radius_meters):
    """Bound the circle; omit a bbox when it would cross a pole or antimeridian."""
    angle = radius_meters / EARTH_RADIUS_METERS
    delta_lat = math.degrees(angle)
    if abs(latitude) + delta_lat >= 90:
        return None
    delta_lon = math.degrees(math.asin(min(1, math.sin(angle) / math.cos(math.radians(latitude)))))
    if longitude - delta_lon < -180 or longitude + delta_lon > 180:
        return None
    return longitude - delta_lon, latitude - delta_lat, longitude + delta_lon, latitude + delta_lat
