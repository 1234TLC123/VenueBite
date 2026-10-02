"""Competition model v1: a transparent heuristic over a capped observed sample."""

from dataclasses import dataclass
from math import isfinite

from venuebite.distance import METERS_PER_MILE

MODEL_VERSION = "competition-v1"
DIRECT_PRESSURE_POINTS = 10
GENERAL_PRESSURE_POINTS = 1.5
HALF_SCORE_PRESSURE = 40
DISTANCE_BANDS = ((0.5, 1.0), (1, 0.7), (3, 0.35), (5, 0.15))
LOW_PRESSURE_SCORE = 75
MODERATE_PRESSURE_SCORE = 45


@dataclass(frozen=True)
class CompetitionScore:
    score: float
    pressure: float
    level: str
    version: str = MODEL_VERSION


def calculate_competition(rows):
    pressure = 0.0
    for row in rows:
        if not isfinite(row.distance_meters) or row.distance_meters < 0:
            raise ValueError("Competition distances must be finite and nonnegative.")
        miles = row.distance_meters / METERS_PER_MILE
        multiplier = next((weight for boundary, weight in DISTANCE_BANDS if miles <= boundary), 0)
        pressure += (DIRECT_PRESSURE_POINTS if row.is_direct else GENERAL_PRESSURE_POINTS) * multiplier
    score = round(100 / (1 + pressure / HALF_SCORE_PRESSURE), 1)
    level = "Low" if score >= LOW_PRESSURE_SCORE else "Moderate" if score >= MODERATE_PRESSURE_SCORE else "High"
    return CompetitionScore(score, round(pressure, 2), level)
