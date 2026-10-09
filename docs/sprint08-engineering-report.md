# Sprint 08 Engineering Report

Completed verification: October 6, 2026. Architecture: Flask, Jinja, native CSS and JavaScript. No frontend framework, provider, dependency, database, authentication feature, or backend model was added.

`AGENTS.md` and `prompts/08-futuristic-ui-modernization.md` were read completely before changes. Repository, branch, status, Sprint 01-07 architecture, existing tests, and desktop/mobile presentation were inspected first. The pre-existing uncommitted Sprint 07 implementation was preserved.

## 1. Overall Visual Redesign

VenueBite is now an application-first intelligence workspace with a restrained futuristic identity: charcoal surfaces, cyan geography/commands, green real evidence, amber review/demo states, coral challenging classifications, and violet partial occupancy evidence. System typography, tabular metrics, compact headings, 6px corners, and unframed sections replace the previous dense presentation. The map is the primary functional visual asset; this is not a marketing landing page.

Decision metrics appear immediately. Detailed sources, assumptions and methodology use native progressive disclosure without removing the underlying information or upgrading evidence claims.

## 2. Navigation Changes

Primary navigation exposes only the working Analyze workflow. Compare, Saved Locations, Find an Area, and repeated Coming soon labels are absent. No dead replacement links were added. A report-section navigation links to actual Overview, Factors, Market context, Site and Occupancy headings; Site is omitted when there is no site section.

## 3. Application Shell

A compact sticky header gives VenueBite a clear first-viewport identity and retains a single functioning application command. The workspace has responsive gutters and a 1480px content constraint. The footer is concise and retains the non-guarantee/evidence caution. The shell, form, dashboard and disclosures share common color, spacing, border and focus tokens.

## 4. Background and Motion

`static/images/geospatial-field.svg` is a locally authored abstract contour/grid field, not a fabricated map. A single pointer-inert, aria-hidden CSS scan plane animates transform/opacity on a slow 32-second cycle. No remote video, canvas particle loop, animation dependency, gradient orb, or extra API is involved.

Reduced-motion CSS disables animation, transitions, smooth scrolling and hover translation. Metrics do not depend on animated counters. Existing Mapbox reduced-motion behavior is preserved.

## 5. Search Experience

Location receives the dominant form track, with concept, radius and Analyze nearby. Existing autocomplete, signed selection, clear-location control, validation, explicit demo fallback and submission semantics remain intact.

Optional commercial terms use a native disclosure and five labeled fieldsets: Space, Lease, Additional costs, Business threshold and Source. All 11 occupancy input names and invalidation hooks remain intact. The submit button stays in a predictable location when the disclosure opens. Invalid server responses expand the terms and focus the first invalid field.

Submitting shows a disabled busy button and truthful status text, without invented progress percentages. Duplicate submissions are blocked. Page restoration clears loading state while respecting the existing resolved-geography gate.

## 6. Results Workspace

The report has a location/concept/radius heading, source mode, section anchors, paired score/map overview, factors, weighted contributions, decision signals, market context and property context. Fresh results focus their report heading and arrive below the sticky header without animation. Back-forward restoration does not re-focus a stale report.

Existing analysis invalidation still hides all outputs and clears Census identity, competition payload/markers and parcel evidence when inputs change. Editing occupancy terms invalidates the entire report, not only the rent visualization.

## 7. Opportunity Score Visualization

The original numeric score, classification, Score Model v2 label and non-prediction warning remain visible. An aria-hidden SVG circle uses the same server score on a 100-unit path; its color follows the existing classification. It does not recalculate scores or change thresholds.

Live Aurora without commercial terms remained 46.1/100. With the specified NNN terms it was 48.3/100. No values or weights were changed to improve appearance.

## 8. Data Coverage Visualization

Data Coverage is a separate metric with its own percentage, original label and visible "not success probability" caution. Four segments retain the 30/30/20/20 model weights and existing evidence credits: real 1, partial 0.5, other 0. Partial segments also use stripes. The original accessible native meter retains the exact coverage value.

Live Aurora coverage was 80% with demo rent and 90% with qualifying user-supplied occupancy terms. Partial rent adds 10 coverage points, not 20, and does not halve the rent score. Regrid remains outside both score and coverage.

## 9. Factor Intelligence

Each factor exposes its original score, weight, source/evidence label, meter and weighted contribution. Source/model details retain the existing explanations and provenance. `data-factor-evidence` reflects the actual source status and supports semantic regression tests. Color is supplemented by explicit labels.

## 10. Contribution Visualization

The separate contribution chart compares actual weighted points on one common 0-30 point scale, not raw scores or independent normalized bars. Values remain available as text. Aurora's baseline contributions were population 11.04, income 13.35, rent 11.00 and competition 10.70 points. The occupancy scenario replaced only the rent contribution with 13.20 points.

## 11. Map UI

The map has a substantial framed workspace: 500px desktop, 480px smaller laptop/tablet, 370px narrow layouts and 340px phone. Standard/satellite segmented controls, recentering, parcel focus, location summary, legend and status overlays share the new shell styling. Attribution remains present.

Mapbox configuration, token loading, SDK, requests, marker/pop-up logic, style switching and parcel layers were not rewritten. Live standard and satellite maps rendered, with one candidate and 26 restaurant markers retained across style switches. No private provider credential was added to the browser.

## 12. Demographic UI

Population and income have larger primary metrics with original evidence labels. Growth and school/demo limitations remain distinguishable. The tract-proxy and ACS survey interpretation caution stays visible. Census geography, GEOID, vintage, boundary, source and margins of error are available in native source details.

Live Aurora used GEOID 08001008100, Tract 81, Adams County, Colorado: population 1,676 (MOE +/-148), median household income $49,500 (MOE +/-$22,322), ACS 2024 five-year estimates covering 2020-2024, with ACS2024_Current geography. These are tract estimates, not trade-area demand or a current headcount.

## 13. Competition UI

The summary emphasizes score, observed restaurants, direct matches and radius, with nearest-distance facts nearby. A presentation pressure index uses `100 - competition score`; it is explicitly distinct from the original raw pressure-points quantity retained in the model disclosure.

Direct matches are open by default; the general restaurant environment is expandable. Tables retain names, addresses, match basis and distances, use sticky headers and bounded internal scrolling, and wrap on mobile. Limited-sample/provider-cap caveats and Mapbox attribution remain visible.

Live Aurora returned 26 restaurants, including one direct match, Taz Indian Restaurant at 2.62 mi. The nearest observed restaurant was 0.03 mi away; the unchanged competition score was 53.5. This remains a limited sample, not a complete restaurant census.

## 14. Site Intelligence UI

Site intelligence has a calm no-parcel state and preserves the original lookup explanation. Available facts and zoning caution are primary; match quality, source and additional considerations use disclosures. Always-visible text states that parcels are separate from scoring, assessments are not verified market values or asking rent, sales are historical, and missing fields are unknown rather than negative facts.

The live Aurora point returned no matching parcel. The UI correctly explained that the point may be in a street or outside token coverage and did not establish parcel nonexistence. Available parcel facts and source disclosures were inspected with existing synthetic provider fixtures, not represented as live Regrid results. No extra live Regrid requests were made just to populate the redesign.

## 15. Commercial Occupancy UI

Known monthly occupancy and the user's monthly budget receive an unframed headline strip. Detailed facts preserve space, lease structure, rates/bases, base costs, additional charges, total, budget and factor integration. User-supplied/unverified status and supplied-cost-only limitation stay visible; assumptions, verification items and source notes are expandable.

The gauge uses a 0-150% visual scale with a marked 100% budget line. Its fill is capped for layout stability, but true utilization is always shown in text and `aria-valuetext`, including extreme overruns. Missing sufficient terms or budget retains demo rent and the original fallback reason. Raw asking rent does not become a nationwide affordability score.

Live 2,800 SF NNN at $32/SF/year plus $8.50/SF/year, with a $10,000 monthly budget:

- Base: $7,466.67/month; $89,600/year.
- Additional: $1,983.33/month; $23,800/year.
- Known occupancy: $9,450/month; $113,400/year.
- Utilization: 94.5%; rent factor 66/100, PARTIAL; contribution 13.20 points.
- Opportunity Score 48.3; Data Coverage 90%.

Budget fit remains relative to a user threshold, not verified market rent, revenue, fair value or profitability.

## 16. Strengths and Risks

The existing structured explanations drive a separate decision-signals section. Strengths and risks/review items are visually distinct, with factor scores and readable explanations. Partial rent remains a verify-data review item. No generic promotional claims, new AI text, or invented location facts were introduced.

## 17. Responsive and Mobile Work

Desktop, smaller laptop, tablet and phone were visually inspected at 1440x960, 1280x900, 768x1024 and 390x844. DOM overflow checks returned no page-wide horizontal overflow. Layout tracks adapt independently; the phone order is score/coverage, map, factors, review, market and property context. Long addresses wrap and tables remain inside their sections.

The optional lease form becomes single-column on phones. Budget figures and extreme utilization values remain within their containers. The four factors become a two-column layout, with stable meter/ring/map dimensions rather than viewport-scaled fonts.

## 18. Accessibility Work

Semantic landmarks, labels, fieldsets/legends, tables and native disclosures remain server-rendered. The skip link, keyboard focus, status regions, busy state, input errors and report arrival are supported. Input wrappers supply one visible focus indicator instead of doubled outlines. Existing local Lucide icons and accessible names/title tooltips are reused.

Numeric text and native meter/progress semantics supplement decorative graphics; evidence is never conveyed by color alone. Keyboard autocomplete selection, disclosure toggles, map-mode selection and invalid-field recovery were manually checked. Reduced-motion rules were inspected, but an OS-level reduced-motion emulation, full screen-reader audit and formal WCAG certification were not performed.

## 19. Performance Work

No new dependencies or heavy chart/media/font assets were added. The local background SVG is 1,049 bytes, form UI module 2,335 bytes, and unminified stylesheet 37,021 bytes. Only one decorative plane continuously animates transform/opacity; backdrop blur is restricted to the header. Native disclosures need no extra script. UI loading/focus responsibilities are separate from Mapbox/provider code.

These are implementation/asset-size checks, not a production Lighthouse or GPU performance benchmark. Existing Mapbox network/SDK costs remain unchanged.

## 20. Files Created

- `static/images/geospatial-field.svg`
- `static/js/form-ui.js`
- `templates/_score_overview.html`
- `templates/_factor_intelligence.html`
- `templates/_strengths_risks.html`
- `tests/form-ui.test.mjs`
- `tests/run-js-tests.mjs`
- `tests/test_ui_modernization.py`
- `docs/sprint08-ui-system.md`
- `docs/sprint08-engineering-report.md`

Preview/fixture helpers and sanitized-check logs are temporary and ignored under `.venv/`; they are not application features or tracked deliverables.

## 21. Files Modified

Sprint 08 modified `README.md`, `static/css/style.css`, `static/js/main.js`, `templates/base.html`, `templates/index.html`, `templates/results.html`, `templates/_competition.html`, `templates/_demographics.html`, `templates/_site_intelligence.html`, `tests/test_routes.py`, `tests/test_competition_routes.py`, and `tests/test_demographic_integration.py`.

It also modernized the pre-existing untracked Sprint 07 `templates/_occupancy.html` and `templates/_occupancy_form.html`. The existing test changes update intentional navigation/presentation assertions to semantic checks rather than deleting coverage.

The backend, scoring, provider, dependency and `analysis-state.js` changes visible against HEAD were already present from Sprint 07. Sprint 08 did not rewrite those modules. Existing Sprint 07 documents, tests, providers and prompt files were not discarded. `templates/_map_workspace.html` was inspected and retained unchanged.

## 22. Python Tests

Baseline: 919 passed. Final: **935 passed in 10.72s**, using `.venv\Scripts\python.exe -m pytest`, with Python 3.14.6 and pytest 9.1.1. No tests failed or were hidden. The 16 new cases cover semantic UI/navigation, empty state, form grouping, original score/coverage/contributions, evidence, optional validation, gauges, failure presentation and stale-output guards. Existing Sprint 01-07 tests remain in the full suite. Automated tests use injected fixtures, not live provider calls.

Python compilation and `git diff --check` also passed. Git reports normal Windows LF-to-CRLF advisory warnings, not whitespace errors.

## 23. JavaScript Tests

Baseline: 25 passed. Final: **37 passed**: 9 parcel-layer tests, 16 occupancy/state invalidation tests and 12 form/loading/report-arrival tests. Every suite was executed in the provided Node JavaScript runtime. There is no terminal `node` executable on this machine; the same exports are runnable with `node tests/run-js-tests.mjs` when Node is installed.

The new cases exercise truthful loading, duplicate-submit prevention, page restoration, unresolved selection, demo behavior, validation focus and fresh versus persisted report arrival. Existing map/state cases remain intact.

## 24. Manual Browser Verification

Scenario A, no analysis: inspected clean navigation, search controls, local background, neutral pending evidence, no fabricated score or coverage, and Mapbox workspace. Unfinished navigation is absent.

Scenario B, standard analysis: live Aurora, Colorado, Indian Restaurant, 3 mi at 39.74033/-104.83067. Standard and satellite map imagery rendered; the candidate and 26 competition markers survived style switching. Census, score/classification, coverage, factors, weighted contributions, demographics, competition and structured review signals were inspected. The unchanged calculation was `36.8 * .30 + 44.5 * .30 + 55 * .20 + 53.5 * .20 = 46.09`, displayed as 46.1. Real population/income/competition support 80% coverage.

Scenario C, occupancy: submitted the exact live NNN scenario above. Non-rent factors, geography, Census tract and POIs remained unchanged. `11.04 + 13.35 + 13.20 + 10.70 = 48.29`, displayed as 48.3; coverage became 90%. The partial evidence, cost/budget facts and 94.5% gauge were inspected. Missing additional NNN costs, missing budget, and extreme 945% utilization were also checked using clearly labeled offline fixtures; fallback rent and gauge behavior were correct.

Scenario D, no parcel: live Aurora returned `not_found`; the explanation stayed neutral, no boundary/facts were fabricated, and nonexistence was not claimed. Available parcel facts, zoning cautions and source disclosures were reviewed through existing offline parcel fixtures. The final always-visible assessment/model caution was confirmed outside disclosures.

Scenario E, partial provider failure: offline Census failure left competition usable with 20% coverage and demographic fallback; offline competition failure left Census usable with 60% coverage and no live competitor rows. Error states did not fabricate real evidence. No provider outage was induced against live services.

Scenario F, mobile: all main sections and controls were visually reviewed across the four viewport sizes. The real direct-competitor table wrapped its address within the phone width, and the general table disclosure toggled with Enter. Expanded lease groups and final cost/budget layout were inspected with fixtures. No page-wide horizontal overflow was observed.

Additional checks: keyboard autocomplete with ArrowDown/Enter; native evidence/source disclosures; keyboard satellite control; input edits clearing reports, Census GEOID and map overlays; invalid monthly budget returning HTTP 400 with the disclosure open, invalid input focused, no stale report, and submit state reset. Final live and validation browser warning/error logs were empty. Sanitized Flask logs showed successful requests and no traceback; no credential values were printed.

## 25. Known Limitations

- Live Aurora did not return a parcel. A supported live parcel boundary was not claimed or repeatedly requested; existing parcel automation and fixture presentation were verified instead.
- Census can transiently fail; an earlier unavailable response recovered on the successful live analysis. Existing fallbacks and limitations remain unchanged.
- Mapbox POIs remain capped/partial observations; Census is a tract proxy; listing terms are unverified; demo factors remain explicitly labeled.
- Native disclosures reduce visible density but do not replace a complete screen-reader, cross-browser, contrast or production performance audit. Reduced-motion CSS was checked without an OS-level media setting change.
- No terminal Node installation was added. JavaScript suites passed in the available Node runtime.
- The final live report establishes the data/math and provider behavior; final presentation-only refinements were additionally checked with offline fixtures to avoid unnecessary paid parcel usage.

## 26. Git Status and Security

Branch is unchanged: `1234tlc123-probable-succotash`. HEAD is unchanged: `f01f256 Complete VenueBite Sprint 06 Site Intelligence`. Nothing was staged, committed or pushed; `git diff --cached --stat` is empty. Diff scope was reviewed and `git diff --check` passed. The status below includes preserved Sprint 07 work as well as Sprint 08, not solely this sprint's changes.

```text
## 1234tlc123-probable-succotash...origin/1234tlc123-probable-succotash
 M README.md
 M docs/scoring-model-v2.md
 M static/css/style.css
 M static/js/analysis-state.js
 M static/js/main.js
 M templates/_competition.html
 M templates/_demographics.html
 M templates/_search_form.html
 M templates/_site_intelligence.html
 M templates/base.html
 M templates/index.html
 M templates/results.html
 M tests/test_competition_routes.py
 M tests/test_demographic_integration.py
 M tests/test_routes.py
 M tests/test_site_intelligence.py
 M venuebite/__init__.py
 M venuebite/routes.py
 M venuebite/services/analysis_service.py
 M venuebite/services/explanation_service.py
 M venuebite/services/site_intelligence_service.py
?? docs/commercial-occupancy-v1.md
?? docs/sprint07-engineering-report.md
?? docs/sprint08-engineering-report.md
?? docs/sprint08-ui-system.md
?? prompts/07-commercial-occupancy.md
?? prompts/08-futuristic-ui-modernization.md
?? static/images/
?? static/js/form-ui.js
?? templates/_factor_intelligence.html
?? templates/_occupancy.html
?? templates/_occupancy_form.html
?? templates/_score_overview.html
?? templates/_strengths_risks.html
?? tests/form-ui.test.mjs
?? tests/occupancy-state.test.mjs
?? tests/run-js-tests.mjs
?? tests/test_occupancy.py
?? tests/test_occupancy_integration.py
?? tests/test_ui_modernization.py
?? venuebite/occupancy.py
?? venuebite/services/occupancy_service.py
```

`.env` and `.venv` remain ignored. The only tracked `.env`-named file is the placeholder `.env.example`. An exact-value credential scan of tracked and untracked nonignored files found no configured secret values. Private Census/Regrid credentials were absent from rendered HTML and browser map configuration. Configured credentials were absent from preview/fixture logs. The existing Mapbox public client configuration remains necessary and unchanged; its token value was not printed in snapshots or this report.

## 27. Chris's Manual Review

Preview: `http://127.0.0.1:5008`. No new dependencies, configuration, migrations or provider credentials are required for Sprint 08. Restart any previously running application server to ensure cached Jinja templates are refreshed. The isolated fixture server is stopped after verification; the normal preview remains available.

Review the overall design preference, density, phone behavior and expandable source information. Repeat the Aurora/NNN scenario with your own browser as desired; the expected values for the observed dataset are 46.1/80% without terms and 48.3/90% with the stated terms, subject to live-provider data changes.

For final release QA, inspect an actual covered exact-address parcel when one is available, native reduced-motion behavior on your device, a screen reader, and Firefox/Safari as well as Chrome. Installing Node is optional for direct terminal JS-test execution, not required to run VenueBite. The next logical work is focused user/accessibility/cross-browser QA and release review, not adding unfinished navigation or changing scoring weights.
