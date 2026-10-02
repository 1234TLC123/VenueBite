from dataclasses import replace
from datetime import date

import pytest

from venuebite.providers.location_provider import GeographicLocation
from venuebite.providers.site_provider import ParcelRecord, SiteError, parcel_geometry
from venuebite.services.site_intelligence_service import SiteIntelligenceService


LOCATION = GeographicLocation("123 Sample St, Denver, Colorado", 39.5, -104.5, "address", "mapbox", "test.site", country_code="us")
GEOMETRY = parcel_geometry({"type": "Polygon", "coordinates": [[[-105, 39], [-104, 39], [-104, 40], [-105, 40], [-105, 39]]]})
PARCEL = ParcelRecord(regrid_id="12345678-1234-4234-8234-123456789abc", parcel_number="APN-01", display_address="123 Sample St",
                     parcel_area_acres=1.25, geometry=GEOMETRY, provider_refresh_date=date(2025, 6, 1))


class Parcels:
    enabled = True

    def __init__(self, *results):
        self.results = list(results or [(PARCEL,)])
        self.calls = []

    def lookup(self, latitude, longitude, *, radius_meters=0):
        self.calls.append((latitude, longitude, radius_meters))
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def test_exact_uses_existing_point_once_and_separate_provenance():
    provider = Parcels()
    result = SiteIntelligenceService(provider).analyze(LOCATION)
    assert result.status == "exact" and result.available
    assert provider.calls == [(39.5, -104.5, 0)]
    assert result.query_count == result.returned_records == 1
    assert result.provenance.match_quality == "exact" and result.provenance.provider == "Regrid"
    assert result.provenance.refresh_date == date(2025, 6, 1)
    assert result.provenance.parcel_id == PARCEL.regrid_id
    assert any(fact.value == "1.250 acres" for fact in result.facts)
    assert result.map_payload(LOCATION, "Indian", 3)["geometry"]["type"] == "Polygon"


def test_single_nearby_fallback_is_bounded_explicit_and_not_exact():
    provider = Parcels((), (PARCEL,))
    result = SiteIntelligenceService(provider).analyze(LOCATION)
    assert [call[2] for call in provider.calls] == [0, 25]
    assert result.status == "nearby" and result.available
    assert "not confirmed exact containment" in result.message
    assert result.query_count == 2 and result.returned_records == 1
    assert result.map_payload(LOCATION, "Indian", 3)["match_quality"] == "nearby"


@pytest.mark.parametrize("nearby", [False, True])
def test_multiple_records_never_choose_first_or_render_boundary(nearby):
    records = (PARCEL, replace(PARCEL, parcel_number="APN-02"))
    provider = Parcels((), records) if nearby else Parcels(records)
    result = SiteIntelligenceService(provider).analyze(LOCATION)
    assert result.status == "ambiguous" and not result.available
    assert result.parcel is None and not result.facts
    assert result.map_payload(LOCATION, "Indian", 3) is None
    assert result.returned_records == 2 and len(provider.calls) == (2 if nearby else 1)


def test_no_result_is_not_parcel_nonexistence_and_no_widening():
    provider = Parcels((), ())
    result = SiteIntelligenceService(provider).analyze(LOCATION)
    assert result.status == "not_found"
    assert result.query_count == 2 and result.returned_records == 0
    assert "parcel nonexistence is not established" in result.message
    assert result.parcel is None and result.map_payload(LOCATION, "Indian", 3) is None


def test_fallback_can_be_disabled():
    provider = Parcels(())
    result = SiteIntelligenceService(provider, fallback_radius_meters=0).analyze(LOCATION)
    assert result.status == "not_found" and len(provider.calls) == 1


@pytest.mark.parametrize("code,status", [("authorization", "unavailable"), ("restricted", "restricted"), ("rate_limit", "unavailable"),
    ("network", "unavailable"), ("invalid_response", "unavailable"), ("secret-error-test", "unavailable")])
def test_failures_do_not_trigger_fallback_or_expose_provider_error(code, status):
    provider = Parcels(SiteError(code))
    result = SiteIntelligenceService(provider).analyze(LOCATION)
    assert result.status == status and len(provider.calls) == 1
    assert not result.parcel and result.map_payload(LOCATION, "Indian", 3) is None
    assert "secret-error-test" not in result.message


def test_unexpected_adapter_failure_is_isolated_without_exception_logging(caplog):
    result = SiteIntelligenceService(Parcels(RuntimeError("synthetic-secret"))).analyze(LOCATION)
    assert result.status == "unavailable" and "synthetic-secret" not in result.message
    assert "synthetic-secret" not in caplog.text


def test_restricted_fallback_does_not_become_not_found():
    provider = Parcels((), SiteError("restricted"))
    result = SiteIntelligenceService(provider).analyze(LOCATION)
    assert result.status == "restricted" and len(provider.calls) == 2
    assert "does not mean the parcel does not exist" in result.message


def test_missing_token_and_demo_do_not_request_provider():
    provider = Parcels()
    provider.enabled = False
    service = SiteIntelligenceService(provider)
    assert service.analyze(LOCATION).status == "unavailable"
    assert "not configured" in service.analyze(LOCATION).message
    assert service.analyze(None).query_count == 0 and not provider.calls


def test_unsupported_country_skips_requests_unknown_country_defers_to_provider():
    provider = Parcels()
    service = SiteIntelligenceService(provider)
    assert service.analyze(replace(LOCATION, country_code="fr")).status == "restricted"
    assert not provider.calls
    assert service.analyze(replace(LOCATION, country_code=None)).status == "exact"


def test_exact_point_outside_geometry_is_rejected_no_nearby_fallback():
    provider = Parcels()
    result = SiteIntelligenceService(provider).analyze(replace(LOCATION, longitude=-106))
    assert result.status == "unavailable" and result.parcel is None
    assert "does not contain" in result.message and len(provider.calls) == 1


def test_boundary_point_is_valid_but_polygon_hole_is_not_containment():
    assert SiteIntelligenceService(Parcels()).analyze(replace(LOCATION, longitude=-105)).available
    hole = parcel_geometry({"type": "Polygon", "coordinates": [
        [[-105, 39], [-104, 39], [-104, 40], [-105, 40], [-105, 39]],
        [[-104.8, 39.2], [-104.2, 39.2], [-104.2, 39.8], [-104.8, 39.8], [-104.8, 39.2]],
    ]})
    result = SiteIntelligenceService(Parcels((replace(PARCEL, geometry=hole),))).analyze(LOCATION)
    assert result.status == "unavailable"


def test_good_attributes_survive_missing_geometry_with_explicit_caveat():
    provider = Parcels((replace(PARCEL, geometry=None),))
    result = SiteIntelligenceService(provider).analyze(LOCATION)
    assert result.available and result.facts and result.map_payload(LOCATION, "Indian", 3) is None
    assert "containment cannot be checked locally" in " ".join(result.considerations)


@pytest.mark.parametrize("updates,state", [({}, "unknown"), ({"building_count": 0}, "no_structure_evidence"),
    ({"building_count": 2}, "developed_evidence"), ({"building_area_sqft": 100}, "developed_evidence"),
    ({"assessor_structure_count": 1}, "developed_evidence"), ({"building_footprint_sqft": 20}, "developed_evidence"),
    ({"building_count": 0, "building_area_sqft": 100}, "developed_evidence")])
def test_conservative_development_evidence(updates, state):
    result = SiteIntelligenceService(Parcels((replace(PARCEL, **updates),))).analyze(LOCATION)
    assert result.development_state == state
    notes = " ".join(result.considerations)
    assert "Missing data is unknown" in notes and "Commercial occupancy cost remains demo" in notes
    if state == "unknown":
        assert "missing fields do not mean vacant land" in notes
    if state == "no_structure_evidence":
        assert "not proof of vacant land" in notes


def test_zoning_assessment_sale_and_floor_area_semantics():
    parcel = replace(PARCEL, zoning_code="C", land_value=100000, improvement_value=200000,
                     value_type="Fair market", last_sale_price=250000, last_sale_date=date(2017, 1, 1),
                     building_area_sqft=2000, building_footprint_sqft=1000)
    result = SiteIntelligenceService(Parcels((parcel,))).analyze(LOCATION)
    facts = {item.key: item for item in result.facts}
    assert facts["land_value"].label == "Assessor-reported land value"
    assert "County value type: Fair market" == facts["land_value"].detail
    assert "not total floor area" in facts["footprint"].detail
    assert "not footprint" in facts["building_area"].detail
    assert "Historical sale" in facts["sale_price"].detail
    assert "not current asking prices" in " ".join(result.considerations)
    assert "have not been verified" in result.zoning_disclaimer


def test_optional_fields_omitted_not_repeated_unavailable_rows_and_broad_point_caution():
    result = SiteIntelligenceService(Parcels()).analyze(replace(LOCATION, place_type="place"))
    assert not any(item.key in {"zoning", "year_built", "sale_price", "land_value"} for item in result.facts)
    notes = " ".join(result.considerations)
    assert "representative point, not a verified storefront" in notes
    assert "Zoning data not available" in notes


def test_no_cache_repeated_analyses_each_use_one_point_request():
    provider = Parcels((PARCEL,), (PARCEL,))
    service = SiteIntelligenceService(provider)
    assert service.analyze(LOCATION).status == service.analyze(LOCATION).status == "exact"
    assert len(provider.calls) == 2
