# VenueBite

VenueBite is a restaurant location-intelligence application built with Flask, Jinja, and vanilla JavaScript. Sprint 04 adds official Census tract population and median household income to Sprint 03 competition intelligence and the existing geographic explorer. Commercial rent remains demo; scores remain unvalidated heuristics.

## Current Features

- Geographic autocomplete for cities, neighborhoods, postcodes, landmarks, streets, and addresses, with keyboard and mouse selection.
- Real coordinates, a candidate-location marker, zoom controls, recentering, smooth camera transitions, and standard/satellite map modes.
- A responsive charcoal dashboard with the map beside the opportunity score on desktop and stacked content on mobile.
- Restaurant concept submission, a 1/3/5 mile competition radius, the existing weighted score, factor bars, classifications, strengths, risks, and individually labeled area insights.
- Coordinate-to-tract Census lookup and 2024 ACS 5-year estimates, margins of error, geography identifiers, vintage, and independent population/income context scores.
- Request-scoped Mapbox restaurant discovery, direct/general matching, straight-line distances, observed-sample metrics, deterministic competition explanations, and distinct map markers with safe popups.
- Hybrid analysis on live success; transparent demo-score fallback on live failure. Editing location, concept, or radius immediately invalidates the previous report and restaurant markers.
- Loading, empty, error, retry, and missing-configuration states; explicit demo-only fallback when geographic search fails.
- Server-side validation, signed geographic selections, replaceable geographic and market-data providers, and offline automated tests.
- Compare, Saved Locations, and Find an Area remain coming soon. No accounts or persistence are implemented.

## Real and Demo Data

**Successful live analysis is hybrid, not fully verified market intelligence.**

| Component | Source / status |
| --- | --- |
| Location, coordinates, map imagery | Real Mapbox geography when configured |
| Nearby restaurant sample and distances | Live Mapbox POIs; VenueBite computes distances |
| Competition factor | Real-derived heuristic on successful live retrieval |
| Population / income estimates | Official 2024 ACS 5-year tract estimates when available |
| Population / income factors | Real-derived Population / Income Model v1; individually demo fallback (85 / 80) if unavailable |
| Commercial rent / occupancy factor and metric | Fictional demo fixture: score 55; $28/sq ft annual base rent |
| Observed restaurant count | Live capped Mapbox sample, not all nearby businesses |
| Schools / universities | Fictional demo fixture, individually labeled |
| Population growth | Unavailable for geographic analysis; not fabricated |
| Overall opportunity score | Hybrid: available real-derived factors plus explicitly demo factors |

Missing geography/configuration or explicit demo-only analysis preserves the original fixture (85/80/55/60; overall 72.5), including clearly fictional area metrics and restaurant records. Geographic analysis never substitutes mock raw Census metrics or mock POIs for failed live retrieval. Each unavailable Census factor independently retains its demo score, while its raw metric says unavailable. If competition fails, its score alone falls back to 60; available Census scores still apply. If Census and competition both fail, the four-factor score is demo 72.5. A broad area's marker is a representative point, not a verified rentable site.

The opportunity score is not a prediction or guarantee of business success. Weights, classifications, and normalization thresholds are product assumptions, not scientifically validated findings.

## Installation

Use Python 3.13 or newer. This workspace uses Python 3.14; the implementation does not require newer language features.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

`requirements.txt` contains Flask and python-dotenv. `requirements-dev.txt` adds pytest. Install just `requirements.txt` when tests are not needed. No database or Node tooling is required to run the app.

## Mapbox Setup

1. Create a Mapbox account and create a **public `pk.` access token** in its access-token dashboard. See the official [token guide](https://docs.mapbox.com/accounts/guides/tokens/).
2. For this local project, duplicate `.env.example` as `.env`, then replace the placeholder `MAPBOX_ACCESS_TOKEN` value with that public token. Do not put credentials in source code or commit `.env`.
3. Use the minimum public scopes required for GL JS: `styles:read` and `fonts:read`. Enable `styles:tiles` only if the account/style workflow requires it. Search Box uses the public token; do not add server-only secret scopes. Consult the official [GL JS setup](https://docs.mapbox.com/mapbox-gl-js/guides/get-started/) and [Search Box authentication](https://docs.mapbox.com/api/search/search-box/).
4. Add URL restrictions for the origins where the application runs, including the exact local host/port used during development. For a restricted token, set `MAPBOX_REQUEST_ORIGIN` to that same trusted origin so backend search requests send an authorized Referer. For example, use `http://127.0.0.1:5000` with the normal run command. If running on port 5001, update both the token restrictions and this setting accordingly. `localhost` and `127.0.0.1` are different origins.
5. Restart Flask after changing `.env`. The app loads the root `.env` without overriding existing environment variables. Shell/hosting environment values take precedence.

Environment variables:

```dotenv
MAPBOX_ACCESS_TOKEN=your_mapbox_access_token_here
MAPBOX_SEARCH_COUNTRIES=
MAPBOX_REQUEST_ORIGIN=http://127.0.0.1:5000
MAPBOX_HTTP_TIMEOUT_SECONDS=6
COMPETITION_RADIUS_MILES=3
SECRET_KEY=
```

`MAPBOX_SEARCH_COUNTRIES` is an optional comma-separated ISO country filter, such as `us,ca`; empty leaves supported geography unrestricted. There is no hardcoded city or state. Coverage, including intersections, depends on Mapbox. Search Box currently documents coverage in the United States, Canada, and Europe; it is not a promise of worldwide search coverage.

`MAPBOX_HTTP_TIMEOUT_SECONDS` applies to each provider request (default 6 seconds; invalid or out-of-range values fall back to 6). A competition analysis makes at most two sequential requests, so its combined wait can approach twice the timeout. `COMPETITION_RADIUS_MILES` sets the initial radius to 1, 3, or 5 (default 3); the form selects the request's radius. No additional credentials or packages are required for Sprint 03.

`SECRET_KEY` optionally supplies a stable, randomly generated signing key. Without it, the app generates an ephemeral key at startup, so restarting invalidates existing selected-location forms. Configure one stable key across workers before running multiple app processes. This key is private and must never be sent to the browser. It signs selections; it does not introduce user sessions or accounts.

A public Mapbox token is intentionally visible to the browser via `/api/map-config`. Secret `sk.` tokens are rejected and never exposed. Use a dedicated URL-restricted public token for production and protect the private signing key in deployment environment variables. Maps, autocomplete sessions, and one-off category/text searches have separate usage/billing implications; check the official [Search Box documentation](https://docs.mapbox.com/api/search/search-box/) and account billing. Competition queries run only on analysis submission, never on each keystroke.

**No Mapbox credentials are required for demo analysis or tests.** Missing or invalid configuration shows a clear map-area message while Flask and the original analysis continue to work.

## Census Setup

Set `CENSUS_API_KEY=your_census_api_key_here` in the server environment or ignored root `.env`, replacing only the placeholder locally. Request and activate a key using the official [Census key registration](https://api.census.gov/data/key_signup.html). Current Census documentation requires a key for all data queries; the geography lookup itself is public. Set optional `CENSUS_HTTP_TIMEOUT_SECONDS=8` (valid range above 0 through 30 seconds). Restart Flask after configuration changes. Never put this key in JavaScript, templates, screenshots, source control, or client configuration. `.env.example` contains placeholders only; shell environment values override `.env`.

The ACS year, geography vintage, dataset, and variable IDs are centralized in `providers/demographic_provider.py`, not guessed or derived from the current date. Sprint 04 deliberately pins 2024. Before changing release years, reverify variables, supported geography, and compatible benchmark/vintage discovery. No new dependencies are required. Missing Census credentials do not disable maps or competition.

## Run

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

Open <http://127.0.0.1:5000>. With Mapbox configured, select a geographic suggestion, choose a concept and radius, and analyze. The selected place updates the map before analysis; a successful report includes live competition and Census context when configured. Editing the location clears the old selection but preserves the concept. Editing location, concept, or radius hides the entire stale report, clears Census GEOID/status metadata, and removes competitor markers. Without configuration, enter any location label and concept to run the clearly labeled demo.

Use another port when 5000 is occupied:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --port 5001
```

On macOS/Linux replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`. Debugging is off by default; add `--debug` only for local development. The Flask development server is not a production server.

## Tests and Checks

```powershell
python -m pytest
.\.venv\Scripts\python.exe -m compileall -q app.py venuebite tests
git diff --check
git status --short
```

Tests retain all 487 Sprint 01-04 tests and add exact v2 contributions, score traces, independent coverage credits/bands, provenance-aware explanation thresholds and ranking, rent verification risks, close direct matches, empty samples, mixed failures, partial Census results, and UI/stale-report regressions. External calls are mocked. Testing app instances skip `.env` and ignore developer Mapbox and Census credentials unless explicitly configured in a test.

## Architecture

```text
app.py                              Local entry point and Flask CLI export
venuebite/
    __init__.py                     Factory, environment configuration, headers
    routes.py                       Form handling and geographic JSON endpoints
    scoring.py                      Score Model v2, weights, contributions, audit trace
    data_coverage.py                Independent weighted usable-evidence coverage
    competition_scoring.py          Centralized Competition Model v1
    demographic_scoring.py          Population / Income Model v1 anchors
    concepts.py                     Concept aliases, categories, matching rules
    distance.py                     Haversine meters, mile labels, search bbox
    providers/
        location_provider.py        Geographic contract and input validation
        mapbox_provider.py          Mapbox HTTP adapter and response normalization
        poi_provider.py             Normalized POI contract and provider protocol
        mapbox_poi_provider.py       Bounded category/text searches and normalization
        demographic_provider.py     Census contracts, verified release/variable constants
        census_provider.py          Bounded Census geography and ACS adapters
    services/
        __init__.py                  Market-data contract
        analysis_service.py         Independent factors, structured provenance, report
        explanation_service.py      Pure factor/provenance-driven explanations
        demographic_service.py      Eligibility, geography/ACS orchestration, fallback
        competition_service.py      Deduplication, filtering, matching, metrics
        mock_data_service.py        Immutable fictional market fixture
        geography_service.py        Signed selections and form resolution
templates/
    base.html                       Shell and conditional official Mapbox CSS
    _search_form.html               Accessible search and concept form
    _map_workspace.html             Map surface, controls, location metadata
    _competition.html               Live metrics, explanation, sorted tables
    _demographics.html              Tract source, vintage, coverage and MOEs
    index.html / results.html       Initial/error workspace and analysis report
static/
    css/style.css                   Responsive dashboard and map styles
    js/api.js                       JSON requests and safe error feedback
    js/location-search.js           Debounced autocomplete and selection state
    js/map-viewer.js                Map lifecycle, marker, camera, style changes
    js/competition-markers.js       Bounded DOM markers, safe popups, snapshot guard
    js/analysis-state.js            Immediate stale-report/marker invalidation
    js/main.js                      Form submission and module orchestration
    icons/                          Locally vendored Lucide assets and license
tests/                              Original and new mocked-provider coverage
.env.example                        Configuration placeholders only
```

`create_app(config=None, data_provider=..., location_provider=..., poi_provider=..., census_geo_provider=..., demographic_provider=...)` supports independent provider substitution. Routes use services; templates consume normalized objects, never raw provider JSON. The shared `MapboxSearchClient` owns Mapbox transport; `MapboxPoiProvider` and `CompetitionService` preserve Sprint 03 discovery. Census adapters have a separate credential-safe transport. `competition_scoring.py` and `demographic_scoring.py` own factor normalization; the existing `scoring.py` still owns weighted overall scoring.

Search uses Mapbox Search Box `/suggest` and `/retrieve` with the same UUID session token. After a successful retrieval, a new search session begins. The server signs the normalized selection with a 30-minute lifetime. Analysis validates that signature, location name, and any submitted coordinates, avoiding a second retrieve request. Without JavaScript, a normal form POST uses `/forward` to resolve the query on the server. A demo-only fallback bypasses lookup but never accepts unsigned client coordinates.

The adapter has timeouts, response-size limits, schema validation, and sanitized errors. API responses and submitted reports use `Cache-Control: no-store`. No geographic data is persisted, cached in application storage, or placed in localStorage; Search Box data is subject to Mapbox's temporary-use terms. Mapbox GL JS and its stylesheet load from the official, version-pinned CDN. The CSP permits Mapbox requests, blob workers, WebAssembly compilation, and dynamic styles without permitting inline JavaScript. An origin-only cross-origin referrer supports restricted public tokens without leaking form values.

### Nearby Discovery and Matching

One `/category/restaurant` query discovers the general environment. A second category query uses a verified canonical category for Indian, Mexican, Cuban, pizza, burgers, coffee, cafe/bakery, or bakery. The registry was checked against Mapbox `/list/category`; mappings are centralized, not invented. An unmapped concept, such as Congolese, uses `/forward` with the concept text and a restaurant filter. Related African cuisine alone is not treated as Congolese. Literal name/category word matches are explicitly approximate; category-search provenance can supply matching evidence when optional category metadata is absent. Unknown cuisine or business status is never guessed.

Category queries deliberately omit `types`: the live endpoint returned HTTP 400 (`unknown field types`) even though the current docs list it. Category search is already POI-only. Text search still uses `types=poi`. Categories such as `indian_restaurant`, `mexican_restaurant`, and `pizza_restaurant` work with the same existing public token. Diagnostics log only endpoint family and HTTP status, never URLs, tokens, or provider bodies.

Search uses selected longitude/latitude as `proximity` and a spherical-circle bounding box. At poles/antimeridian crossings it uses a conservative degree-radius search instead, because provider bbox cannot cross longitude 180. Every result then receives a Haversine distance in meters using mean Earth radius 6,371,008.8 m, is filtered to the exact 1/3/5 mile circle, and sorted by distance/name. Displayed distances are miles (1609.344 m per mile), not driving distances. IDs deduplicate across queries; missing IDs use a conservative normalized-name/coordinate fallback. Known closed results are removed; unknown status remains unknown.

Category queries are capped at 25 each; text search at 10. There are no per-business requests or pagination. The UI always describes an observed sample, discloses caps/malformed skipped results, and does not claim exhaustive restaurant counts. A failure in either query makes competition unavailable rather than scoring a silently partial result. An empty successful sample yields a low-observed-pressure score with a warning that this is not proof of no restaurants.

### VenueBite Competition Model v1

Each direct match contributes 10 pressure points; a general restaurant contributes 1.5. Multiply each contribution by its distance band: 1.0 within 0.5 mi, 0.7 through 1 mi, 0.35 through 3 mi, or 0.15 through 5 mi. Sum contributions and compute:

```text
competition_score = round(100 / (1 + observed_pressure / 40), 1)
```

The score is 0-100, with 100 for an empty sample. Higher pressure lowers the score; direct and closer matches matter more. Low observed pressure is score 75+, moderate 45+, high below 45. Named constants and the version are centralized. This is a transparent, unvalidated heuristic: sample caps, broad categories, and provider coverage affect comparisons. It does not measure actual market share, demand, business quality, or success probability. No AI is involved.

### Census Geography and Demographics

Only an explicit Analyze submission runs Census. The verified/signed Mapbox point is reused: there is no Census address/name geocode, no request on autocomplete, map movement, recentering, or map-style changes. One request to `https://geocoding.geo.census.gov/geocoder/geographies/coordinates` sends `x=longitude`, `y=latitude`, `benchmark=Public_AR_Current`, `vintage=ACS2024_Current`, and `format=json`. Both names were verified against the official [benchmark](https://geocoding.geo.census.gov/geocoder/benchmarks) and [vintage discovery](https://geocoding.geo.census.gov/geocoder/vintages?benchmark=4) endpoints; coordinate semantics are documented in the [Geocoder API](https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.pdf).

`CensusGeoProvider` normalizes two-digit state, three-digit county, six-digit tract FIPS, and their eleven-digit GEOID; the returned GEOID must match. County/state names are optional. `CensusDemographicProvider` then requests `https://api.census.gov/data/2024/acs/acs5` with `for=tract:<tract>` and `in=state:<state> county:<county>`, one combined `get`, and the private key. Returned geographic codes must exactly match the requested tract, preventing wrong or stale rows. Headers drive parsing, not column positions. Missing variables may produce partial results; malformed rows/headers/geography fail safely.

Verified variables, including annotations, in official [B01003 metadata](https://api.census.gov/data/2024/acs/acs5/groups/B01003.html) and [B19013 metadata](https://api.census.gov/data/2024/acs/acs5/groups/B19013.html):

- `B01003_001E`: total population estimate; `B01003_001M`: population margin of error.
- `B19013_001E`: median household income in the past 12 months, in 2024 inflation-adjusted dollars; `B19013_001M`: its margin of error.
- Each corresponding `EA`/`MA` annotation is retrieved in that same call, along with `NAME`.

Nulls, empty/invalid values, negative sentinel codes, and annotated estimates are unavailable, never measurements. Open-ended income medians such as `250,000+` are not treated as exact medians or scored. A usable estimate remains usable when its MOE is missing/suppressed. Negative or annotated MOEs, including the controlled-estimate sentinel, are retained as unavailable with their annotations rather than shown as negative numbers or assumed zero. See [official annotation definitions](https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-estimate-and-annotation-values.html).

The UI retains and displays available MOEs at the Census standard 90% confidence level. ACS is a survey and estimates can have substantial uncertainty, especially in small areas; MOEs do not impose an undocumented score penalty. This is a 2020-2024 pooled estimate, not a 2024-only count or a current headcount. The containing tract is a **local demographic proxy**, not a restaurant trade area, exact neighborhood, walking radius, demand estimate, or total addressable market. Competition radius never changes the tract or Census query.

`DemographicService` centrally skips known non-U.S. country codes from signed Mapbox metadata. Coverage is the 50 states and DC. Unknown country metadata can be resolved authoritatively by the tract lookup; unsupported states/territories or no matching tract fail safely. Paris keeps real geography and available Mapbox POIs, but Census metrics are unavailable and demographic scores are explicitly demo fallback. No U.S. demographic values are passed off as Paris statistics.

Each HTTP request has a bounded timeout and 1 MiB response limit. Redirects are rejected so credentials are never forwarded to another host. Authorization, rate limits, DNS/network/timeouts, empty results, and malformed data become application-owned messages. Logs contain only Census endpoint family and HTTP status, never URLs, raw errors, bodies, or keys. Missing keys skip both Census requests. Failure in either Census step preserves independent competition/map functionality. There is no response cache, persistence, retry loop, or extra per-variable request; two Census calls can take up to twice the configured timeout.

Population growth is explicitly unavailable in geographic reports. Adjacent ACS 5-year releases overlap and are not used for growth. A future implementation needs non-overlapping periods (2015-2019 vs 2020-2024), verified comparable tract boundaries, and uncertainty-aware comparison. Pure demo-only reports retain the original explicitly fictional growth fixture. Residential ACS rent is never substituted for commercial asking rent.

For a point on a shared tract boundary, Census can return multiple matches. The app explicitly reports ambiguity and does not choose an arbitrary tract or move the selected coordinates. Select a more specific address or landmark. This occurred live with Greeley's autocomplete city point; a different server-resolved Greeley point returned a single valid tract.

### Population and Income Models v1

Both models use deterministic piecewise-linear interpolation between centralized anchors, round to one decimal, and cap at 100. Missing values return unavailable, not zero. Negative, nonnumeric, boolean, and nonfinite input is rejected; genuine zero scores zero. Thresholds are transparent, uncalibrated application assumptions, not Census recommendations.

- `population-v1` anchors (tract people -> score): 0 -> 0; 1,000 -> 25; 3,000 -> 60; 6,000 -> 85; 10,000+ -> 100. This measures population context only, not density, foot traffic, daytime population, demand, or customers. No unverified land area is used.
- `income-v1` anchors (annual household dollars -> score): 0 -> 0; 25,000 -> 20; 50,000 -> 45; 75,000 -> 65; 100,000 -> 80; 150,000+ -> 100. Higher scores represent stronger household purchasing-power context, not disposable income, concept fit, or restaurant spending.

Structured per-factor provenance includes status (`real`, `demo`, `fallback`), provider, vintage, GEOID, model version, description, and fallback reason. The banner, factor badges, area metric labels, and strength/risk explanations use this state rather than inferring source from label text. Rent and schools remain demo; nearby businesses are not falsely inferred from a restaurant-only sample.

### VenueBite Score Model v2

`VENUEBITE_SCORE_MODEL_VERSION = "2.0"` identifies composition and explainability, not a recalibration of the underlying Population, Income, or Competition Models v1. Population and income each weigh 30%; rent and competition each weigh 20%. `FACTOR_DEFINITIONS` centrally specifies weights, higher-is-better direction, and expected provenance (Census, Census, demo rent, Mapbox):

```text
weighted_points[factor] = factor_score * factor_weight
raw_weighted_sum = sum(weighted_points)
overall = round(clamp(raw_weighted_sum, 0, 100), 1)
       = round(population_score * 0.30 + income_score * 0.30 + rent_score * 0.20 + competition_score * 0.20, 1)
demo-only / all providers unavailable: 85 * .30 + 80 * .30 + 55 * .20 + 60 * .20 = 72.5
```

Higher factor scores always mean better opportunity context. Population describes tract demographic context, not customer demand; income describes household purchasing-power context, not restaurant spending. A high rent score means more affordable occupancy costs; a high competition score means lower observed competitive pressure. These normalized factors are not raw prices or restaurant counts. Rent stays fictional, and displayed demo metrics do not feed a real normalization process. Weights and all v1 anchors/pressure formulas are unchanged.

Contributions are backend-computed and retained without rounding. The UI displays two decimals (74 at 30% contributes 22.20 points); the total is rounded once to one decimal before classification. Display rounding never feeds score calculation. The internal immutable trace retains model version, each factor's score, weight, contribution, direction, expected/actual source, status, vintage/GEOID/model/reason, coverage credit, raw sum, final score, and coverage. It is not serialized as raw debugging JSON in the UI.

Classification thresholds are centralized: Strong at 80+, Promising at 65+, Mixed at 50+, Challenging below 50. These are neutral decision-support bands, not advice to invest or guarantees. Invalid factors (nonnumeric, boolean, nonfinite, missing, unknown or outside 0-100) remain rejected; final bounding protects arithmetic, not bad input.

### Data Coverage, Not Success Probability

Data Coverage is separate from Opportunity Score and never adjusts factor scores or their weights:

```text
credit = real: 1.0; explicit partial: 0.5; demo/fallback/unavailable: 0.0
coverage = round(sum(factor_weight * credit * 100), 1)
current successful hybrid = 30 + 30 + 0 + 20 = 80%
```

Labels are Very high at 90+, High at 70+, Moderate at 50+, Limited at 25+, and Very limited below 25. A nonblocking verification notice appears below 70%. Full Census + failed competition yields 60%; failed Census + usable competition yields 20%; both fail or demo-only yields 0%. A single usable Census estimate plus competition yields 50%. Genuine zero estimates are usable and receive full coverage even though their opportunity scores are zero.

Coverage reads structured per-factor statuses, never label text. A partially available Census response does **not** halve an otherwise usable population or income factor: usable estimates are `real`, missing ones are `fallback`. Explicit factor-level `partial` is supported at half credit for future incomplete inputs; no current provider result is newly marked partial. A usable capped POI sample gets its full factor weight, not a claim that all restaurants were found. MOEs and discovery completeness remain quality notes, not hidden coverage penalties.

Coverage measures how much of this four-factor model has real usable evidence. It is **not** scientific confidence, accuracy, restaurant demand, statistical significance, or probability of success. The current model cannot reach 100% real coverage while rent remains demo.

### Deterministic Explanations

`explanation_service.py` consumes only assembled score, provenance, coverage, Census metadata and observed competition; it performs no I/O, AI or random generation. Fully real factors scoring 75+ qualify as strengths, ranked by weighted contribution with stable factor-order ties; at most two appear. A real factor below 65 is a review risk. Two or more observed direct matches within 0.5 mile also flag a proximity risk, even in the balanced band. Competition prose uses its actual Low/Moderate/High pressure level, direct counts, radius and nearest distance; an empty sample never means no competitors exist.

Demo, fallback, partial and unavailable factors produce verification risks regardless of score. Rent is a risk because live commercial occupancy cost is unverified, not because the demo price proves local rents are expensive. Risks rank by weighted deficit for real factors or missing coverage weight for evidence gaps, with stable ties and at most four items (one per factor). A factor cannot appear as both a strength and a risk. Each item includes its score, contribution and weight; the short summary is generated from the same structured data. Expandable source/model and evidence-quality details retain ACS survey/MOE/tract limitations, capped Mapbox sampling, and demo rent caveats. No model has been scientifically validated or calibrated against restaurant outcomes.

## Manual Verification

- Search cities in different states (Miami, Chicago, Dallas, New York), postcode `10001`, a neighborhood, Times Square, and a complete address. Try intersections where supported. Verify names and coordinates, marker placement, and camera framing.
- Select with mouse and with Arrow Up/Down + Enter; dismiss with Escape. Clear/change the place and confirm the concept stays intact and stale coordinates disappear. Normal analysis remains disabled until a suggestion is resolved.
- Analyze Denver + Indian, Miami + Cuban, Chicago + pizza, New York + coffee, and Greeley + Mexican. Verify selected coordinates, correct tract/GEOID/state/county, actual Census estimates/MOEs/source/vintage, actual POIs, and varying factor/overall scores. Verify rent/schools remain demo, growth unavailable, and no old fictional population/income metrics appear. Do not hardcode business names or expect city-wide population at a selected point.
- Analyze Paris, France: real geography and competition should continue where supported; Census should show U.S.-only unavailable coverage and explicitly demo demographic factors. Remove/disable only the Census key and restart: maps/competition should still work, Census scores should be fallback, and raw Census metrics unavailable.
- Change location, concept, and radius independently after a report. Confirm score, all Census values/geography/source, competition metrics, and competitor markers disappear immediately. Submit a new analysis and confirm only the new point's tract/data return. Inspect browser source/network configuration to ensure no Census key or browser Census request appears.
- Analyze Denver Union Station with Indian or Cuban: confirm exact selected landmark coordinates are used, category requests succeed, and both marker types/popups work. Change location/concept/radius and confirm previous results disappear immediately. Test 1/3/5 mile radii and cap/zero-result notices.
- Switch Map/Satellite, use zoom and recenter, resize to tablet/mobile, and check attribution, controls, readable text, touch targets, and no horizontal page overflow.
- Test reduced motion, keyboard-only navigation, no results, a disconnected network, an invalid public token, and map retry. Search failures should offer explicit demo-only analysis, not invented geographic results.
- Remove the token and restart: the app should still open and analyze demo data. Disable JavaScript: analysis should still work; map/autocomplete require JavaScript. Test blank/long fields and a changed or expired selection for useful feedback.

## Limitations and Next Steps

Live map/search/competition verification requires a Mapbox account, authorized public token, and network access. Map rendering also requires WebGL. Failures preserve geography where possible and explicitly demo scoring, not invented real results. Discovery is a capped, potentially incomplete provider sample; unsupported categories use approximate text matching. Provider data and scores can change between requests. No ratings, reviews, pricing, travel times, or opening-hours inference are used.

Broad places resolve to representative points, not storefront availability. Official tract population/income estimates provide limited demographic context, not comprehensive market research. Tract size/boundaries, representative-point placement, high MOEs, group quarters, five-year pooling, POI coverage/caps, income caps, and uncalibrated scoring can materially affect comparisons. Values may change between releases and scores can saturate; differences are not claims of statistical significance. No real commercial property, zoning, traffic, demand, or business-success estimates are provided. There is **no persistent POI storage**, database, response cache, or browser localStorage. Provider results are processed per request and rendered as a temporary snapshot only. Selections and analyses are not saved.

Next: calibrate context scoring and evaluate trustworthy commercial property/economic sources. Growth needs comparable boundaries and non-overlapping periods. Saved analyses and comparisons require provider-storage licensing review before persistence; accounts, Find an Area, AI explanations, deployment, and production hardening remain future work.

Icons are from [Lucide 0.468.0](https://github.com/lucide-icons/lucide/tree/0.468.0), with the license in `static/icons/LICENSE`. Maps and imagery retain Mapbox's built-in attribution.
