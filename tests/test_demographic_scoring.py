import pytest

from venuebite.demographic_scoring import (
    INCOME_ANCHORS, INCOME_MODEL_VERSION, POPULATION_ANCHORS, POPULATION_MODEL_VERSION,
    income_score, population_score,
)


@pytest.mark.parametrize("value,expected", POPULATION_ANCHORS)
def test_population_anchors(value, expected):
    assert population_score(value) == expected


@pytest.mark.parametrize("value,expected", INCOME_ANCHORS)
def test_income_anchors(value, expected):
    assert income_score(value) == expected


@pytest.mark.parametrize("score,values", [(population_score, [0, 500, 1000, 2000, 3000, 4500, 6000, 8000, 10000, 10**1000]),
                                         (income_score, [0, 10000, 25000, 40000, 50000, 65000, 75000, 100000, 150000, 10**1000])])
def test_monotonic_bounded_context_scores(score, values):
    scores = [score(value) for value in values]
    assert scores == sorted(scores) and all(0 <= result <= 100 for result in scores)
    assert scores[-1] == 100


@pytest.mark.parametrize("score", [population_score, income_score])
@pytest.mark.parametrize("value", [-1, True, False, "5000", [], {}, float("nan"), float("inf"), -float("inf")])
def test_invalid_context_values(score, value):
    with pytest.raises(ValueError):
        score(value)


def test_missing_context_is_not_zero():
    assert population_score(None) is None and income_score(None) is None
    assert POPULATION_MODEL_VERSION == "population-v1" and INCOME_MODEL_VERSION == "income-v1"


def test_interpolation_and_determinism():
    assert population_score(2000) == 42.5
    assert income_score(62500) == 55
    assert population_score(4321) == population_score(4321)
