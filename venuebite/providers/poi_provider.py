from dataclasses import dataclass
from typing import Protocol

from venuebite.concepts import ConceptProfile
from venuebite.providers.location_provider import GeographicLocation, validate_coordinates


class PoiError(Exception):
    """A sanitized provider failure; never include response bodies or credentials."""


@dataclass(frozen=True)
class RestaurantPoi:
    name: str
    latitude: float
    longitude: float
    provider_id: str | None = None
    provider: str = "mapbox"
    address: str = ""
    category_ids: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    status: str | None = None
    search_categories: tuple[str, ...] = ()

    def __post_init__(self):
        latitude, longitude = validate_coordinates(self.latitude, self.longitude)
        if not isinstance(self.name, str) or not self.name.strip() or len(self.name) > 200 or any(ord(char) < 32 or ord(char) == 127 for char in self.name):
            raise ValueError("The restaurant provider returned an invalid name.")
        object.__setattr__(self, "name", " ".join(self.name.split()))
        object.__setattr__(self, "latitude", latitude)
        object.__setattr__(self, "longitude", longitude)


@dataclass(frozen=True)
class PoiSearchResult:
    pois: tuple[RestaurantPoi, ...]
    attribution: str = ""
    query_count: int = 0
    limit_reached: bool = False
    discarded_count: int = 0


class RestaurantPoiProvider(Protocol):
    enabled: bool

    def search(self, location: GeographicLocation, concept: ConceptProfile, radius_meters: float) -> PoiSearchResult:
        ...
