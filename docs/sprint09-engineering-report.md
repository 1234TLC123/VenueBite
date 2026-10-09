# Sprint 09 Engineering Report

Verified October 7, 2026, America/Denver (analysis timestamps cross into October 8 UTC). Continued the existing worktree; no discard, recreation, commit or push.

### Final Safety Re-Verification - October 8, 2026

Rechecked the current worktree before changing application code; no application changes were necessary. All ten requested final safety checks passed:

1. Stopped the verified VenueBite Flask preview process and restarted Flask against the same development SQLite database. All three saved sites and details remained available.
2. Compared persisted snapshots with analysis, score calculation and coverage calculation disabled by fail-fast guards. The comparison snapshots matched repository records exactly; no recalculation occurred.
3. Opened Saved Sites, each detail, the comparison picker, two-site comparison and three-site comparison in the browser after restart. Cumulative provider invocation counts remained zero for Mapbox location, competition, Census geography, Census data and Regrid. Saved pages loaded only the local saved-sites module, not the map SDK.
4. Inspected SQLite directly in read-only mode: schema 3, snapshot format 2, three readable records, integrity OK, no coordinate columns or prohibited nested fields, no Mapbox IDs, no POI records/details, no raw provider payloads, and no configured credentials or credential patterns. All locations are user-supplied labels with coordinates not retained. All stored score/contribution and coverage/credit sums match.
5. Confirmed `instance/venuebite.db` and SQLite sidecars are Git ignored and no database files are tracked.
6. Confirmed `.env` remains Git ignored and untracked. Scanned 145 tracked/non-ignored files and the new verification logs: no configured credentials or token-pattern hits.
7. Complete Python suite: **1,025 passed in 14.25 seconds**, using `.venv/Scripts/python.exe -m pytest -o cache_dir=.venv/pytest-cache-sprint09 -q --tb=short`.
8. Complete JavaScript suite: **58 passed** (parcel 9, occupancy 16, form 12, saved/compare 21), using the available JavaScript runtime and refreshed modules. Node CLI remains unavailable on PowerShell PATH.
9. Inspected Git diff/status; diff whitespace check passed. Branch remains `1234tlc123-probable-succotash`, HEAD `f01f256`, 24 modified tracked files, 40 untracked entries, no staged changes.
10. Nothing was staged, committed, pushed, discarded or recreated. Existing Sprint 07-09 work and all three saved records were preserved.

The SHA-256 digest of all persisted rows was identical before restart and after saved/detail/comparison browsing: `6c95f0ee5c0731708e99ccd13bdb3df7ea17162eef5c144562cfddd78a1585d8`. This covers names, timestamps, models, scores, evidence and occupancy data. Browser warning/error logs were empty. The NNN snapshot still displays $9,450 known monthly occupancy, 94.5% budget utilization, rent 66 with partial evidence and 90% coverage; demo-rent comparisons retain the explicit unequal-evidence warning.

No incomplete Sprint 09 acceptance items were found. Sections 27-28 retain the original live save, four-site comparison and confirmed deletion evidence; this safety-only pass did not spend additional provider requests or create/delete further records. The limitations and optional manual follow-up in sections 29-32 still apply. Preview: http://127.0.0.1:5010/saved.

## 1. Sprint 09 Summary

Completed SQLite Saved Sites, validated save action, immutable historical snapshots, detail, confirmed deletion, functional navigation, 2-4 comparison, evidence-aware deterministic highlights, persistence restart verification, mobile/keyboard review and documentation. Sprint 01-08 functionality/model semantics remain intact.

At continuation, AGENTS.md and the complete Sprint 09 prompt were read. Git status/diff/branch and current tests were inspected before edits. Outstanding acceptance areas were the Mapbox retention refactor, live save/detail/compare validation, migration safety, new persistence/JS tests, deletion/restart/no-provider-call verification, mobile/accessibility review, credential/database/diff inspection and final documents. Those areas are now completed. The old comparison template also needed a dict-key lookup fix (`row['values']`, not the `dict.values` method), and UTC display needed timezone normalization.

## 2. Persistence Architecture

Flask/Jinja remains the application architecture. Database boundary -> parameterized repository -> SavedSiteService / ComparisonService -> HTTP blueprint -> templates. Existing AnalysisService never reads/writes SQLite. No ORM, framework, database server, provider API or dependency was introduced.

## 3. Database Path

Default: `instance/venuebite.db` under this repository. Optional server environment override: `VENUEBITE_DATABASE_PATH`. Three manual verification snapshots remain: Aurora demo-rent, Greeley demo-rent, Aurora NNN. Test-only fourth snapshot was deleted. Automated tests use separate temporary databases, not this file.

## 4. Database Schema

Schema version 3. `saved_sites`: id, unique analysis_id, display_name, user location_label, restaurant_concept, search_radius_miles, opportunity_score/classification/model_version, data_coverage/label, analysis_timestamp, created_at, snapshot_version, snapshot_json. Name/radius/score/coverage constraints and created_at/id index. **No latitude/longitude columns.** Factors, evidence, contributions and normalized sections are versioned JSON.

## 5. Schema Initialization

Lazy first saved operation or `python -m flask --app app init-db`. Repeatable and non-destructive. Prototype schema 1 migrates to the coordinate-free schema while retaining records/model outputs; schema 2 removes response attribution metadata. Transactions, secure_delete and VACUUM scrub obsolete data. Unsupported schemas/corrupt migration records fail safely rather than recreating or deleting saved data. Actual starting database was schema 1 and empty; nonempty migration safety is separately tested.

## 6. Repository Architecture

SavedSiteRepository owns insert/upsert/get/list/delete SQL with bound parameters. Core columns must match decoded JSON. List orders newest save first. Duplicate analysis ID returns the same record. Malformed records remain stored but are omitted with an unreadable count; detail returns an explicit unreadable response. Reconstruction preserves records across repository/app instances.

## 7. SavedSiteService

Only a completed resolved analysis can prepare a signed save token. Token expires after two hours and is bound to a canonical hash of every analysis input. Names are trimmed/bounded, normal punctuation and Unicode allowed, control characters/credential-like content rejected. A separately entered user location label is required. Tampered/expired/stale inputs fail without provider calls or persistence. New analyses/scenarios may coexist; repeat submission of one completed analysis is idempotent.

## 8. Snapshot Contents

User identity/location label and concept/radius; actual UTC analysis/save times; exact stored scores/classification/raw sum/model versions; four factor weights/contributions/evidence/provenance/coverage credits; Census estimates/MOEs/GEOID/vintage; VenueBite aggregate competition counts/distances/pressure/model; permitted normalized parcel status/facts/source; supplied occupancy terms/Decimal results/budget/model/evidence; deterministic explanations. No provider payloads, Search Box geography or POI records. Automatically defaulted live property address is not stored as user input.

## 9. Snapshot Versioning

Snapshot format 2, independent of DB schema 3 and Score Model 2.0. Strict whitelists, finite numeric values, type/status/range checks, bounded JSON, unique keys, UTC-aware timestamps and safe URLs. Unknown format fails clearly. Historical scores are never recalculated using current scoring code. Migration changes retention metadata only, not model outputs, timestamps or evidence.

## 10. Saved Sites UX

Premium Sprint 08 shell, count, stacked/responsive cards, names/user locations/concepts/radii, Opportunity Score/classification, Data Coverage, factor/evidence strips, key facts, analysis dates, view/compare/delete actions. Empty states return to Analyze. Compare checkboxes announce 0-4 selection and disable incompatible counts. Find an Area remains hidden; no Coming soon navigation.

## 11. Saved Detail UX

Clearly labeled SAVED SNAPSHOT. Stored score ring and independent coverage segments, exact factors/contributions/source/model detail, demographic/competition/parcel/occupancy facts, timestamps and limitations. Saved map deliberately omitted: coordinates were not retained. Analyze again prefills user inputs but leaves geographic selection empty and analysis disabled until a fresh suggestion is chosen; no automatic provider refresh or overwrite.

## 12. Delete Behavior

Named accessible confirmation page, cancel path, scoped CSRF and explicit POST confirmation. No destructive GET. IDs validated; already-absent deletion succeeds gracefully. Live test record 4 was deleted via POST -> 303; record disappeared. Previously selected deleted record generated a clear comparison recovery message instead of a broken table.

## 13. Compare Selection UX

Native labeled checkboxes on list/picker, GET site_id parameters, submitted order preserved, exactly 2-4 unique records. Client count/max controls plus independent server validation. The saved list's DOM/form order is the submitted order, not click chronology. Two-, three- and four-site matrices were manually opened; invalid/duplicate/missing/one/five selections are tested.

## 14. Comparison Architecture

ComparisonService loads validated saved snapshots only, does not mutate them or call providers/scoring. Produces normalized sections, missing-aware values, warnings, neutral deterministic highlights and subtle badges. Routes contain neither SQL nor comparison formulas.

## 15. Metrics Compared

Score/classification/coverage/model, factors/evidence/weights/contributions, tract population/income/MOEs/GEOID/source/vintage, observed/direct competition counts/nearest distance/pressure/model, parcel availability/identifier/area/building/land use/zoning/source/match/refresh, occupancy size/lease/rent bases/extra charges/monthly costs/budget/utilization/model. Missing values remain unavailable/not supplied/unknown total; zero remains zero.

## 16. Evidence-Aware Comparison

Every factor displays evidence beside its exact score. Partial user rent is never equal to independently verified real-market data or demo rent. Mixed rent states produce an explicit warning. Different concept/radius/model/weights/evidence suppress inappropriate rankings. Greeley's ambiguous Census match stays missing with population/income fallback; its large stored score is not presented as superior verified demographic evidence.

## 17. Deterministic Highlights

Highest stored score requires matching models/weights/context/full evidence vectors. Highest coverage requires matching models/weights, and never means success probability. Strongest competition requires real usable evidence and matching context/model. Lowest known occupancy requires partial known totals, equal numeric size and lease structure, with unverified-terms caveat. Ties retain selection order. No choose/best-site recommendation or AI.

## 18. Provider-Data Retention

Search Box coordinates, IDs, result names/labels/place metadata, POI names/addresses/details/raw payloads and directories are not persisted. No flag permits them and no API was switched. Location labels are explicit user metadata; Census geography metadata originates from Census. Only VenueBite aggregate/model outputs and approved normalized non-Search-Box facts survive. Response attribution text was replaced by an application-owned provenance note and scrubbed from old DB pages. A future saved map requires a permanent-storage-capable source and explicit policy/schema review.

## 19. Provider Calls on Saved Pages

Live final restart used an ignored verification launcher that counts provider method invocations without logging arguments, keys, URLs or bodies. Browsed Saved Sites, details 1/2/3 and three-way Compare. Cumulative counts: location 0, competition 0, Census geography 0, Census data 0, parcel 0. Saved pages load only saved-sites.js, no map SDK/config/search. Automated spy tests independently verify save/list/detail/compare/delete/reanalysis-prefill make no fresh provider calls.

## 20. Security Controls

Parameterized SQL, validated IDs/counts/names, signed expiring input-bound snapshot, new-route CSRF, HttpOnly/SameSite=Lax cookies, no-store saved responses, safe escaped HTTP(S) source links, no pickle, bounded strict JSON and sanitized failures/logging. Database integrity check: OK. Actual database audit: no configured credentials, prohibited coordinate/POI/raw fields or response attribution copies. Tracked/non-ignored source scan found no configured credentials/token patterns. `.env`, database/sidecars and runtime helper/logs are ignored; no environment/database files are tracked. Local app has no user privacy boundary or encryption; keep loopback-only.

## 21. Mobile Behavior

Inspected screenshots and DOM geometry at 1440x1000 desktop, 768x1024 tablet and 390x844 phone. Saved cards stack and wrap, detail score/coverage remains readable, delete actions are usable. Four-site comparison scrolls inside its panel, not the page: phone matrix 1015px inside a 328px panel, document width 375px with viewport 390px (scrollbar). Sticky metric label stayed at x=16 while keyboard scrolling moved the matrix 220px. No broken images on saved detail.

## 22. Accessibility Work

Semantic navigation/current page, native details/forms/table headers/caption, named compare checkboxes, explicit field labels, visible focus and status messages, no color-only evidence, real exact numbers alongside graphics, 44px actions, keyboard save/autocomplete/selection/deletion. Focused comparison matrix explicitly handles left/right keys without stealing child-control/browser shortcut behavior. Instant scroll and existing global reduced-motion CSS retained. Full screen-reader/OS reduced-motion and zoom audit remains useful manual follow-up, not falsely claimed as performed.

## 23. Files Created

Sprint 09 source: `venuebite/db.py`, `venuebite/snapshots.py`, `venuebite/saved_routes.py`, `venuebite/repositories/__init__.py`, `venuebite/repositories/saved_site_repository.py`, `venuebite/services/saved_site_service.py`, `venuebite/services/comparison_service.py`, `static/js/saved-sites.js`.

Templates: `_save_site.html`, `_saved_site_card.html`, `saved_sites.html`, `saved_detail.html`, `saved_delete.html`, `saved_error.html`, `compare.html`.

Tests/docs: `tests/test_saved_sites.py`, `tests/saved-sites.test.mjs`, `docs/saved-sites-comparison-v1.md`, this report. Ignored local verification helper/logs under `.venv/` and development DB under `instance/` are not source changes or commit artifacts.

## 24. Files Modified

Sprint 09 integration: `.env.example`, `.gitignore`, `README.md`, `venuebite/__init__.py`, `venuebite/routes.py`, `templates/base.html`, `templates/_search_form.html`, `templates/results.html`, `static/css/style.css`, `static/js/main.js`, `static/js/form-ui.js`, `tests/test_routes.py`, `tests/test_ui_modernization.py`, `tests/test_competition_routes.py`, `tests/test_geography_routes.py`, `tests/form-ui.test.mjs`, `tests/run-js-tests.mjs`. Existing Sprint 07/08 edits in these and other files were preserved. The broader Git diff also includes untouched preexisting sprint work, not all authored in this continuation.

## 25. Python Tests

Continuation baseline: **932 passed, 3 failed**, 935 total, two cache warnings. Failures were obsolete hidden-Compare assertions, updated only after functionality existed. First integration run also revealed old no-cookie assertions; updated to require CSRF cookie security on resolved live save forms. No regression assertion was simply deleted.

Final full suite: **1,025 passed**, including **90 Sprint 09 tests**. Standard `python -m pytest` invocation passed with an existing cache ACL warning; final repeat with `-o cache_dir=.venv/pytest-cache-sprint09` passed in 14.81 seconds without warnings. An intermediate elevated run could not use the default Windows temp directory (76 setup errors); normal sandbox execution with isolated temporary DBs passed. Python compileall and git diff --check passed. Tests never call live Regrid or write the developer database. Final real-database audit also confirmed every stored score equals its rounded contribution sum and every coverage value equals its coverage-point sum.

## 26. JavaScript Tests

Continuation baseline: parcel 9 and occupancy 16 passed; the existing 12-case form suite failed because its demo-button mock claimed every attribute, including the newly added save attribute. Corrected the mock to report only its actual demo attribute.

Final: **58 passed**: parcel 9, occupancy state 16, form UI 12, saved/compare/keyboard 21. Executed using the available JavaScript runtime with refreshed edited modules; Node CLI is not on this machine's PowerShell PATH. Standard standalone command remains `node tests/run-js-tests.mjs` when Node is installed. No JS failures remain.

## 27. Manual Acceptance

- A: Live Aurora / Indian Restaurant / 3mi saved as Aurora - Indian Restaurant: score **46.1**, coverage **80%**, factors **36.8 / 44.5 / 55 / 53.5**. Census **1,676 / $49,500**, GEOID **08001008100**, ACS 2024; competition **26 observed / 1 direct / 2.62mi nearest direct**. Correct timestamps and card/detail.
- B: Live Greeley / Indian Restaurant / 3mi saved: score **70.2**, coverage **20%**, competition **48.3**, **26 observed / 2 direct / 0.79mi nearest direct**. City point matches multiple Census tracts; estimates unavailable and demographic scores explicitly fallback **85 / 80**, not invented real statistics. Rent demo **55**.
- C: Aurora/Greeley comparison renders exact scores/coverage/factors, real vs fallback evidence, competition differences, demographic missing state, unavailable parcel state and gated highlights. No automatic score winner where evidence differs.
- D: Aurora NNN **2,800SF, $32/SF/year, $8.50/SF/year extra, $10,000 budget** saved: **$7,466.67 base + $1,983.33 extra = $9,450/month**, **94.5%**, rent **66 partial**, **48.3 score / 90% coverage**. Rent contribution **13.20**; non-rent factors unchanged from that live Aurora analysis. Coverage **30+30+10+20=90**, not probability.
- E: Demo-rent vs occupancy-supported snapshot shows **55 Demo vs 66 Partial - user supplied**, explicit unequal-evidence warning, and 80% vs 90% coverage. Score ranking withheld; tied real competition handled.
- F: Additional genuine live Aurora NNN scenario with $10,500 budget saved only to verify four-way comparison/deletion. Four columns render; confirmation, keyboard POST deletion, disappearance and deleted-selection error pass. Remaining original three records preserved. Provider sample outputs can vary between live analyses; scores were not adjusted for appearance.
- G: Flask restart after deletion retains the original three records, timestamps, model versions, scores/evidence and occupancy terms.

Live map/search and competition worked. Aurora Census worked; Greeley ambiguity preserved correctly. Regrid returned no parcel for these representative city points, with conservative coverage/street-point caution, not a claim that parcels do not exist. No unnecessary per-business/provider requests were introduced. Browser console had no warning/error entries during final saved/compare review; final Flask logs contain expected saved requests/statuses and zero-call audit counts, no traceback or credentials.

## 28. Restart Verification

Stopped only verified preview processes launched for this task. Restarted against the same `instance/venuebite.db`, first to apply retention migration and finally after deleting test site 4. List retained records 1/2/3 and each detail reopened. No DB regeneration or provider refresh was needed. Saved data is independent of transient signing/session keys. Final loopback preview: **http://127.0.0.1:5010/**.

## 29. Known Limitations

Local shared records, no accounts/access control/encryption, pagination or backup UI. Historical evidence can become stale; census proxies and capped POI samples remain limited. Greeley city-point Census ambiguity is not repaired by silently moving coordinates. Representative city points returned no Regrid parcel; supported parcel field preservation is covered offline. No saved coordinates/maps or POI details. Permanent-storage/provider-rights review is still required before broader commercial deployment. Existing model heuristic limitations remain unchanged. Source terms and budgets are unverified partial evidence.

## 30. PostgreSQL / Authentication Path

Preserve service/repository contracts and versioned historical snapshots. Replace SQLite connection/upsert/migration mechanics for PostgreSQL later. Add explicit ownership migration, authorize every saved read/write/delete/compare and handle existing local records deliberately. No fake owner IDs, accounts, Docker, AI or PostgreSQL were added. Review production CSRF/session policy, TLS, encryption/backups, logging, rate limits and permitted geography retention first.

## 31. Git Status

Branch **1234tlc123-probable-succotash**, unchanged HEAD **f01f256**. Final short status: **24 modified tracked files, 40 untracked entries, 0 staged** (directory entries may contain multiple files). Dirty tracked/untracked Sprint 07-09 work remains intentionally available for Chris's review. Nothing committed, pushed, reset or discarded. `.env` and SQLite files are absent from tracked paths; targeted database/sidecar ignores confirmed. Diff check clean; line-ending normalization warnings are Git's existing Windows configuration, not code failures. Changed-file categories are described in sections 23/24.

## 32. Chris's Manual Follow-Up

Open the local preview's Saved Sites and compare the three retained examples. Review the stored snapshot location policy: names/location labels are user input, saved maps intentionally unavailable, Analyze again requires a fresh suggestion. For Greeley Census, select a specific address/landmark rather than expecting a unique tract at the city point. Regrid detail verification needs an address inside the token's documented coverage; do not spend records on repeated city-point retries. Set a stable private SECRET_KEY for in-progress form continuity, protect the SQLite file, and review the whole dirty worktree before your own commit. For CLI JS tests, make Node available and run the documented runner. Full screen-reader, 200% zoom and OS reduced-motion review are sensible additional checks. No new provider credentials or APIs are required for Sprint 09.
