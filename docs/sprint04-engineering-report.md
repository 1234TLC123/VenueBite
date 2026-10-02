# Sprint 04 Engineering Report

Verification date: October 2, 2026. Branch: `1234tlc123-probable-succotash`.

## 1. Implementation

Added official tract-level Census population and median household income, independent deterministic context scores, source/vintage/GEOID/MOE presentation, partial/unavailable handling, and structured factor/metric provenance. Preserved Flask/Jinja, signed Mapbox selections, autocomplete, maps/satellite, live competition, and the original four-factor weights. No dependency, database, persistence, AI, or frontend-framework changes.

## 2. Files Created

- `venuebite/providers/demographic_provider.py`: normalized geography/demographic contracts and verified constants.
- `venuebite/providers/census_provider.py`: bounded Census geography and ACS adapters.
- `venuebite/services/demographic_service.py`: coverage, orchestration, scoring inputs, sanitized fallback.
- `venuebite/demographic_scoring.py`: Population and Income Models v1.
- `templates/_demographics.html`: Census context, geography, source, vintage, uncertainty.
- `tests/test_census_provider.py`: transport, geography, response parsing, sentinels, annotations, MOEs.
- `tests/test_demographic_scoring.py`: anchors, interpolation, monotonicity, bounds, invalid/missing input.
- `tests/test_demographic_integration.py`: report/route provenance, partial/failure paths, non-U.S. coverage, signed-coordinate reuse, stale clearing, escaping.
- `docs/sprint04-engineering-report.md`: this report.

The untracked `prompts/04-demographic-intelligence.md` already existed and was not modified.

## 3. Files Modified

- `.env.example`, `README.md`: placeholder configuration and current architecture/methodology/setup/limitations.
- `venuebite/__init__.py`, `venuebite/routes.py`: injected Census providers/service; testing ignores developer credentials.
- `venuebite/providers/location_provider.py`, `venuebite/providers/mapbox_provider.py`: optional normalized country metadata, included in signed selections; legacy selections remain compatible.
- `venuebite/services/__init__.py`, `venuebite/services/mock_data_service.py`: metric status and stable keys; original demo values remain unchanged.
- `venuebite/services/analysis_service.py`: independent real/demo/fallback factors, Census metrics, report provenance.
- `venuebite/scoring.py`: stable insight keys only; formulas, weights, thresholds unchanged.
- `templates/results.html`, `templates/base.html`: correct hybrid/source labels and Census report rendering.
- `static/css/style.css`, `static/js/main.js`, `static/js/analysis-state.js`: compact responsive Census presentation, submission state, explicit Census snapshot invalidation.

## 4. Provider Architecture

`CensusGeoProvider.lookup(point)` -> `CensusTract` -> `CensusDemographicProvider.fetch(tract)` -> `DemographicData` -> `DemographicService` -> independent population/income scores -> `AnalysisService` -> existing weighted `calculate_opportunity`.

Routes contain no external-data parsing or scoring formulas. Templates consume normalized state rather than raw Census/Mapbox responses. Injected providers make all automated tests offline. Separate Census transport rejects redirects, bounds responses to 1 MiB, uses an 8-second default per-request timeout, and logs only endpoint family plus HTTP status. No cache or storage was added.

## 5. Coordinate-to-Geography Strategy

Reuse the already verified/signed Mapbox longitude/latitude. Call `https://geocoding.geo.census.gov/geocoder/geographies/coordinates` with `x`, `y`, `benchmark=Public_AR_Current`, `vintage=ACS2024_Current`, and `format=json`. No Census address/name geocode or coordinate adjustment occurs.

Normalize state/county/tract FIPS to 2/3/6 digits and derive the 11-digit GEOID; the returned GEOID must agree. Optional county/state names can be absent. Require one tract: no match or multiple matches are explicit unavailable states, not permission to guess a tract. Requests occur only on Analyze, never autocomplete, camera movement, recentering, or style changes.

Verified against the [official Geocoder API](https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.pdf), [benchmark discovery](https://geocoding.geo.census.gov/geocoder/benchmarks), and [compatible vintage discovery](https://geocoding.geo.census.gov/geocoder/vintages?benchmark=4) before implementation.

## 6. ACS Endpoint and Vintage

`https://api.census.gov/data/2024/acs/acs5`: 2024 ACS 5-Year Detailed Tables, covering 2020-2024. Geography vintage is `ACS2024_Current`, with benchmark `Public_AR_Current`. Release/dataset/vintage constants are centralized, not inferred from the current date. Geography predicates are `for=tract:<six-digit tract>` and `in=state:<two-digit state> county:<three-digit county>`.

The [official release documentation](https://www.census.gov/data/developers/data-sets/acs-5year.html) and [tract example calls](https://api.census.gov/data/2024/acs/acs5/examples.html) were checked. Returned geography must exactly match the requested tract.

## 7. Variables

- `B01003_001E`: population estimate; `B01003_001M`: population MOE.
- `B19013_001E`: median household income in the past 12 months, in 2024 inflation-adjusted dollars; `B19013_001M`: income MOE.
- Corresponding `B01003_001EA`, `B01003_001MA`, `B19013_001EA`, `B19013_001MA`, plus `NAME`, in the same request.

Verified through official [population metadata](https://api.census.gov/data/2024/acs/acs5/groups/B01003.html) and [income metadata](https://api.census.gov/data/2024/acs/acs5/groups/B19013.html), including their JSON discovery responses. Parsing uses header names, validates rows and geography, supports independent missing variables, and never treats negative sentinel values as measurements.

## 8. Population Model v1

`population-v1`: piecewise-linear interpolation over people -> score anchors: 0 -> 0, 1,000 -> 25, 3,000 -> 60, 6,000 -> 85, 10,000+ -> 100. Round to one decimal; cap at 100. Missing returns unavailable; invalid, negative, boolean, or nonfinite input is rejected.

This is tract population context, not population density, restaurant demand, foot traffic, customer counts, or a trade area. Thresholds are transparent application assumptions requiring future calibration, not Census recommendations.

## 9. Income Model v1

`income-v1`: annual household dollars -> score anchors: 0 -> 0, 25,000 -> 20, 50,000 -> 45, 75,000 -> 65, 100,000 -> 80, 150,000+ -> 100. Same interpolation, rounding, bounds, missing/invalid handling. Higher means stronger household purchasing-power context, not disposable income, restaurant spending, concept fit, or guaranteed success.

Overall weights remain population 30%, income 30%, rent 20%, competition 20%. Only the existing overall scoring module combines them.

## 10. Margins of Error

Retain and display usable population/income MOEs at the Census-standard 90% confidence level. Missing/suppressed MOEs do not discard valid estimates or apply an undocumented score penalty. Negative/annotated MOEs are unavailable, with annotations retained; controlled-estimate sentinel MOEs are not represented as literal negative measurements or assumed zero. Annotated/open-ended estimates such as `250,000+` are unavailable for exact-value scoring.

See [official annotation definitions](https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-estimate-and-annotation-values.html) and [sampling-error guidance](https://www.census.gov/programs-surveys/acs/methodology/sample-size-and-data-quality/sample-size-definitions.html). Large uncertainty is visible, not hidden behind the score.

## 11. Provenance Matrix

| Component | Successful geographic analysis | Unavailable behavior |
| --- | --- | --- |
| Location/maps | Real Mapbox geography/imagery | Existing geographic/map error states |
| Population/income metrics | Official ACS tract estimates | Unavailable; no fictional raw replacement |
| Population/income scores | Real-derived context heuristic | Individually demo fallback 85/80 |
| Competition metrics | Live bounded Mapbox sample | Unavailable; no fake POIs |
| Competition score | Existing real-derived Competition Model v1 | Demo fallback 60 |
| Commercial rent metric/score | Demo $28/sq ft annual base rent; score 55 | Still explicitly demo |
| Nearby businesses | Not claimed; observed restaurants labeled as such | Unavailable restaurant sample |
| Schools/universities | Individually labeled demo fixture | Still demo |
| Population growth | Unavailable | Never invented for geographic reports |
| Overall | Hybrid; real-derived plus demo factors | Fully demo 72.5 if all live factors unavailable |

Pure demo-only reports retain the original explicitly fictional fixture. Factor provenance includes status, provider, vintage, GEOID, model version, description, and fallback reason. Stable keys, not display text or icons, drive report provenance.

## 12. Population Growth Decision

Not implemented. Adjacent ACS 5-year releases overlap and do not provide defensible growth comparisons. Future growth needs non-overlapping periods, verified compatible tract boundaries, and uncertainty-aware comparison. Geographic reports explicitly say unavailable; only the original clearly fictional demo-only fixture retains its sample growth value. Residential rent was not queried or substituted for commercial rent.

## 13. U.S. Coverage

Sprint 04 Census coverage is the 50 states and DC. Known non-U.S. country codes from signed Mapbox metadata skip both Census requests. Unknown metadata can be resolved by the authoritative point lookup. Unsupported territories, no tract, and ambiguous tract boundaries fail clearly. Paris keeps its real map and observed competition without being assigned U.S. demographic values.

## 14. Failure and Fallback

Missing configuration skips Census calls. Authorization, rate limits, DNS/network/timeout failures, malformed/empty responses, sentinels, annotations, missing variables, and geography mismatches produce sanitized unavailable/partial state. Usable population and income are independent; one does not require the other. Census failure does not discard geography or live competition, and competition failure does not discard Census. Missing raw metrics stay unavailable, while corresponding fallback scores are explicitly demo. Changing location/concept/radius hides all report output, clears Census GEOID/status, and removes competition markers.

## 15. Automated Verification

Baseline: `python -m pytest`, **312 passed**. Final: `python -m pytest`, **487 passed**, including all baseline tests and **175 new tests**. Python 3.14.6 / pytest 9.1.1 in the existing virtual environment. `python -m compileall -q app.py venuebite tests` passed. `git diff --check` passed; Git's existing Windows LF/CRLF notices are informational.

No live provider requests occur in tests. The app was started successfully through its existing `app.py` Flask CLI export on free port 5003 because port 5000 is occupied. `app.py` and the normal `python app.py` startup path were not changed.

## 16. Live Verification

All five U.S. examples succeeded with live Census population/income and live Mapbox competition. Values below are **tract estimates at the browser-selected point**, not city-wide statistics. Each used a 3-mile competition radius; rent stayed demo 55 and growth unavailable.

| Browser-selected example | Tract GEOID | Population | Median household income | Observed restaurants | Overall |
| --- | --- | ---: | ---: | ---: | ---: |
| Denver + Indian | 08031002604 | 2,362 | $41,818 | 37 | 42.6 |
| 701 10th Avenue, Greeley + Mexican | 08123000100 | 2,757 | $33,788 | 42 | 39.8 |
| Chicago + pizza | 17031839100 | 8,355 | $132,361 | 50 | 69.8 |
| Miami + Cuban | 12086003704 | 1,309 | $48,036 | 49 | 36.8 |
| New York City + coffee | 36061003100 | 2,910 | $189,250 | 50 | 61.0 |

Additional end-to-end Flask analyses using server-resolved Mapbox points succeeded for Denver/Greeley/Chicago/Miami/New York. Their overall scores were 70.9/53.6/69.8/36.8/73.6 respectively. Different representative points legitimately select different tracts and POI samples; no city-specific statistics or scores were hardcoded.

Greeley's autocomplete city point (40.422649, -104.707781) returned two Census tracts, 08123000502 and 08123000402. The final code explicitly reports ambiguity and keeps real competition; it does not choose an arbitrary tract or perturb coordinates. Selecting 701 10th Avenue (40.426181, -104.695145) resolved uniquely and produced the successful browser result above.

Paris + Indian succeeded in both Flask and browser verification: no Census tract/estimates, U.S.-only notice, demo population/income factors, 50 real observed restaurants, overall 63.8. Missing and rejected test Census keys were verified live: HTTP 200 reports, explicit demographic fallback, and retained live competition. The rejected-key redirect produced only a sanitized `endpoint=acs5 status=302` diagnostic.

Browser checks passed: Map/Satellite imagery, direct/general markers, safe popup name/address/distance, zoom/recenter, source/vintage/MOE labels, desktop 1920/1366 and mobile 390px screenshots, no horizontal page overflow, and concept/radius/location stale clearing. Old Census GEOIDs were removed, all report sections hidden, and markers dropped to zero before reanalysis. Browser console returned no warnings or errors. Temporary viewport overrides were reset.

Census key absence was checked in actual rendered reports and `/api/map-config`. Census credentials are never sent in browser data or JS. Final preview Flask logs contained normal successful requests and no application tracebacks; an incidental browser `/favicon.ico` 404 is unrelated to analysis (the app declares its SVG favicon).

## 17. Known Limitations

Tracts are local demographic proxies, not trade areas or exact neighborhoods. ACS estimates pool five years, can have large MOEs, and may suppress or annotate income. Representative points can differ between Mapbox search modes or lie on shared boundaries. Context models are uncalibrated and can saturate; score differences are not statistical-significance claims or predictions. Competition remains capped/provider-dependent. Real commercial rent, schools, growth, zoning, daytime demand, property availability, and traffic are not implemented. Sequential requests can approach the combined configured timeouts. No cache, persistence, retries, or new dependencies were added.

Next logical work: score calibration and trustworthy commercial property/economic inputs, with uncertainty and coverage validation. No future phase was implemented here.

## 18. Git and Security

Branch unchanged: `1234tlc123-probable-succotash`. **Nothing staged, committed, or pushed.** Initial worktree had only the existing untracked Sprint 04 prompt. Final state has 15 tracked files modified, 9 files created, and that prompt still untracked/unmodified.

```text
 M .env.example
 M README.md
 M static/css/style.css
 M static/js/analysis-state.js
 M static/js/main.js
 M templates/base.html
 M templates/results.html
 M venuebite/__init__.py
 M venuebite/providers/location_provider.py
 M venuebite/providers/mapbox_provider.py
 M venuebite/routes.py
 M venuebite/scoring.py
 M venuebite/services/__init__.py
 M venuebite/services/analysis_service.py
 M venuebite/services/mock_data_service.py
?? docs/sprint04-engineering-report.md
?? prompts/04-demographic-intelligence.md
?? templates/_demographics.html
?? tests/test_census_provider.py
?? tests/test_demographic_integration.py
?? tests/test_demographic_scoring.py
?? venuebite/demographic_scoring.py
?? venuebite/providers/census_provider.py
?? venuebite/providers/demographic_provider.py
?? venuebite/services/demographic_service.py
```

Actual credential comparison scanned tracked and nonignored untracked files through private stdin, with only pass/fail output. Hardcoded Mapbox-token/Census-key pattern scanning also passed. `.env` remains ignored (`.gitignore:151`), is not tracked, and was not modified; `.env.example` is the only tracked environment file and contains placeholders only. No real credential was printed, logged, written, committed, or pushed. Existing Mapbox public-token, secret-token rejection, signing, escaping, and CSP protections remain intact.

## 19. Manual Setup and Remaining Checks

Preview is running at **http://127.0.0.1:5003**. No dependency installation or credential change is required in this configured workspace. Restart older Flask instances on other ports before expecting Sprint 04 there; those processes were not stopped. Reselect locations after restarting when using the default ephemeral signing key. To use `python app.py`, first make port 5000 available.

For another environment, set an activated `CENSUS_API_KEY` only server-side, retain the existing authorized public Mapbox configuration, and restart Flask. Never commit `.env`. Use an exact address/landmark when a city point is ambiguous. Manual follow-up remains useful for keyboard-only/screen-reader/reduced-motion behavior, real network disruption, and deployment-specific token/origin restrictions. Automated rate-limit/timeouts/schema tests do not simulate a real provider outage. Do not interpret scores as investment advice or business-success forecasts.
