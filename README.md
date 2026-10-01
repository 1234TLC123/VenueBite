# VenueBite

VenueBite is a Flask + Jinja restaurant location intelligence application. Sprint 01 provides a working analysis workspace backed by a fictional dataset. It is intended to grow into a tool for evaluating restaurant locations using real demographic, economic, property, and competition data.

## Current Features

- Location and restaurant concept submission using POST, with server-side validation.
- A weighted 0-100 Opportunity Score, classification, and individual factor scores.
- Strengths and risks derived deterministically from the factor scores.
- A clearly identified location/map placeholder; no live map or geocoding yet.
- Sample area metrics and fictional nearby restaurant records.
- Responsive desktop/mobile layout, accessible form feedback, and repeat analysis.
- Navigation for Analyze, Compare, Saved Locations, and Find an Area. The last three are coming soon.
- Provider substitution, safe error pages, and automated tests.

## Demo Data Limitation

**Nothing in this MVP is verified information about a real location.** Every location and restaurant concept uses the same fixture: population 85, income 80, rent 55, and competition 60. Location and concept inputs identify the user's request; they do not change the fictional dataset or score. Area metrics, restaurants, and distances are also fictional. No external API calls occur during analysis.

The score is not a prediction or guarantee of business success. The weights, classifications, and insight thresholds are MVP assumptions and are not scientifically validated.

## Installation

Use Python 3.13 or newer. The current workspace was verified using its existing Python 3.14 virtual environment; no newer Python features are required by the code.

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

On macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

`requirements.txt` contains only the application dependency, Flask. `requirements-dev.txt` adds pytest for development and testing. For running the app without tests, install `requirements.txt` instead.

No API credentials, database, Node tooling, or `.env` file are needed. `.env.example` documents optional Flask CLI environment settings; the application does not automatically load `.env` files. `.env` and local environment variants are ignored by Git.

## Run

```powershell
.\.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:5000>. Enter a location and restaurant concept, then submit the form. Change either field and submit again for another report.

To choose another port or explicitly enable development debugging:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --port 5001
.\.venv\Scripts\python.exe -m flask --app app run --debug
```

On macOS/Linux use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`. Debugging is off by default. The Flask development server is for local development.

## Tests and Syntax Checks

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app.py venuebite tests
```

Tests cover score calculations and thresholds, invalid/non-finite values, factor orientation, deterministic insights, input validation and escaping, repeat analysis, provider replacement/failure, error responses, and local asset delivery.

## Project Structure

```text
app.py                         Local entry point; exports app for Flask CLI
venuebite/
    __init__.py                App factory, configuration, errors, headers
    routes.py                  GET/POST handling and form validation
    scoring.py                 Factor definitions, weights, score and insights
    services/
        __init__.py            Structured data and provider contract
        analysis_service.py    Provider-to-scoring orchestration
        mock_data_service.py   Immutable fictional fixture
templates/
    base.html                  Application shell and navigation
    _icons.html                Local icon macro
    _search_form.html          Shared POST form and validation feedback
    index.html                 Initial/error workspace
    results.html               Analysis report
static/
    css/style.css              Responsive workspace styles
    js/main.js                 Submission state and error focus
    icons/                     Local Lucide assets and license
tests/                         Scoring, routes, and provider tests
prompts/01-full-stack-mvp.md    Sprint requirements
requirements.txt               Runtime dependency
requirements-dev.txt           Test dependency
.env.example                   Optional CLI settings; no secrets
```

## Architecture and Scoring

`create_app(config=None, data_provider=...)` builds independent Flask app instances. Routes validate requests, call `AnalysisService`, and render Jinja templates. The analysis service calls a provider's `get_location_data(location, concept)` method and passes its factor scores to the scoring engine. Templates receive a structured report and do not calculate scores. A future provider can replace `MockLocationDataService` without changing routes or templates, provided it returns the same `LocationData` contract.

The scoring engine accepts exactly four numeric, finite factor scores in the inclusive range 0-100. It rejects booleans, strings, missing/unknown factors, and out-of-range values. Centralized definitions assign population and income 30% each, and rent and competition 20% each. This preserves the prototype's calculation:

```text
85 * 0.30 + 80 * 0.30 + 55 * 0.20 + 60 * 0.20 = 72.5
```

Higher scores always mean better opportunity. In particular, a high **rent score** means more affordable occupancy costs, and a high **competition score** means less direct competitive pressure. These are normalized opportunity factors, not raw prices or restaurant counts. The fixture's raw display metrics are illustrative; this sprint does not normalize those metrics into scores.

Scores are rounded to one decimal before classification. Classifications are Strong opportunity at 80+, Promising opportunity at 65+, Mixed opportunity at 50+, and Challenging opportunity below 50. Individual factors produce strengths at 75+ and risks below 65. Scores from 65 through below 75 produce neither. This uses explicit, deterministic rules rather than generated claims.

Form limits are 200 characters for location and 120 for concept. Whitespace is normalized, duplicate fields and remaining control characters are rejected, and the request body is capped at 16 KiB. Jinja escapes user input. The app has no accounts, saved state, sessions, or external credentials in this phase. Error responses hide internal exception details.

## Visual Assets

Icons are locally vendored from [Lucide 0.468.0](https://github.com/lucide-icons/lucide/tree/0.468.0), with the upstream license in `static/icons/LICENSE`. No external fonts or runtime CDN are needed.

## Roadmap

1. **Sprint 01:** Application-first MVP using explicitly labeled demo data.
2. **Recommended next sprint:** Geocoding and an actual interactive map, with server-side provider configuration and failure handling.
3. Real nearby restaurants and businesses, then real demographic/economic data.
4. Review and calibrate scoring against real source data.
5. Persistence, saved analyses, and authentication when those workflows are needed.
6. Comparisons, Find an Area, and optional AI explanations grounded in collected data.
7. Deployment, Docker, CI/CD, monitoring, and production hardening.

Sprint 01 does not implement these later phases.
