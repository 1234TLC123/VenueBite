from dataclasses import asdict, dataclass
from math import isfinite
from typing import Protocol
from uuid import UUID
import re


class LocationError(Exception):
    def __init__(self, message, *, code="provider_unavailable", status=503):
        super().__init__(message)
        self.code = code
        self.status = status


def validate_coordinates(latitude, longitude):
    if isinstance(latitude, bool) or isinstance(longitude, bool):
        raise LocationError("Latitude and longitude must be valid numbers.", code="invalid_coordinates", status=400)
    try:
        latitude, longitude = float(latitude), float(longitude)
    except (TypeError, ValueError, OverflowError):
        raise LocationError("Latitude and longitude must be valid numbers.", code="invalid_coordinates", status=400) from None
    if not isfinite(latitude) or not -90 <= latitude <= 90:
        raise LocationError("Latitude must be between -90 and 90.", code="invalid_coordinates", status=400)
    if not isfinite(longitude) or not -180 <= longitude <= 180:
        raise LocationError("Longitude must be between -180 and 180.", code="invalid_coordinates", status=400)
    return latitude, longitude


def validate_query(query):
    if not isinstance(query, str):
        raise LocationError("Enter a location to search.", code="invalid_query", status=400)
    query = " ".join(query.split())
    if not 2 <= len(query) <= 200 or any(ord(char) < 32 or ord(char) == 127 for char in query):
        raise LocationError("Search with 2 to 200 characters.", code="invalid_query", status=400)
    return query


def validate_session(session_token):
    try:
        value = UUID(session_token)
        if value.version != 4:
            raise ValueError
        return str(value)
    except (ValueError, TypeError, AttributeError):
        raise LocationError("Start a new location search and try again.", code="invalid_session", status=400) from None


def validate_identifier(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9:._=+\-]{0,511}", identifier):
        raise LocationError("Select a valid location suggestion.", code="invalid_identifier", status=400)
    return identifier


@dataclass(frozen=True)
class LocationSuggestion:
    display_name: str
    provider_id: str
    place_type: str
    provider: str

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class GeographicLocation:
    display_name: str
    latitude: float
    longitude: float
    place_type: str
    provider: str
    provider_id: str
    bbox: tuple[float, float, float, float] | None = None
    country_code: str | None = None

    def __post_init__(self):
        latitude, longitude = validate_coordinates(self.latitude, self.longitude)
        if not isinstance(self.display_name, str) or not self.display_name.strip() or len(self.display_name) > 200:
            raise LocationError("The location provider returned an invalid name.", code="invalid_response", status=502)
        validate_identifier(self.provider_id)
        if not isinstance(self.place_type, str) or not isinstance(self.provider, str):
            raise LocationError("The location provider returned invalid data.", code="invalid_response", status=502)
        object.__setattr__(self, "latitude", latitude)
        object.__setattr__(self, "longitude", longitude)
        if self.country_code is not None:
            if not isinstance(self.country_code, str) or not re.fullmatch(r"[A-Za-z]{2}", self.country_code):
                raise LocationError("The location provider returned invalid country data.", code="invalid_response", status=502)
            object.__setattr__(self, "country_code", self.country_code.lower())

    def to_dict(self):
        result = asdict(self)
        if self.country_code is None:
            result.pop("country_code")
        return result


class GeographicLocationProvider(Protocol):
    enabled: bool
    configuration_message: str

    def suggest(self, query: str, session_token: str) -> tuple[list[LocationSuggestion], str]:
        ...

    def retrieve(self, identifier: str, session_token: str) -> GeographicLocation:
        ...

    def forward(self, query: str) -> GeographicLocation:
        ...
