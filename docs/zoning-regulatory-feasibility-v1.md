# Zoning and Regulatory Feasibility v1

## Purpose and Boundaries

Identify authoritative zoning context and provide an evidence-aware research workflow, not legal advice, a permission engine or an investment recommendation. Live regulatory coverage is initially the **City and County of Denver**, determined geometrically. A marketing concept such as Indian Restaurant is not a statutory use classification. All restaurant-use permission remains unverified.

Regulatory status is independent of Score Model v2 and Data Coverage. Population/income remain 30% each; rent/competition remain 20% each. No factor, normalization, threshold, evidence credit or historical score is changed. Regrid informational zoning remains a separate parcel fact, not a replacement for the official district lookup.

## Architecture and Flow

1. The existing route validates optional enum-only project inputs and resolves the existing signed geographic selection. Invalid or duplicate fields stop before provider calls.
2. `AnalysisService` assembles existing competition, Census, parcel, occupancy, scores, coverage and explanations unchanged, then asks `RegulatoryService` for an independent review.
3. The provider protocol returns immutable `ZoningLookup` / `ZoningRecord` objects. Denver's implementation queries official county polygons, checks unique interior containment, then queries zoning only for confirmed Denver jurisdiction.
4. `RegulatoryService` normalizes district/framework facts, user plans, unresolved questions, checklist topics, next steps, provenance and dates. It does not implement zoning-use tables or evaluate approvals.
5. The shared Jinja partial renders live and historical review. Snapshot format 3 adds a strictly validated regulatory section; SQLite SQL remains in the repository/database boundary. Compare is a persisted-data read.

The provider contract contains no coordinates, geometry, IDs or raw feature properties. Transient returned geometry is validated with the existing Shapely/GEOS helper solely for point containment and then discarded. No new dependency, API key, frontend framework or scraping system is introduced.

## Verified Official Sources

Verified October 8, 2026. These are Denver government sources; ArcGIS hosts Denver-owned public datasets, not a third-party zoning interpretation.

- [Denver county boundary layer 40](https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_ENG_SRVCCDBOUNDARY_A/FeatureServer/40), service item `53a0ae35c018471788efe36b6f730a79`.
- [Denver zoning layer 209](https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_ZONE_ZONING_A/FeatureServer/209), service item `480d73ed76e041ba9f4faa05699c4f93`.
- [Denver Zoning Code and Former Chapter 59](https://denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Community-Planning-and-Development/Denver-Zoning-Code).
- [Restaurant and commercial kitchen permits](https://denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Community-Planning-and-Development/Plan-Review-Permits-and-Inspections/Commercial-and-Multifamily-Projects/Restaurants-and-Commercial-Kitchen-Permits).
- [Denver business licensing](https://denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Business-Licensing).
- [Building and fire codes, policies and guides](https://www.denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Community-Planning-and-Development/Building-Codes-Policies-and-Guides). The linked 2025 Denver Building Code, second printing, includes accessibility in chapter 11; this supports an accessibility research topic, not a premises compliance determination.
- [Denver Open Data Catalog](https://opendata-geospatialdenver.hub.arcgis.com/), its [official Hub configuration and catalog terms](https://www.arcgis.com/sharing/rest/content/items/08ac95d2733c45059ec5a3c76faa770d/data?f=json), and [Denver website terms](https://www.denvergov.org/Terms-of-Use).

Both dataset items were verified as owned by `The_City_and_County_of_Denver` in organization `zdB7qR0BtYrg0Xpl`. Technical point-query parameters were checked against [Esri's official query documentation](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/); Esri documentation is not used as regulatory evidence.

## Query and Schema

GET `/query` on the two fixed layer endpoints uses `f=geojson`, `geometry=longitude,latitude`, `geometryType=esriGeometryPoint`, `inSR=4326`, `outSR=4326`, `spatialRel=esriSpatialRelIntersects`, `returnGeometry=true`, `resultRecordCount=2`, and whitelisted `outFields`. No buffer, nearby zoning fallback, broad query, pagination, arbitrary URL, API switch or retry is used. At most two queries per Denver lookup; unsupported boundary results stop after one.

The boundary dataset includes neighboring county polygons. Only a unique valid polygon with `COUNTY=Denver` and strict interior containment establishes jurisdiction `08031`. A neighboring county name can be reported as unsupported when actually returned. A missing polygon does not establish an alternative jurisdiction. Multiple matches, transfer-limit flags and boundary-edge points are ambiguous. Empty zoning results mean no district match, not that the site is unzoned.

Zoning requested fields: `ZONE_DISTRICT`, `ZCODE_VERSION`, `ZONE_DESCRIPTION`, `NBHD_CONTEXT`, `ZONE_DISTRICT_GROUP`, `ZONE_USE_FORM`, `ZONE_DIST_TYPE`, `OVERLAY_DISTRICT`, `WAIVERS`, `CONDITIONS`, `PUD_NUM`. Text is nullable, bounded and validated. Missing optional fields are unknown, not evidence of no overlay or restriction. Geometry is never retained or displayed as a fabricated zoning boundary.

Live schema/data verification found `ZCODE_VERSION` values 2010 and 1959. Denver's official framework documentation supports the corresponding Denver Zoning Code and Former Chapter 59 families. This field is **not the current amendment date**. Unknown/null flags remain unknown and require official confirmation. PUD/Former Chapter 59 and site-specific cases get additional review guidance; none of their documents is automatically legally evaluated.

## Status and Evidence

Review statuses: `use_review_required`, `unsupported`, `unavailable`, `ambiguous`, `no_match`, `unknown`. An identified district becomes `use_review_required`; every status retains `Restaurant-use permission not yet verified`. Unsupported is neither bad zoning nor a low score. The strict snapshot validator rejects invented approval states and numeric regulatory scores.

Evidence states: `verified_official_fact` for returned district/boundary facts; `user_supplied` for project inputs; `interpretation_requires_confirmation` for unresolved application; `general_guidance` for government research topics; `unknown` for missing information; `unsupported` for coverage. A review's district evidence status does not verify its permit checklist or legal feasibility.

Sources preserve agency, title, exact safe HTTPS URL, type, retrieval time when queried, curated-link verification date, version and effective date when actually known. GIS retrieval time is distinct from analysis/save times. Guidance links were checked October 8 and are explicitly not re-fetched per analysis. No legal effective date was established for a selected site, so it is blank/unknown, not guessed from retrieval time or the code-family flag.

## Project Profile and Checklist

Optional native disclosures contain project type (unknown/full-service/quick-service/cafe/takeout/commercial kitchen) and tri-state proposed/not proposed/unspecified alcohol, patio, drive-through, major renovation and change of use. Defaults are unknown, not false. Input is validated on the server and included in the signed save fingerprint; editing any plan invalidates the whole report and save token.

The Denver checklist contains 16 research topics: primary use, zoning permit/zone lot, building/kitchen, change of use, retail food licensing, health, fire/life safety, ventilation/mechanical, plumbing/electrical, accessibility, signage, outdoor/ROW, drive-through, alcohol, parking/transportation and landmark/overlay/site-specific review. Each has an official source and evidence status. Proposed accessories require confirmation; not proposed is a user statement, **not an exemption**. Unknown plans are not evaluated. No fee, timetable, guaranteed permit or approval probability is generated.

Deterministic steps first confirm premises and statutory use, then code/zone lot/conditions, then agency pathways, followed by proposed accessory/project questions in stable order. No LLM, legal table parser or chatbot is involved.

## Storage and Licensing Assessment

Denver's official catalog terms explicitly identify CC BY 3.0 reuse with City of Denver Open Data Catalog attribution, license identification and website terms. Dataset terms also disclaim warranties, accuracy/completeness and engineering use. The app credits the catalog/license, describes VenueBite normalization, retains source links/dates and displays limitations. This is a source-based engineering retention decision, not an independent legal opinion or municipal endorsement.

Only normalized district/framework/nullable context fields, user project inputs, generated review, checklist, limitations and source metadata are persisted. No GIS geometry, raw GeoJSON, global/object IDs, PUD document payload or external page HTML is stored. These facts are independently Denver-sourced and licensed; Mapbox Search Box coordinates, IDs, labels, POI names/details and raw responses remain transient. User location labels remain explicit user inputs; saved maps remain omitted.

Database schema 3 already stores strict JSON snapshots, so no SQL column migration is needed. New format-3 snapshots add the regulatory section. Existing format-2 snapshots remain byte-for-byte historical data, show Not captured, and are never upgraded by a provider call. Prior legacy geography/attribution scrub migrations remain unchanged. Unsupported, outage and missing states can also be captured in format 3. Unknown future versions or unsafe/corrupt fields are reported unreadable, never silently deleted.

Saved list/detail/Compare/Analyze again prefill perform zero provider calls and no rule reinterpretation or score recalculation. Compare adds missing-aware regulatory rows including status, jurisdiction, district, framework, use review, evidence, unresolved information, dates, model version and source URL. Regulatory coverage has no effect on ranking badges or deterministic comparison highlights.

## Security and UI

Fixed Denver-owned HTTPS endpoints and exact allowlisted displayed source URLs prevent user-directed fetches/SSRF. Redirects are rejected. Each network response is bounded at 1 MiB and a default six-second timeout (0 < timeout <= 15); malformed JSON, duplicate keys, NaN, bad CRS, invalid topology or excessive geometry are rejected. Logs and exceptions contain fixed messages, never provider bodies, request arguments or tokens. Automated tests make no real calls.

Strict versioned snapshot whitelists, bounded strings/lists, enum values, aware timestamps, valid source dates and safe HTTPS sources are validated before storage and reading. SQL remains parameterized in the existing repository. Existing CSRF, HTML escaping, CSP, no-store headers, signed selections, stale-save validation and ignored database/environment rules remain in force. The existing intentional public Mapbox GL token behavior is preserved; no regulatory credential exists and Census/Regrid/private server secrets are not rendered.

The full-width evidence section uses existing shell tokens, native keyboard disclosures, labeled selects, visible focus, stacked mobile layouts and existing reduced-motion behavior. Zoning is an evidence card, not an extra map layer: no parcel/zoning confusion, new map requests or false boundaries. Existing Map/Satellite, competition markers and parcel controls are unchanged.

## Limitations and Future Jurisdictions

Live coverage is Denver only and the representative point is not a surveyed premises/zone lot. Boundary datasets can change. No permission, approved-existing-use, overlay applicability, exemption, license availability, fee, legal-currentness or compliance conclusion is made. Current site documents and Denver staff review remain essential before committing to a lease. Curated guidance requires periodic verification.

Add future jurisdictions behind the same provider/service boundary only after verifying ownership, geometry/schema, jurisdiction detection, frameworks, source/retention rights and legal limitations. Do not infer coverage from a city string. A licensed permanent-storage geocoder, owner-scoped persistence and production hardening remain separate future work.
