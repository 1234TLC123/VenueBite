"""Versioned tract-context heuristics, not demand or success predictions."""

from math import isfinite
from numbers import Real


POPULATION_MODEL_VERSION = "population-v1"
INCOME_MODEL_VERSION = "income-v1"
POPULATION_ANCHORS = ((0, 0), (1000, 25), (3000, 60), (6000, 85), (10000, 100))
INCOME_ANCHORS = ((0, 0), (25000, 20), (50000, 45), (75000, 65), (100000, 80), (150000, 100))
POPULATION_DESCRIPTION = "Tract population context only; not density, restaurant demand, or a customer trade area."
INCOME_DESCRIPTION = "Tract household purchasing-power context; not disposable income or restaurant spending."


def _context_score(value, anchors):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("Context estimates must be nonnegative finite numbers.")
    if value < 0:
        raise ValueError("Context estimates must be nonnegative finite numbers.")
    # Compare before float conversion so arbitrarily large valid integers cap safely.
    if isinstance(value, int) and value >= anchors[-1][0]:
        return 100.0
    if not isfinite(value):
        raise ValueError("Context estimates must be nonnegative finite numbers.")
    if value >= anchors[-1][0]:
        return 100.0
    for (low, low_score), (high, high_score) in zip(anchors, anchors[1:]):
        if value <= high:
            return round(low_score + (value - low) / (high - low) * (high_score - low_score), 1)
    raise ValueError("Invalid scoring anchors.")


def population_score(population):
    return _context_score(population, POPULATION_ANCHORS)


def income_score(median_household_income):
    return _context_score(median_household_income, INCOME_ANCHORS)
