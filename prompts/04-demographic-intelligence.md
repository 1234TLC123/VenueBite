# Sprint 04 — Real Census Demographic Intelligence

You are working inside the existing VenueBite repository.

VenueBite is a production-oriented Flask/Jinja restaurant location-intelligence application.

Sprint 01 established:
- Flask/Jinja application architecture
- scoring engine
- services
- mock market data
- testing foundation

Sprint 02 established:
- real Mapbox location search
- normalized geographic locations
- real coordinates
- interactive map
- satellite view
- provider abstraction
- geographic services
- professional application dashboard

Sprint 03 established:
- real nearby restaurant/POI discovery
- direct competitor classification
- real competition factor
- competition scoring
- competitor map markers
- search-radius controls
- hybrid analysis
- 312 passing tests

Sprint 03 is complete, committed, and pushed.

Sprint 04 must extend the existing architecture rather than rebuild it.

======================================================================
SPRINT 04 PRIMARY GOAL
======================================================================

Replace VenueBite's fake POPULATION and INCOME information with real
U.S. Census Bureau ACS 5-year demographic data tied to the selected
candidate location.

After Sprint 04, VenueBite should have:

REAL DATA
- selected geographic location
- latitude / longitude
- interactive map
- nearby restaurant POIs
- competition factor
- local population
- median household income
- Census geography metadata
- Census source/vintage metadata

DEMO DATA
- commercial rent / occupancy factor
- any area metrics for which no real provider exists yet

The application remains a HYBRID analysis.

Do not pretend VenueBite has become a fully real market-feasibility
model yet.

======================================================================
CRITICAL STARTING PROCEDURE
======================================================================

Before editing anything:

1. Read AGENTS.md completely.
2. Read this entire Sprint 04 prompt.
3. Inspect the current repository.
4. Run:

   git status
   git branch --show-current
   python -m pytest

5. Confirm the current test baseline.

6. Inspect at minimum:

   venuebite/__init__.py
   venuebite/routes.py
   venuebite/scoring.py
   venuebite/services/analysis_service.py

   existing provider modules
   existing geography services
   competition service
   competition scoring
   results templates
   map JavaScript
   .env.example
   README.md

7. Understand Sprint 01–03 architecture before changing code.

Do not assume this prompt's suggested filenames are better than an
existing clean abstraction. Preserve established patterns where they
already solve the problem well.

======================================================================
GIT RULES
======================================================================

DO NOT:

- commit
- push
- create a new branch
- reset the repository
- modify Git history
- delete unrelated functionality
- stage files automatically unless needed temporarily for a requested
  verification step

Chris will review the completed sprint manually.

======================================================================
AUTHORITATIVE DATA SOURCES
======================================================================

Use official U.S. Census Bureau services.

Primary demographic source:

U.S. Census Bureau
American Community Survey
2024 ACS 5-Year Detailed Tables

API dataset:

/data/2024/acs/acs5

As of this sprint, 2024 is the current ACS 5-year release available
through the Census API.

Centralize the ACS vintage in configuration.

Do NOT scatter "2024" throughout the codebase.

For example:

CENSUS_ACS_YEAR = 2024

or an equivalent configuration approach.

Before implementation, verify endpoint behavior and variable definitions
against current official Census documentation.

Do not use blogs or third-party copies as the authority for Census
variables.

======================================================================
API KEY
======================================================================

Read the Census API key only from:

CENSUS_API_KEY

The key must remain server-side.

Never expose it through:

- browser JavaScript
- rendered HTML
- data attributes
- public configuration objects
- logs
- tests
- screenshots
- README examples
- prompt files

.env must remain ignored by Git.

.env.example should contain only:

MAPBOX_ACCESS_TOKEN=your_mapbox_access_token_here
CENSUS_API_KEY=your_census_api_key_here

Missing Census configuration must NOT prevent Flask from starting.

======================================================================
CENSUS VARIABLES
======================================================================

Use documented ACS variables.

Required:

B01003_001E
Total population estimate

B19013_001E
Median household income in the past 12 months
(in 2024 inflation-adjusted dollars for the 2024 ACS vintage)

Where practical, also retrieve:

B01003_001M
Margin of error for total population

B19013_001M
Margin of error for median household income

Do not invent variable IDs.

Do not silently substitute different variables without documenting the
decision.

Keep Census variable IDs centralized.

For example:

POPULATION_ESTIMATE = "B01003_001E"
POPULATION_MOE = "B01003_001M"
HOUSEHOLD_INCOME_ESTIMATE = "B19013_001E"
HOUSEHOLD_INCOME_MOE = "B19013_001M"

======================================================================
IMPORTANT: COMMERCIAL RENT
======================================================================

DO NOT replace VenueBite's commercial rent factor with ACS residential
rent data.

Residential rent is not restaurant commercial occupancy cost.

The existing commercial rent / occupancy factor remains DEMO in
Sprint 04.

The interface must continue to label it as demo data.

Do not use:

median gross residential rent
housing rent
mortgage cost

as substitutes for restaurant lease economics.

Commercial occupancy intelligence belongs in a later sprint with an
appropriate commercial-property source.

======================================================================
COORDINATE → CENSUS GEOGRAPHY RESOLUTION
======================================================================

Mapbox already provides the selected candidate latitude and longitude.

Reuse those coordinates.

Do NOT re-geocode the typed location.

Resolve the coordinates to Census geography through an authoritative
Census geography service.

Preferred approach:

Census Geocoder Geographic Lookup using coordinates.

Conceptually:

Mapbox selected location
        ↓
latitude + longitude
        ↓
Census coordinate geography lookup
        ↓
state FIPS
county FIPS
tract
additional geography metadata where available
        ↓
ACS 5-year query

The Census Geocoder supports coordinate geographic lookup through its
geographies/coordinates flow.

Use the Census-provided benchmark/vintage system correctly.

Do not guess benchmark/vintage IDs.

Use documented values or resolve them through the official discovery
endpoints where appropriate.

The geography vintage used for tract resolution should be compatible
with the ACS geography vintage being queried.

======================================================================
GEOGRAPHY PROVIDER ARCHITECTURE
======================================================================

Do not put Census API calls inside routes.py.

Introduce clean provider boundaries.

A reasonable structure is:

venuebite/
    providers/
        demographic_provider.py
        census_demographic_provider.py
        census_geography_provider.py

    services/
        demographic_service.py

The exact filenames may differ if the existing provider architecture
suggests a cleaner design.

Required separation:

Census geography provider
    coordinate → Census geography

Census demographic provider
    geography → ACS estimates

Demographic service
    orchestration
    validation
    scoring inputs
    availability/fallback state

Scoring modules
    deterministic population/income score calculations

Routes
    HTTP request/response handling only

Templates
    rendering only

======================================================================
NORMALIZED CENSUS GEOGRAPHY
======================================================================

Never pass raw Census Geocoder JSON throughout the application.

Normalize the geography.

Conceptual example:

{
    "country": "US",
    "state_fips": "08",
    "county_fips": "031",
    "tract": "002801",
    "geoid": "08031002801",
    "state_name": "Colorado",
    "county_name": "Denver County",
    "geography_level": "tract",
    "provider": "census"
}

Only include fields actually returned or safely derived.

Validate FIPS formats.

State FIPS:
2 digits

County FIPS:
3 digits

Tract:
6 digits where applicable

Do not crash if optional geography fields are missing.

======================================================================
NORMALIZED DEMOGRAPHIC RESULT
======================================================================

The application should operate on a normalized model rather than raw
Census table arrays.

Conceptual structure:

{
    "status": "available",
    "population": 5234,
    "population_moe": 418,
    "median_household_income": 81250,
    "median_household_income_moe": 9200,
    "geography_name": "...",
    "geography_level": "tract",
    "geoid": "...",
    "state_name": "Colorado",
    "county_name": "Denver County",
    "acs_year": 2024,
    "dataset": "ACS 5-Year",
    "provider": "U.S. Census Bureau"
}

Do not require every optional field.

Create an explicit unavailable/error state rather than using fake values.

======================================================================
CENSUS RESPONSE PARSING
======================================================================

Census Data API results may be array-oriented.

Parse them centrally.

Do not make templates understand Census array positions.

Handle:

- missing headers
- missing rows
- extra fields
- invalid numbers
- null values
- empty strings
- Census annotation/sentinel values
- estimates marked unavailable/not applicable

Census uses special negative values for some unavailable or
non-applicable estimates.

Do not accidentally treat values such as large negative Census sentinel
numbers as real population or income.

Create explicit parsing/validation utilities.

======================================================================
GEOGRAPHY LEVEL
======================================================================

Use Census TRACT as the primary local demographic context for Sprint 04.

Why:

VenueBite evaluates specific restaurant locations and citywide values
are usually too broad.

However:

A Census tract is NOT the restaurant's exact trade area.

The UI and README must make this clear.

Use wording such as:

"Census tract demographic context"

Do not say:

"People within walking distance"
"Customers around this restaurant"
"Exact neighborhood population"

unless the data actually supports those claims.

======================================================================
TRADE-AREA LIMITATION
======================================================================

This requirement is important.

A single tract is only a local demographic proxy.

Do NOT describe tract population as the exact number of potential
customers.

Do NOT describe it as a restaurant's total addressable market.

Future VenueBite versions may build drive-time or radius-based
multi-geography trade areas.

Sprint 04 does not need to implement those yet.

Document this limitation clearly.

======================================================================
POPULATION GROWTH
======================================================================

Do NOT calculate fake or statistically weak year-over-year growth by
comparing adjacent overlapping ACS 5-year vintages such as:

2023 ACS 5-year
vs
2024 ACS 5-year

Those periods overlap heavily.

If growth is implemented in Sprint 04, use a method consistent with
official ACS comparison guidance.

For the 2020–2024 ACS 5-year estimates, an appropriate comparison may
use a non-overlapping earlier ACS 5-year period such as 2015–2019,
subject to geographic and variable comparability.

Before implementing tract-level growth:

- verify tract geography comparability
- verify variable comparability
- document both periods
- do not silently compare changed tract boundaries

If reliable comparable growth cannot be established cleanly:

DO NOT IMPLEMENT POPULATION GROWTH YET.

Show:

"Population growth: unavailable"

or remove the demo growth value from the real demographic section.

Never keep a fake +1.8% value while making the section appear real.

Growth is optional for Sprint 04.

Correctness is more important than filling the card.

======================================================================
MARGIN OF ERROR / ACS UNCERTAINTY
======================================================================

ACS values are survey estimates.

Preserve margin-of-error information when retrieved.

Sprint 04 does not need a complex statistical-confidence dashboard.

However:

- retain MOE in the normalized model
- make it available for future scoring-quality work
- optionally show a subtle information tooltip
- explain in README that ACS values are estimates

Do not present ACS values as perfectly exact measurements.

Do not penalize or reward score directly from MOE unless intentionally
designed and tested.

======================================================================
POPULATION SCORE
======================================================================

Replace the demo population factor with a REAL Census-derived factor.

Semantic meaning remains:

HIGHER SCORE =
more favorable local population context

Score must always satisfy:

0 <= score <= 100

Create:

VenueBite Population Model v1

Requirements:

- deterministic
- explainable
- backend-owned
- constants centralized
- thoroughly tested
- no AI
- no hidden template math

IMPORTANT:

Raw tract population alone is an imperfect restaurant-demand metric.

Do not label this:

"Demand score"

Prefer:

"Population context score"

or retain "Population" while explaining that it measures demographic
context rather than guaranteed restaurant demand.

The model can use tract population with conservative documented
thresholds for Sprint 04.

If reliable density or other Census-supported context can be added
without unnecessary complexity, it may be incorporated.

Do not invent density from unavailable land-area information.

Do not pretend the model is scientifically validated.

======================================================================
INCOME SCORE
======================================================================

Replace the fake income factor with REAL Census median household income.

Semantic meaning remains:

HIGHER SCORE =
stronger local household purchasing-power context

Create:

VenueBite Income Model v1

Requirements:

0 <= income_score <= 100

The model must be:

- deterministic
- explainable
- centralized
- tested

Avoid scattered magic values.

Document thresholds.

Do not claim:

"Residents will spend more at this restaurant."

Prefer:

"Higher median household income indicates stronger local household
purchasing-power context."

Median household income is context, not guaranteed restaurant spending.

======================================================================
SCORING VERSIONING
======================================================================

Create clear version names/constants.

Examples:

POPULATION_MODEL_VERSION = "v1"
INCOME_MODEL_VERSION = "v1"

Do not version logic through comments alone.

The design should make future scoring calibration possible without
rewriting provider code.

======================================================================
OVERALL VENUEBITE SCORE
======================================================================

The existing VenueBite scoring engine remains authoritative for the
overall opportunity score.

Do not calculate the overall score in:

- templates
- JavaScript
- census provider
- demographic service

On successful Sprint 04 data retrieval:

Population = real Census-derived score
Income = real Census-derived score
Rent = demo
Competition = real observed score

Feed those factor scores into the existing scoring engine.

Preserve current factor weights unless a verified existing bug is found.

Current expected semantics:

Population:
higher = more favorable

Income:
higher = more favorable

Rent:
higher = more favorable / more affordable

Competition:
higher = more favorable / less observed pressure

Do not invert these semantics.

======================================================================
FACTOR PROVENANCE
======================================================================

Each analysis factor should carry provenance.

Conceptually:

population:
    status: real
    provider: census
    vintage: 2024

income:
    status: real
    provider: census
    vintage: 2024

competition:
    status: real
    provider: mapbox

rent:
    status: demo

Avoid determining provenance from UI strings.

Use structured backend state.

This will become important as VenueBite gains more providers.

======================================================================
ANALYSIS STATUS
======================================================================

A successful Sprint 04 result should display something equivalent to:

Hybrid analysis

Real:
- geography
- Census population
- Census household income
- observed competition

Demo:
- commercial rent

Suggested concise banner:

"Hybrid analysis. Real Census demographics and observed competition;
commercial rent remains demo."

Do not claim the full opportunity score is entirely real.

======================================================================
AREA INSIGHTS
======================================================================

Replace fake demographic area insights when Census succeeds.

REAL values:

Population
Median household income
Census geography
ACS vintage
County / state context

Population growth:
real only if properly implemented
otherwise unavailable

Commercial asking rent:
DEMO

Nearby businesses:
use existing real POI data where appropriate

Schools/universities:
do not relabel as real unless currently backed by a real provider

Remove old fake demographic numbers from successful Census analyses.

======================================================================
SOURCE LABELING
======================================================================

Display:

U.S. Census Bureau
ACS 5-Year
2020–2024 / ACS 2024
Census tract context

Avoid clutter.

Example:

Source
U.S. Census Bureau ACS 2024 5-Year
Census tract

The data is not real-time.

Do not describe ACS as current live population.

======================================================================
CENSUS FAILURE BEHAVIOR
======================================================================

If Census retrieval fails:

Mapbox geography must continue working.

Competition must continue working when available.

Never silently substitute demo demographics while labeling them real.

Allowed fallback:

Population:
Demo fallback

Income:
Demo fallback

Banner:

"Live Census demographics unavailable. Population and income are using
demo fallback values."

OR:

mark population/income unavailable if the existing scoring architecture
can support missing factors safely.

Whichever approach is used:

the user must be able to tell exactly which factors are real.

======================================================================
PARTIAL CENSUS DATA
======================================================================

Population may succeed while income is unavailable, or vice versa.

Support partial provider results.

Do not make Census demographics all-or-nothing unnecessarily.

Examples:

Population:
Real Census data

Income:
Unavailable

Competition:
Real observed data

Rent:
Demo

The analysis-status banner should reflect actual factor provenance.

======================================================================
NON-U.S. LOCATIONS
======================================================================

VenueBite's Mapbox architecture is designed for broader geographic
support.

The U.S. Census provider is not.

Detect whether the selected candidate is eligible for U.S. Census
coverage before calling the Census provider where practical.

For a location such as:

Paris, France

Expected behavior:

- Mapbox search works
- map works
- coordinates work
- Census provider does not crash
- no misleading U.S. Census values are displayed
- UI explains U.S. demographic coverage is currently unavailable
- existing non-demographic features continue where supported

Do not hardcode individual countries or cities throughout the code.

Centralize eligibility logic.

======================================================================
HTTP CLIENT BEHAVIOR
======================================================================

All external calls must have explicit timeouts.

Handle:

- timeout
- DNS/network failure
- HTTP errors
- API key failure
- service unavailable
- malformed JSON
- unexpected schema
- empty result
- rate-limit response where applicable

Never expose raw provider error payloads to end users.

Never log API keys.

Use sanitized development logging.

======================================================================
REQUEST EFFICIENCY
======================================================================

Do not call Census:

- on every keystroke
- when autocomplete runs
- every time the map moves
- when switching satellite mode

Run demographic analysis only after an explicit VenueBite analysis.

Reuse the coordinates already selected in Sprint 02.

Avoid duplicate geography lookup calls during the same request.

If demographic service needs multiple ACS variables, request them
together whenever practical.

======================================================================
CACHING
======================================================================

Do not add:

- Redis
- database caching
- persistent Census storage

A small process-local TTL cache may be introduced only if:

- clearly useful
- bounded
- deterministic in tests
- easy to invalidate
- not hiding provider errors

Caching is optional.

Correctness is more important.

======================================================================
FRONTEND STATE CONSISTENCY
======================================================================

Preserve the critical invariant:

search location
result heading
candidate coordinates
map marker
competition results
Census geography
demographic values

must all refer to the SAME analysis.

When the user changes:

- selected location
- restaurant concept
- radius

invalidate stale analysis state appropriately.

Changing restaurant concept does not necessarily require new Census data,
but do not display an old completed report as though it belongs to a
new unsubmitted form state.

======================================================================
UI REQUIREMENTS
======================================================================

Preserve Sprint 02/03 design.

Do not redesign VenueBite again.

Improve only what Sprint 04 requires.

Population factor card:

Population
REAL CENSUS DATA
[value-derived score]

Local population:
[value]

ACS 2024 5-Year
Census tract context

Income factor card:

Income
REAL CENSUS DATA
[value-derived score]

Median household income:
[$value]

ACS 2024 5-Year

Competition card:

Real observed data

Rent card:

Demo data

Use concise badges.

Avoid turning every metric into a giant panel.

======================================================================
ACCESSIBILITY
======================================================================

Maintain:

- semantic HTML
- keyboard usability
- focus states
- contrast
- reduced-motion support
- screen-reader labels where required

Source/provenance information must not rely exclusively on color.

======================================================================
SECURITY
======================================================================

CENSUS_API_KEY is server-only.

Do not:

- send it to frontend JavaScript
- embed it in HTML
- expose it in Flask errors
- expose it in logs
- commit it
- copy it into tests
- put it in documentation

Continue preserving existing Mapbox-token protections.

======================================================================
TESTING
======================================================================

Run all baseline tests first.

Use:

python -m pytest

Do not rely on plain pytest on this Windows setup.

All Sprint 01–03 tests must remain green.

No automated test may make a live Census request.

Mock all Census network calls.

Add comprehensive Sprint 04 coverage.

At minimum test:

Census geography
- valid coordinate lookup
- state FIPS normalization
- county FIPS normalization
- tract normalization
- missing tract
- malformed geography response
- invalid coordinates

Census demographic provider
- successful population + income response
- population only
- income only
- empty response
- malformed headers
- malformed row
- sentinel values
- missing variables
- invalid numeric values
- timeout
- network failure
- HTTP failure
- missing API key

Population scoring
- zero/very low
- low
- moderate
- high
- extreme
- invalid
- unavailable
- always 0–100

Income scoring
- very low
- low
- moderate
- high
- extreme
- invalid
- unavailable
- always 0–100

Analysis integration
- successful demographics
- partial demographics
- Census failure
- demo rent remains demo
- competition remains real
- overall score recalculates
- provenance is correct
- source/vintage is correct
- old mock demographic values do not leak into successful real results

State consistency
- new location invalidates old report
- demographic location matches map location
- demographic GEOID belongs to current result
- no stale Census values appear

Non-U.S.
- Census lookup skipped/fails gracefully
- map continues working
- no U.S. demographic values shown

======================================================================
LIVE MANUAL TESTS
======================================================================

After automated tests pass, manually test real Census integration.

Use several materially different U.S. locations.

Examples:

Denver, Colorado
Indian Restaurant

Greeley, Colorado
Mexican Restaurant

Chicago, Illinois
Pizza Restaurant

Miami, Florida
Cuban Restaurant

New York, New York
Coffee Shop

Verify for every location:

- correct selected location
- correct map
- correct candidate marker
- correct competitor markers
- Census tract resolves
- population changes by geography
- income changes by geography
- population score changes where appropriate
- income score changes where appropriate
- competition remains live
- rent stays demo
- overall score recalculates
- Census source/vintage shown
- no stale previous-location demographics

Also test:

Paris, France

Confirm graceful U.S.-only demographic handling.

======================================================================
POPULATION GROWTH MANUAL RULE
======================================================================

Do not consider Sprint 04 incomplete merely because population growth
is not implemented.

It is better to remove/mark growth unavailable than to calculate a
misleading number from overlapping ACS periods.

If growth is implemented, document exactly:

Current period
Earlier comparison period
Geography level
Comparability assumptions

and test it.

======================================================================
README
======================================================================

Update README with:

- Sprint 04 capabilities
- Census provider architecture
- coordinate → Census geography flow
- ACS API dependency
- CENSUS_API_KEY configuration
- ACS vintage
- exact ACS variables
- Population Model v1
- Income Model v1
- ACS estimate/MOE explanation
- tract-context limitation
- real-vs-demo matrix
- U.S.-only Census limitation
- failure/fallback behavior
- population-growth policy
- commercial-rent disclaimer
- startup command

  python app.py

- testing command

  python -m pytest

Do not include a real API key.

======================================================================
ENVIRONMENT FILE
======================================================================

.env.example should contain:

MAPBOX_ACCESS_TOKEN=your_mapbox_access_token_here
CENSUS_API_KEY=your_census_api_key_here

.env must remain ignored.

Never overwrite Chris's existing .env.

======================================================================
DO NOT BUILD IN SPRINT 04
======================================================================

Do NOT implement:

- commercial property data
- commercial lease pricing
- residential rent as commercial rent
- Zillow integration
- LoopNet scraping
- CoStar scraping
- property listings
- zoning
- permits
- restaurant licenses
- traffic data
- foot traffic
- parking intelligence
- saved analyses
- database persistence
- authentication
- accounts
- AI
- LLMs
- chatbot
- recommendation generation
- Docker
- cloud deployment
- payments
- subscriptions
- React
- Vue
- Angular

Keep Sprint 04 focused on Census demographic intelligence.

======================================================================
ACCEPTANCE CRITERIA
======================================================================

Sprint 04 is complete only when:

1. Sprint 01 functionality remains working.
2. Sprint 02 map/location functionality remains working.
3. Sprint 03 competition functionality remains working.
4. Current coordinates resolve to authoritative Census geography.
5. Candidate Census tract is identified.
6. Real ACS population is retrieved.
7. Real ACS median household income is retrieved.
8. Population factor uses real Census data.
9. Income factor uses real Census data.
10. Competition remains real observed data.
11. Commercial rent remains demo.
12. Overall score recalculates from the updated factors.
13. Factor provenance is structured and accurate.
14. Census source is displayed.
15. ACS vintage is displayed.
16. Census geography level is displayed.
17. MOE is retained where retrieved.
18. Sentinel values are safely handled.
19. Census API failure is handled transparently.
20. Missing Census key does not crash Flask.
21. Partial Census results are handled.
22. Non-U.S. locations do not crash demographic analysis.
23. Census key never reaches browser code.
24. No real credentials are committed.
25. Existing tests pass.
26. New tests pass.
27. App starts with:

    python app.py

28. Test suite runs with:

    python -m pytest

29. UI clearly indicates:

    Real population
    Real income
    Real competition
    Demo commercial rent

30. Population growth is either legitimately calculated or explicitly
    unavailable — never fabricated.

31. git status is shown at completion.

32. Codex does not commit.

33. Codex does not push.

======================================================================
FINAL SECURITY CHECK
======================================================================

Before completion:

Confirm .env remains ignored.

Search tracked/changed files for Census secrets.

Do NOT print the real key while scanning.

Look for accidental hardcoded credential patterns without echoing
environment contents.

Also confirm existing Mapbox credential protections remain intact.

======================================================================
FINAL VERIFICATION
======================================================================

Before declaring Sprint 04 complete:

1. Run:

   python -m pytest

2. Start the application.

3. Perform live U.S. tests.

4. Perform one non-U.S. test.

5. Verify Census geography.

6. Verify real population.

7. Verify real median household income.

8. Verify Census source/vintage.

9. Verify competition still works.

10. Verify map/satellite still work.

11. Verify competitor markers still work.

12. Verify commercial rent remains demo.

13. Verify opportunity score recalculates.

14. Verify no stale results.

15. Inspect browser console.

16. Inspect sanitized server logs.

17. Inspect git diff.

18. Inspect git status.

19. Confirm no secret is tracked.

20. Confirm unrelated features were not rewritten.

DO NOT COMMIT.

DO NOT PUSH.

======================================================================
FINAL REPORT
======================================================================

When finished, report:

1. What Sprint 04 implemented.
2. Files created.
3. Files modified.
4. Census provider architecture.
5. Coordinate-to-Census-geography strategy.
6. ACS endpoint and vintage used.
7. Census variables used.
8. Population Model v1 design.
9. Income Model v1 design.
10. How margins of error are handled.
11. Real/demo provenance matrix.
12. Population-growth decision and why.
13. U.S.-only coverage behavior.
14. Census failure/fallback behavior.
15. Test count and result.
16. Live manual test results.
17. Known limitations.
18. Current git status.
19. Anything Chris must manually verify.

Do not commit.
Do not push.