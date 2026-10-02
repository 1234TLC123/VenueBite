"""Bounded parcel resolution and conservative site facts, outside Score Model v2."""

from dataclasses import dataclass
from datetime import date
import logging

from shapely.geometry import Point

from venuebite.providers.regrid_provider import fallback_radius
from venuebite.providers.site_provider import ParcelRecord, SiteError, SiteProvider


ZONING_DISCLAIMER = "Parcel zoning data is informational. Restaurant use permissions, overlays, conditional-use requirements and local approvals have not been verified."
VALUE_DISCLAIMER = "Assessor-reported values are assessment context, not current asking prices, lease rates, buildout costs or independently verified market values."
SALE_DISCLAIMER = "Recorded sales are historical, not current asking prices or evidence the property is available."
FAILURE_MESSAGES = {
    "not_configured": "Parcel data unavailable. Regrid is not configured on the server.",
    "authorization": "Parcel data unavailable. Regrid authorization was rejected.",
    "restricted": "Outside current provider coverage or dataset entitlement. This does not mean the parcel does not exist.",
    "rate_limit": "Parcel data unavailable. Regrid is rate- or usage-limited; try again later.",
    "network": "Parcel data unavailable. Regrid could not connect; try again later.",
    "unsupported_geography": "This parcel integration supports U.S. and Puerto Rico records only; the selected country is outside its coverage.",
    "geometry_mismatch": "Parcel data unavailable. The returned boundary does not contain the selected point; verify the site before relying on property facts.",
}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SiteFact:
    key: str
    label: str
    value: str
    detail: str = ""


@dataclass(frozen=True)
class SiteProvenance:
    status: str
    match_quality: str
    provider: str = "Regrid"
    refresh_date: date | None = None
    parcel_id: str = ""
    coverage_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class SiteIntelligence:
    status: str
    message: str
    parcel: ParcelRecord | None = None
    facts: tuple[SiteFact, ...] = ()
    considerations: tuple[str, ...] = ()
    development_state: str = "unknown"
    provenance: SiteProvenance | None = None
    query_count: int = 0
    returned_records: int = 0

    @property
    def available(self):
        return self.status in {"exact", "nearby"}

    @property
    def label(self):
        return {"exact": "Real parcel data", "nearby": "Nearby parcel match - verify", "ambiguous": "Multiple parcels - verification needed",
                "not_found": "No matching parcel returned", "restricted": "Outside current provider coverage", "unavailable": "Parcel data unavailable"}[self.status]

    @property
    def zoning_disclaimer(self):
        return ZONING_DISCLAIMER

    def map_payload(self, location, concept, radius_miles):
        if not self.available or not self.parcel or self.parcel.geometry is None:
            return None
        return {"latitude": location.latitude, "longitude": location.longitude, "concept": concept,
                "radius_miles": radius_miles, "match_quality": self.status,
                "geometry": self.parcel.geojson(), "bounds": list(self.parcel.geometry.bounds)}


def _site_facts(parcel):
    facts = []
    def add(key, label, value, detail=""):
        if value is not None and value != "":
            facts.append(SiteFact(key, label, value, detail))
    add("parcel_number", "Parcel number", parcel.parcel_number)
    add("address", "Parcel situs address", parcel.display_address)
    add("acres", "Parcel size", f"{parcel.parcel_area_acres:,.3f} acres" if parcel.parcel_area_acres is not None else None, "Regrid geometry-calculated area")
    add("sqft", "Parcel area", f"{parcel.parcel_area_sqft:,.0f} sq ft" if parcel.parcel_area_sqft is not None else None, "Regrid geometry-calculated area")
    add("land_use", "Provider land-use description", parcel.land_use_description)
    add("use_code", "Local land-use code", parcel.land_use_code, "Local code; no restaurant eligibility inferred")
    add("building_count", "Regrid calculated building count", str(parcel.building_count) if parcel.building_count is not None else None)
    add("structno", "Assessor-reported structure count", str(parcel.assessor_structure_count) if parcel.assessor_structure_count is not None else None)
    add("building_area", "Assessor building area", f"{parcel.building_area_sqft:,.0f} sq ft" if parcel.building_area_sqft is not None else None,
        parcel.building_area_definition or "County-defined total structure area, not footprint")
    add("footprint", "Calculated building footprint", f"{parcel.building_footprint_sqft:,.0f} sq ft" if parcel.building_footprint_sqft is not None else None, "Regrid footprint area, not total floor area")
    add("year_built", "Assessor-reported year built", str(parcel.year_built) if parcel.year_built is not None else None)
    add("zoning", "Zoning context", parcel.zoning_code)
    add("zoning_description", "Local zoning description", parcel.zoning_description)
    add("zoning_type", "Provider standardized zoning type", parcel.zoning_type)
    detail = f"County value type: {parcel.value_type}" if parcel.value_type else "County value type unavailable"
    add("land_value", "Assessor-reported land value", f"${parcel.land_value:,.0f}" if parcel.land_value is not None else None, detail)
    add("improvement_value", "Assessor-reported improvement value", f"${parcel.improvement_value:,.0f}" if parcel.improvement_value is not None else None, detail)
    add("sale_price", "Last recorded sale price", f"${parcel.last_sale_price:,.0f}" if parcel.last_sale_price is not None else None, "Historical sale, not a current asking price")
    add("sale_date", "Last recorded sale date", parcel.last_sale_date.isoformat() if parcel.last_sale_date else None)
    add("county", "County FIPS", parcel.county_fips)
    add("refresh", "County data refreshed", parcel.provider_refresh_date.isoformat() if parcel.provider_refresh_date else None, "Periodic county refresh, not real-time property data")
    return tuple(facts)


def _development(parcel):
    counts = (parcel.building_count, parcel.assessor_structure_count, parcel.building_area_sqft, parcel.building_footprint_sqft)
    if any(value is not None and value > 0 for value in counts):
        return "developed_evidence", "Existing structure evidence is present in the returned record; condition and suitability are unverified."
    if any(value == 0 for value in counts):
        return "no_structure_evidence", "Available structure measurements report zero; this is not proof of vacant land."
    return "unknown", "Building attributes are unavailable from this record; missing fields do not mean vacant land."


class SiteIntelligenceService:
    def __init__(self, provider: SiteProvider, *, fallback_radius_meters=25):
        self.provider = provider
        self.fallback_radius_meters = fallback_radius(fallback_radius_meters)

    def analyze(self, location):
        calls, returned = 0, 0
        if location is None:
            return SiteIntelligence("unavailable", "Parcel lookup requires a resolved candidate location; no parcel data is invented for demo analysis.", provenance=SiteProvenance("unavailable", "unavailable"))
        try:
            if location.country_code and location.country_code not in {"us", "pr"}:
                raise SiteError("unsupported_geography")
            if not self.provider.enabled:
                raise SiteError("not_configured")
            calls += 1
            parcels = self.provider.lookup(location.latitude, location.longitude, radius_meters=0)
            returned += len(parcels)
            quality = "exact"
            if not parcels and self.fallback_radius_meters:
                calls += 1
                parcels = self.provider.lookup(location.latitude, location.longitude, radius_meters=self.fallback_radius_meters)
                returned += len(parcels)
                quality = "nearby"
            if not parcels:
                return SiteIntelligence("not_found", "No matching parcel returned. The point may be in a street or outside token coverage; parcel nonexistence is not established.", provenance=SiteProvenance("unavailable", "not_found"), query_count=calls, returned_records=returned)
            if len(parcels) != 1:
                return SiteIntelligence("ambiguous", "Multiple parcel records correspond to this location. Site details require parcel-level verification; no record has been selected.", provenance=SiteProvenance("unavailable", "ambiguous"), query_count=calls, returned_records=returned)
            parcel = parcels[0]
            if quality == "exact" and parcel.geometry is not None and not parcel.geometry.covers(Point(location.longitude, location.latitude)):
                raise SiteError("geometry_mismatch")
            message = "Exact point lookup matched one parcel record."
            notes = []
            if quality == "nearby":
                message = f"One parcel was returned within {self.fallback_radius_meters} meters, not confirmed exact containment. Verify the parcel before relying on site facts."
                notes.append(message)
            if parcel.geometry is None:
                notes.append("Parcel boundary is unavailable or invalid; property attributes remain usable, but containment cannot be checked locally.")
            if location.place_type not in {"address", "poi"}:
                notes.append("This broad place resolves to a representative point, not a verified storefront. Select a complete site address for parcel decisions.")
            development, structure_note = _development(parcel)
            notes.append(structure_note)
            notes.append("Optional fields vary by county, account and dataset entitlement. Missing data is unknown, not a negative property fact.")
            if not parcel.zoning_code and not parcel.zoning_description and not parcel.zoning_type:
                notes.append("Zoning data not available from current parcel record.")
            if parcel.land_value is not None or parcel.improvement_value is not None:
                notes.append(VALUE_DISCLAIMER)
            if parcel.last_sale_price is not None or parcel.last_sale_date:
                notes.append(SALE_DISCLAIMER)
            notes.append("Commercial occupancy cost remains demo; parcel facts do not change Opportunity Score or its Data Coverage.")
            provenance = SiteProvenance("real", quality, refresh_date=parcel.provider_refresh_date, parcel_id=parcel.regrid_id,
                                        coverage_notes=("County/plan-dependent fields; periodic source refresh, not real-time property information.",))
            return SiteIntelligence(quality, message, parcel, _site_facts(parcel), tuple(notes), development, provenance, calls, returned)
        except SiteError as error:
            status = "restricted" if error.code in {"restricted", "unsupported_geography"} else "unavailable"
            return SiteIntelligence(status, FAILURE_MESSAGES.get(error.code, "Parcel data unavailable. Regrid returned unavailable or unreadable data."),
                                    provenance=SiteProvenance("unavailable", status), query_count=calls, returned_records=returned)
        except Exception:
            # Isolate an unexpected adapter failure without logging credential-bearing exception details.
            logger.warning("Site intelligence unavailable: unexpected adapter failure")
            return SiteIntelligence("unavailable", "Parcel data unavailable. Site lookup could not be completed.",
                                    provenance=SiteProvenance("unavailable", "unavailable"), query_count=calls, returned_records=returned)
