from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AreaInsight:
    label: str
    value: str
    detail: str
    icon: str


@dataclass(frozen=True)
class Competitor:
    name: str
    concept: str
    distance: str
    price: str


@dataclass(frozen=True)
class LocationData:
    location: str
    concept: str
    factor_scores: Mapping[str, float]
    area_insights: tuple[AreaInsight, ...]
    competitors: tuple[Competitor, ...]
    is_demo: bool
    source_label: str


class DataProviderError(Exception):
    """A provider could not supply the requested location data."""


class LocationDataProvider(Protocol):
    def get_location_data(self, location: str, concept: str) -> LocationData:
        ...
