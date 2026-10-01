from dataclasses import dataclass

from venuebite.scoring import ScoreResult, calculate_opportunity
from venuebite.services import LocationData, LocationDataProvider


@dataclass(frozen=True)
class AnalysisReport:
    data: LocationData
    score: ScoreResult


class AnalysisService:
    def __init__(self, provider: LocationDataProvider):
        self.provider = provider

    def analyze(self, location, concept):
        data = self.provider.get_location_data(location, concept)
        return AnalysisReport(data=data, score=calculate_opportunity(data.factor_scores))
