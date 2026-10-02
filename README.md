# VenueBite

VenueBite is a restaurant location-intelligence learning project built with Flask, Jinja, and vanilla JavaScript. Sprint 03 adds live nearby restaurants, concept matching, competitor markers, and a real-derived competition factor to the existing geographic explorer and weighted scoring engine.

## Current Features

- Geographic autocomplete for cities, neighborhoods, postcodes, landmarks, streets, and addresses, with keyboard and mouse selection.
- Real coordinates, a candidate-location marker, zoom controls, recentering, smooth camera transitions, and standard/satellite map modes.
- A responsive charcoal dashboard with the map beside the opportunity score on desktop and stacked content on mobile.
- Restaurant concept submission, a 1/3/5 mile radius, the existing weighted score, factor bars, classifications, strengths, risks, and demo area insights.
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
| Population / income / rent factors | Demo fixture: 85 / 80 / 55 |
| Area insights, businesses, schools, growth, rent metrics | Fictional demo data |
| Overall opportunity score | Hybrid: three demo factors plus real-derived competition |

Missing geography/configuration or explicit demo-only analysis preserves the original fixture (competition 60; overall 72.5) and its clearly fictional restaurant list. If geography works but POI discovery fails, the UI says **Demo analysis - live competition unavailable**, retains that demo score, and shows no fake restaurant results or competitor markers. A broad area's marker is a representative point, not a verified rentable site.

The opportunity score is not a prediction or guarantee of business success. Weights, classifications, and insight thresholds are learning-project assumptions, not scientifically validated findings.

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

## Run

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

Open <http://127.0.0.1:5000>. With Mapbox configured, select a geographic suggestion, choose a concept and radius, and analyze. The selected place updates the map before analysis; a successful report includes live competition. Editing the location clears the old selection but preserves the concept. Editing location, concept, or radius removes the stale report/competition markers. Without configuration, enter any location label and concept to run the clearly labeled demo.

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

Tests retain all Sprint 01/02 coverage and add POI normalization, missing optional fields, HTTP/JSON failures, bounded endpoint-specific queries, deduplication, closed-business exclusion, Haversine checks, radius filtering, aliases, approximate matching, scoring extremes/monotonicity, hybrid rendering, and unavailable/empty states. External calls are mocked. Testing app instances skip `.env` and ignore the developer's Mapbox token unless explicitly configured in a test.

## Architecture

```text
app.py                              Local entry point and Flask CLI export
venuebite/
    __init__.py                     Factory, environment configuration, headers
    routes.py                       Form handling and geographic JSON endpoints
    scoring.py                      Existing weights, classifications, insights
    competition_scoring.py          Centralized Competition Model v1
    concepts.py                     Concept aliases, categories, matching rules
    distance.py                     Haversine meters, mile labels, search bbox
    providers/
        location_provider.py        Geographic contract and input validation
        mapbox_provider.py          Mapbox HTTP adapter and response normalization
        poi_provider.py             Normalized POI contract and provider protocol
        mapbox_poi_provider.py       Bounded category/text searches and normalization
    services/
        __init__.py                  Market-data contract
        analysis_service.py         Demo factors + competition -> existing scoring
        competition_service.py      Deduplication, filtering, matching, metrics
        mock_data_service.py        Immutable fictional market fixture
        geography_service.py        Signed selections and form resolution
templates/
    base.html                       Shell and conditional official Mapbox CSS
    _search_form.html               Accessible search and concept form
    _map_workspace.html             Map surface, controls, location metadata
    _competition.html               Live metrics, explanation, sorted tables
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

`create_app(config=None, data_provider=..., location_provider=..., poi_provider=...)` supports independent provider substitution. Routes use services; templates consume normalized objects, never raw Mapbox JSON. The shared `MapboxSearchClient` owns HTTP transport, timeout, size limits, trusted Referer, and safe errors. `MapboxPoiProvider` normalizes external features; `CompetitionService` owns discovery analysis; `competition_scoring.py` owns competition scoring; the existing `scoring.py` still owns overall scoring.

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

### Overall Scoring Is Unchanged

Population and income each weigh 30%; rent and competition each weigh 20%:

```text
overall = 85 * 0.30 + 80 * 0.30 + 55 * 0.20 + competition_score * 0.20
demo-only / unavailable competition: competition_score = 60; overall = 72.5
```

Higher factor scores always mean better opportunity. A high rent score means more affordable occupancy costs; a high competition score means less direct competitive pressure. These normalized factors are not raw prices or restaurant counts. The displayed demo metrics do not feed a real normalization process.

Scores are rounded to one decimal before classification: Strong at 80+, Promising at 65+, Mixed at 50+, and Challenging below 50. Strengths start at 75; risks are below 65. The engine still rejects nonnumeric, nonfinite, missing, unknown, and out-of-range factors.

## Manual Verification

- Search cities in different states (Miami, Chicago, Dallas, New York), postcode `10001`, a neighborhood, Times Square, and a complete address. Try intersections where supported. Verify names and coordinates, marker placement, and camera framing.
- Select with mouse and with Arrow Up/Down + Enter; dismiss with Escape. Clear/change the place and confirm the concept stays intact and stale coordinates disappear. Normal analysis remains disabled until a suggestion is resolved.
- Analyze Denver + Indian, Miami + Cuban, Chicago + pizza, New York + coffee, Greeley + Mexican, and Denver + Congolese. Verify selected name/coordinates, actual POIs, plausible straight-line distances, changing competition/overall scores, hybrid labels, and demo population/income/rent/area metrics. Do not hardcode business names.
- Analyze Denver Union Station with Indian or Cuban: confirm exact selected landmark coordinates are used, category requests succeed, and both marker types/popups work. Change location/concept/radius and confirm previous results disappear immediately. Test 1/3/5 mile radii and cap/zero-result notices.
- Switch Map/Satellite, use zoom and recenter, resize to tablet/mobile, and check attribution, controls, readable text, touch targets, and no horizontal page overflow.
- Test reduced motion, keyboard-only navigation, no results, a disconnected network, an invalid public token, and map retry. Search failures should offer explicit demo-only analysis, not invented geographic results.
- Remove the token and restart: the app should still open and analyze demo data. Disable JavaScript: analysis should still work; map/autocomplete require JavaScript. Test blank/long fields and a changed or expired selection for useful feedback.

## Limitations and Next Steps

Live map/search/competition verification requires a Mapbox account, authorized public token, and network access. Map rendering also requires WebGL. Failures preserve geography where possible and explicitly demo scoring, not invented real results. Discovery is a capped, potentially incomplete provider sample; unsupported categories use approximate text matching. Provider data and scores can change between requests. No ratings, reviews, pricing, travel times, or opening-hours inference are used.

Broad places resolve to representative points, not storefront availability. No real demographics, economics, property, zoning, traffic, demand, or business-success estimates are provided. There is **no persistent POI storage**, database, disk response cache, or browser localStorage. Provider results are processed per request and rendered as a temporary snapshot only, under Mapbox's temporary-use rules. Selections and analyses are not saved.

Next: trustworthy demographic/economic sources with provenance and coverage checks, then scoring calibration. Saved analyses and comparisons require provider-storage licensing review before persistence; accounts, Find an Area, AI explanations, deployment, and production hardening remain future work.

Icons are from [Lucide 0.468.0](https://github.com/lucide-icons/lucide/tree/0.468.0), with the license in `static/icons/LICENSE`. Maps and imagery retain Mapbox's built-in attribution.
