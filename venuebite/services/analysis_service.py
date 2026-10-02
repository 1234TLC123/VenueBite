from dataclasses import dataclass, replace

from venuebite.scoring import ScoreResult, calculate_opportunity
from venuebite.services import LocationData, LocationDataProvider
from venuebite.services.competition_service import CompetitionAnalysis


@dataclass(frozen=True)
class AnalysisReport:
    data: LocationData
    score: ScoreResult
    competition: CompetitionAnalysis | None = None


class AnalysisService:
    def __init__(self, provider: LocationDataProvider, competition_service=None):
        self.provider = provider
        self.competition_service = competition_service

    def analyze(self, location, concept, *, geographic_location=None, radius_miles=3):
        data = self.provider.get_location_data(location, concept)
        competition = None
        if geographic_location is not None and self.competition_service is not None:
            competition = self.competition_service.analyze(geographic_location, concept, radius_miles)
            if competition.available:
                factors = {**data.factor_scores, "competition": competition.model.score}
                data = replace(data, factor_scores=factors, competitors=(), is_demo=False, source_label="Hybrid analysis")
            else:
                data = replace(data, competitors=(), is_demo=True, source_label="Demo analysis - live competition unavailable")
        return AnalysisReport(data=data, score=calculate_opportunity(data.factor_scores), competition=competition)
