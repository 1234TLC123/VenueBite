from dataclasses import dataclass

from venuebite.demographic_scoring import income_score, population_score
from venuebite.providers.demographic_provider import CensusError, DemographicData


@dataclass(frozen=True)
class DemographicAnalysis:
    data: DemographicData
    population_score: float | None = None
    income_score: float | None = None


FAILURE_MESSAGES = {
    "not_configured": "Census is not configured. Demo population and income scores are used.",
    "authorization": "Census rejected authorization. Demo demographic scores are used.",
    "rate_limit": "Census is rate-limited. Demo demographic scores are used; try again later.",
    "network": "Census could not connect. Demo demographic scores are used; try again later.",
    "no_tract": "No Census tract matched the selected coordinates. Demo demographic scores are used.",
    "ambiguous_geography": "The selected point matches multiple Census tracts, usually at a shared boundary. Choose a more specific address or landmark. Demo demographic scores are used.",
    "unsupported_geography": "Census demographics currently support the 50 U.S. states and DC only. Demo demographic scores are used.",
}


class DemographicService:
    def __init__(self, geography_provider, demographic_provider):
        self.geography_provider = geography_provider
        self.demographic_provider = demographic_provider

    def analyze(self, location):
        geography = None
        try:
            if location.country_code and location.country_code != "us":
                raise CensusError("unsupported_geography")
            if not self.demographic_provider.enabled:
                raise CensusError("not_configured")
            geography = self.geography_provider.lookup(location.latitude, location.longitude)
            data = self.demographic_provider.fetch(geography)
            if data.geography != geography:
                raise CensusError("geography_mismatch")
            return DemographicAnalysis(data, population_score(data.population), income_score(data.median_household_income))
        except CensusError as error:
            return DemographicAnalysis(DemographicData(
                geography=geography,
                reason=FAILURE_MESSAGES.get(error.code, "Census returned unavailable or unreadable data. Demo demographic scores are used."),
            ))
