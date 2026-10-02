from dataclasses import replace

import pytest

from venuebite.concepts import classify_poi, resolve_concept
from venuebite.distance import EARTH_RADIUS_METERS, haversine_meters, miles_label, search_bounds
from venuebite.providers.location_provider import LocationError
from venuebite.providers.poi_provider import RestaurantPoi


def test_distance_is_symmetric_and_zero_at_same_point():
    assert haversine_meters(39, -104, 39, -104) == 0
    assert haversine_meters(39, -104, 40, -105) == pytest.approx(haversine_meters(40, -105, 39, -104))


def test_known_equatorial_distance():
    assert haversine_meters(0, 0, 0, 1) == pytest.approx(111_195.08, abs=0.1)


def test_antimeridian_is_short_crossing_and_antipodes_are_finite():
    assert haversine_meters(0, 179.99, 0, -179.99) == pytest.approx(2223.9, abs=1)
    assert haversine_meters(0, 0, 0, 180) == pytest.approx(3.141592653589793 * EARTH_RADIUS_METERS)


def test_search_bounds_contain_candidate_and_handle_extremes():
    west, south, east, north = search_bounds(39, -104, 5000)
    assert west < -104 < east
    assert south < 39 < north
    assert search_bounds(90, 0, 5000) is None
    assert search_bounds(0, 179.99, 5000) is None


def test_distance_labels_never_invent_missing_distance():
    assert miles_label(1609.344) == "1.00 mi"
    assert miles_label(None) == "Not returned"


@pytest.mark.parametrize("value,category", [("INDIAN restaurant", "indian_restaurant"), (" Coffee   Shop ", "coffee_shop"), ("Pizzeria", "pizza_restaurant"), ("Cafe & Bakery", "cafe"), ("Mexican", "mexican_restaurant"), ("Cuban restaurant", "cuban_restaurant"), ("Burgers", "burger_restaurant")])
def test_aliases_resolve_only_verified_categories(value, category):
    assert resolve_concept(value).category == category


def test_unmapped_concept_uses_approximate_matching_not_related_cuisine():
    concept = resolve_concept("Congolese Restaurant")
    assert concept.approximate
    assert concept.category is None
    assert classify_poi(RestaurantPoi("African Kitchen", 39, -104, category_ids=("african_restaurant",)), concept)[0] is False
    assert classify_poi(RestaurantPoi("Congolese Kitchen", 39, -104), concept) == (True, "Approximate text match")
    assert classify_poi(RestaurantPoi("NotCongolese Kitchen", 39, -104), concept)[0] is False


def test_indian_category_is_not_equivalent_to_mexican():
    poi = RestaurantPoi("Kitchen", 39, -104, category_ids=("mexican_restaurant",))
    assert classify_poi(poi, resolve_concept("Indian restaurant"))[0] is False
    assert classify_poi(poi, resolve_concept("Mexican restaurant")) == (True, "Provider category")


def test_category_search_provenance_handles_missing_optional_categories():
    poi = RestaurantPoi("Kitchen", 39, -104, search_categories=("indian_restaurant",))
    assert classify_poi(poi, resolve_concept("Indian restaurant")) == (True, "Provider category")
    assert classify_poi(replace(poi, search_categories=()), resolve_concept("Indian restaurant"))[0] is False


@pytest.mark.parametrize("latitude,longitude", [(91, 0), (0, 181), (float("nan"), 0), (True, 0), (None, 0)])
def test_normalized_poi_contract_rejects_invalid_coordinates(latitude, longitude):
    with pytest.raises(LocationError):
        RestaurantPoi("Kitchen", latitude, longitude)


@pytest.mark.parametrize("name", [None, "", "   ", "x" * 201, "bad\x00name"])
def test_normalized_poi_contract_rejects_invalid_names(name):
    with pytest.raises(ValueError):
        RestaurantPoi(name, 39, -104)
