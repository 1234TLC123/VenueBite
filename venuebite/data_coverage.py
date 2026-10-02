"""Weighted usable evidence, independent of opportunity scores and uncertainty."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import fsum
from types import MappingProxyType

from venuebite.scoring import FACTOR_DEFINITIONS, WEIGHTS


COVERAGE_CREDITS = MappingProxyType({
    "real": 1.0, "partial": 0.5, "demo": 0.0, "fallback": 0.0, "unavailable": 0.0,
})
COVERAGE_BANDS = (
    (90, "Very high data coverage", "very-high"),
    (70, "High data coverage", "high"),
    (50, "Moderate data coverage", "moderate"),
    (25, "Limited data coverage", "limited"),
    (0, "Very limited data coverage", "very-limited"),
)
COVERAGE_WARNING_THRESHOLD = 70


@dataclass(frozen=True)
class FactorCoverage:
    key: str
    status: str
    weight: float
    credit: float
    coverage_points: float


@dataclass(frozen=True)
class DataCoverage:
    percent: float
    label: str
    key: str
    factors: tuple[FactorCoverage, ...]
    warning: str


def calculate_data_coverage(statuses):
    if not isinstance(statuses, Mapping) or set(statuses) != set(WEIGHTS):
        raise ValueError("Coverage requires exactly the four factor statuses.")
    factors = []
    for definition in FACTOR_DEFINITIONS:
        status = statuses[definition.key]
        if not isinstance(status, str) or status not in COVERAGE_CREDITS:
            raise ValueError("Unknown factor coverage status.")
        credit = COVERAGE_CREDITS[status]
        factors.append(FactorCoverage(definition.key, status, definition.weight,
                                      credit, definition.weight * credit * 100))
    percent = round(min(100.0, max(0.0, fsum(item.coverage_points for item in factors))), 1)
    _, label, key = next(band for band in COVERAGE_BANDS if percent >= band[0])
    warning = ""
    if percent < COVERAGE_WARNING_THRESHOLD:
        warning = "Data gaps need verification: some model factors are demo, fallback, partial, or unavailable."
    return DataCoverage(percent, label, key, tuple(factors), warning)
