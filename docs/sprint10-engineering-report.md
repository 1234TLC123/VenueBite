# Sprint 10 Engineering Report

Initial implementation verification: October 8, 2026, America/Denver (live timestamps after midnight are October 9 UTC).

Final acceptance review: **October 11, 2026, America/Denver** (the new live smoke timestamps are October 12 UTC). All requested runtime, storage, scoring, test and Git checks were repeated or verified. Subsequently, the owner confirmed completion of public Mapbox token rotation or appropriate URL restrictions in the Mapbox dashboard. A targeted security closure recheck passed without requesting or exposing the token. The October 8 diagnostic exposure note is preserved, acceptance item 21 is now closed, and **SPRINT 10 FULLY COMPLETE**.

## 1. Sprint Objective

Add authoritative Denver zoning identification and a conservative, evidence-aware regulatory research workflow, integrated with live analysis, Saved Sites and Compare. Preserve all Sprint 01-09 functionality, Score Model v2, Data Coverage, occupancy semantics and Mapbox storage restrictions. No automated legal permission engine was added.

## 2. Baseline State

Read `AGENTS.md` and `prompts/10-zoning-regulatory-feasibility.md` completely before implementation. Inspected repository, branch, Git status/diff, existing providers/services/templates, persistence and comparison architecture, prior engineering/design documentation and tests.

Branch: `1234tlc123-probable-succotash`; starting HEAD: `5ca4bcb`. Source was clean; the Sprint 10 prompt was already an untracked user-provided file. Baselines passed: **1,025 Python tests** and **58 JavaScript tests**. The development database contained three format-2 snapshots under SQL schema 3. No previous sprint was recreated or discarded.

## 3. Deliverables

Official Denver county and zoning point provider; normalized regulatory service; validated optional project plans; deterministic, sourced checklist and next steps; futuristic full-width results/detail section; persisted regulatory snapshots; missing-aware Compare rows; backward compatibility; security and regression tests; design documentation and this report. No new dependencies or unrelated features.

## 4. Files Changed

New files (12):

- `venuebite/providers/zoning_provider.py`
- `venuebite/providers/denver_zoning_provider.py`
- `venuebite/regulatory.py`
- `venuebite/services/regulatory_service.py`
- `templates/_regulatory_form.html`
- `templates/_regulatory_feasibility.html`
- `tests/test_zoning_provider.py`
- `tests/test_regulatory.py`
- `tests/test_regulatory_integration.py`
- `tests/regulatory-state.test.mjs`
- `docs/zoning-regulatory-feasibility-v1.md`
- `docs/sprint10-engineering-report.md`

Modified files (15): `.env.example`, `README.md`, `static/css/style.css`, `static/js/analysis-state.js`, `templates/_search_form.html`, `templates/results.html`, `templates/saved_detail.html`, `tests/run-js-tests.mjs`, `venuebite/__init__.py`, `venuebite/routes.py`, `venuebite/saved_routes.py`, `venuebite/services/analysis_service.py`, `venuebite/services/comparison_service.py`, `venuebite/services/saved_site_service.py`, `venuebite/snapshots.py`.

The existing untracked `prompts/10-zoning-regulatory-feasibility.md` remains untouched. Ignored verification launcher/logs/database are local testing artifacts, not source deliverables.

## 5. Architecture

Flask routes remain HTTP/validation/service adapters. `ZoningProvider` exposes immutable normalized lookup/record contracts, with a Denver implementation. `RegulatoryService` owns deterministic review generation. `regulatory.py` centralizes enums, exact official URL allowlisting and persisted validation. Shared Jinja handles presentation; SQLite remains behind existing repository/service boundaries. SQL and formulas were not added to routes.

## 6. Data Flow

Validate project form, resolve the existing signed location, assemble all prior analysis/scoring, then obtain independent regulatory review. Official geometry is used transiently for containment and discarded. Live review is displayed; explicit saving persists normalized review and user plans. History reads only saved JSON and never requests current evidence or recalculates scores.

## 7. Provider Design

Two fixed public HTTPS ArcGIS queries, with no credential: county boundary first, then zoning only for confirmed Denver. GeoJSON/WGS84, strict containment, at most two matches, no proximity zoning fallback, retry, pagination or arbitrary fetch URL. Six-second default per-request timeout, capped at 15 seconds; one-MiB response cap; duplicate-key/nonfinite JSON rejection; geometry/CRS validation; redirects rejected; sanitized fixed errors. Default provider is disabled in automated testing.

## 8. Official Sources

The exact endpoints, item ownership, schema and terms were verified before selecting fields or parameters. Dataset organization: `zdB7qR0BtYrg0Xpl`; item owner: `The_City_and_County_of_Denver`.

- [Official Denver county boundary layer 40](https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_ENG_SRVCCDBOUNDARY_A/FeatureServer/40).
- [Official Denver zoning layer 209](https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_ZONE_ZONING_A/FeatureServer/209).
- [Denver zoning frameworks](https://denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Community-Planning-and-Development/Denver-Zoning-Code).
- [Restaurant/commercial kitchen permit guidance](https://denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Community-Planning-and-Development/Plan-Review-Permits-and-Inspections/Commercial-and-Multifamily-Projects/Restaurants-and-Commercial-Kitchen-Permits).
- [Business licensing](https://denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Business-Licensing).
- [Building/fire codes and accessibility source](https://www.denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Community-Planning-and-Development/Building-Codes-Policies-and-Guides).
- [Denver Open Data Catalog](https://opendata-geospatialdenver.hub.arcgis.com/) and its [official Hub terms configuration](https://www.arcgis.com/sharing/rest/content/items/08ac95d2733c45059ec5a3c76faa770d/data?f=json).

Esri's official query documentation informed technical request parameters, not regulatory conclusions. No commercial zoning interpretation or non-government regulatory evidence was used.

## 9. Source/Licensing Assessment

Catalog terms explicitly identify CC BY 3.0 reuse with City of Denver Open Data Catalog attribution, license identification and website terms. Dataset terms disclaim warranties and engineering use. Normalized Denver facts retain attribution, source links, dates and limitations; VenueBite normalization is disclosed. No municipal endorsement or independent legal licensing opinion is claimed. Geometry/raw responses and page contents are not persisted. See the design document for source ownership, exact schema and retention reasoning.

## 10. Jurisdiction Handling

The official county layer contains Denver and neighboring polygons. Only a unique valid interior `COUNTY=Denver` match establishes jurisdiction `08031`. City labels, mailing addresses, Census metadata and Regrid zoning fields do not establish it. Non-US country metadata avoids a Denver request. Other counties or no boundary match are unsupported; missing alternatives remain unnamed. Multiple or edge matches are ambiguous, not first-match guesses.

## 11. Denver Zoning Lookup

The provider queries `ZONE_DISTRICT`, `ZCODE_VERSION` and nine explicitly verified optional context fields. Longitude/latitude order, geometry type, WGS84 SRs, intersection relation, field whitelist, response format and cap are tested. A unique interior zoning polygon yields an official GIS district, not a verified premises or legal zone lot. Empty results remain no match; missing overlay/waiver/condition values remain unknown.

## 12. Denver Code-Framework Handling

Verified live code-family values 2010 and 1959 correspond to Denver Zoning Code and Former Chapter 59. Unknown/null values remain unknown. Code-family flags are not current amendment/effective dates. PUD/Former Chapter 59/site-specific cases surface additional official review needs. No use table, waiver, condition, overlay or PUD document is automatically legally interpreted.

## 13. Regulatory Evidence Model

Version `regulatory-review-v1`; independent states `use_review_required`, `unsupported`, `unavailable`, `ambiguous`, `no_match`, `unknown`. Evidence separates verified official facts, user-supplied facts, interpretation requiring confirmation, general guidance, unknown and unsupported. Sources preserve title, URL, agency, type, retrieval/verification dates, version and actual effective date when known. Guidance links show their curated October 8 verification date and explicitly are not re-fetched per analysis. Legal effective dates remain unknown.

## 14. Restaurant-Use Safeguards

Every result says **Restaurant-use permission not yet verified**. District identification never implies restaurant permission, an exemption, compliance or approval. Concept and government classification stay separate. Snapshot validation rejects invented approved/permitted states and numeric regulatory scores. Unknown/missing fields are not negative site facts. No fee, timing, confidence percentage or success probability is fabricated.

## 15. Project-Specific Attributes

Optional native disclosure: unknown/full-service/quick-service/cafe/takeout/commercial kitchen; tri-state alcohol, patio, drive-through, major renovation and change of use. Server-side enum and duplicate validation happens before provider calls. Unknown is distinct from no. The signed save fingerprint binds every project input. Analyze again prefills user plans but clears geographic selection and does not refresh providers.

## 16. Permit/License Checklist

Sixteen sourced research topics cover primary use, zoning permit, kitchen/building, occupancy/use change, food licensing, health, fire, mechanical/hood, plumbing/electrical, accessibility, signage, outdoor/ROW, drive-through, alcohol, parking and site-specific/landmark review. Core topics are government guidance, proposed options require confirmation, missing plans are unknown/not evaluated, and not proposed is user supplied rather than a verified exemption. Accessibility links to the verified building-code source. Exact applicability remains unresolved.

## 17. Deterministic Next Steps

Stable ordering: confirm exact premises and statutory primary/accessory use; confirm code, zone lot and site conditions; review agency pathways; then confirm proposed accessory/project questions. Project omissions generate explicit missing-information items. No LLM, AI feature or random generation is used.

## 18. UI Integration

The existing form adds only an optional progressive disclosure. Results add a Regulatory section anchor and a full-width, restrained intelligence section. Live and saved detail share the same section: independent status, jurisdiction/district/framework/use status, priority steps, expandable facts/questions, checklist, project profile and source history. Legacy detail explicitly says Not captured, without silently filling it with current Denver guidance. Existing navigation and futuristic visual tokens are preserved.

## 19. Map Integration

Use the reliable evidence section rather than an extra polygon layer. Transient query geometry is not a published zoning overlay, not confused with a parcel and not saved. Existing Map/Satellite/competition/parcel logic is untouched. Browser Mapbox geography and GL rendering worked; JavaScript parcel/style/marker regression tests passed. No saved map or provider-originated coordinate was added.

## 20. Saved Sites Integration

Completed live reviews can be explicitly saved with own user location labels. New regulatory facts, project profile, sources, retrieval dates, legal unknowns and generated guidance are stored as a historical snapshot. Browser saving of the live Denver review succeeded in the separate verification database. Unsupported/outage/missing states also persist, tested offline. Saved list/detail and reanalysis prefill never analyze, fetch or reinterpret.

## 21. Snapshot Migration/Backward Compatibility

SQL schema remains 3 because its existing versioned JSON column needs no DDL change. New analyses with regulatory review use snapshot format 3; existing format-2 records remain unchanged and readable. Validators support both formats and reject unsupported/malformed regulatory data. Previous prototype geography/attribution scrub migrations remain unchanged. Old snapshots are not promoted or enriched. All three original rows match their starting values exactly; mixed 2/3 history survives an actual Flask process restart.

## 22. Compare Integration

Persisted rows include review status, jurisdiction, district, framework, unverified permission, evidence, unresolved/missing conditions, retrieval/effective dates, workflow version and official GIS source URLs. Both county and zoning evidence URLs are available for identified sites. Legacy data is Not captured/Unknown, not zero or bad zoning. Two- and four-site browser comparison passed, including live Denver versus the historical Aurora NNN snapshot. Three-site comparison is covered by the existing full suite. Ranking badges/highlights remain governed only by prior model/context/evidence rules, not zoning coverage.

## 23. Scoring Separation

No scoring module or weights changed. Ten integration scenarios compare score, coverage, trace, explanations, factor provenance and occupancy exactly against analysis without regulatory service across identified/unsupported/unavailable/ambiguous/no-match states, with and without NNN terms. Weights remain .30/.30/.20/.20. No historical recalculation.

Live Denver selected-point math: 85*.30 + 80*.30 + 55*.20 + 29.4*.20 = 66.38, displayed **66.4**, reflecting Census fallback and real competition, not zoning. Original stored values remain 46.1, 70.2 and 48.3.

## 24. Data Coverage Separation

No coverage calculation or credit changed. The live Denver review had verified zoning but still **20%** Data Coverage, because Census was unavailable, competition was real, and rent demo. Offline full-Census/competition fixtures remain 80%; sufficient user NNN terms remain partial and produce 90%. Original Aurora NNN remains 90%, $9,450 known monthly cost against $10,000 budget, 94.5% utilization and rent score 66. Zoning adds no coverage credit. Coverage is not business-success or approval probability.

## 25. Security Controls

Exact HTTPS provider/source allowlists; redirect refusal; timeout/size caps; duplicate/nonfinite JSON rejection; WGS84/topology/containment validation; bounded text/enums/lists/dates; strict snapshot whitelist; no arbitrary URL fetching. Existing parameterized SQL, CSRF, signed selections, stale-save checks, Jinja escaping, CSP and no-store behavior remain. Provider details are omitted from errors/logs. Synthetic malicious HTML, source URLs, dates, payload fields, IDs and stale inputs are tested.

Private-key scans of tracked/untracked source, SQLite bytes and local verification logs found zero real credential values. No regulatory credential is required. The preexisting intentionally public Mapbox GL token behavior remains unchanged; it is not a private server secret. An early browser DOM diagnostic included its existing attribution-link URL before output redaction was applied; subsequent diagnostics redacted public token URLs. No Census/Regrid/private server key was printed or persisted. Public-token origin restrictions should remain configured according to existing Mapbox setup guidance.

October 11 recheck: all 158 tracked/unignored project files were scanned against configured Mapbox, Census, Regrid and server-secret values from the ignored environment and process environment, plus public/secret/temporary Mapbox JWT patterns. **Zero active credential matches**; neither `.env` nor a SQLite database is tracked. SQLite byte scans also found zero configured credential values. No credential value was printed in this acceptance review. The historical exposure remains documented rather than erased.

Earlier October 11 review status: remediation was unverified and acceptance item 21 was open because the owner had not yet confirmed rotation or URL restrictions. This earlier status is superseded by the subsequent owner confirmation below; the historical exposure itself is not erased.

Current remediation status: **REMEDIATED / acceptance item 21 CLOSED (owner-confirmed)**. The owner subsequently confirmed on October 11: the previously exposed public Mapbox token was rotated or appropriate URL restrictions were added in the Mapbox dashboard. The agent did not independently inspect the dashboard, determine which of those two measures was used, request the token value or perform a token/account change. Source-file scans do not establish remote revocation or restriction settings; the dashboard remediation is supported by the owner's explicit confirmation. Mapbox's [official Tokens API documentation](https://docs.mapbox.com/api/accounts/tokens/) distinguishes token validity from `allowedUrls` metadata.

Targeted closure recheck: 158 tracked/unignored files again contained zero configured Mapbox/Census/Regrid/server-secret values or Mapbox JWT patterns. Both SQLite databases passed integrity, strict snapshot/prohibited-data and credential checks, with original row digests unchanged. Six actual-development Saved Sites/detail/Compare routes returned HTTP 200 with all six provider counters, HTTP opens and analysis calls zero. `.env` and both databases remain ignored. No other issue was found. Only this report was edited; the complete suites and live smoke checks were not repeated unnecessarily. Their immediately preceding October 11 results remain 1,191 Python tests and 70 JavaScript checks passed, with Denver D-CV and unsupported Greeley smoke checks passed.

## 26. Data Retention/Database Inspection

Direct read-only SQLite checks passed `PRAGMA integrity_check` for both databases. Strict decoding of every row found no coordinate/geometry/feature/raw-response/Mapbox-ID/POI-directory/credential keys, no coordinate columns and no real credential bytes. Regulatory format-3 storage contains only the intended normalized 34-field structure, including nested user plans/evidence/source records, never raw GIS payloads. Existing aggregate VenueBite competition outputs remain, not business records.

`instance/venuebite.db`: three unchanged format-2 rows, digest `00e54b04874d5f519954ce5d8656df062962cd33d8649a7a336636b4aab88d1f` before and after. `instance/sprint10-verification.db`: backup of those rows plus the manually saved live Denver format-3 record, ID 5. Its four-row digest `d75c883a2f9d6e02088bfe8ddbb32b118707c59d82e92c4b3cc5f063038ebf4b` remained identical across Flask restart and history reads. Your development records were not edited.

Ignored local counters wrap all six provider families without printing arguments. After actual restart, Saved Sites, legacy detail, new detail and two-/four-site Compare all recorded **0 location, 0 competition, 0 Census geography, 0 Census data, 0 parcel, 0 regulatory** calls. Integration reconstruction also replaces provider methods and `AnalysisService.analyze` with failures to prove these paths cannot refresh/recalculate.

An additional manual check used the actual development database with every provider method replaced by a failing counter. `/saved`, all three existing detail pages and Compare returned HTTP 200 with all six counters zero. Final scans covered 158 tracked/untracked source files with zero credential findings; both database digests remained unchanged.

October 11 final recheck: both databases passed `PRAGMA integrity_check`, strict decoding, prohibited-field/coordinate-column checks and configured-credential byte scans again. The original development rows remain IDs 1/2/3, format 2, scores 46.1/70.2/48.3 and coverage 80/20/90; their original digest still matches. The verification database remains those exact rows plus the format-3 Denver record, ID 5, with only the normalized 34-field regulatory structure. Its original digest also matches. No raw regulatory geometry/payload, Search Box coordinates/IDs/POI details/directory or credential value was found.

The actual development database was tested again through Saved Sites, all three detail pages and two-/three-site Compare with provider methods, HTTP opening and `AnalysisService.analyze` blocked: six HTTP-200 routes, **zero provider calls, zero HTTP opens, zero analysis calls**. Then the two identity-verified Sprint 10 preview processes were stopped and Flask was started again against the existing separate verification database. Seven local HTTP requests covered Saved Sites, all four details, and two-/four-site Compare: all HTTP 200, no Mapbox GL script/initial-location payload, and all six runtime provider counters remained zero. Both row digests remained unchanged after the real process restart and reads. No database records were created, edited or deleted during this acceptance review.

## 27. Python Test Results

Full command: `.venv\Scripts\python.exe -m pytest -q --tb=short -o cache_dir=.venv/pytest-cache-sprint10`.

**1,191 passed**, baseline 1,025, net 166 new cases. Tests cover official query/schema normalization, malformed/oversized responses, network/rate/redirect errors, topology/edges/multiple matches, country/county coverage, frameworks/PUD, project validation, checklist semantics, source security, exact score/coverage separation, route degradation, formats 2/3, reconstruction, persistence whitelists, no providers on history, stale saves and escaping. No live provider calls or development database use in automated tests. Python compileall passed. Controlled cache avoids the workspace's earlier Windows cache permission issue; no application workaround was introduced.

October 11 full rerun: `.venv\Scripts\python.exe -m pytest -q --tb=short -o cache_dir=.venv/pytest-cache-sprint10-acceptance` -> **1,191 passed in 21.12 seconds**. Python compileall passed again. Score/coverage equality tests passed, and `git diff` confirms `scoring.py`, `data_coverage.py`, demographic/competition scoring, occupancy and existing factor explanations are unchanged from HEAD. No model or source-code edit was needed for this review.

## 28. JavaScript Test Results

Full `tests/run-js-tests.mjs` suite: **70 passed**, baseline 58. Initial implementation checks used the provided Node runtime. The October 11 acceptance rerun used **Node.js v24.20.0**, independently verified at `C:\Program Files\nodejs\node.exe`, with PowerShell command `& 'C:\Program Files\nodejs\node.exe' tests/run-js-tests.mjs`; **70 passed**. This review shell does not resolve `node` by name, so the explicit executable path was used without changing system PATH. Counts: parcel 9, occupancy 16, form 12, saved/comparison 21, regulatory 12. New cases cover all six project input/change events, location/concept/radius invalidation, back-forward stale evidence and normal page-load preservation. Existing map/parcel/style, busy form, saved token and comparison keyboard behavior all passed.

## 29. Live Smoke Test Results

These are separate from offline automated tests:

- Implemented provider/service against live Denver-owned GIS: civic-center test point returned **D-CV**, Denver jurisdiction, Denver Zoning Code, official use review required, seven source records and sixteen checklist topics. UTC retrieval October 9 04:19:56. Legal permission/effective date remained unverified/unknown.
- Live Greeley point: unsupported, no district, no Denver permit checklist and no invented local conclusion. UTC retrieval 04:19:57.
- Full browser analysis: Mapbox-selected Denver representative point returned **D-C**, Denver Zoning Code and populated **UO-1 overlay field**, without interpreting it as legally applicable or granting permission. Alcohol/patio plans were user supplied and drive-through not proposed. Official zoning retrieval UTC 04:22:07. Live competition returned 37 observed restaurants, 12 direct matches and factor 29.4. No POI records were saved.
- Census geography timed out in that live analysis; no ACS request followed, and existing raw-metric-unavailable/demo-score behavior remained. Regrid exact/nearby bounded lookups returned no match; parcel nonexistence was not inferred. These live external outcomes were not hidden or marked successful.
- Live regulatory save, actual restart, mixed-format detail and comparison passed. Manual injected regulatory outage returned HTTP 200 and retained working fixture map/Census/competition/parcel behavior. This last check is explicitly injected, not an observed Denver outage.

October 11 acceptance live rerun, using the implemented service and public official Denver GIS only:

- Denver civic-center point -> **D-CV**, City and County of Denver, Denver Zoning Code, `use_review_required`, seven source records and sixteen checklist items. Retrieval **2026-10-12T04:40:38.221149+00:00**. Restaurant permission remains unverified; legal effective date remains unknown.
- Greeley point -> **unsupported**, blank district, unknown framework, one official boundary-query source record and no Denver permit checklist. Retrieval **2026-10-12T04:40:39.349867+00:00**. No local legal conclusion was invented.
- No fresh Mapbox, Census or Regrid analysis was needed for this acceptance review. The earlier Census timeout and parcel no-match remain historical outcomes, not claims about current provider availability. No new regulatory facts were written into either database by these smoke checks.

## 30. Accessibility/Mobile Review

Browser review at 1440x1000, 768x1024 and 390x844. Desktop four-column, tablet two-column and phone one-column regulatory summaries fit; no horizontal page overflow. Phone project controls have labels and 50px targets. Native disclosure activation via Enter worked with visible solid focus; checklist links have 44px minimum targets. Four-site comparison scrolls inside its region, with ArrowRight moving it 220px, not the page. Unknown/missing states are textual, not color-only. Existing reduced-motion stylesheet was inspected; no new animation was introduced. Browser error count was zero during detail review.

No formal screen-reader certification or OS reduced-motion preference toggle was performed. Semantic markup, keyboard behavior and existing motion rules were verified; these optional deeper audits are not claimed as performed.

## 31. Known Limitations / Manual Checks

Denver-only coverage; representative points are not verified storefronts/zone lots; legal use permission, overlay applicability, existing approvals, current site documents and project-specific permits remain unresolved. Curated official links need periodic maintenance. No fee/timeline/compliance/approval determination exists. SQLite is still local, unencrypted and not owner-scoped; do not deploy publicly without later hardening. Saved records remain historical.

No new API setup is required. Restart normal Flask to pick up source/config changes; regulatory defaults enabled. Use `REGULATORY_ENABLED=false` for explicit offline fallback. The local verification preview is at `http://127.0.0.1:5011/` and deliberately uses **the separate ignored verification DB**, not your development DB. Normal `python -m flask --app app run` retains the default development DB. A future site decision still requires direct Denver staff/code/document review. Live Census timeout can be retried independently; it is not a regulatory dependency and was not changed in this sprint.

Historical safety incident, now remediated on owner confirmation: the October 8 diagnostic public-token disclosure described in section 25 cannot be undone from the conversation transcript. The token was already intentionally client-visible in the existing Mapbox application, but the strict instruction prohibited printing it. The agent did not rotate the token or change the account. On October 11 the owner confirmed rotation or appropriate URL restrictions in the Mapbox dashboard, closing item 21. No real token value is reproduced in source, this report or subsequent diagnostics. If the configured environment token was replaced, restart any existing Flask process to load that replacement; no token value needs to be shared.

Exact remaining caveats after the October 11 review:

- **No incomplete acceptance items remain.** Item 21 is remediated on explicit owner confirmation; the historical incident remains documented. Remote dashboard settings were not independently inspected by the agent.
- Regulatory live coverage remains Denver-only. Point/district identification does not verify premises/zone lot, restaurant permission, overlay/condition applicability, approvals, permit exemptions or legal effective dates; current official site-specific review is still required.
- Saved analyses are historical and never automatically refreshed. Curated guidance links were checked October 8; this review did not revalidate every guidance page or establish its current legal applicability.
- SQLite remains local, unencrypted and not owner-scoped; production security/ownership is outside Sprint 10. The preview uses the separate ignored verification database, not the unchanged development database.
- Screen-reader certification and an OS reduced-motion toggle were not performed. Prior visual/keyboard review and current semantic/motion regression checks stand; deeper audits are optional, not falsely claimed as passed.
- October 8 Census timeout/Regrid no-match are historical limitations. Those providers were intentionally not called again during this review; their current live availability is unverified.

## 32. Final Acceptance and Git Status

Acceptance checks:

1. Existing analyses: all baseline regressions pass; live full analysis works with honest external fallbacks.
2. Score Model v2 unchanged: equality tests and untouched scoring modules.
3. Data Coverage unchanged: equality/math tests and live 20% despite verified zoning.
4. Authoritative supported Denver lookup: live D-CV and browser D-C.
5. Unsupported jurisdictions: live Greeley and offline country/county tests.
6. No invented permission: fixed unverified state and strict validation.
7. Framework distinctions: 2010/1959/unknown and PUD tests.
8. Provenance: stored agency/title/type/URL/dates and per-finding evidence.
9. Safe official links: exact HTTPS allowlisting and escaping tests.
10. Evidence-aware checklist: tested sourced statuses and user-plan distinctions.
11. Missing requirements remain missing: explicit unknowns; no exemptions guessed.
12. Outage isolation: automated and manual injected HTTP-200 checks.
13. Existing Saved Sites load: actual restart and legacy-detail checks.
14. Historical records unchanged: original row digest and format-2 equality checks.
15. Backward-compatible persistence: strict formats 2/3, SQL schema 3, migration regressions.
16. Saved detail zero providers: runtime counters and failing-provider tests.
17. Compare zero providers: runtime counters and failing-provider tests.
18. Persisted-only Compare: reconstruction/failing-analysis tests and immutable row digests.
19. No unauthorized Search Box storage: whitelist and SQLite audits.
20. No raw regulatory response storage: contract/whitelist and SQLite audits.
21. **PASS / REMEDIATED (owner-confirmed):** the owner confirmed post-exposure public Mapbox token rotation or appropriate URL restrictions in the dashboard. Targeted source/storage/credential and history-isolation checks passed again. The October 8 diagnostic exposure remains documented in sections 25 and 31; no independent dashboard inspection or token-value disclosure is claimed.
22. Development DB ignored: `git check-ignore -v`, `.gitignore:223`.
23. `.env` ignored: `git check-ignore -v`, `.gitignore:151`.
24. Existing futuristic design retained: shared tokens and desktop/phone visual review.
25. Mobile usability: no page overflow; responsive controls and scroll-contained matrix.
26. Accessibility preserved: labels, targets, native keyboard disclosures/focus and existing motion rules.
27. Complete Python suite: 1,191 passed.
28. Complete JavaScript suite: 70 passed.
29. Live Denver smoke performed: passed; external Census/parcel limitations reported separately.
30. Documentation: README, design document and 32-part report supplied.
31. Diff scope: only Sprint 10 source/docs/tests/config plus the preexisting untracked prompt.
32. Git discipline: nothing staged, committed or pushed; HEAD remains `5ca4bcb`.

**SPRINT 10 FULLY COMPLETE**. All 32 acceptance items are satisfied, with item 21 remediation supported by explicit owner confirmation and the passing targeted closure checks. No required acceptance item remains incomplete. Explicit product limitations and unperformed optional audits remain listed above, not represented as verified legal facts or tests.

Final Git status consists of the 15 modified files and 12 new Sprint 10 files listed in section 4, plus the original untracked prompt. `git diff --cached --name-only` is empty and `git diff --check` passes. `.env`, development/verification SQLite files, sidecars, preview launcher and logs are ignored and untracked by Git. No staging, commit or push command was run.

October 11 review and closure Git confirmation: same branch and HEAD `5ca4bcb`; **15 modified / 13 untracked** (including the preexisting prompt). Nothing staged. No stage, commit, push, fetch or history-rewrite operation was performed. Only this engineering report was edited during the acceptance review and item-21 closure. Runtime restart logs remain ignored. Final `git diff --check` is clean; ordinary Windows line-ending warnings are not whitespace failures. **All 32 acceptance items are satisfied; item 21 is closed.**
