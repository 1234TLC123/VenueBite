from dataclasses import replace

import pytest

from venuebite.data_coverage import calculate_data_coverage
from venuebite.providers.demographic_provider import CensusTract, DemographicData
from venuebite.providers.location_provider import GeographicLocation
from venuebite.providers.poi_provider import PoiSearchResult, RestaurantPoi
from venuebite.scoring import WEIGHTS, calculate_opportunity
from venuebite.services.analysis_service import FactorProvenance
from venuebite.services.competition_service import CompetitionService
from venuebite.services.demographic_service import DemographicAnalysis
from venuebite.services.explanation_service import MAX_STRENGTHS, explain_analysis


def explanation(values=None, statuses=None, **context):
    values = values or {"population": 85, "income": 80, "rent": 55, "competition": 60}
    statuses = statuses or {key: "demo" if key == "rent" else "real" for key in WEIGHTS}
    provenance = {key: FactorProvenance(status, "Test provider", "Renamed source label") for key, status in statuses.items()}
    return explain_analysis(calculate_opportunity(values), provenance, calculate_data_coverage(statuses), **context)


@pytest.mark.parametrize("key,score,strength,risk", [
    ("population", 90, True, False), ("population", 30, False, True),
    ("income", 100, True, False), ("income", 20, False, True),
    ("competition", 80, True, False), ("competition", 30, False, True),
    ("population", 74.9, False, False), ("population", 75, True, False),
    ("income", 64.9, False, True), ("income", 65, False, False),
])
def test_strength_and_review_thresholds(key, score, strength, risk):
    values = {**dict.fromkeys(WEIGHTS, 70), key: score}
    result = explanation(values)
    assert (key in [item.key for item in result.strengths]) == strength
    assert (key in [item.key for item in result.risks]) == risk


def test_strong_income_and_population_rank_by_weighted_contribution():
    result = explanation({"population": 85, "income": 100, "rent": 55, "competition": 100})
    assert [item.key for item in result.strengths] == ["income", "population"]
    assert len(result.strengths) == MAX_STRENGTHS
    assert "30.00 points" in result.strengths[0].explanation
    assert "not a customer or demand estimate" in result.strengths[1].explanation


def test_demo_rent_is_a_verification_risk_not_a_claim_of_expensive_rent():
    result = explanation()
    rent = next(item for item in result.risks if item.key == "rent")
    assert "Commercial rent remains demo" in rent.explanation
    assert "Verify occupancy costs" in rent.explanation
    assert "pressure margins" not in rent.explanation
    assert "11.00 points" in rent.explanation and "no real-data coverage" in rent.explanation


@pytest.mark.parametrize("status", ["demo", "fallback", "unavailable", "partial"])
def test_high_scores_without_full_real_evidence_are_not_strengths(status):
    result = explanation(dict.fromkeys(WEIGHTS, 100), dict.fromkeys(WEIGHTS, status))
    assert not result.strengths and len(result.risks) == 4
    assert "No fully real-data factor" in result.summary
    assert "probability of business success" in result.summary
    population = next(item for item in result.risks if item.key == "population")
    assert status in population.explanation


def test_census_metrics_are_used_without_inventing_missing_values():
    census = DemographicData(CensusTract("08", "031", "002000"), population=7200, median_household_income=110000)
    demographics = DemographicAnalysis(census, 89.5, 84)
    result = explanation(demographics=demographics)
    texts = " ".join(item.explanation for item in result.strengths)
    assert "7,200 people" in texts and "$110,000" in texts
    missing = replace(demographics, data=replace(census, population=None))
    assert "None people" not in " ".join(item.explanation for item in explanation(demographics=missing).strengths)


def competition(pois):
    class Provider:
        enabled = True

        def search(self, location, concept, radius):
            return PoiSearchResult(tuple(pois))

    point = GeographicLocation("Denver", 39.7392, -104.9903, "place", "mapbox", "test.denver")
    return CompetitionService(Provider()).analyze(point, "Indian restaurant", 3)


def test_competition_pressure_explains_actual_nearest_direct_matches():
    observed = competition([RestaurantPoi(f"Indian kitchen {i}", 39.7392, -104.9903, category_ids=("indian_restaurant",)) for i in range(4)])
    result = explanation({"population": 70, "income": 70, "rent": 55, "competition": observed.model.score}, competition=observed)
    item = next(item for item in result.risks if item.key == "competition")
    assert "4 direct matches" in item.explanation and "Nearest direct match: 0.00 mi" in item.explanation
    assert "within 0.5 mi" in item.explanation
    assert "Moderate observed pressure" in item.explanation
    assert "High observed pressure" not in item.explanation
    assert "competition" not in [item.key for item in result.strengths]


def test_nearby_direct_matches_can_be_risk_even_at_balanced_score():
    observed = competition([RestaurantPoi(f"Indian kitchen {i}", 39.7392, -104.9903, category_ids=("indian_restaurant",)) for i in range(2)])
    assert observed.model.score >= 65
    result = explanation({"population": 70, "income": 70, "rent": 55, "competition": observed.model.score}, competition=observed)
    assert "competition" in [item.key for item in result.risks]


def test_empty_observed_sample_does_not_claim_no_competitors_exist():
    observed = competition([])
    result = explanation({"population": 70, "income": 70, "rent": 55, "competition": 100}, competition=observed)
    assert "not proof that no restaurants exist" in result.strengths[0].explanation
    assert "not an exhaustive business census" in " ".join(result.quality_notes)


def test_no_duplicates_no_contradictions_and_deterministic_output():
    first = explanation()
    second = explanation(dict(reversed(list({"population": 85, "income": 80, "rent": 55, "competition": 60}.items()))))
    assert first == second
    keys = [item.key for item in (*first.strengths, *first.risks)]
    assert len(keys) == len(set(keys))
    assert len(first.quality_notes) == len(set(first.quality_notes))


def test_fallback_reason_and_renamed_source_label_do_not_affect_coverage():
    score = calculate_opportunity(dict.fromkeys(WEIGHTS, 80))
    provenance = {key: FactorProvenance("fallback", "Demo fixture", "Real-looking label", reason="Census is not configured.") for key in WEIGHTS}
    result = explain_analysis(score, provenance, calculate_data_coverage(dict.fromkeys(WEIGHTS, "fallback")))
    assert "Data Coverage is 0%" in result.summary and not result.strengths
    assert "Census is not configured" in result.risks[0].explanation
