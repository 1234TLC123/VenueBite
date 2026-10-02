# VenueBite

VenueBite is a learning project for restaurant location intelligence built with Flask, Jinja, and vanilla JavaScript. Sprint 02 adds real Mapbox geographic search and an interactive map to Sprint 01's working demo analysis.

## Current Features

- Geographic autocomplete for cities, neighborhoods, postcodes, landmarks, streets, and addresses, with keyboard and mouse selection.
- Real coordinates, a candidate-location marker, zoom controls, recentering, smooth camera transitions, and standard/satellite map modes.
- A responsive charcoal dashboard with the map beside the opportunity score on desktop and stacked content on mobile.
- Restaurant concept submission, the existing weighted score, factor bars, classifications, strengths, risks, area insights, and fictional nearby restaurants.
- Loading, empty, error, retry, and missing-configuration states; explicit demo-only fallback when geographic search fails.
- Server-side validation, signed geographic selections, replaceable geographic and market-data providers, and offline automated tests.
- Compare, Saved Locations, and Find an Area remain coming soon. No accounts or persistence are implemented.

## Real Geography, Demo Market Analysis

**Mapbox location names, coordinates, and map imagery are real geographic data when configured. All market analysis remains fictional.**

Every location and concept still uses the same fixture: population 85, income 80, rent 55, and competition 60. Area metrics, restaurant records, and competition distances are also fictional; those records are not placed on the real map. A broad area's marker represents its resolved geographic point, not a verified rentable site.

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
SECRET_KEY=
```

`MAPBOX_SEARCH_COUNTRIES` is an optional comma-separated ISO country filter, such as `us,ca`; empty leaves supported geography unrestricted. There is no hardcoded city or state. Coverage, including intersections, depends on Mapbox. Search Box currently documents coverage in the United States, Canada, and Europe; it is not a promise of worldwide search coverage.

`SECRET_KEY` optionally supplies a stable, randomly generated signing key. Without it, the app generates an ephemeral key at startup, so restarting invalidates existing selected-location forms. Configure one stable key across workers before running multiple app processes. This key is private and must never be sent to the browser. It signs selections; it does not introduce user sessions or accounts.

A public Mapbox token is intentionally visible to the browser via `/api/map-config`. Secret `sk.` tokens are rejected and never exposed. Use a dedicated URL-restricted public token for production and protect the private signing key in deployment environment variables. Review Mapbox usage limits and billing for maps and [session-based search requests](https://docs.mapbox.com/api/search/search-box/); debounce reduces calls but does not make the service free.

**No Mapbox credentials are required for demo analysis or tests.** Missing or invalid configuration shows a clear map-area message while Flask and the original analysis continue to work.

## Run

```powershell
.\.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:5000>. With Mapbox configured, select a geographic suggestion, choose a restaurant concept, and analyze. The selected place updates the map before analysis. Editing the location clears the old selection but preserves the concept. Without configuration, enter any location label and concept to run the clearly labeled demo.

Use another port when 5000 is occupied:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --port 5001
```

On macOS/Linux replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`. Debugging is off by default; add `--debug` only for local development. The Flask development server is not a production server.

## Tests and Checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app.py venuebite tests
git diff --check
git status --short
```

Tests retain all Sprint 01 coverage and add normalized suggestions/locations, wide-area queries, malformed/oversized responses, network/API failures, missing configuration, secret-token rejection, coordinate bounds, endpoint validation, signed/tampered/expired selections, replacement locations, and explicit demo fallback. External calls are mocked. Testing app instances skip `.env` and ignore the developer's Mapbox token unless explicitly configured in a test.

## Architecture

```text
app.py                              Local entry point and Flask CLI export
venuebite/
    __init__.py                     Factory, environment configuration, headers
    routes.py                       Form handling and geographic JSON endpoints
    scoring.py                      Existing weights, classifications, insights
    providers/
        location_provider.py        Geographic contract and input validation
        mapbox_provider.py          Mapbox HTTP adapter and response normalization
    services/
        __init__.py                  Market-data contract
        analysis_service.py         Market provider -> existing scoring engine
        mock_data_service.py        Immutable fictional market fixture
        geography_service.py        Signed selections and form resolution
templates/
    base.html                       Shell and conditional official Mapbox CSS
    _search_form.html               Accessible search and concept form
    _map_workspace.html             Map surface, controls, location metadata
    index.html / results.html       Initial/error workspace and analysis report
static/
    css/style.css                   Responsive dashboard and map styles
    js/api.js                       JSON requests and safe error feedback
    js/location-search.js           Debounced autocomplete and selection state
    js/map-viewer.js                Map lifecycle, marker, camera, style changes
    js/main.js                      Form submission and module orchestration
    icons/                          Locally vendored Lucide assets and license
tests/                              Original and new mocked-provider coverage
.env.example                        Configuration placeholders only
```

`create_app(config=None, data_provider=..., location_provider=...)` allows independent app instances and provider substitution. Routes and templates consume normalized `GeographicLocation`/`LocationSuggestion` objects, not raw Mapbox payloads. The separate market-data provider still feeds `AnalysisService` and the scoring engine. Replacing geographic search does not require rewriting market analysis; replacing the browser map renderer is isolated to the map module.

Search uses Mapbox Search Box `/suggest` and `/retrieve` with the same UUID session token. After a successful retrieval, a new search session begins. The server signs the normalized selection with a 30-minute lifetime. Analysis validates that signature, location name, and any submitted coordinates, avoiding a second retrieve request. Without JavaScript, a normal form POST uses `/forward` to resolve the query on the server. A demo-only fallback bypasses lookup but never accepts unsigned client coordinates.

The adapter has timeouts, response-size limits, schema validation, and sanitized errors. API responses and submitted reports use `Cache-Control: no-store`. No geographic data is persisted, cached in application storage, or placed in localStorage; Search Box data is subject to Mapbox's temporary-use terms. Mapbox GL JS and its stylesheet load from the official, version-pinned CDN. The CSP permits Mapbox requests, blob workers, WebAssembly compilation, and dynamic styles without permitting inline JavaScript. An origin-only cross-origin referrer supports restricted public tokens without leaking form values.

### Scoring Is Unchanged

Population and income each weigh 30%; rent and competition each weigh 20%:

```text
85 * 0.30 + 80 * 0.30 + 55 * 0.20 + 60 * 0.20 = 72.5
```

Higher factor scores always mean better opportunity. A high rent score means more affordable occupancy costs; a high competition score means less direct competitive pressure. These normalized factors are not raw prices or restaurant counts. The displayed demo metrics do not feed a real normalization process.

Scores are rounded to one decimal before classification: Strong at 80+, Promising at 65+, Mixed at 50+, and Challenging below 50. Strengths start at 75; risks are below 65. The engine still rejects nonnumeric, nonfinite, missing, unknown, and out-of-range factors.

## Manual Verification

- Search cities in different states (Miami, Chicago, Dallas, New York), postcode `10001`, a neighborhood, Times Square, and a complete address. Try intersections where supported. Verify names and coordinates, marker placement, and camera framing.
- Select with mouse and with Arrow Up/Down + Enter; dismiss with Escape. Clear/change the place and confirm the concept stays intact and stale coordinates disappear. Normal analysis remains disabled until a suggestion is resolved.
- Run analysis and verify the unchanged 72.5 demo score, factors, concept, strengths, risks, area insights, and fictional competition. Confirm the separate real-location/demo-market labels.
- Switch Map/Satellite, use zoom and recenter, resize to tablet/mobile, and check attribution, controls, readable text, touch targets, and no horizontal page overflow.
- Test reduced motion, keyboard-only navigation, no results, a disconnected network, an invalid public token, and map retry. Search failures should offer explicit demo-only analysis, not invented geographic results.
- Remove the token and restart: the app should still open and analyze demo data. Disable JavaScript: analysis should still work; map/autocomplete require JavaScript. Test blank/long fields and a changed or expired selection for useful feedback.

## Limitations and Next Steps

Live map/search verification requires Chris's Mapbox account and a correctly scoped public token. Map rendering requires network access and a WebGL-capable browser. This implementation does not silently substitute a fake map when tiles or search fail. Offline/rejected-token states preserve demo analysis.

Broad places resolve to representative points, not storefront availability. Provider coverage and place boundaries vary. No real demographics, economics, property, zoning, regulations, competition, or business-success estimates are provided. Geographic selections are temporary; saved locations, comparisons, accounts, and databases are deliberately deferred.

The next logical step is to integrate a real nearby-business provider, then trustworthy demographic/economic sources, with provenance and coverage checks before calibrating scoring. Persistence and authentication should follow only when those workflows are needed.

Icons are from [Lucide 0.468.0](https://github.com/lucide-icons/lucide/tree/0.468.0), with the license in `static/icons/LICENSE`. Maps and imagery retain Mapbox's built-in attribution.
