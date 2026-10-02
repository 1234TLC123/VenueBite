import json
from numbers import Real
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

from venuebite.providers.location_provider import (
    GeographicLocation, LocationError, LocationSuggestion,
    validate_coordinates, validate_identifier, validate_query, validate_session,
)


PUBLIC_TOKEN_MESSAGE = "Set MAPBOX_ACCESS_TOKEN in .env to enable real location search and maps. Demo analysis is available."
FEATURE_TYPES = "country,region,postcode,district,place,locality,neighborhood,street,address,poi"


def public_token(token):
    if isinstance(token, str):
        token = token.strip()
        if token.startswith("pk.") and len(token) <= 2048 and not any(char.isspace() for char in token):
            return token
    return ""


def _text(value):
    return " ".join(value.split()) if isinstance(value, str) else ""


def _display_name(properties):
    name = _text(properties.get("name_preferred")) or _text(properties.get("name"))
    if not name or any(ord(char) < 32 or ord(char) == 127 for char in name):
        raise ValueError("Missing location name")
    address = _text(properties.get("full_address"))
    context = _text(properties.get("place_formatted"))
    if address:
        result = f"{name}, {address}" if properties.get("feature_type") == "poi" else address
    elif context and not context.casefold().startswith(name.casefold()):
        result = f"{name}, {context}"
    else:
        result = context or name
    return result[:200]


class MapboxLocationProvider:
    base_url = "https://api.mapbox.com/search/searchbox/v1"

    def __init__(self, token, *, countries="", request_origin="", timeout=6):
        self._token = public_token(token)
        self.enabled = bool(self._token)
        self.configuration_message = (
            "MAPBOX_ACCESS_TOKEN must be a public pk. token. Server-only secret tokens are not exposed."
            if token and not self.enabled else PUBLIC_TOKEN_MESSAGE
        )
        self.countries = countries
        self.timeout = timeout
        try:
            origin = urlsplit(request_origin)
        except ValueError:
            origin = urlsplit("")
        self.request_origin = request_origin if origin.scheme in {"http", "https"} and origin.netloc and not origin.username and not origin.password else ""

    def _request_json(self, endpoint, params):
        if not self.enabled:
            raise LocationError(self.configuration_message, code="not_configured")
        params = {**params, "access_token": self._token, "language": "en"}
        if self.countries and not endpoint.startswith("retrieve/"):
            params["country"] = self.countries
        headers = {"Accept": "application/json", "User-Agent": "VenueBite/2"}
        if self.request_origin:
            headers["Referer"] = self.request_origin
        request = Request(f"{self.base_url}/{endpoint}?{urlencode(params)}", headers=headers)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(1024 * 1024 + 1)
                if len(raw) > 1024 * 1024:
                    raise ValueError("Oversized provider response")
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise ValueError("Unexpected provider response")
                return payload
        except HTTPError as error:
            if error.code in {401, 403}:
                message = "Mapbox rejected the configuration. Check the public token, scopes, and URL restrictions."
            elif error.code == 429:
                message = "Location search is busy. Wait a moment and try again."
            else:
                message = "Location search is temporarily unavailable. Please try again."
            raise LocationError(message) from None
        except (URLError, TimeoutError, OSError):
            raise LocationError("Location search could not connect. Please try again.") from None
        except (ValueError, UnicodeDecodeError, RecursionError):
            raise LocationError("Mapbox returned an unreadable response. Please try another search.", code="invalid_response", status=502) from None

    def suggest(self, query, session_token):
        payload = self._request_json("suggest", {
            "q": validate_query(query), "session_token": validate_session(session_token),
            "limit": 6, "types": FEATURE_TYPES,
        })
        suggestions = payload.get("suggestions")
        if not isinstance(suggestions, list):
            raise LocationError("Mapbox returned invalid suggestions. Please try again.", code="invalid_response", status=502)
        results = []
        for item in suggestions[:10]:
            try:
                if not isinstance(item, dict) or item.get("feature_type") == "category":
                    continue
                identifier = validate_identifier(item.get("mapbox_id"))
                place_type = item.get("feature_type")
                if place_type not in FEATURE_TYPES.split(","):
                    continue
                results.append(LocationSuggestion(_display_name(item), identifier, place_type, "mapbox"))
            except (ValueError, LocationError):
                continue
        if suggestions and not results:
            raise LocationError("Mapbox returned unusable suggestions. Please try another search.", code="invalid_response", status=502)
        return results, _text(payload.get("attribution"))[:2000]

    def _normalize_feature(self, feature):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("Invalid feature")
        geometry, properties = feature.get("geometry"), feature.get("properties")
        if not isinstance(geometry, dict) or not isinstance(properties, dict) or geometry.get("type") != "Point":
            raise ValueError("Invalid point")
        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 2 or any(isinstance(value, bool) or not isinstance(value, Real) for value in coordinates):
            raise ValueError("Invalid coordinates")
        latitude, longitude = validate_coordinates(coordinates[1], coordinates[0])
        bbox = properties.get("bbox")
        normalized_bbox = None
        if isinstance(bbox, list) and len(bbox) == 4:
            try:
                south, west = validate_coordinates(bbox[1], bbox[0])
                north, east = validate_coordinates(bbox[3], bbox[2])
                if west < east and south < north:
                    normalized_bbox = (west, south, east, north)
            except LocationError:
                pass
        place_type = properties.get("feature_type")
        if place_type not in FEATURE_TYPES.split(","):
            raise ValueError("Invalid location type")
        return GeographicLocation(
            display_name=_display_name(properties), latitude=latitude, longitude=longitude,
            place_type=place_type, provider="mapbox",
            provider_id=validate_identifier(properties.get("mapbox_id")), bbox=normalized_bbox,
        )

    def _location_from_response(self, payload):
        features = payload.get("features")
        if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
            raise LocationError("Mapbox returned invalid location data.", code="invalid_response", status=502)
        if not features:
            raise LocationError("No matching location found. Try a more specific location.", code="no_results", status=404)
        for feature in features[:10]:
            try:
                return self._normalize_feature(feature)
            except (ValueError, TypeError, LocationError):
                continue
        raise LocationError("Mapbox returned unusable location data. Try another location.", code="invalid_response", status=502)

    def retrieve(self, identifier, session_token):
        identifier = validate_identifier(identifier)
        payload = self._request_json(f"retrieve/{quote(identifier, safe='')}", {"session_token": validate_session(session_token)})
        location = self._location_from_response(payload)
        if location.provider_id != identifier:
            raise LocationError("Mapbox returned a different location. Select a suggestion again.", code="invalid_response", status=502)
        return location

    def forward(self, query):
        payload = self._request_json("forward", {"q": validate_query(query), "limit": 1, "types": FEATURE_TYPES})
        return self._location_from_response(payload)
