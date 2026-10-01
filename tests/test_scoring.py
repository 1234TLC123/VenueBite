import math

import pytest

from venuebite.scoring import WEIGHTS, calculate_opportunity, classify_score


def scores(value):
    return {key: value for key in WEIGHTS}


def test_prototype_weighted_score_and_factor_results():
    result = calculate_opportunity({"population": 85, "income": 80, "rent": 55, "competition": 60})
    assert result.overall_score == 72.5
    assert result.classification == "Promising opportunity"
    assert {factor.key: factor.score for factor in result.factors} == {
        "population": 85, "income": 80, "rent": 55, "competition": 60,
    }
    assert math.fsum(WEIGHTS.values()) == 1
    assert [item.label for item in result.strengths] == ["Population", "Income"]
    assert [item.label for item in result.risks] == ["Rent", "Competition"]


@pytest.mark.parametrize("value", [0, 100, 0.1, 49.9, 65, 80])
def test_score_boundaries_and_uniform_inputs(value):
    assert calculate_opportunity(scores(value)).overall_score == value


@pytest.mark.parametrize("value, expected", [
    (0, "Challenging opportunity"),
    (49.9, "Challenging opportunity"),
    (50, "Mixed opportunity"),
    (64.9, "Mixed opportunity"),
    (65, "Promising opportunity"),
    (79.9, "Promising opportunity"),
    (80, "Strong opportunity"),
    (100, "Strong opportunity"),
])
def test_classification_thresholds(value, expected):
    assert classify_score(value)[0] == expected
    assert calculate_opportunity(scores(value)).classification == expected


@pytest.mark.parametrize("value", [-1, 101, float("nan"), float("inf"), float("-inf"), "85", None, True, False, 10 ** 1000])
def test_invalid_factor_values_are_rejected(value):
    factors = scores(50)
    factors["rent"] = value
    with pytest.raises(ValueError):
        calculate_opportunity(factors)


@pytest.mark.parametrize("value", [-1, 101, float("nan"), "80", None, True])
def test_invalid_overall_values_are_rejected(value):
    with pytest.raises(ValueError):
        classify_score(value)


@pytest.mark.parametrize("factors", [None, [85, 80, 55, 60], {}, {"population": 85}, {**scores(50), "traffic": 50}])
def test_missing_extra_and_non_mapping_inputs_are_rejected(factors):
    with pytest.raises(ValueError):
        calculate_opportunity(factors)


def test_factor_order_does_not_change_result():
    factors = {"population": 85, "income": 80, "rent": 55, "competition": 60}
    assert calculate_opportunity(factors) == calculate_opportunity(dict(reversed(list(factors.items()))))


def test_higher_rent_and_competition_scores_improve_opportunity():
    baseline = scores(50)
    for key in ("rent", "competition"):
        improved = {**baseline, key: 100}
        assert calculate_opportunity(improved).overall_score == 60


def test_strengths_and_risks_follow_thresholds():
    result = calculate_opportunity({"population": 75, "income": 74.9, "rent": 65, "competition": 64.9})
    assert [item.label for item in result.strengths] == ["Population"]
    assert [item.label for item in result.risks] == ["Competition"]
    assert result.strengths[0].score == 75
    assert result.risks[0].score == 64.9


def test_no_generic_insights_when_no_threshold_matches():
    result = calculate_opportunity(scores(70))
    assert result.strengths == ()
    assert result.risks == ()
