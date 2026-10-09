from dataclasses import replace
from decimal import Decimal

import pytest
from werkzeug.datastructures import MultiDict

from venuebite.occupancy import (
    BUDGET_ANCHORS, CandidateProperty, OccupancyRate, calculate_budget_fit, calculate_costs, currency, normalize_cost,
)
from venuebite.services.occupancy_service import FIELD_NAMES, OccupancyService, normalize_candidate_input


TERMS = {"space_size_sqft": "2800", "asking_rent": "32", "asking_rent_basis": "per_sqft_per_year",
         "lease_structure": "nnn", "additional_occupancy_rate": "8.50", "additional_occupancy_basis": "per_sqft_per_year",
         "monthly_occupancy_budget": "10000"}


def candidate(**changes):
    normalized = normalize_candidate_input({**TERMS, **changes})
    assert not normalized.errors
    return normalized.candidate


@pytest.mark.parametrize("basis,amount,monthly,annual", [
    ("per_sqft_per_year", "32", "7466.666666666666666666666667", "89600"),
    ("per_sqft_per_month", "2.5", "7000", "84000"),
    ("total_monthly", "7500.25", "7500.25", "90003"),
    ("total_annual", "90003", "7500.25", "90003"),
])
@pytest.mark.parametrize("field,basis_field", [("asking_rent", "asking_rent_basis"), ("additional_occupancy_rate", "additional_occupancy_basis")])
def test_all_base_and_additional_formats(basis, amount, monthly, annual, field, basis_field):
    result = calculate_costs(candidate(**{field: amount, basis_field: basis}))
    cost = result.base if field == "asking_rent" else result.additional
    assert cost.monthly == Decimal(monthly) and cost.annual == Decimal(annual)


def test_nnn_acceptance_math_is_decimal_not_display_rounded():
    result = calculate_costs(candidate())
    assert result.base.annual == 89600 and result.additional.annual == 23800
    assert result.total.monthly == 9450 and result.total.annual == 113400
    assert result.base.label == "$7,466.67 / month"
    assert result.additional.label == "$1,983.33 / month"
    assert result.total.label == "$9,450.00 / month"
    assert currency(Decimal("0.005")) == "$0.01"
    fit = calculate_budget_fit(result.total.monthly, Decimal(10000))
    assert fit.ratio == Decimal("0.945") and fit.utilization_label == "94.5%" and fit.score == 66


@pytest.mark.parametrize("lease", ["nnn", "gross", "modified_gross", "unknown"])
def test_missing_extras_never_claim_total_or_activate_score_even_gross(lease):
    result = OccupancyService().analyze(candidate(lease_structure=lease, additional_occupancy_rate=""))
    assert result.costs.base is not None and result.costs.additional is None and result.costs.total is None
    assert result.costs.completeness == "base_only" and result.status == "partial"
    assert not result.supported and "insufficient lease terms" in result.fallback_reason
    assert "total occupancy cost is not known" in result.summary
    assert any("Base rent only" in item for item in result.warnings)
    assert not any(item.label == "Estimated occupancy cost" for item in result.facts)


@pytest.mark.parametrize("lease", ["nnn", "gross", "modified_gross", "unknown"])
def test_explicit_zero_is_supplied_evidence_not_missing(lease):
    result = OccupancyService().analyze(candidate(lease_structure=lease, additional_occupancy_rate="0"))
    assert result.supported and result.status == "complete" and result.costs.additional.monthly == 0
    assert result.costs.total.monthly == result.costs.base.monthly
    assert not any("Base rent only" in text for text in result.warnings)


def test_no_terms_defaults_are_not_evidence_and_no_budget_cannot_score():
    normalized = normalize_candidate_input({})
    assert normalized.status == "not_provided" and not normalized.candidate.provided
    assert OccupancyService().analyze(normalized.candidate).status == "not_provided"
    no_budget = OccupancyService().analyze(candidate(monthly_occupancy_budget=""))
    assert no_budget.costs.total.monthly == 9450 and no_budget.status == "complete"
    assert no_budget.model is None and "budget not supplied" in no_budget.fallback_reason


@pytest.mark.parametrize("basis", ["total_monthly", "total_annual"])
def test_flat_costs_calculable_without_size_but_size_required_for_scoring(basis):
    result = OccupancyService().analyze(candidate(space_size_sqft="", asking_rent_basis=basis, additional_occupancy_basis=basis))
    assert result.costs.total is not None and result.status == "partial" and not result.supported


def test_per_sf_requires_size_without_inference_from_parcel_or_default():
    result = OccupancyService().analyze(candidate(space_size_sqft=""))
    assert result.costs.base is result.costs.additional is result.costs.total is None
    assert result.costs.completeness == "unknown_expenses"
    assert any("no space size has been inferred" in warning for warning in result.warnings)


def test_flat_base_with_unusable_per_sf_extras_does_not_call_supplied_charges_missing():
    result = OccupancyService().analyze(candidate(space_size_sqft="", asking_rent_basis="total_monthly"))
    assert result.costs.base is not None and result.costs.additional is None and result.costs.total is None
    assert any("supplied additional charges could not be calculated" in warning for warning in result.warnings)
    assert not any("charges were not supplied" in warning for warning in result.warnings)


@pytest.mark.parametrize("field", ["space_size_sqft", "asking_rent", "additional_occupancy_rate", "monthly_occupancy_budget"])
@pytest.mark.parametrize("value", ["-1", "NaN", "Infinity", "-Infinity", "1e300", "32 dollars", "1,00.00", "1.2.3", "0.1234567", "9" * 100, "100000001", "<script>1</script>"])
def test_numeric_validation(field, value):
    result = normalize_candidate_input({**TERMS, field: value})
    assert field in result.errors and result.status == "invalid"


@pytest.mark.parametrize("field", ["space_size_sqft", "monthly_occupancy_budget"])
def test_zero_size_and_budget_rejected(field):
    assert field in normalize_candidate_input({**TERMS, field: "0"}).errors


@pytest.mark.parametrize("value,expected", [("32.50", "32.50"), ("$32.50", "32.50"), ("1,000.25", "1000.25"), (" $1,000.25 ", "1000.25"), ("0", "0"), ("100000000", "100000000")])
def test_supported_currency_normalization_and_high_but_legitimate_amounts(value, expected):
    result = normalize_candidate_input({**TERMS, "asking_rent": value})
    assert not result.errors and result.candidate.asking_rent.value == Decimal(expected)


@pytest.mark.parametrize("field", ["asking_rent_basis", "additional_occupancy_basis", "lease_structure"])
@pytest.mark.parametrize("value", ["invalid", "", "<script>", "real"])
def test_enum_validation(field, value):
    assert field in normalize_candidate_input({**TERMS, field: value}).errors


@pytest.mark.parametrize("value", ["javascript:alert(1)", "data:text/html,hello", "file:///secret", "//example.com", "https://user:pass@example.com", "https://localhost/path", "https://example.com?api_key=private", "https://example.com:bad", "https://example.com/ has-space"])
def test_unsafe_or_credential_bearing_source_urls_rejected(value):
    assert "source_url" in normalize_candidate_input({**TERMS, "source_url": value}).errors


@pytest.mark.parametrize("value", ["https://example.com/listing/123", "http://broker.example.com/listing?id=123", ""])
def test_source_urls_are_metadata_only_and_http_allowed(value):
    result = normalize_candidate_input({**TERMS, "source_url": value})
    assert not result.errors and result.candidate.source_url == value


@pytest.mark.parametrize("field,limit", [("source_label", 120), ("source_url", 2000), ("occupancy_notes", 1000), ("property_address", 300)])
def test_text_limits_and_control_characters(field, limit):
    for value in ("x" * (limit + 1), "bad\x00text", "bad\x7ftext"):
        assert field in normalize_candidate_input({**TERMS, field: value}).errors


@pytest.mark.parametrize("field", FIELD_NAMES)
def test_duplicate_fields_rejected(field):
    form = MultiDict(TERMS)
    form.add(field, "x")
    if field not in TERMS:
        form.add(field, "y")
    assert field in normalize_candidate_input(form).errors


@pytest.mark.parametrize("ratio,score", [("0", 100), ("0.25", 100), ("0.70", 100), ("0.80", 90), ("0.85", 85),
    ("0.90", 75), ("0.945", 66), ("1.00", 55), ("1.01", 53), ("1.10", 35), ("1.15", 25),
    ("1.325", 12.5), ("1.50", 0), ("2", 0), ("1000000", 0)])
def test_budget_model_anchors_interpolation_and_bounds(ratio, score):
    result = calculate_budget_fit(Decimal(ratio) * 10000, Decimal(10000))
    assert result.score == score and 0 <= result.score <= 100


def test_model_is_monotonic_continuous_near_anchors_and_not_absolute_rent():
    scores = [calculate_budget_fit(Decimal(i), Decimal(100)).score for i in range(301)]
    assert scores == sorted(scores, reverse=True)
    for ratio, score in BUDGET_ANCHORS:
        before = calculate_budget_fit(ratio - Decimal("0.00001"), Decimal(1))
        after = calculate_budget_fit(ratio + Decimal("0.00001"), Decimal(1))
        assert abs(before.score - float(score)) <= 0.1 and abs(after.score - float(score)) <= 0.1
    assert calculate_budget_fit(Decimal(1000), Decimal(2000)).score == calculate_budget_fit(Decimal(10000), Decimal(20000)).score


@pytest.mark.parametrize("cost,budget", [(Decimal(-1), Decimal(100)), (Decimal(1), Decimal(0)), (Decimal(1), Decimal(-1)),
    (Decimal("NaN"), Decimal(1)), (Decimal(1), Decimal("Infinity")), (1.0, Decimal(1)), (True, Decimal(1))])
def test_calculator_rejects_invalid_domain_values(cost, budget):
    with pytest.raises(ValueError):
        calculate_budget_fit(cost, budget)


@pytest.mark.parametrize("value,basis,size", [(Decimal(-1), "total_monthly", None), (Decimal("NaN"), "total_annual", None),
    (Decimal(1), "invalid", None), (Decimal(1), "per_sqft_per_year", Decimal(0)), (Decimal(1), "per_sqft_per_month", Decimal("Infinity"))])
def test_invalid_rate_or_size_not_silently_normalized(value, basis, size):
    with pytest.raises(ValueError):
        normalize_cost(OccupancyRate(value, basis), size)


def test_address_defaults_to_selected_point_and_mismatch_is_warning_only():
    service = OccupancyService()
    defaulted = service.analyze(candidate(), selected_address="123 Main St, Denver")
    assert defaulted.candidate.property_address == "123 Main St, Denver"
    same = service.analyze(candidate(property_address="123 MAIN ST. Denver"), selected_address="123 Main St, Denver")
    assert not any("address differs" in warning for warning in same.warnings)
    other = service.analyze(candidate(property_address="500 Other St"), selected_address="123 Main St, Denver")
    assert any("Property address differs" in warning for warning in other.warnings)
    assert defaulted.model == other.model


def test_immutable_inputs_and_reports():
    normalized = normalize_candidate_input(TERMS)
    with pytest.raises(TypeError):
        normalized.values["asking_rent"] = "0"
    assert replace(normalized.candidate, source_label="REAL VERIFIED").source_type == "user_supplied"
