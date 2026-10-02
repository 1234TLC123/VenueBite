from dataclasses import asdict
from math import fsum

import pytest

from venuebite.data_coverage import calculate_data_coverage
from venuebite.scoring import (
    CLASSIFICATION_BANDS, FACTOR_DEFINITIONS, VENUEBITE_SCORE_MODEL_VERSION,
    WEIGHTS, build_score_trace, calculate_opportunity,
)
from venuebite.services.analysis_service import FactorProvenance


def test_version_configuration_and_unchanged_semantics():
    assert VENUEBITE_SCORE_MODEL_VERSION == "2.0"
    assert dict(WEIGHTS) == {"population": .3, "income": .3, "rent": .2, "competition": .2}
    assert fsum(WEIGHTS.values()) == 1
    assert all(item.direction == "higher_is_better" for item in FACTOR_DEFINITIONS)
    assert [item.provenance_expected for item in FACTOR_DEFINITIONS] == ["census", "census", "demo", "mapbox"]
    assert [band[0] for band in CLASSIFICATION_BANDS] == [80, 65, 50, 0]


@pytest.mark.parametrize("inputs,points,total", [
    ({"population": 74, "income": 81, "rent": 55, "competition": 60}, [22.2, 24.3, 11, 12], 69.5),
    ({"population": 0, "income": 100, "rent": 0, "competition": 100}, [0, 30, 0, 20], 50),
    ({"population": 48.8, "income": 36.8, "rent": 55, "competition": 29.4}, [14.64, 11.04, 11, 5.88], 42.6),
])
def test_exact_backend_contributions(inputs, points, total):
    result = calculate_opportunity(inputs)
    assert [factor.weighted_points for factor in result.factors] == pytest.approx(points)
    assert result.raw_weighted_sum == fsum(factor.weighted_points for factor in result.factors)
    assert result.overall_score == total
    assert result.model_version == "2.0" and result.model_label == "VenueBite Score Model v2"
    assert result.factors[0].weighted_points_label == f"{points[0]:.2f}"


@pytest.mark.parametrize("value", [0, .00001, 49.96, 64.96, 79.96, 99.99999, 100])
def test_final_rounding_is_deterministic_and_bounded(value):
    inputs = dict.fromkeys(WEIGHTS, value)
    result = calculate_opportunity(inputs)
    assert 0 <= result.overall_score <= 100
    assert result.overall_score == round(fsum(value * weight for weight in WEIGHTS.values()), 1)
    assert result == calculate_opportunity(dict(reversed(list(inputs.items()))))


def test_contributions_are_not_rounded_before_aggregation():
    result = calculate_opportunity(dict.fromkeys(WEIGHTS, 1.16))
    assert result.raw_weighted_sum == pytest.approx(1.16)
    assert result.overall_score == 1.2
    assert result.factors[0].weighted_points == pytest.approx(.348)


def test_trace_includes_composition_provenance_and_coverage_without_penalty():
    score = calculate_opportunity(dict.fromkeys(WEIGHTS, 80))
    sources = {key: FactorProvenance("demo" if key == "rent" else "real", "Test provider", "Arbitrary label",
                                   vintage=2024 if key == "population" else None, geoid="08031002000" if key == "population" else "",
                                   model_version=f"{key}-v1") for key in WEIGHTS}
    coverage = calculate_data_coverage({key: source.status for key, source in sources.items()})
    trace = build_score_trace(score, sources, coverage)
    assert trace.model_version == "2.0" and trace.coverage == 80
    assert trace.raw_weighted_sum == trace.final_score == 80
    assert asdict(trace)["factors"][0]["geoid"] == "08031002000"
    assert trace.factors[0].coverage_points == 30 and trace.factors[2].coverage_points == 0
    assert all(item.weighted_points == item.score * item.weight for item in trace.factors)
    no_evidence = calculate_data_coverage(dict.fromkeys(WEIGHTS, "unavailable"))
    assert build_score_trace(score, sources, no_evidence).final_score == trace.final_score
