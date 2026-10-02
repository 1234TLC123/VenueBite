from dataclasses import replace
import math

import pytest

from venuebite.distance import EARTH_RADIUS_METERS, METERS_PER_MILE
from venuebite.providers.location_provider import GeographicLocation
from venuebite.providers.poi_provider import PoiError, PoiSearchResult, RestaurantPoi
from venuebite.services.analysis_service import AnalysisService
from venuebite.services.competition_service import CompetitionService, deduplicate
from venuebite.services.mock_data_service import MOCK_FACTOR_SCORES, MockLocationDataService

LOCATION = GeographicLocation("Candidate", 0, 0, "address", "mapbox", "test.candidate")


def poi(name, miles=0.1, *, direct=False, **kwargs):
    return RestaurantPoi(name, math.degrees(miles * METERS_PER_MILE / EARTH_RADIUS_METERS), 0,
                         category_ids=("indian_restaurant",) if direct else ("mexican_restaurant",), **kwargs)


class FakePoiProvider:
    enabled = True

    def __init__(self, pois=(), failure=None, **batch_kwargs):
        self.batch = PoiSearchResult(tuple(pois), **batch_kwargs)
        self.failure = failure
        self.calls = []

    def search(self, location, concept, radius_meters):
        self.calls.append((location, concept, radius_meters))
        if self.failure:
            raise self.failure
        return self.batch


def test_service_deduplicates_filters_closed_and_outside_radius_and_sorts():
    provider = FakePoiProvider([
        poi("Zulu", 0.5, provider_id="z"), poi("Outside", 3.1),
        poi("Indian", 0.3, direct=True, provider_id="i"), poi("Indian duplicate", 0.3, direct=True, provider_id="i"),
        poi("Closed", 0.01, direct=True, status="closed"), poi("Alpha", 0.5, provider_id="a"),
    ])
    result = CompetitionService(provider).analyze(LOCATION, "Indian restaurant", 3)
    assert result.available
    assert [row.poi.name for row in result.rows] == ["Indian", "Alpha", "Zulu"]
    assert result.direct_count == 1
    assert result.nearest_direct_meters == pytest.approx(0.3 * METERS_PER_MILE)
    assert result.nearest_restaurant_meters == result.nearest_direct_meters
    assert result.average_direct_meters == result.nearest_direct_meters
    assert provider.calls[0][0] is LOCATION
    assert provider.calls[0][2] == 3 * METERS_PER_MILE


def test_dedup_merges_category_evidence_from_two_queries():
    generic = poi("Kitchen", provider_id="same")
    specific = replace(generic, search_categories=("indian_restaurant",))
    result = CompetitionService(FakePoiProvider([generic, specific])).analyze(LOCATION, "Indian", 3)
    assert len(result.rows) == result.direct_count == 1
    assert result.rows[0].match_basis == "Provider category"


def test_missing_id_fallback_is_conservative_and_normalizes_name():
    first = poi("  Kitchen  House ")
    same = replace(first, name="kitchen house", provider_id="known", address="1 Main")
    distinct = replace(first, latitude=first.latitude + 0.001)
    results = deduplicate([first, same, distinct])
    assert len(results) == 2
    assert results[0].provider_id == "known"
    assert results[0].address == "1 Main"


def test_distinct_provider_ids_at_same_coordinates_are_not_collapsed():
    assert len(deduplicate([poi("Kitchen", provider_id="one"), poi("Kitchen", provider_id="two")])) == 2


def test_known_closed_status_wins_over_unknown_duplicate():
    first = poi("Kitchen", provider_id="same")
    result = CompetitionService(FakePoiProvider([first, replace(first, status="closed")])).analyze(LOCATION, "Indian", 3)
    assert result.rows == ()


def test_unknown_operational_status_is_retained_not_guessed():
    result = CompetitionService(FakePoiProvider([poi("Kitchen")])).analyze(LOCATION, "Indian", 3)
    assert len(result.rows) == 1
    assert result.rows[0].poi.status is None


def test_unknown_concept_does_not_promote_related_cuisine_and_has_disclaimer():
    result = CompetitionService(FakePoiProvider([poi("African Kitchen"), poi("Congolese Kitchen")])).analyze(LOCATION, "Congolese restaurant", 3)
    assert result.direct_count == 1
    assert "approximate" in result.matching_note
    assert "not automatically equivalent" in result.matching_note
    assert result.rows[1].match_basis == "Approximate text match"


def test_zero_results_are_not_claimed_as_zero_restaurants():
    result = CompetitionService(FakePoiProvider()).analyze(LOCATION, "Indian", 3)
    assert result.model.score == 100
    assert result.direct_count == 0
    assert result.nearest_direct_meters is None
    assert result.nearest_restaurant_meters is None
    assert result.average_direct_meters is None
    assert "No nearby restaurant results were returned" in result.explanation
    assert "not evidence" in result.explanation
    assert "not a complete restaurant census" in result.coverage_note


def test_cap_and_partial_malformed_results_are_disclosed():
    result = CompetitionService(FakePoiProvider([poi("Kitchen")], limit_reached=True, discarded_count=2)).analyze(LOCATION, "Indian", 3)
    assert "cap was reached" in result.coverage_note
    assert "2 malformed" in result.coverage_note


def test_nearest_and_average_metrics_come_from_computed_distances():
    result = CompetitionService(FakePoiProvider([poi("Direct near", 0.2, direct=True), poi("Direct far", 0.8, direct=True), poi("General", 0.1)])).analyze(LOCATION, "Indian", 1)
    assert result.nearest_restaurant_label == "0.10 mi"
    assert result.nearest_direct_label == "0.20 mi"
    assert result.average_direct_label == "0.50 mi"


@pytest.mark.parametrize("radius,expected", [(1, 1), (3, 2), (5, 3)])
def test_radius_changes_filtering(radius, expected):
    result = CompetitionService(FakePoiProvider([poi("Near", 0.5), poi("Middle", 2), poi("Far", 4)])).analyze(LOCATION, "Indian", radius)
    assert len(result.rows) == expected


def test_failure_is_unavailable_without_invented_live_metrics():
    result = CompetitionService(FakePoiProvider(failure=PoiError("Provider busy"))).analyze(LOCATION, "Indian", 3)
    assert result.status == "unavailable"
    assert not result.available
    assert result.error == "Provider busy"
    assert result.model is None
    assert result.map_payload(LOCATION, "Indian") is None


def test_map_payload_is_filtered_and_tied_to_candidate_concept_and_radius():
    result = CompetitionService(FakePoiProvider([poi("Near", 0.5), poi("Far", 4)])).analyze(LOCATION, "Indian", 3)
    payload = result.map_payload(LOCATION, "Indian")
    assert (payload["latitude"], payload["longitude"]) == (0, 0)
    assert payload["concept"] == "Indian"
    assert payload["radius_miles"] == 3
    assert [item["name"] for item in payload["pois"]] == ["Near"]
    assert payload["pois"][0]["distance"] == "0.50 mi"


def test_hybrid_replaces_only_competition_without_mutating_mock_fixture():
    service = AnalysisService(MockLocationDataService(), CompetitionService(FakePoiProvider([poi("Direct", direct=True)])))
    report = service.analyze("Candidate", "Indian", geographic_location=LOCATION)
    assert report.data.source_label == "Hybrid analysis"
    assert not report.data.is_demo
    assert report.data.competitors == ()
    assert report.data.factor_scores["competition"] == report.competition.model.score != 60
    assert [report.data.factor_scores[key] for key in ("population", "income", "rent")] == [85, 80, 55]
    assert report.score.overall_score == round(60.5 + 0.2 * report.competition.model.score, 1)
    assert MOCK_FACTOR_SCORES["competition"] == 60


def test_no_geography_preserves_original_demo_without_poi_call():
    provider = FakePoiProvider()
    report = AnalysisService(MockLocationDataService(), CompetitionService(provider)).analyze("Label", "Concept")
    assert report.score.overall_score == 72.5
    assert report.competition is None
    assert report.data.competitors
    assert not provider.calls


def test_unavailable_preserves_demo_score_but_never_fake_live_restaurants():
    report = AnalysisService(MockLocationDataService(), CompetitionService(FakePoiProvider(failure=PoiError("Busy")))).analyze("Candidate", "Indian", geographic_location=LOCATION)
    assert report.score.overall_score == 72.5
    assert report.data.is_demo
    assert report.data.competitors == ()
    assert report.data.source_label == "Demo analysis - live competition unavailable"
