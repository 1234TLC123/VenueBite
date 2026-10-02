# Sprint 06: Site Intelligence v1

Engineering report for the `1234tlc123-probable-succotash` branch, verified October 2, 2026. This sprint adds temporary parcel context, not a fifth scoring factor, legal-use determination or commercial rent feed.

## 1. Implementation

Regrid point lookup now enriches a resolved candidate with parcel identifiers, optional site facts, a validated boundary, conservative considerations and separate provenance. All six outcomes are explicit: exact, nearby, ambiguous, not found, restricted and unavailable. Existing Flask/Jinja, geography, competition, Census and Score Model v2 workflows remain intact.

## 2. Files Created

- `venuebite/providers/site_provider.py`
- `venuebite/providers/regrid_provider.py`
- `venuebite/services/site_intelligence_service.py`
- `static/js/parcel-layer.js`
- `templates/_site_intelligence.html`
- `tests/test_site_provider.py`
- `tests/test_site_intelligence.py`
- `tests/test_site_integration.py`
- `tests/parcel-layer.test.mjs`
- `docs/site-intelligence-v1.md`

## 3. Files Modified

`.env.example`, `requirements.txt`, `README.md`, `venuebite/__init__.py`, `venuebite/routes.py`, `venuebite/services/analysis_service.py`, `templates/base.html`, `templates/results.html`, `templates/_map_workspace.html`, `static/css/style.css`, `static/js/map-viewer.js` and `static/js/analysis-state.js`.

The pre-existing untracked `prompts/06-site-intelligence.md` belongs to the user and was not modified. No scoring, competition, Census, existing test, or private environment file was edited.

## 4. Provider Architecture

`SiteProvider` accepts the already validated Mapbox point and returns immutable `ParcelRecord` objects. `RegridProvider` owns HTTP, bounded parsing and field normalization. `SiteIntelligenceService` owns match selection, facts and cautious site notes. `AnalysisService` appends this result only after score, coverage, explanations and scoring trace are calculated. Routes orchestrate and Jinja renders normalized data. `create_app(..., site_provider=...)` supports offline substitution.

Shapely 2.1 supplies GEOS topology and point-containment checks rather than a handwritten polygon engine. Its NumPy dependency is installed transitively. Geometry checks use longitude/latitude only for topology/containment, never to invent acreage or metric area.

## 5. Endpoints

Application requests use only `GET https://app.regrid.com/api/v2/parcels/point`. Verified parameters: `lat`, `lon`, `radius`, `limit=2`, `return_geometry=true`, `return_stacked=true`, `return_custom=false`; matched buildings, matched addresses, enhanced ownership and add-on zoning responses are explicitly disabled. Core parcel attributes are retained when returned. No Regrid re-geocoding, tiles, paging, broad queries or batch calls occur. See the official [point reference](https://support.regrid.com/reference/get_parcels-point-1).

Two manual metadata checks used the documented free `GET /api/v2/usage` endpoint, outside application code. Only HTTP status and field names/types were emitted. Usage metadata did not identify geographic entitlement.

## 6. Authentication and Security

Only the server reads `REGRID_API_TOKEN`; requests use `Authorization: Bearer`. Header authentication is documented in [Regrid's guide](https://support.regrid.com/docs/mcp-server). The token never enters URLs, HTML, browser configuration, map payloads or CSP. Redirects are disabled so authorization cannot follow an untrusted destination. HTTP logs include only the constant endpoint family and numeric status; error bodies/exception text are not logged or rendered.

Responses are bounded to 1 MiB; timeout defaults to eight seconds, configurable above zero through 30 seconds. Unknown or malformed results become sanitized unavailability. Unexpected adapter errors are isolated without credential-bearing exception traces. County links accept only safe HTTP(S) URLs without user/password or credential-style query parameters; Jinja escapes provider text. No owner names or mailing addresses are normalized.

## 7. Observed Token Coverage

The configured token authenticated successfully. Dallas County, Texas and Durham County, North Carolina returned records. Denver Union Station returned empty exact and 25-meter collections. This is consistent with a geographically restricted sandbox token, but empty results alone do not conclusively establish plan entitlement. Nationwide coverage was not demonstrated and no additional nationwide probes were made.

The official [trial guide](https://support.regrid.com/reference/getting-started-with-your-api) distinguishes the seven-county sandbox from a nationwide self-serve trial. Documentation varies on premium access; actual returned optional fields, not assumed plan benefits, govern display. No trial-specific county logic is hardcoded. Confirm the account/token's exact plan and scope in the dashboard.

## 8. Resolution Algorithm

1. Require resolved candidate coordinates; demo or missing token makes zero requests.
2. Skip countries explicitly outside U.S./Puerto Rico; unknown country metadata defers to the provider.
3. Query radius zero with limit two and stacked results retained.
4. Only an empty exact collection allows one fallback at 25 meters (configurable 0-30; zero disables).
5. Never widen, retry, paginate or choose the first of multiple records.
6. Validate exact containment when a usable boundary exists; mismatch rejects site facts without another query.

## 9. Match Behavior

An exact single record is labeled as an exact point-query match. Without usable geometry, its attributes remain available with an explicit local-containment limitation. A single nearby result is not an exact site and has warning text plus a dashed boundary. Two records are ambiguous; neither facts nor geometry is selected. Empty collections are not evidence of parcel nonexistence. HTTP 403 is restricted entitlement; 401, 429, network, malformed response and server failures are isolated unavailable states.

## 10. Normalized Fields

Field mapping follows Regrid's official [schema](https://support.regrid.com/docs/schema-overview):

- ID/APN/situs: `ll_uuid`, `parcelnumb`, `address`.
- Parcel area/use: `ll_gisacre`, `ll_gissqft`, `usecode`, `usedesc`.
- Zoning context: `zoning`, `zoning_description`, `zoning_type`.
- Structures: `ll_bldg_count`, `structno`, `area_building`, `area_building_definition`, `ll_bldg_footprint_sqft`, `yearbuilt`.
- County-reported values: `landval`, `improvval`, `parvaltype`.
- Sale/source: `saleprice`, `saledate`, `geoid` (county FIPS), `ll_last_refresh`, `sourceurl`.

The normalized object also retains safe geometry and per-field availability. Invalid numeric/date fields become unknown; genuine zero values are not replaced by missing values.

## 11. Geometry and Map

Only valid WGS84 Polygon/MultiPolygon geometry is accepted, with explicit closed rings, finite coordinate bounds, nonzero area, valid topology, holes and a 10,000-point cap. Invalid geometry is omitted without losing usable identifiers/attributes.

Mapbox receives a minimal GeoJSON geometry, derived bounds and snapshot guard, never raw Regrid JSON. Separate cyan fill/outline layers survive Standard/Satellite style reloads without replacing candidate or competitor markers. Emissive paint preserves visibility under dusk lighting. A manual icon-only focus command frames the parcel with capped zoom and respects reduced motion; automatic competitor/candidate framing is unchanged. [Mapbox polygon example](https://docs.mapbox.com/mapbox-gl-js/example/geojson-polygon/), [paint reference](https://docs.mapbox.com/style-spec/reference/layers/).

Browser testing caught an initial `isStyleLoaded()` gate that suppressed overlay creation while style tiles/configuration were settling. Explicit `style.load` readiness now controls insertion; a runtime regression check covers this case. Location, concept, radius and back-forward restoration invalidate site status/ID, payload, layers and facts together.

## 12. UI

A full-width Site intelligence section sits outside the score panel. It uses responsive definition-list columns, match/status feedback, optional fact rows, site considerations and expandable source/match metadata. Unavailable outcomes show one concise message, no fake property facts, and no selected boundary. The mobile layout was checked at 390 by 844; desktop at 1366 by 900.

## 13. Optional Fields

Missing attributes are omitted, with a single county/account coverage caveat. Development evidence is `developed_evidence`, `no_structure_evidence` or `unknown`. A positive structure measurement is evidence of structures, not suitability; an explicit zero is not proof of vacant land. Missing building fields never become zero or a vacancy conclusion. Broad-area points receive a site-address caution.

## 14. Zoning

Available zoning descriptions/codes are informational only. Every usable site report states that restaurant permissions, overlays, conditional-use requirements and approvals have not been verified. Missing zoning gets one concise note rather than fabricated eligibility or repeated unavailable rows. No local land-use code is interpreted as restaurant permission.

## 15. Values and Sales

The schema does not guarantee every county's `landval`/`improvval` is an assessed rather than another value type. Labels therefore say **assessor-reported**, retaining `parvaltype`; no independently verified market value is claimed. Assessor building area and calculated footprint have separate labels/definitions. Recorded sale price/date are historical, not asking prices or current availability. Provider-reported zero prices are displayed as reported, not a commercial cost estimate. Commercial rent/buildout cost is never inferred.

## 16. Score Regression

The original score formulas, normalizations, classification bands, model version, contributions, weights and explanations were not edited. Controlled tests compare full reports before/after exact, nearby, ambiguous, not-found, restricted, unavailable and unexpected-error site outcomes; score, factor provenance, explanation report and audit trace are identical. Weights remain population 30%, income 30%, rent 20%, competition 20%.

## 17. Coverage Regression

Site availability cannot affect the four-factor Data Coverage calculation. Full real Census plus real competition still yields 80%; parcel success does not increase it. Existing partial/failure/demo coverage scenarios all remain tested. Coverage is usable model support, never success probability.

## 18. Rent

The factor stays demo 55/100, with the existing fictional $28/sq-ft annual base-rent metric clearly labeled demo. Real parcel values do not replace it or contribute coverage.

## 19. Tests and Startup

Baseline: **578 passed**. Final Python suite: **732 passed**, including 154 new parcel tests, via `python -m pytest`. Nine isolated JavaScript lifecycle checks passed through the available JavaScript runtime; the executable harness is `tests/parcel-layer.test.mjs`. No automated test calls live Regrid.

`python app.py` started successfully with debugging off and was stopped after the startup smoke check. A separate local preview runs on port 5005; other existing development servers were preserved. Compile, diff and credential checks are included in final verification.

## 20. Live Verification

All observed analyses used signed/retrieved Mapbox coordinates and a one-mile competition radius:

- Dallas, 1500 Marilla Street + Mexican restaurant: exact parcel; situs 1400 Young St; 16.031 acres; calculated building count 1; commercial-improvements description; county refresh 2026-09-30. Overall 60.5, coverage 80%; real Census and live competition retained.
- Durham, 101 City Hall Plaza + Mexican restaurant: exact parcel; 2.430 acres; calculated building count 2; government/community-service description; county refresh 2026-06-09. Overall 59.5, coverage 80%; both real-data providers retained.
- Denver Union Station + Indian restaurant: no records from exact or bounded fallback; no site facts/boundary selected. Overall 66.5, coverage 80%; real Census/competition continue. No parcel nonexistence claim.
- Durham, East Chapel Hill Street/North Mangum Street selection + Indian restaurant: the retrieved point matched a 0.099-acre parcel at situs 109 N Mangum St, with provider description VACANT COMMERCIAL and calculated count zero. Overall 62.1, coverage 80%. These are provider facts, not a verified storefront or legal vacancy determination.
- One repeated Durham City Hall analysis was necessary to verify the final manual-focus control/build after restart; this repeated record counts toward usage.

Standard/Satellite rendering, candidate/competitor preservation, mobile fact layout, source/refresh metadata, disclaimers and stale site removal were checked in the browser. Successful nearby or ambiguous live samples were not encountered; those branches are covered offline. Denver exercised the actual empty fallback path. Provider values differ materially among the supported sites; the score differences come only from existing Census/competition factors.

## 21. Usage

Manual verification made **six point requests returning four parcel records**: three supported single-record analyses, two empty Denver queries and one single-record final-build repeat. Two free usage-metadata checks returned no parcel data. Map interactions/invalidation made no Regrid queries. No wider search was performed. Records returned, including repeats, count toward account use; details and monitoring guidance are in [Regrid's API guide](https://support.regrid.com/docs/getting-started-api).

## 22. Limitations

Entitlement, county fields and freshness vary; no nationwide token scope has been proven. Provider geometry/assessor data are not a survey, title, legal zoning verification, rentable unit, usable-floor-area measurement or availability feed. Multiple stacked/adjacent records require human verification. A nearby result is not an exact site. Geometry caps can omit unusually large boundaries while preserving facts. Source links and optional datasets may be absent. Sequential provider timeouts add to analysis latency. There is no parcel cache, storage, saved analysis or outcome-calibrated site scoring.

## 23. Git and Credentials

Branch unchanged. Twelve tracked files modified; ten implementation/test/documentation files created and unstaged; the user's untracked sprint prompt preserved. No commit, push or index staging was performed. `.env` remains ignored; only `.env.example` is tracked. Exact configured Regrid, Census, Mapbox and signing credentials were scanned via stdin without printing them; no matches were found in tracked/untracked non-ignored files. Private keys were absent from rendered browser configuration/responses.

## 24. Manual Follow-Up

Install the updated requirements in other environments and restart any older server still running before trying Sprint 06. Use the port-5005 preview or `python app.py` normally. Confirm the account's geographic/premium entitlement, record balance/caps and permitted temporary-display use in the Regrid dashboard. Recheck nationwide sites only when the token explicitly supports them. For a real restaurant decision, verify exact parcel/unit, survey, local zoning/approvals, usable floor area, occupancy costs and current availability independently. With a small record budget, identify a real nearby or stacked parcel case for additional live verification; no application setup change is needed to test those branches offline.

Next logical work: evaluate a trustworthy live commercial occupancy-cost source and scoring calibration, with licensing review before any persistence. No future roadmap features were implemented here.
