"""Score Model v2: transparent composition, not a validated success prediction."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import fsum, isfinite
from numbers import Real
from types import MappingProxyType


VENUEBITE_SCORE_MODEL_VERSION = "2.0"
VENUEBITE_SCORE_MODEL_LABEL = "VenueBite Score Model v2"
STRENGTH_THRESHOLD = 75
RISK_THRESHOLD = 65
CLASSIFICATION_BANDS = (
    (80, "Strong opportunity", "strong"),
    (65, "Promising opportunity", "promising"),
    (50, "Mixed opportunity", "mixed"),
    (0, "Challenging opportunity", "challenging"),
)


@dataclass(frozen=True)
class FactorDefinition:
    key: str
    label: str
    weight: float
    description: str
    strength: str
    risk: str
    icon: str
    provenance_expected: str
    direction: str = "higher_is_better"


# Preserve the prototype's weights. Rent and competition are opportunity scores:
# higher rent scores mean more affordable rent, not higher asking prices.
FACTOR_DEFINITIONS = (
    FactorDefinition(
        "population", "Population", 0.30,
        "Higher scores indicate more favorable population context, not customer demand.",
        "The population factor supports more favorable demographic context.",
        "The population factor suggests demographic context needs closer review.",
        "users", "census",
    ),
    FactorDefinition(
        "income", "Income", 0.30,
        "Higher scores indicate stronger household purchasing power.",
        "The income factor supports stronger household purchasing power.",
        "The income factor suggests purchasing power needs closer review.",
        "wallet", "census",
    ),
    FactorDefinition(
        "rent", "Rent", 0.20,
        "Higher scores indicate more affordable occupancy costs.",
        "The rent factor suggests more manageable occupancy costs.",
        "The rent factor suggests occupancy costs may pressure margins.",
        "building-2", "demo",
    ),
    FactorDefinition(
        "competition", "Competition", 0.20,
        "Higher scores indicate less direct competitive pressure.",
        "The competition factor suggests less direct competitive pressure.",
        "The competition factor suggests differentiation needs closer review.",
        "utensils", "mapbox",
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

    @property
    def weighted_points(self):
        return self.score * self.weight

    @property
    def weighted_points_label(self):
        return f"{self.weighted_points:.2f}"


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
    raw_weighted_sum: float = 0
    model_version: str = VENUEBITE_SCORE_MODEL_VERSION
    model_label: str = VENUEBITE_SCORE_MODEL_LABEL


@dataclass(frozen=True)
class FactorTrace:
    key: str
    score: float
    weight: float
    weighted_points: float
    direction: str
    provenance_expected: str
    status: str
    provider: str
    model_version: str
    vintage: int | None
    geoid: str
    reason: str
    coverage_credit: float
    coverage_points: float


@dataclass(frozen=True)
class ScoreTrace:
    model_version: str
    factors: tuple[FactorTrace, ...]
    raw_weighted_sum: float
    final_score: float
    coverage: float


def build_score_trace(score, provenance, coverage):
    definitions = {item.key: item for item in FACTOR_DEFINITIONS}
    coverage_factors = {item.key: item for item in coverage.factors}
    factors = []
    for factor in score.factors:
        source, definition = provenance[factor.key], definitions[factor.key]
        evidence = coverage_factors[factor.key]
        factors.append(FactorTrace(
            factor.key, factor.score, factor.weight, factor.weighted_points,
            definition.direction, definition.provenance_expected, source.status,
            source.provider, source.model_version, source.vintage, source.geoid, source.reason,
            evidence.credit, evidence.coverage_points,
        ))
    return ScoreTrace(score.model_version, tuple(factors), score.raw_weighted_sum,
                      score.overall_score, coverage.percent)


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
    for minimum, label, key in CLASSIFICATION_BANDS:
        if score >= minimum:
            return label, key


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
        signal = "strong" if score >= STRENGTH_THRESHOLD else "watch" if score < RISK_THRESHOLD else "balanced"
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

    raw_weighted_sum = fsum(factor.weighted_points for factor in factors)
    overall = round(min(100.0, max(0.0, raw_weighted_sum)), 1)
    classification, classification_key = classify_score(overall)
    return ScoreResult(
        overall, classification, classification_key,
        tuple(factors), tuple(strengths), tuple(risks), raw_weighted_sum,
    )
