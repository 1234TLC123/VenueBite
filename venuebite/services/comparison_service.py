"""Read-only, deterministic comparison of stored facts and model outputs."""

from dataclasses import dataclass
from decimal import Decimal

from venuebite.distance import miles_label
from venuebite.occupancy import LEASE_STRUCTURES, RENT_BASES, currency
from venuebite.services.saved_site_service import SaveError, validated_id


EVIDENCE_LABELS = {"real": "Real evidence", "partial": "Partial - user supplied", "demo": "Demo", "fallback": "Fallback - demo", "unavailable": "Unavailable"}
SITE_LABELS = {"exact": "Exact parcel match", "nearby": "Nearby match - verify", "not_found": "No matching parcel returned", "ambiguous": "Ambiguous parcel match", "restricted": "Outside provider coverage", "unavailable": "Unavailable"}


def amount(value, *, money=False, suffix="", missing="Unavailable"):
    if value is None or value == "":
        return missing
    number = Decimal(str(value))
    return (currency(number) if money else f"{number:,.2f}".rstrip("0").rstrip(".")) + suffix


def snapshot_sections(snapshot, *, include_regulatory=True):
    demo, competition, site, occupancy = (snapshot[key] for key in ("demographics", "competition", "site", "occupancy"))
    rate = lambda value, basis: amount(value, money=True, missing="Not supplied") + (" " + RENT_BASES[basis].removeprefix("USD ") if value is not None and basis in RENT_BASES else "")
    sections = [
        {"label": "Demographics", "rows": [
            ("Tract population", amount(demo["population"])), ("Median household income", amount(demo["income"], money=True)),
            ("Population / income MOE", amount(demo["population_moe"]) + " / " + amount(demo["income_moe"], money=True)),
            ("Census tract", demo["tract_name"] or "Unavailable"), ("Tract GEOID", demo["geoid"] or "Unavailable"),
            ("Census source", demo["provider"] + (f" / unavailable (configured ACS {demo['vintage']})" if demo["status"] == "unavailable" else f" / {demo['dataset']} / {demo['vintage']}")),
            ("Boundary vintage", demo["boundary_vintage"] or "Unavailable"),
        ]},
        {"label": "Competition", "rows": [
            ("Restaurants observed", amount(competition["observed_count"])), ("Direct competitors", amount(competition["direct_count"])),
            ("Nearest direct competitor", miles_label(competition["nearest_direct_meters"]) if competition["nearest_direct_meters"] is not None else "Unavailable"),
            ("Observed pressure points", amount(competition["pressure"])), ("Competition model", competition["model_version"] or "Not available in saved snapshot"),
        ]},
        {"label": "Site intelligence", "rows": [
            ("Parcel availability", SITE_LABELS[site["status"]]), ("Parcel identifier", site["parcel_number"] or site["parcel_id"] or "Unavailable"),
            ("Parcel area", amount(site["area_acres"], suffix=" acres")), ("Parcel square feet", amount(site["area_sqft"], suffix=" SF")),
            ("Assessor building area", amount(site["building_area_sqft"], suffix=" SF")),
            ("Land use", site["land_use_description"] or "Unavailable"), ("Local land-use code", site["land_use_code"] or "Unavailable"),
            ("Informational zoning code", site["zoning_code"] or "Unavailable"), ("County refresh", site["refresh_date"] or "Unavailable"),
            ("Parcel source / match", site["provider"] + " / " + site["match_quality"]),
        ]},
        {"label": "Commercial occupancy", "rows": [
            ("User property / space address", occupancy["property_address"] or "Not supplied"),
            ("Terms supplied", "Yes - unverified user terms" if occupancy["provided"] else "Not supplied"),
            ("Space size", amount(occupancy["space_size_sqft"], suffix=" SF", missing="Not supplied")),
            ("Lease structure", LEASE_STRUCTURES.get(occupancy["lease_structure"], "Unknown / Not stated")),
            ("Asking rent", rate(occupancy["asking_rent"], occupancy["asking_rent_basis"])),
            ("Additional charges", rate(occupancy["additional_rate"], occupancy["additional_basis"])),
            ("Monthly base rent", amount(occupancy["monthly_base"], money=True, missing="Not supplied / not calculable")),
            ("Monthly additional charges", amount(occupancy["monthly_additional"], money=True, missing="Not supplied / not calculable")),
            ("Known monthly occupancy", amount(occupancy["monthly_known_total"], money=True, missing="Unknown total")),
            ("Monthly occupancy budget", amount(occupancy["monthly_budget"], money=True, missing="Not supplied")),
            ("Budget utilization", amount(occupancy["budget_utilization"], suffix="%", missing="Not available in saved snapshot")),
            ("Occupancy model", occupancy["model_version"] or "Demo rent - no occupancy model"),
        ]},
    ]
    if not include_regulatory:
        return sections
    regulatory = snapshot.get("regulatory")
    gis_sources = "; ".join(source["url"] for source in regulatory["sources"] if source["type"] == "GIS point query") if regulatory else ""
    sections.insert(-1, {"label": "Zoning & regulatory feasibility", "rows": [
        ("Regulatory review status", regulatory["status_label"] if regulatory else "Not captured in this snapshot"),
        ("Jurisdiction", regulatory["jurisdiction"] or "Not established" if regulatory else "Unknown"),
        ("Official GIS district", regulatory["district"] or "Unknown" if regulatory else "Unknown"),
        ("Zoning framework", regulatory["framework"] if regulatory else "Unknown"),
        ("Restaurant-use permission", regulatory["use_status"] if regulatory else "Not verified"),
        ("Regulatory evidence", regulatory["evidence_status"].replace("_", " ") if regulatory else "Not captured"),
        ("Unresolved conditions", " ".join(regulatory["unresolved"] + regulatory["missing"]) if regulatory else "Not evaluated"),
        ("Regulatory retrieval time", regulatory["retrieved_at"] or "Not retrieved" if regulatory else "Not captured"),
        ("Legal effective date", regulatory["effective_date"] or "Unknown" if regulatory else "Unknown"),
        ("Stored regulatory workflow", regulatory["version"] if regulatory else "Not captured"),
        ("Official GIS sources", gis_sources or "Not captured"),
    ]})
    return sections


@dataclass(frozen=True)
class Comparison:
    sites: tuple
    sections: tuple
    highlights: tuple[str, ...]
    badges: dict
    warnings: tuple[str, ...]


class ComparisonService:
    def __init__(self, saved_sites):
        self.saved_sites = saved_sites

    def compare(self, selected):
        if len(selected) < 2:
            raise SaveError("Select at least two saved sites.")
        if len(selected) > 4:
            raise SaveError("Maximum four sites can be compared.")
        ids = [validated_id(value) for value in selected]
        if len(set(ids)) != len(ids):
            raise SaveError("Select each saved site only once.")
        sites = tuple(self.saved_sites.get(site_id) for site_id in ids)
        if any(site is None for site in sites):
            raise SaveError("A selected saved site was deleted or no longer exists. Choose the remaining sites again.")
        snapshots = [site.snapshot for site in sites]
        tables = [snapshot_sections(snapshot) for snapshot in snapshots]
        sections = []
        for index, section in enumerate(tables[0]):
            sections.append({"label": section["label"], "rows": [
                {"label": row[0], "values": tuple(table[index]["rows"][row_index][1] for table in tables)}
                for row_index, row in enumerate(section["rows"])
            ]})
        highlights, warnings, badges = [], [], {site.id: [] for site in sites}
        same_model = len({snapshot["score"]["model_version"] for snapshot in snapshots}) == 1 and len({tuple(f["weight"] for f in snapshot["factors"]) for snapshot in snapshots}) == 1
        same_context = len({(snapshot["analysis"]["concept"].casefold(), snapshot["analysis"]["radius_miles"]) for snapshot in snapshots}) == 1
        same_evidence = len({tuple(f["status"] for f in snapshot["factors"]) for snapshot in snapshots}) == 1

        def highlight(values, label, detail, *, lowest=False):
            best = min(values) if lowest else max(values)
            winners = [site for site, value in zip(sites, values) if value == best]
            names = ", ".join(site.display_name for site in winners)
            verb = "tie for the" if len(winners) > 1 else "has the"
            highlights.append(f"{names} {verb} {label.lower()} among these saved snapshots. {detail}")
            for site in winners:
                badges[site.id].append(label)

        if same_model and same_context and same_evidence:
            highlight([s["score"]["value"] for s in snapshots], "Highest stored score", "This is a model-output comparison, not a site recommendation.")
        else:
            warnings.append("Stored scores are shown without a ranking badge because concepts, radii, model versions, weights or factor evidence differ.")
        if same_model:
            highlight([s["coverage"]["percent"] for s in snapshots], "Highest Data Coverage", "Coverage measures usable model evidence, not success probability.")
        else:
            warnings.append("Model versions or weights differ; scores and coverage are not ranked across models.")
        competition_factors = [s["factors"][3] for s in snapshots]
        if same_context and all(f["status"] == "real" for f in competition_factors) and len({f["model_version"] for f in competition_factors}) == 1:
            highlight([f["score"] for f in competition_factors], "Strongest competition factor", "Higher means lower observed pressure in a capped saved sample, not proven lower market competition.")
        else:
            warnings.append("Competition scores are not ranked where search context, model or usable evidence differs.")
        occupancies = [s["occupancy"] for s in snapshots]
        if all(o["monthly_known_total"] is not None and o["evidence_status"] == "partial" for o in occupancies):
            if all(o["space_size_sqft"] is not None for o in occupancies) and len({(Decimal(o["space_size_sqft"]), o["lease_structure"]) for o in occupancies}) == 1:
                highlight([Decimal(o["monthly_known_total"]) for o in occupancies], "Lowest known occupancy", "Based on saved user-supplied terms for equal-size, equal-structure spaces; not verified market rent.", lowest=True)
            else:
                warnings.append("Space sizes or lease structures differ; known occupancy totals are displayed but not ranked.")
        rent_statuses = [s["factors"][2]["status"] for s in snapshots]
        if len(set(rent_statuses)) > 1:
            groups = [f"{site.display_name}: {EVIDENCE_LABELS[status]}" for site, status in zip(sites, rent_statuses)]
            highlights.append("Rent evidence differs. " + "; ".join(groups) + ". These scores are not equally supported facts.")
        if not same_context:
            warnings.append("Concepts or search radii differ. Observed counts and factor context are not like-for-like market comparisons.")
        warnings.append("All values are historical snapshots. Census tract proxies, capped restaurant samples and unverified occupancy terms retain their original limitations.")
        return Comparison(sites, tuple(sections), tuple(highlights), badges, tuple(warnings))
