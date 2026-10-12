"""Deterministic whitelist: model outputs, Census, user terms and official guidance."""

from decimal import Decimal
from itertools import combinations

from venuebite.regulatory import CODE_URL, RESTAURANT_URL, official_url

CENSUS_URL = "https://www.census.gov/programs-surveys/acs/"


class EvidenceRegistry:
    def __init__(self):
        self.entries = {}

    def add(self, identifier, label, value, *, units="", status="model", source="VenueBite", date="", url="", limitation=""):
        if identifier in self.entries:
            raise ValueError("Duplicate evidence ID")
        display = "Unknown / not supplied" if value is None or value == "" else str(value)
        if value is not None and value != "" and units in {"USD / month", "USD / year", "people", "%", "points", "/ 100", "sq ft", "fraction"}:
            amount = Decimal(str(value))
            display = f"{amount:,.2f}" if units.startswith("USD") else f"{amount:,.2f}".rstrip("0").rstrip(".")
        self.entries[identifier] = {
            "id": identifier, "label": label, "value": value, "display": display, "units": units,
            "status": status, "source": source, "date": date, "source_url": url, "limitation": limitation,
        }

    def site(self, snapshot, prefix):
        date = snapshot["analysis"]["timestamp"]
        def add(key, label, value, **kwargs):
            self.add(f"{prefix}.{key}", label, value, date=date, **kwargs)
        add("score", "Opportunity Score", snapshot["score"]["value"], units="/ 100", limitation="Not a success prediction.")
        add("model", "Score model version", snapshot["score"]["model_version"])
        add("classification", "Opportunity classification", snapshot["score"]["classification"], limitation="Model classification, not a business recommendation.")
        add("timestamp", "Analyzed at", date, limitation="Analysis time does not establish current evidence.")
        add("coverage", "Data Coverage", snapshot["coverage"]["percent"], units="%", limitation="Usable evidence support; not probability or confidence.")
        add("concept", "User restaurant concept", snapshot["analysis"]["concept"], status="user_supplied")
        add("radius", "Requested radius", snapshot["analysis"]["radius_miles"], units="miles", status="user_supplied", limitation="Not a Census trade area or an exhaustive business inventory.")
        for factor in snapshot["factors"]:
            key, label = factor["key"], factor["label"]
            for metric, title, unit in (("score", "factor score", "/ 100"), ("weight", "model weight", "fraction"),
                                        ("contribution", "weighted contribution", "points"), ("coverage_points", "coverage contribution", "points"),
                                        ("coverage_credit", "evidence credit", "fraction")):
                add(f"{key}.{metric}", f"{label} {title}", factor[metric], units=unit, status=factor["status"],
                    limitation="VenueBite model output; underlying evidence status is preserved, not independently verified by AI.")
            add(f"{key}.model", f"{label} model version", factor["model_version"] or "Demo fixture", status=factor["status"])
        demo = snapshot["demographics"]
        for key, label, unit in (("population", "ACS tract population estimate", "people"), ("population_moe", "Population margin of error", "people"),
                                 ("income", "ACS median household income estimate", "USD / year"), ("income_moe", "Income margin of error", "USD / year"),
                                 ("vintage", "ACS vintage", "year"), ("geoid", "Containing Census tract GEOID", "")):
            value = demo[key]
            add(f"census.{key}", label, value, units=unit, status="real" if value is not None and value != "" else "unavailable",
                source="U.S. Census Bureau ACS", url=CENSUS_URL, limitation="Survey estimate for a containing tract, not a current headcount, demand estimate or requested-radius population.")
        add("competition.details", "Business detail sharing", None, status="unavailable",
            limitation="Search Box coordinates, IDs, POI names, rows, counts and distances are excluded from AI sharing. Discuss the VenueBite competition factor only.")
        site = snapshot["site"]
        add("site.match", "Parcel match outcome", site["status"], status="model",
            limitation="Match outcome only. Regrid attributes withheld pending external-sharing permission; missing premium facts are unknown, not zero.")
        add("site.details", "Parcel attributes and asking price", None, status="unavailable",
            limitation="Direct parcel data is not sent to AI. Assessed values and historical sales are not current asking prices. Site facts do not change scoring or coverage.")
        occupancy = snapshot["occupancy"]
        status = "partial" if occupancy["provided"] else "demo"
        for key, label, unit in (("space_size_sqft", "User space size", "sq ft"), ("asking_rent", "User asking rent rate", "supplied basis"),
                                 ("asking_rent_basis", "User rent basis", ""), ("lease_structure", "User lease structure", ""),
                                 ("monthly_base", "Known monthly base rent", "USD / month"), ("monthly_additional", "Known monthly additional costs", "USD / month"),
                                 ("monthly_known_total", "Known monthly occupancy total", "USD / month"), ("monthly_budget", "User occupancy budget", "USD / month"),
                                 ("budget_utilization", "Budget utilization", "%")):
            value = occupancy[key]
            add(f"occupancy.{key}", label, value, units=unit, status=status if value is not None and value != "" else "unavailable",
                source="User-supplied terms / Commercial Occupancy Model v1", limitation="Partial evidence, not independent market verification. Only supplied costs; budget fit is not profitability or national affordability.")
        reg = snapshot.get("regulatory")
        add("regulatory.status", "Regulatory lookup status", reg["status"] if reg else "unknown", status=reg["evidence_status"] if reg else "unknown",
            source="Denver government / VenueBite regulatory review", url=CODE_URL,
            limitation="Only Denver is supported; lookup status is not restaurant-use permission.")
        add("regulatory.permission", "Restaurant-use permission", "Not verified", status="unknown", source="Official confirmation required", url=RESTAURANT_URL)
        if reg:
            for key in ("district", "code_family", "framework", "overlay", "effective_date", "version"):
                value = reg[key]
                self.add(f"{prefix}.regulatory.{key}", f"Official regulatory {key.replace('_', ' ')}", value,
                         date=reg["retrieved_at"], status="verified_official_fact" if value else "unknown",
                         source="City and County of Denver", url=CODE_URL, limitation="District identification, not a permitted-use determination; Denver attribution retained.")
            for key, value in reg["project"].items():
                add(f"project.{key}", f"User proposed {key.replace('_', ' ')}", value, status="user_supplied",
                    limitation="User plan, not an agency-confirmed requirement or approval.")
            for index, item in enumerate(reg["checklist"], 1):
                add(f"regulatory.check.{index}", item["topic"], item["status"], status=item["evidence"],
                    source="Denver government guidance", url=official_url(item["source_url"]), limitation="Confirm applicability and requirements with the authority; not legal advice.")

    def comparisons(self, snapshots):
        for (left, a), (right, b) in combinations(enumerate(snapshots, 1), 2):
            for key, section, field in (("score", "score", "value"), ("coverage", "coverage", "percent")):
                delta = Decimal(str(a[section][field])) - Decimal(str(b[section][field]))
                self.add(f"compare.s{left}_s{right}.{key}", f"Site {left} minus site {right}: {key} difference", str(delta), units="points",
                         limitation="Deterministic stored-value subtraction, not an automatic best-site recommendation. Check context and evidence compatibility.")
