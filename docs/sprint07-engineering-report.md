# Sprint 07 Engineering Report

Branch `1234tlc123-probable-succotash`, October 2, 2026. Implementation and offline acceptance verification are complete. Fresh live Mapbox/Map/Satellite integration verification remains blocked by the configured token's HTTP 401 response. No credential, commit, push, branch or index change was made.

## 1. Implementation

Optional user-supplied commercial property terms now produce deterministic USD base rent, supplied additional charges, occupancy estimates, personal-budget fit, source provenance and lease-cost cautions. Supported rent replaces only the existing rent factor. Incomplete terms or missing budget keep the demo fallback. Existing Flask/Jinja architecture and the four-factor model remain authoritative; no new API, scraper, database, authentication or AI was introduced.

## 2. Files Created

- `venuebite/occupancy.py`
- `venuebite/services/occupancy_service.py`
- `templates/_occupancy_form.html`
- `templates/_occupancy.html`
- `tests/test_occupancy.py`
- `tests/test_occupancy_integration.py`
- `tests/occupancy-state.test.mjs`
- `docs/commercial-occupancy-v1.md`
- `docs/sprint07-engineering-report.md`

The pre-existing untracked `prompts/07-commercial-occupancy.md` belongs to Chris and was read but not changed.

## 3. Files Modified

`README.md`, `docs/scoring-model-v2.md`, `static/css/style.css`, `static/js/analysis-state.js`, `templates/_search_form.html`, `templates/_site_intelligence.html`, `templates/base.html`, `templates/results.html`, `tests/test_site_intelligence.py`, `venuebite/__init__.py`, `venuebite/routes.py`, `venuebite/services/analysis_service.py`, `venuebite/services/explanation_service.py`, and `venuebite/services/site_intelligence_service.py`.

The existing parcel test retains all its cases and now asserts the correct parcel-only caution instead of assuming commercial occupancy is always demo. Existing scoring/coverage calculators, weights, provider adapters, credentials, dependency manifests and map rendering modules were not modified.

## 4. Input Architecture

Frozen `CandidateProperty` and `OccupancyRate` contracts hold normalized terms. `normalize_candidate_input` validates all fields and returns immutable bounded values/errors. `OccupancyService` creates structured costs, completeness, budget fit, candidate facts, cautions and summary. `AnalysisService` integrates supported rent before the existing score/coverage/explanation/trace functions, then assembles Regrid site intelligence independently afterward. Routes only validate/orchestrate/render; formulas never live in Jinja or JavaScript.

The optional form is collapsed by default and open when supplied terms/errors need review. On expansion its existing Analyze command moves after the fields. The selected coordinates remain authoritative; a different contextual property address warns rather than moving/geocoding the site. URLs are provenance metadata only. No inputs persist across a new request or browser storage.

## 5. Rent Bases

Base and additional charges independently support USD per SF per year, USD per SF per month, total monthly USD, and total annual USD. Enum IDs are `per_sqft_per_year`, `per_sqft_per_month`, `total_monthly`, `total_annual`. Missing size prevents per-SF calculation; flat totals can still be calculated, but without size they cannot activate rent scoring. Money is explicitly USD for all countries, with no conversion.

## 6. Lease Structures

NNN, Gross, Modified Gross and Unknown/Not stated are recorded. NNN cautions explain possible excluded pass-throughs; Gross inclusions vary; Modified Gross responsibility depends on the lease; Unknown assumes nothing. A lease label never supplies missing costs, determines legal use or establishes availability.

## 7. Formulas

```text
SF/year: annual = size * rate; monthly = annual / 12
SF/month: monthly = size * rate; annual = monthly * 12
monthly total: annual = monthly * 12
annual total: monthly = annual / 12
supplied monthly/annual occupancy = corresponding base + additional cost
budget ratio = supplied monthly occupancy / monthly occupancy budget
```

Decimal arithmetic retains precision; money is displayed at cents using half-up rounding. Inputs allow correctly grouped numbers, optional monetary dollar signs and up to six decimal places; display values do not feed calculation/scoring.

## 8. Completeness

Candidate states: not provided, partial, complete; invalid exists in normalization and yields HTTP 400, never a successful scored report. Cost states: `unknown_expenses`, `base_only`, `base_plus_additional`.

All lease structures conservatively require explicit calculable additional charges to show a combined estimate or activate scoring. Missing NNN/CAM, including for Gross, means base rent only. An explicit zero is accepted as a user assertion, not independent verification of no further costs. Complete means complete supplied components, not all-in lease underwriting. Unsupplied utilities, tax/insurance beyond quoted charges, buildout, deposits, fees, concessions, percentage rent and future escalations are never invented.

## 9. Model Formula

Commercial Occupancy Model v1 measures personal-budget fit only. For `r = monthly supplied occupancy / monthly stated budget`, score anchors are:

```text
70% -> 100; 85% -> 85; 100% -> 55; 115% -> 25; 150% -> 0
between anchors: s = sa + (r-a)/(b-a) * (sb-sa)
at/below 70%: 100; at/above 150%: 0
```

The model rounds to one decimal, stays 0-100, and is monotonic/continuous at the anchors before display rounding. Band labels distinguish well within, within, near, above and materially above the stated budget. Anchors are centralized and documented, not tuned to make opportunity scores look better. They are unvalidated product assumptions and cannot judge whether the budget itself is realistic.

## 10. Activation

Usable positive size, calculable nonnegative asking rent, explicit calculable nonnegative additional charges, and a positive monthly occupancy budget are all required. Otherwise rent stays the established demo 55/100. Costs remain visible when calculable even with no budget. Source label, URL, asking rate alone, assessed values and building area never activate rent.

Malformed/nonfinite/negative amounts, zero size/budget, invalid enums/URLs, duplicates, excessive lengths and control characters produce field-specific errors before external requests. Numeric caps are 10 million SF and $100 million per monetary field, solely for calculation safety; they are not price judgments.

## 11. Provenance

Active rent is `partial`, provider `user_supplied`, label `PARTIAL EVIDENCE`, model `commercial-occupancy-v1`; the source label and budget-relative description are retained. It is never REAL VERIFIED MARKET DATA. No-input provenance remains unchanged; insufficient supplied terms retain demo provenance with a reason. URL/source text cannot upgrade the status.

The original expected-source field in the internal trace remains the default demo expectation for compatibility; actual source/status/model fields identify supported rent. The mock asking-rent area metric is omitted when supplied base rent is calculated, preventing simultaneous fictional and candidate-cost presentation; demo metrics otherwise remain clearly labeled.

## 12. Data Coverage

Coverage remains independent of Opportunity Score:

```text
normal: 30 population + 30 income + 20 competition + 0 demo rent = 80%
supported user rent: 30 + 30 + 20 + (20 * .5) = 90%
failed Census + supported rent + competition = 30%
failed competition + supported rent + Census = 70%
both failures + supported rent = 10%
one usable Census factor + competition + supported rent = 60%
```

User evidence contributes 10 points, never 20 or 100% total. Evidence support is not success probability, accuracy, demand or scientific confidence. Missing Census estimates and genuine zero estimates retain their existing independent semantics. Regrid contributes no coverage weight.

## 13. Score Model v2 Regression

The overall model remains `2.0`, weights population/income/rent/competition 30/30/20/20. Full-precision contributions sum, then the overall score rounds once to one decimal. No classification, overall formula, factor direction or coverage-credit change was made.

Manual fixture math without terms: `18.51 + 21.66 + 11.00 + 16.00 = 67.17 -> 67.2`. With the complete NNN example, rent 66 contributes 13.20: `18.51 + 21.66 + 13.20 + 16.00 = 69.37 -> 69.4`. The only contribution change is +2.20 rent points; coverage separately changes 80 to 90.

## 14. Other Factors and Parcel Regression

Population Model v1, Income Model v1 and Competition Model v1 files are unchanged. Controlled service/browser comparisons keep population 61.7, income 72.2, competition 80 and their contributions identical, including Census GEOID, POI snapshot and parcel payload. Provider failures, missing estimates and zero estimates retain their original factor behavior. Parcel intelligence remains outside all score/coverage inputs; assessor values and building sizes cannot fill missing lease terms. All earlier test cases remain present and passing.

## 15. Explanations

Summaries and risks use structured costs, budget ratio and provenance. Within-budget terms are described as within the user's stated budget; above-budget terms are a budget risk, not a bad lease. Partial rent always carries an independent-verification caution and cannot become a fully real global strength, preserving Sprint 05 semantics. Base-only estimates, missing budget, unknown inclusions and excluded costs receive explicit cautions. No market-price comparison, revenue/profit forecast or sign/invest recommendation is generated.

## 16. Tests and Startup

Baseline: **732 passed**. Final complete Python suite: **919 passed**, adding **187** occupancy cases, via `python -m pytest` (about 8.5 seconds in this workspace's Python 3.14.6 environment). Tests cover eight rate-normalization paths, Decimal math, all lease structures, explicit zero versus missing charges, numeric/text/enum/URL validation, monotonic anchors/bounds, provenance, coverage failures, unchanged factor contributions, escaping, request isolation, fixture integrations, explicit demo-geography fallback and all form-field invalidation bindings. No test calls live providers.

Two JavaScript harnesses passed **25 lifecycle checks**: nine parcel/style/invalidated-snapshot checks and 16 occupancy/input/location/back-forward checks. The latter exercises both input and change events for every optional field. Python compile checks and `git diff --check` pass. `python app.py` started with debugging off and was stopped after the smoke check. A separate final preview is available at `http://127.0.0.1:5006`; pre-existing servers were not stopped.

## 17. Manual Acceptance

All A-F browser scenarios were performed on a temporary, visibly labeled **synthetic verification-fixture session**, not represented as live-world findings. The temporary fixture server was stopped after verification.

- A, no occupancy: rent demo 55, coverage 80%, overall 67.2, no occupancy panel.
- B, 2,800 SF at $32/SF/year, NNN, $8.50/SF/year charges, $10,000 budget: annual base $89,600; monthly base $7,466.67; annual additional $23,800; monthly additional $1,983.33; annual supplied occupancy $113,400; monthly $9,450; ratio 94.5%; rent 66, partial, contribution 13.20; coverage 90%; overall 69.4.
- C, same but no charges: base $7,466.67/month; additional not supplied; no total claimed; missing-cost warning; rent demo 55; coverage 80%; overall 67.2.
- D, complete costs but no budget: $9,450/month displayed; budget not supplied; rent demo 55; coverage 80%; overall 67.2.
- E, $8,000 budget: ratio 118.1%; rent 22.8, contribution 4.56; coverage remains 90%; overall `18.51 + 21.66 + 4.56 + 16.00 = 60.73 -> 60.7`; risk says exceeds stated budget, no bad-lease language.
- F, negative size and NaN rent: HTTP 400, both field-specific messages, expanded correction form, retained signed selection, no old score/occupancy report and no Flask 500.

Browser checks also covered whole-report invalidation after field edits, source/notes disclosure, safe external link attributes, unchanged Census/POI/parcel payloads and the final form submission. Screenshots/DOM geometry at 1366x900 and 390x844 showed no horizontal page overflow, overflowing occupancy labels or broken local image assets. Expanded Analyze is after terms on both sizes; the default search stays uncluttered. The fixture session's browser warning/error log was empty.

**Fresh live limitation:** configured Mapbox geography returned upstream HTTP 401 on the new preview. Older servers on ports 5000 and 5005 also failed suggestions using the same public token as `.env`, demonstrating the failure was not introduced by Sprint 07. No credential was printed or changed. Consequently fresh real Mapbox selection, rendered Map/Satellite imagery, real competitor markers and live parcel/Census-on-selected-point verification could not be completed. Their provider contracts, template payloads and lifecycle regressions passed offline, but those checks are not a substitute for fresh live rendering. No Regrid live request or paid parcel record was consumed in this sprint.

The actual final application, without injected providers, also completed an explicit demo-geography fallback with the B terms. Rent remained partial 66, other factors were visibly demo, occupancy stayed $9,450/month, overall was 74.7 and coverage correctly only 10%, not 90%. Fictional competitors stayed labeled and parcel data was unavailable. This verified graceful geographic failure without presenting synthetic data as a live finding.

## 18. Limitations

User terms and budget are unverified, the model is uncalibrated, and estimates omit unsupplied expenses. Gross inclusions cannot be assumed. The address comparison is conservative text matching, not unit/address verification. USD-only input is not currency conversion. No local rent benchmark, profitability forecast, zoning determination, availability feed, persistence or advanced lease underwriting exists. Existing Mapbox sampling, Census uncertainty and Regrid entitlement/refresh limitations remain. Fresh live rendering awaits working Mapbox authorization.

## 19. Git and Security

HEAD remains `f01f256` (`Complete VenueBite Sprint 06 Site Intelligence`) on the original branch. Final status consists of **14 modified tracked files**, **9 new implementation/test/documentation files**, and the **pre-existing untracked sprint prompt**. All are unstaged; no commit or push was performed. Diff review found no scoring-weight/model/provider/map-rendering or unrelated changes.

`.env` and preview logs remain ignored; only `.env.example` is tracked. Configured Mapbox/Census/Regrid/signing credentials were scanned through stdin against tracked and untracked non-ignored files: no matches. Private keys were absent from rendered home/config responses. The preview log contained no configured credential or traceback; its sanitized authorization diagnostic was `endpoint=suggest status=401`. New occupancy terms are not logged; source URLs are not fetched. Jinja escaping, no-store responses and the existing CSP remain in force.

## 20. Chris's Manual Follow-Up

No new dependencies, API keys, database migrations or setup are required for occupancy. Restart an older server or use the port-5006 preview for the new modules/templates. Correct Mapbox authorization privately in the ignored `.env`/server environment, ensuring a valid public token and any required origin restrictions; never paste credentials into chat or source control. Restart the server afterward, then repeat A-F at one supported live address and verify Map/Satellite, actual competitor markers, Census provenance and Regrid boundary/facts. Keep paid Regrid repeats small and confirm token coverage/record balance in the account dashboard.

Before using real candidate terms, verify the exact unit/address, rentable area, full pass-through/inclusion schedule and realistic budget with the source. Review the conservative completeness and budget anchors as product assumptions. The next focused work is completeness/anchor review using legitimate supplied lease packages and restored live-provider verification, not an unrequested provider, persistence or forecasting phase.
