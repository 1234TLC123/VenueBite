from itertools import product

import pytest

from venuebite.data_coverage import COVERAGE_CREDITS, calculate_data_coverage
from venuebite.scoring import WEIGHTS


@pytest.mark.parametrize("status,percent,label", [
    ("real", 100, "Very high data coverage"),
    ("partial", 50, "Moderate data coverage"),
    ("demo", 0, "Very limited data coverage"),
    ("fallback", 0, "Very limited data coverage"),
    ("unavailable", 0, "Very limited data coverage"),
])
def test_uniform_coverage(status, percent, label):
    result = calculate_data_coverage(dict.fromkeys(WEIGHTS, status))
    assert result.percent == percent and result.label == label
    assert bool(result.warning) == (percent < 70)


@pytest.mark.parametrize("real_keys,expected,label", [
    (("population", "income", "competition"), 80, "High data coverage"),
    (("population", "income"), 60, "Moderate data coverage"),
    (("population", "competition"), 50, "Moderate data coverage"),
    (("competition",), 20, "Very limited data coverage"),
    (("population",), 30, "Limited data coverage"),
    (("population", "income", "rent"), 80, "High data coverage"),
])
def test_mixed_coverage(real_keys, expected, label):
    statuses = {key: "real" if key in real_keys else "fallback" for key in WEIGHTS}
    coverage = calculate_data_coverage(statuses)
    assert coverage.percent == expected and coverage.label == label
    assert coverage == calculate_data_coverage(dict(reversed(list(statuses.items()))))


@pytest.mark.parametrize("key", WEIGHTS)
def test_factor_partial_credits_exactly_half_its_weight(key):
    statuses = dict.fromkeys(WEIGHTS, "unavailable")
    statuses[key] = "partial"
    result = calculate_data_coverage(statuses)
    assert result.percent == WEIGHTS[key] * 50
    assert next(item for item in result.factors if item.key == key).credit == .5


@pytest.mark.parametrize("statuses", tuple(product(("real", "demo"), repeat=4)))
def test_all_real_demo_combinations_are_bounded(statuses):
    inputs = dict(zip(WEIGHTS, statuses))
    result = calculate_data_coverage(inputs)
    assert 0 <= result.percent <= 100
    assert result.percent == pytest.approx(sum(WEIGHTS[key] * COVERAGE_CREDITS[status] * 100 for key, status in inputs.items()))


@pytest.mark.parametrize("rent_status,expected,label", [
    ("partial", 90, "Very high data coverage"),
    ("demo", 80, "High data coverage"),
])
def test_high_coverage_boundaries(rent_status, expected, label):
    result = calculate_data_coverage({**dict.fromkeys(WEIGHTS, "real"), "rent": rent_status})
    assert result.percent == expected and result.label == label


def test_coverage_warning_boundary():
    result = calculate_data_coverage({"population": "real", "income": "real", "rent": "partial", "competition": "demo"})
    assert result.percent == 70 and not result.warning
    result = calculate_data_coverage({"population": "partial", "income": "demo", "rent": "partial", "competition": "demo"})
    assert result.percent == 25 and result.label == "Limited data coverage"


@pytest.mark.parametrize("inputs", [None, [], {}, {"population": "real"}, {**dict.fromkeys(WEIGHTS, "real"), "traffic": "real"}])
def test_invalid_factor_sets_rejected(inputs):
    with pytest.raises(ValueError):
        calculate_data_coverage(inputs)


@pytest.mark.parametrize("invalid", ["Real observed data", "unknown", "", None, True, [], 1])
def test_coverage_does_not_guess_status_from_labels(invalid):
    with pytest.raises(ValueError):
        calculate_data_coverage({**dict.fromkeys(WEIGHTS, "real"), "population": invalid})
