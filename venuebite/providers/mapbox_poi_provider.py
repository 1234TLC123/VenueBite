"""Request-scoped Search Box discovery; no persistent storage or per-POI calls."""

import math
from numbers import Real
from urllib.parse import quote

from venuebite.distance import EARTH_RADIUS_METERS, search_bounds
from venuebite.providers.location_provider import LocationError, validate_coordinates
from venuebite.providers.mapbox_provider import MapboxSearchClient
from venuebite.providers.poi_provider import PoiError, PoiSearchResult, RestaurantPoi

CATEGORY_LIMIT = 25
TEXT_LIMIT = 10


def clean_text(value, limit=200):
    if not isinstance(value, str) or any(ord(char) < 32 or ord(char) == 127 for char in value):
        return ""
    return " ".join(value.split())[:limit]


def string_list(value):
    if not isinstance(value, list):
        return ()
    return tuple(dict.fromkeys(text for item in value[:50] if (text := clean_text(item, 100))))


class MapboxPoiProvider(MapboxSearchClient):
    def _normalize(self, feature, category):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("Invalid feature")
        properties, geometry = feature.get("properties"), feature.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict) or geometry.get("type") != "Point":
            raise ValueError("Invalid point")
        if properties.get("feature_type", "poi") != "poi":
            raise ValueError("Not a POI")
        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 2 or any(isinstance(v, bool) or not isinstance(v, Real) for v in coordinates):
            raise ValueError("Invalid coordinates")
        latitude, longitude = validate_coordinates(coordinates[1], coordinates[0])
        name = clean_text(properties.get("name_preferred")) or clean_text(properties.get("name"))
        if not name:
            raise ValueError("Missing name")
        status = properties.get("operational_status")
        return RestaurantPoi(
            name=name, latitude=latitude, longitude=longitude,
            provider_id=clean_text(properties.get("mapbox_id"), 512) or None,
            address=clean_text(properties.get("full_address"), 400) or clean_text(properties.get("address"), 400),
            category_ids=string_list(properties.get("poi_category_ids")),
            categories=string_list(properties.get("poi_category")),
            status=status if status in ("active", "closed") else None,
            search_categories=(category,) if category else (),
        )

    def search(self, location, concept, radius_meters):
        if not self.enabled:
            raise PoiError("Live competition is not configured. Set a public Mapbox token to enable it.")
        common = {
            "proximity": f"{location.longitude},{location.latitude}",
            "show_closed_pois": "false",
        }
        bounds = search_bounds(location.latitude, location.longitude, radius_meters)
        if bounds:
            common["bbox"] = ",".join(str(value) for value in bounds)
        else:
            # Search Box radius is in degrees, not meters. Final filtering is always spherical.
            common["radius"] = min(10, math.degrees(radius_meters / EARTH_RADIUS_METERS) / max(0.001, math.cos(math.radians(location.latitude))))
        # Category is inherently POI-only. The live endpoint rejects `types` despite its docs listing it.
        queries = [("category/restaurant", {"limit": CATEGORY_LIMIT}, "restaurant", CATEGORY_LIMIT)]
        if concept.category and concept.category != "restaurant":
            queries.append((f"category/{quote(concept.category, safe='')}", {"limit": CATEGORY_LIMIT}, concept.category, CATEGORY_LIMIT))
        elif concept.approximate:
            queries.append(("forward", {"q": concept.label, "types": "poi", "poi_category": "restaurant", "limit": TEXT_LIMIT}, None, TEXT_LIMIT))
        pois, attributions, discarded, capped = [], [], 0, False
        for endpoint, params, category, limit in queries:
            try:
                payload = self._request_json(endpoint, {**common, **params})
            except LocationError as error:
                # Retain helpful, sanitized transport guidance without echoing upstream text.
                message = str(error).replace("Location search", "Nearby competition search").replace("location search", "competition search")
                raise PoiError(message) from None
            features = payload.get("features")
            if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
                raise PoiError("Mapbox returned invalid restaurant data. Live competition is unavailable.")
            capped = capped or len(features) >= limit
            normalized = []
            for feature in features[:limit]:
                try:
                    normalized.append(self._normalize(feature, category))
                except (ValueError, TypeError, LocationError):
                    discarded += 1
            if features and not normalized:
                raise PoiError("Mapbox returned unusable restaurant data. Live competition is unavailable.")
            pois.extend(normalized)
            attribution = clean_text(payload.get("attribution"), 2000)
            if attribution and attribution not in attributions:
                attributions.append(attribution)
        return PoiSearchResult(tuple(pois), " | ".join(attributions), len(queries), capped, discarded)
