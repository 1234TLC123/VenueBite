"""Normalized Census contracts. No credentials or raw provider payloads."""

from dataclasses import dataclass
import re
from typing import Protocol


ACS_YEAR = 2024
ACS_DATASET = "ACS 5-Year Detailed Tables"
CENSUS_BENCHMARK = "Public_AR_Current"
CENSUS_VINTAGE = "ACS2024_Current"
POPULATION_ESTIMATE = "B01003_001E"
POPULATION_MOE = "B01003_001M"
INCOME_ESTIMATE = "B19013_001E"
INCOME_MOE = "B19013_001M"
ACS_VARIABLES = (
    POPULATION_ESTIMATE, POPULATION_MOE, "B01003_001EA", "B01003_001MA",
    INCOME_ESTIMATE, INCOME_MOE, "B19013_001EA", "B19013_001MA",
)
# Sprint 04 supports the 50 states and DC, not the separate Puerto Rico survey.
US_STATE_FIPS = frozenset("01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56".split())


class CensusError(Exception):
    """Only application-owned messages may cross the provider boundary."""

    def __init__(self, code="unavailable"):
        self.code = code
        super().__init__("Census data is unavailable. Demo demographic scores are used where needed.")


def normalize_fips(value, width):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise CensusError("invalid_geography")
    value = str(value)
    if not re.fullmatch(r"[0-9]{1," + str(width) + r"}", value):
        raise CensusError("invalid_geography")
    return value.zfill(width)


@dataclass(frozen=True)
class CensusTract:
    state_fips: str
    county_fips: str
    tract_fips: str
    name: str = ""
    state_name: str = ""
    county_name: str = ""
    country_code: str = "us"
    geography_level: str = "tract"
    provider: str = "U.S. Census Bureau"
    geography_vintage: str = CENSUS_VINTAGE

    def __post_init__(self):
        for field, width in (("state_fips", 2), ("county_fips", 3), ("tract_fips", 6)):
            object.__setattr__(self, field, normalize_fips(getattr(self, field), width))
        if self.state_fips not in US_STATE_FIPS or self.country_code != "us" or self.geography_level != "tract":
            raise CensusError("unsupported_geography")

    @property
    def geoid(self):
        return self.state_fips + self.county_fips + self.tract_fips


@dataclass(frozen=True)
class DemographicData:
    geography: CensusTract | None = None
    population: int | None = None
    population_moe: int | None = None
    median_household_income: int | None = None
    income_moe: int | None = None
    population_annotation: str = ""
    income_annotation: str = ""
    population_moe_annotation: str = ""
    income_moe_annotation: str = ""
    geography_name: str = ""
    year: int = ACS_YEAR
    dataset: str = ACS_DATASET
    provider: str = "U.S. Census Bureau"
    reason: str = ""

    def __post_init__(self):
        for field in ("population", "population_moe", "median_household_income", "income_moe"):
            value = getattr(self, field)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise CensusError("invalid_response")
        if (self.population is not None or self.median_household_income is not None) and self.geography is None:
            raise CensusError("invalid_geography")

    @property
    def status(self):
        count = sum(value is not None for value in (self.population, self.median_household_income))
        return ("unavailable", "partial", "available")[count]


class CensusGeographyProvider(Protocol):
    def lookup(self, latitude: float, longitude: float) -> CensusTract: ...


class DemographicProvider(Protocol):
    enabled: bool

    def fetch(self, geography: CensusTract) -> DemographicData: ...
