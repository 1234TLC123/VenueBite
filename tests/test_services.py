from venuebite.services.mock_data_service import MockLocationDataService


def test_mock_provider_is_explicitly_demo_and_identical_for_all_searches():
    provider = MockLocationDataService()
    first = provider.get_location_data("Aurora, CO", "Congolese Restaurant")
    second = provider.get_location_data("Denver, CO", "Cafe")
    assert first.is_demo and second.is_demo
    assert first.source_label == "Demo data"
    assert first.location == "Aurora, CO"
    assert second.concept == "Cafe"
    assert first.factor_scores == second.factor_scores
    assert first.area_insights == second.area_insights
    assert first.competitors == second.competitors


def test_fixture_scores_cannot_be_mutated_between_requests():
    import pytest

    data = MockLocationDataService().get_location_data("Denver", "Cafe")
    with pytest.raises(TypeError):
        data.factor_scores["rent"] = 0
