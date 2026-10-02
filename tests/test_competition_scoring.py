from types import SimpleNamespace

import pytest

from venuebite.competition_scoring import calculate_competition
from venuebite.distance import METERS_PER_MILE


def row(miles=0.1, direct=True):
    return SimpleNamespace(distance_meters=miles * METERS_PER_MILE, is_direct=direct)


def test_empty_sample_has_low_observed_pressure():
    result = calculate_competition([])
    assert result.score == 100
    assert result.pressure == 0
    assert result.level == "Low"
    assert result.version == "competition-v1"


@pytest.mark.parametrize("count", [1, 10, 100, 100_000])
@pytest.mark.parametrize("miles", [0, 0.5, 1, 3, 5])
def test_extreme_counts_and_distances_remain_bounded(count, miles):
    result = calculate_competition([row(miles)] * count)
    assert 0 <= result.score <= 100


def test_more_direct_matches_monotonically_lower_score():
    scores = [calculate_competition([row()] * count).score for count in (0, 1, 5, 15, 50)]
    assert scores == sorted(scores, reverse=True)
    assert len(set(scores)) == len(scores)


def test_closer_direct_matches_have_more_pressure():
    scores = [calculate_competition([row(miles)] * 5).score for miles in (0.1, 0.8, 2, 4)]
    assert scores == sorted(scores)
    assert len(set(scores)) == len(scores)


def test_direct_matches_outweigh_general_restaurants():
    assert calculate_competition([row(direct=True)]).score < calculate_competition([row(direct=False)]).score


def test_general_environment_also_contributes_pressure():
    assert calculate_competition([row(direct=False)] * 25).score < 100


def test_model_formula_and_band_boundaries_are_explicit():
    result = calculate_competition([row(0.5), row(1), row(3), row(5), row(0.1, False)])
    assert result.pressure == 23.5
    assert result.score == round(100 / (1 + 23.5 / 40), 1)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_invalid_distances_are_not_scored(value):
    with pytest.raises(ValueError):
        calculate_competition([SimpleNamespace(distance_meters=value, is_direct=True)])
