"""Coordinate-free regulatory provider contracts; lookup points are session-only."""

from dataclasses import dataclass
from typing import Protocol


class ZoningError(Exception):
    def __init__(self):
        super().__init__("Official zoning data is temporarily unavailable.")


@dataclass(frozen=True)
class ZoningRecord:
    district: str
    description: str = ""
    code_family: int | None = None
    neighborhood_context: str = ""
    district_group: str = ""
    use_form: str = ""
    district_type: str = ""
    overlay: str = ""
    waivers: str = ""
    conditions: str = ""
    pud_number: str = ""


@dataclass(frozen=True)
class ZoningLookup:
    status: str
    retrieved_at: str = ""
    jurisdiction: str = ""
    jurisdiction_id: str = ""
    record: ZoningRecord | None = None


class ZoningProvider(Protocol):
    enabled: bool

    def lookup(self, latitude: float, longitude: float) -> ZoningLookup:
        ...
