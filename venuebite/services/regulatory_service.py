"""Evidence-aware review workflow, not an automated restaurant permission engine."""

import logging

from venuebite.providers.zoning_provider import ZoningLookup
from venuebite.providers.denver_zoning_provider import BOUNDARY_LAYER, ZONING_LAYER
from venuebite.regulatory import (MODEL_VERSION, CODE_URL, RESTAURANT_URL, LICENSE_URL, BUILDING_URL, CATALOG_URL,
                                 PROJECT_QUESTIONS, STATUS_LABELS, normalize_project, project_profile, validate_regulatory)


logger = logging.getLogger(__name__)
SOURCE_VERIFIED_AT = "2026-10-08"
LIMITATIONS = "Decision support, not legal advice or approval. A district lookup does not verify restaurant permission, overlays, permits or compliance. GIS is as-is, not for engineering purposes. A representative point is not a verified premises or zone lot."
MESSAGES = {"use_review_required": "Official zoning district identified. Confirm the exact premises and proposed use with Denver zoning staff.",
            "unsupported": "Live regulatory coverage is available only for Denver. No local zoning conclusion was made.",
            "no_match": "Denver jurisdiction was identified, but no zoning polygon matched. Official site research is required.",
            "ambiguous": "Multiple polygons or a boundary point prevent a unique district determination. No district was selected.",
            "unavailable": "Official regulatory data could not be retrieved. Other analysis factors remain available.",
            "unknown": "Select a resolved site for regulatory research. Demo analysis does not establish zoning."}


class RegulatoryService:
    def __init__(self, provider):
        self.provider = provider

    def analyze(self, location, concept, values=None):
        lookup = ZoningLookup("unknown")
        if location is not None:
            if location.country_code and location.country_code != "us":
                lookup = ZoningLookup("unsupported")
            else:
                try:
                    lookup = self.provider.lookup(location.latitude, location.longitude)
                    if not isinstance(lookup, ZoningLookup):
                        raise ValueError()
                except Exception:
                    logger.warning("Regulatory lookup unavailable; provider details omitted")
                    lookup = ZoningLookup("unavailable")
        project, _ = normalize_project(values or {})
        try:
            return self._review(lookup, concept, project)
        except (ValueError, TypeError, AttributeError, KeyError):
            logger.warning("Regulatory normalization unavailable; provider details omitted")
            return self._review(ZoningLookup("unavailable"), concept, project)

    def _review(self, lookup, concept, values):
        status = "use_review_required" if lookup.status == "identified" and lookup.record else lookup.status
        if status not in STATUS_LABELS:
            status = "unavailable"
        record = lookup.record if status == "use_review_required" else None
        profile = project_profile(values)
        framework = {2010: "Denver Zoning Code", 1959: "Former Chapter 59"}.get(record.code_family, "Unknown - official framework confirmation required") if record else "Unknown"
        result = {"version": MODEL_VERSION, "status": status, "status_label": STATUS_LABELS[status], "message": MESSAGES[status],
                  "jurisdiction": lookup.jurisdiction, "jurisdiction_id": lookup.jurisdiction_id,
                  "agency": "City and County of Denver / Community Planning and Development" if lookup.jurisdiction_id == "08031" else "", "project_concept": concept,
                  "project": profile, "district": record.district if record else "", "description": record.description if record else "",
                  "code_family": str(record.code_family) if record and record.code_family is not None else "", "framework": framework,
                  "use_status": "Restaurant-use permission not yet verified", "retrieved_at": lookup.retrieved_at, "effective_date": "",
                  "source_version": "Denver GIS layer 209 / schema verified 2026-10-08", "evidence_status": "verified_official_fact" if record else "unsupported" if status == "unsupported" else "unknown",
                  "findings": [], "unresolved": [], "missing": [], "checklist": [], "next_steps": [], "sources": [],
                  "retention_note": "Normalized by VenueBite; geometry omitted. City of Denver Open Data Catalog / CC BY 3.0. Data is as-is and not for engineering purposes.",
                  "limitations": LIMITATIONS}
        for field in ("neighborhood_context", "district_group", "use_form", "district_type", "overlay", "waivers", "conditions", "pud_number"):
            result[field] = getattr(record, field) if record else ""
        if lookup.retrieved_at:
            result["sources"].append(self._source("Official Denver county boundary", BOUNDARY_LAYER, "GIS point query", lookup.retrieved_at))
        if lookup.jurisdiction_id == "08031":
            result["sources"].append(self._source("Official Denver zoning districts", ZONING_LAYER, "GIS point query", lookup.retrieved_at))
            result["findings"].append({"text": "Denver county jurisdiction identified by the official boundary lookup.", "evidence": "verified_official_fact", "source_url": BOUNDARY_LAYER})
        if record:
            result["findings"].append({"text": "Official GIS district: " + record.district, "evidence": "verified_official_fact", "source_url": ZONING_LAYER})
            result["findings"].append({"text": "GIS code-family flag: " + (str(record.code_family) if record.code_family else "unknown") + ". This is not a current amendment or effective date.", "evidence": "interpretation_requires_confirmation", "source_url": CODE_URL})
        if lookup.jurisdiction_id == "08031":
            result["sources"].extend((self._source("Denver zoning frameworks", CODE_URL, "Government guidance"),
                                      self._source("Restaurant and commercial kitchen permits", RESTAURANT_URL, "Government guidance"),
                                      self._source("Denver business licensing", LICENSE_URL, "Government guidance"),
                                      self._source("Denver building and fire codes / accessibility", BUILDING_URL, "Government guidance"),
                                      self._source("City of Denver Open Data Catalog / CC BY 3.0", CATALOG_URL, "Data attribution / terms")))
            topics = [("Primary restaurant land-use classification", None), ("Zoning use permit / zone lot", None),
                      ("Building permit / commercial kitchen", "renovation"), ("Change of use / occupancy", "change_of_use"),
                      ("Retail food establishment licensing", None), ("Health review / inspection", None), ("Fire / life safety", None),
                      ("Hood / ventilation / mechanical work", None), ("Plumbing / electrical work", None), ("Accessibility review", None),
                      ("Signage", None), ("Outdoor seating / right-of-way", "outdoor_seating"), ("Drive-through use review", "drive_through"),
                      ("Alcohol licensing", "alcohol"), ("Parking / transportation", None), ("Landmark / overlays / site-specific review", None)]
            for topic, question in topics:
                answer = profile.get(question, "unknown")
                state = "Government guidance identifies this topic" if question is None else "Requires official confirmation" if answer == "yes" else "Not proposed - user supplied; not an exemption" if answer == "no" else "Not evaluated - project details missing"
                evidence = "general_guidance" if question is None else {"yes": "interpretation_requires_confirmation", "no": "user_supplied", "unknown": "unknown"}[answer]
                result["checklist"].append({"topic": topic, "status": state, "evidence": evidence,
                                            "source_url": LICENSE_URL if topic in ("Retail food establishment licensing", "Alcohol licensing") else BUILDING_URL if topic == "Accessibility review" else RESTAURANT_URL})
            result["unresolved"] = ["Exact premises, zone lot and statutory primary/accessory use classification require official confirmation.",
                                    "Overlays, waivers, conditions and PUD documents were not legally evaluated.",
                                    "Permit requirements, existing approvals and current code amendments are not verified."]
            if framework == "Former Chapter 59" or record and (record.pud_number or "PUD" in record.district.upper()):
                result["unresolved"].insert(0, "Former Chapter 59 / PUD or site-specific documents may control; obtain Denver staff review.")
            result["next_steps"] = ["Confirm the exact premises and restaurant land-use classification with Denver zoning staff.",
                                    "Confirm the applicable code, zone lot, overlays and site-specific conditions before signing a lease.",
                                    "Review zoning use, building, occupancy, health and food-license pathways with the responsible agencies."]
            for key, label in PROJECT_QUESTIONS.items():
                if profile[key] == "yes":
                    result["next_steps"].append("Confirm " + label.lower() + " requirements for the proposed project.")
                elif profile[key] == "unknown":
                    result["missing"].append(label + " plans not supplied.")
            if profile["type"] == "unknown":
                result["missing"].append("Restaurant project type not supplied; the marketing concept is not a statutory use classification.")
        else:
            result["missing"] = ["Authoritative zoning district, framework and site-specific requirements are not established."]
            result["next_steps"] = ["Confirm the governing jurisdiction and obtain current official site-specific zoning and licensing guidance."]
        return validate_regulatory(result)

    @staticmethod
    def _source(title, url, kind, retrieved=""):
        return {"title": title, "url": url, "agency": "City and County of Denver", "type": kind, "retrieved_at": retrieved,
                "verified_at": SOURCE_VERIFIED_AT, "version": "", "effective_date": ""}
