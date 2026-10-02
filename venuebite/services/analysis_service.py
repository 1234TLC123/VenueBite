from dataclasses import dataclass, replace
from types import MappingProxyType

from venuebite.demographic_scoring import (
    POPULATION_DESCRIPTION, INCOME_DESCRIPTION, POPULATION_MODEL_VERSION, INCOME_MODEL_VERSION,
)
from venuebite.scoring import ScoreResult, calculate_opportunity
from venuebite.services import AreaInsight, LocationData, LocationDataProvider
from venuebite.services.competition_service import CompetitionAnalysis
from venuebite.services.demographic_service import DemographicAnalysis


@dataclass(frozen=True)
class FactorProvenance:
    status: str
    provider: str
    label: str
    vintage: int | None = None
    geoid: str = ""
    model_version: str = ""
    description: str = ""
    reason: str = ""

    @property
    def real(self):
        return self.status == "real"


@dataclass(frozen=True)
class AnalysisReport:
    data: LocationData
    score: ScoreResult
    competition: CompetitionAnalysis | None = None
    demographics: DemographicAnalysis | None = None
    provenance: MappingProxyType | None = None


class AnalysisService:
    def __init__(self, provider: LocationDataProvider, competition_service=None, demographic_service=None):
        self.provider = provider
        self.competition_service = competition_service
        self.demographic_service = demographic_service

    def analyze(self, location, concept, *, geographic_location=None, radius_miles=3):
        data = self.provider.get_location_data(location, concept)
        factors = dict(data.factor_scores)
        provenance = {key: FactorProvenance("demo", "Demo fixture", "Demo data") for key in factors}
        competition = None
        demographics = None
        if geographic_location is not None and self.competition_service is not None:
            competition = self.competition_service.analyze(geographic_location, concept, radius_miles)
            if competition.available:
                factors["competition"] = competition.model.score
                provenance["competition"] = FactorProvenance(
                    "real", "Mapbox", "Real observed data", model_version=competition.model.version,
                    description=competition.explanation,
                )
                data = replace(data, factor_scores=factors, competitors=(), is_demo=False, source_label="Hybrid analysis")
            else:
                data = replace(data, competitors=(), is_demo=True, source_label="Demo analysis - live competition unavailable")
                provenance["competition"] = FactorProvenance("fallback", "Demo fixture", "Demo data", reason="Live competition unavailable.")
        if geographic_location is not None and self.demographic_service is not None:
            demographics = self.demographic_service.analyze(geographic_location)
            census = demographics.data
            for key, score, version, description in (
                ("population", demographics.population_score, POPULATION_MODEL_VERSION, POPULATION_DESCRIPTION),
                ("income", demographics.income_score, INCOME_MODEL_VERSION, INCOME_DESCRIPTION),
            ):
                if score is not None:
                    factors[key] = score
                    provenance[key] = FactorProvenance(
                        "real", census.provider, "Real Census estimate", census.year,
                        census.geography.geoid, version, description,
                    )
                else:
                    provenance[key] = FactorProvenance("fallback", "Demo fixture", "Demo data", reason=census.reason)
            data = replace(data, area_insights=_demographic_insights(data, census, competition))
        if any(source.real for source in provenance.values()):
            data = replace(data, is_demo=False, source_label="Hybrid analysis")
        data = replace(data, factor_scores=MappingProxyType(factors))
        return AnalysisReport(data, calculate_opportunity(factors), competition, demographics, MappingProxyType(provenance))


def _demographic_insights(data, census, competition):
    population, income = census.population, census.median_household_income
    source = f"ACS {census.year} 5-year tract estimate"
    insights = [
        AreaInsight("Tract population", f"{population:,}" if population is not None else "Unavailable", source if population is not None else "No usable Census estimate", "users", "real" if population is not None else "unavailable", "population"),
        AreaInsight("Median household income", f"${income:,}" if income is not None else "Unavailable", f"{source}; {census.year} dollars" if income is not None else "No usable Census estimate", "wallet", "real" if income is not None else "unavailable", "income"),
        AreaInsight("Population growth", "Unavailable", "Comparable non-overlapping periods not verified", "trending-up", "unavailable", "population_growth"),
    ]
    insights.extend(item for item in data.area_insights if item.key == "commercial_rent")
    available = competition is not None and competition.available
    insights.append(AreaInsight(
        "Observed nearby restaurants", str(len(competition.rows)) if available else "Unavailable",
        "Mapbox limited sample; not all nearby businesses" if available else "Live restaurant sample unavailable",
        "store", "real" if available else "unavailable", "restaurants",
    ))
    insights.extend(item for item in data.area_insights if item.key == "schools")
    return tuple(insights)
