"""Deterministic MVP scoring; weights are assumptions, not validated predictions."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import fsum, isfinite
from numbers import Real
from types import MappingProxyType


@dataclass(frozen=True)
class FactorDefinition:
    key: str
    label: str
    weight: float
    description: str
    strength: str
    risk: str
    icon: str


# Preserve the prototype's weights. Rent and competition are opportunity scores:
# higher rent scores mean more affordable rent, not higher asking prices.
FACTOR_DEFINITIONS = (
    FactorDefinition(
        "population", "Population", 0.30,
        "Higher scores indicate a stronger potential customer base.",
        "The population factor supports a stronger potential customer base.",
        "The population factor suggests a limited potential customer base.",
        "users",
    ),
    FactorDefinition(
        "income", "Income", 0.30,
        "Higher scores indicate stronger household purchasing power.",
        "The income factor supports stronger household purchasing power.",
        "The income factor suggests purchasing power needs closer review.",
        "wallet",
    ),
    FactorDefinition(
        "rent", "Rent", 0.20,
        "Higher scores indicate more affordable occupancy costs.",
        "The rent factor suggests more manageable occupancy costs.",
        "The rent factor suggests occupancy costs may pressure margins.",
        "building-2",
    ),
    FactorDefinition(
        "competition", "Competition", 0.20,
        "Higher scores indicate less direct competitive pressure.",
        "The competition factor suggests less direct competitive pressure.",
        "The competition factor suggests differentiation needs closer review.",
        "utensils",
    ),
)
WEIGHTS = MappingProxyType({factor.key: factor.weight for factor in FACTOR_DEFINITIONS})


@dataclass(frozen=True)
class FactorResult:
    key: str
    label: str
    score: float
    weight: float
    weight_percent: int
    description: str
    signal: str
    icon: str


@dataclass(frozen=True)
class Insight:
    label: str
    score: float
    explanation: str
    key: str = ""


@dataclass(frozen=True)
class ScoreResult:
    overall_score: float
    classification: str
    classification_key: str
    factors: tuple[FactorResult, ...]
    strengths: tuple[Insight, ...]
    risks: tuple[Insight, ...]


def _validated_score(value, label):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a number between 0 and 100.")
    try:
        score = float(value)
    except (OverflowError, ValueError):
        raise ValueError(f"{label} must be a finite number between 0 and 100.") from None
    if not isfinite(score) or not 0 <= score <= 100:
        raise ValueError(f"{label} must be a finite number between 0 and 100.")
    return score


def classify_score(score):
    score = _validated_score(score, "Overall score")
    if score >= 80:
        return "Strong opportunity", "strong"
    if score >= 65:
        return "Promising opportunity", "promising"
    if score >= 50:
        return "Mixed opportunity", "mixed"
    return "Challenging opportunity", "challenging"


def calculate_opportunity(factor_scores):
    if not isinstance(factor_scores, Mapping):
        raise ValueError("Factor scores must be a mapping.")
    if set(factor_scores) != set(WEIGHTS):
        raise ValueError("Factor scores must include exactly population, income, rent, and competition.")

    factors = []
    strengths = []
    risks = []
    for definition in FACTOR_DEFINITIONS:
        score = _validated_score(factor_scores[definition.key], definition.label)
        signal = "strong" if score >= 75 else "watch" if score < 65 else "balanced"
        factors.append(FactorResult(
            key=definition.key,
            label=definition.label,
            score=score,
            weight=definition.weight,
            weight_percent=round(definition.weight * 100),
            description=definition.description,
            signal=signal,
            icon=definition.icon,
        ))
        if signal == "strong":
            strengths.append(Insight(definition.label, score, definition.strength, definition.key))
        elif signal == "watch":
            risks.append(Insight(definition.label, score, definition.risk, definition.key))

    overall = round(fsum(factor.score * factor.weight for factor in factors), 1)
    classification, classification_key = classify_score(overall)
    return ScoreResult(
        overall, classification, classification_key,
        tuple(factors), tuple(strengths), tuple(risks),
    )
