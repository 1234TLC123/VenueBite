"""One fictional fixture for every search; no location or concept claims."""

from types import MappingProxyType

from venuebite.services import AreaInsight, Competitor, LocationData


MOCK_FACTOR_SCORES = MappingProxyType({
    "population": 85,
    "income": 80,
    "rent": 55,
    "competition": 60,
})
MOCK_AREA_INSIGHTS = (
    AreaInsight("Population", "184,500", "Sample area population", "users"),
    AreaInsight("Median household income", "$72,400", "Sample annual income", "wallet"),
    AreaInsight("Population growth", "+1.8%", "Sample annual change", "trending-up"),
    AreaInsight("Commercial asking rent", "$28 / sq ft", "Sample annual base rent", "building-2"),
    AreaInsight("Nearby businesses", "142", "Sample business count", "store"),
    AreaInsight("Schools & universities", "8", "Sample institution count", "graduation-cap"),
)
MOCK_COMPETITORS = (
    Competitor("Sample Kitchen 01", "Central African", "0.4 mi", "$$"),
    Competitor("Sample Bistro 02", "Contemporary American", "0.7 mi", "$$$"),
    Competitor("Sample Cafe 03", "Cafe & bakery", "0.9 mi", "$"),
    Competitor("Sample Grill 04", "Mediterranean", "1.2 mi", "$$"),
)


class MockLocationDataService:
    def get_location_data(self, location, concept):
        return LocationData(
            location=location,
            concept=concept,
            factor_scores=MOCK_FACTOR_SCORES,
            area_insights=MOCK_AREA_INSIGHTS,
            competitors=MOCK_COMPETITORS,
            is_demo=True,
            source_label="Demo data",
        )
