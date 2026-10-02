from dataclasses import dataclass, replace

from venuebite.competition_scoring import CompetitionScore, calculate_competition
from venuebite.concepts import classify_poi, resolve_concept
from venuebite.distance import METERS_PER_MILE, haversine_meters, miles_label
from venuebite.providers.poi_provider import PoiError, RestaurantPoi


@dataclass(frozen=True)
class NearbyRestaurant:
    poi: RestaurantPoi
    distance_meters: float
    is_direct: bool
    match_basis: str

    @property
    def distance_label(self):
        return miles_label(self.distance_meters)


@dataclass(frozen=True)
class CompetitionAnalysis:
    status: str
    radius_miles: int
    rows: tuple[NearbyRestaurant, ...] = ()
    model: CompetitionScore | None = None
    direct_count: int = 0
    nearest_direct_meters: float | None = None
    nearest_restaurant_meters: float | None = None
    average_direct_meters: float | None = None
    matching_note: str = ""
    coverage_note: str = ""
    explanation: str = ""
    attribution: str = ""
    error: str = ""

    @property
    def available(self):
        return self.status == "available"

    @property
    def nearest_direct_label(self):
        return miles_label(self.nearest_direct_meters)

    @property
    def nearest_restaurant_label(self):
        return miles_label(self.nearest_restaurant_meters)

    @property
    def average_direct_label(self):
        return miles_label(self.average_direct_meters)

    def map_payload(self, location, concept):
        if not self.available:
            return None
        return {
            "latitude": location.latitude, "longitude": location.longitude,
            "concept": concept, "radius_miles": self.radius_miles,
            "pois": [dict(name=row.poi.name, latitude=row.poi.latitude, longitude=row.poi.longitude,
                          address=row.poi.address, distance=row.distance_label,
                          is_direct=row.is_direct, match_basis=row.match_basis) for row in self.rows],
        }


def deduplicate(pois):
    """IDs win; coordinate/name fallback merges only when at least one ID is missing."""
    results, ids, fallbacks = [], {}, {}
    for poi in pois:
        key = (poi.provider, poi.provider_id) if poi.provider_id else None
        fallback = (poi.provider, poi.name.casefold(), round(poi.latitude, 6), round(poi.longitude, 6))
        index = ids.get(key) if key else None
        if index is None:
            candidates = fallbacks.get(fallback, [])
            index = next((i for i in candidates if not poi.provider_id or not results[i].provider_id), None)
        if index is None:
            index = len(results)
            results.append(poi)
            fallbacks.setdefault(fallback, []).append(index)
        else:
            old = results[index]
            results[index] = replace(
                old, provider_id=old.provider_id or poi.provider_id, address=old.address or poi.address,
                category_ids=tuple(sorted(set(old.category_ids) | set(poi.category_ids))),
                categories=tuple(sorted(set(old.categories) | set(poi.categories))),
                search_categories=tuple(sorted(set(old.search_categories) | set(poi.search_categories))),
                status="closed" if "closed" in (old.status, poi.status) else old.status or poi.status,
            )
        if key:
            ids[key] = index
    return results


class CompetitionService:
    def __init__(self, provider):
        self.provider = provider

    def analyze(self, location, concept, radius_miles):
        profile = resolve_concept(concept)
        try:
            batch = self.provider.search(location, profile, radius_miles * METERS_PER_MILE)
        except PoiError as error:
            return CompetitionAnalysis("unavailable", radius_miles, error=str(error))
        rows = []
        for poi in deduplicate(batch.pois):
            if poi.status == "closed":
                continue
            distance = haversine_meters(location.latitude, location.longitude, poi.latitude, poi.longitude)
            if distance <= radius_miles * METERS_PER_MILE:
                direct, basis = classify_poi(poi, profile)
                rows.append(NearbyRestaurant(poi, distance, direct, basis))
        rows.sort(key=lambda row: (row.distance_meters, row.poi.name.casefold(), row.poi.provider_id or "", row.poi.latitude, row.poi.longitude))
        direct_distances = [row.distance_meters for row in rows if row.is_direct]
        model = calculate_competition(rows)
        matching = (
            "No precise provider category is configured for this concept. Direct matches use approximate literal name/category text; related cuisines are not automatically equivalent."
            if profile.approximate else
            "Direct matches use provider categories where available; name/category text matches are labeled approximate. Categories can be broad or incomplete."
        )
        if not rows:
            explanation = f"No nearby restaurant results were returned within {radius_miles} mi. The observed-sample score is 100, not evidence that no restaurants exist."
        else:
            explanation = f"{len(rows)} nearby restaurants returned; {len(direct_distances)} direct matches within {radius_miles} mi. {model.level} observed competition pressure."
            if direct_distances:
                explanation += f" The nearest direct match is {miles_label(min(direct_distances))}."
            explanation += " Closer direct matches contribute more pressure than farther or general restaurants."
        coverage = "Limited Mapbox search sample, not a complete restaurant census. Up to 25 general plus 25 category results (10 for text search), without pagination. Coverage and category accuracy vary."
        if batch.limit_reached:
            coverage += " A provider result cap was reached; additional restaurants may be omitted."
        if batch.discarded_count:
            coverage += f" {batch.discarded_count} malformed provider results were discarded."
        return CompetitionAnalysis(
            "available", radius_miles, tuple(rows), model, len(direct_distances),
            min(direct_distances, default=None), min((row.distance_meters for row in rows), default=None),
            sum(direct_distances) / len(direct_distances) if direct_distances else None,
            matching, coverage, explanation, batch.attribution,
        )
