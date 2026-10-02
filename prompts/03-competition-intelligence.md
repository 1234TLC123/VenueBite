# Sprint 03 — Real Competition Intelligence

You are working inside the existing VenueBite repository.

VenueBite is a Flask/Jinja full-stack restaurant location-intelligence product.

Sprint 01 established the full-stack application architecture, scoring engine, mock market-data service, tests, and application dashboard.

Sprint 02 added:
- real Mapbox geographic search
- real normalized locations
- real coordinates
- interactive Mapbox map
- satellite mode
- location-provider abstraction
- geography service
- redesigned location-intelligence dashboard
- clear separation between real geographic data and demo market data

Sprint 02 is complete and committed.

The application currently has approximately 175 passing tests.

Sprint 03 must build on that architecture.

Do NOT rebuild VenueBite from scratch.

---

# CRITICAL STARTING PROCEDURE

Before changing anything:

1. Read `AGENTS.md` completely.
2. Read `prompts/03-competition-intelligence.md` completely.
3. Inspect the repository structure.
4. Run:

   git status
   git branch --show-current
   python -m pytest

5. Inspect:
   - existing provider architecture
   - geography service
   - scoring module
   - analysis service
   - Mapbox integration
   - results templates
   - map JavaScript
   - current mock competition data

Understand how Sprint 02 works before modifying it.

Do not assume architecture from the prompt if the repository contains a cleaner equivalent.

---

# GIT RULES

DO NOT:

- commit
- push
- create branches
- reset existing work
- delete unrelated functionality

At completion, show `git status`.

Chris will review and commit manually.

---

# SPRINT 03 PRODUCT GOAL

Replace VenueBite's fake nearby-competition information with real nearby restaurant/POI information around the selected candidate location.

A VenueBite analysis should now conceptually work like:

User selects location
        ↓
Mapbox resolves real coordinates
        ↓
User selects restaurant concept
        ↓
VenueBite queries nearby restaurant POIs
        ↓
Competition service normalizes results
        ↓
VenueBite evaluates observed competition pressure
        ↓
Real competition factor replaces demo competition factor
        ↓
Opportunity score recalculates
        ↓
Dashboard displays:
    - nearby restaurants
    - direct competitors
    - distances
    - competition score
    - competition explanation
    - competitor markers on map
        ↓
Other factors remain explicitly demo data

Sprint 03 makes ONE market-analysis factor real:

COMPETITION.

Do not make population, income, rent, demographics, traffic, property costs, or demand appear real yet.

---

# DATA PROVIDER

Use Mapbox Search Box / POI functionality for Sprint 03.

Do not introduce Google Places.

Do not introduce Foursquare or another provider unless the existing Mapbox implementation fundamentally cannot support the required functionality.

Keep provider architecture modular so another POI provider can replace or supplement Mapbox later.

Mapbox should be treated as an external provider, not embedded throughout VenueBite business logic.

---

# IMPORTANT DATA LIMITATION

Mapbox category/POI searches may return only a limited set of nearby results.

Do NOT present returned POIs as an exhaustive census of every restaurant in the area.

Do NOT say:

"There are exactly 17 restaurants within 3 miles."

Prefer language such as:

"17 nearby restaurant results observed"

or:

"17 restaurants returned in the current nearby-search sample"

Include an appropriate coverage note.

Do not imply that the provider represents complete market saturation or exact market share.

---

# STORAGE / LICENSING RULE

Treat Mapbox Search Box POI results as live/ephemeral provider data.

Do not persist raw Mapbox Search Box result content to a database.

Do not build a POI database.

Do not create long-term disk caching of provider POI responses unless explicitly permitted by current provider terms.

Request-scope processing is fine.

The application currently has no persistence requirement for Sprint 03.

---

# PROVIDER ARCHITECTURE

Add or extend a POI/business provider abstraction.

A reasonable architecture would be:

venuebite/
    providers/
        location_provider.py
        mapbox_provider.py

        poi_provider.py
        mapbox_poi_provider.py

or another structure that fits the current repository more cleanly.

The architecture should separate:

1. Provider HTTP/API logic
2. Provider-response normalization
3. Competition analysis
4. Overall VenueBite scoring
5. UI rendering

Do not put Mapbox response parsing directly inside Flask routes.

---

# NORMALIZED POI MODEL

The rest of VenueBite should work with normalized POI objects rather than raw Mapbox JSON.

Create a normalized representation conceptually similar to:

{
    "provider_id": "...",
    "name": "Restaurant Name",
    "latitude": 39.739,
    "longitude": -104.990,
    "address": "123 Main St",
    "categories": [
        "restaurant",
        "indian_restaurant"
    ],
    "distance_meters": 850,
    "operational_status": "active",
    "provider": "mapbox"
}

Include fields only when reliably supported.

Normalize missing fields safely.

Do not crash when:
- address is absent
- categories are absent
- status is absent
- provider ID is absent
- distance is absent
- coordinates are malformed

Coordinate validation remains mandatory.

---

# DISTANCE CALCULATION

VenueBite should calculate geographic distance between the candidate location and each competitor itself.

Implement a tested Haversine or equivalent geodesic-distance utility.

Use normalized candidate coordinates and POI coordinates.

Do not rely exclusively on provider result ordering.

Store/display distance in a user-friendly format such as:

0.4 mi
1.2 mi
3.0 mi

Internally, keep a consistent unit such as meters.

If VenueBite already has an appropriate distance utility, reuse it.

---

# NEARBY SEARCH

Search around the selected candidate location.

Use the selected real coordinates from Sprint 02.

The provider layer should support a configurable search radius.

Recommended initial UX:

- 1 mile
- 3 miles
- 5 miles

Use a sensible default, such as 3 miles.

If implementing the selector significantly harms the existing architecture, a centrally configured default radius is acceptable, but the architecture must support changing it later.

After receiving provider results:

1. normalize them
2. calculate actual distance
3. remove malformed results
4. remove obvious duplicates
5. filter results to the selected radius
6. sort by distance

Do not assume every provider result is actually within the intended radius without validating it.

---

# RESTAURANT CONCEPT MATCHING

VenueBite should distinguish:

## Direct competitors

Restaurants reasonably matching the user's selected concept.

Examples:

Indian restaurant
Mexican restaurant
Coffee shop
Pizza restaurant
Burger restaurant

## General nearby restaurant environment

Restaurants that are nearby but do not necessarily match the concept.

This distinction is important.

A Mexican restaurant should not automatically be treated as an equally direct competitor to an Indian restaurant simply because both are restaurants.

---

# CONCEPT-TO-PROVIDER MAPPING

Do not scatter cuisine/category mappings throughout the code.

Centralize concept normalization.

Examples may conceptually map:

"Indian restaurant"
    → Mapbox documented Indian restaurant category

"Pizza restaurant"
    → documented pizza category if available

"Coffee shop"
    → documented coffee/cafe category if available

However:

DO NOT INVENT MAPBOX CATEGORY IDS.

Only use documented provider categories.

If a precise canonical category is not available, use a safe fallback.

For concepts not cleanly represented by a documented Mapbox category, such as:

"Congolese restaurant"

VenueBite may use a text-based POI search near the candidate coordinates.

If concept-specific matching is approximate, communicate that internally and/or in the UI.

Do not pretend an approximate text match is an authoritative cuisine classification.

---

# PROVIDER QUERY STRATEGY

Build the provider so it can support:

A. Generic nearby restaurant discovery

and

B. Concept-specific competitor discovery

Avoid unnecessary duplicate API calls.

Deduplicate POIs returned by multiple searches.

Prefer provider IDs where available.

If IDs are missing, use a conservative combination such as normalized name + coordinates.

Do not make one provider request per competitor.

---

# COMPETITION SERVICE

Create a dedicated competition-analysis service.

A reasonable structure:

venuebite/
    services/
        geography_service.py
        competition_service.py

Its responsibilities should include:

- receiving candidate location
- receiving restaurant concept
- invoking POI provider
- normalizing/deduplicating results
- filtering by radius
- identifying direct competitors
- ordering competitors by distance
- producing competition metrics
- producing data required by the competition score
- producing user-facing competition insights

Do not put this logic in Flask routes.

---

# REAL COMPETITION METRICS

Generate useful metrics such as:

- nearby restaurants observed
- direct competitors observed
- nearest direct competitor
- nearest restaurant
- average direct-competitor distance where meaningful
- selected search radius
- competition pressure classification

Examples:

Nearby restaurants observed: 18
Direct competitors observed: 4
Nearest direct competitor: 0.6 mi
Search radius: 3 mi

Do not calculate misleading metrics when there is insufficient data.

---

# COMPETITION SCORE

Sprint 03 should replace the MOCK competition factor with a REAL competition factor derived from observed live POI data.

Preserve the current VenueBite semantic convention:

HIGHER COMPETITION SCORE = MORE FAVORABLE COMPETITIVE CONDITIONS / LOWER OBSERVED COMPETITION PRESSURE.

For example:

90 = relatively low observed pressure
60 = moderate observed pressure
25 = relatively high observed pressure

Do not reverse this semantic convention.

---

# COMPETITION SCORING DESIGN

Create a deterministic, transparent Version 1 competition-scoring algorithm.

Do not use AI for scoring.

Do not use a hidden arbitrary formula inside a template.

The scoring logic must live in a tested backend module/service.

The algorithm should reasonably consider:

- number of direct competitors
- proximity of direct competitors
- general nearby restaurant density
- closeness of competitors

Closer direct competitors should generally contribute more competition pressure than distant restaurants.

Direct competitors should generally matter more than unrelated restaurant concepts.

Keep constants centralized and named.

For example, if distance bands or weights are used, define them clearly rather than scattering magic numbers.

Do not pretend this is a scientifically validated market model.

Document it as:

"VenueBite Competition Model v1"

or similar.

---

# SCORING TRANSPARENCY

The UI should explain why the competition score exists.

Example:

Competition Score
68 / 100

Observed pressure: Moderate

4 direct competitors found
Nearest direct competitor: 0.6 mi
18 nearby restaurant results observed

Why this score:
- Several restaurants operate nearby
- Four appear closely related to this concept
- Two direct competitors are within one mile

The actual language should be generated deterministically from structured data.

Do not use an LLM.

---

# ZERO-RESULT BEHAVIOR

A provider returning zero results must not be interpreted as proof that there are literally zero restaurants.

Use wording such as:

"No nearby restaurant results were returned by the provider for this search."

Do not say:

"There are no restaurants nearby."

The competition score may reflect low observed competition, but the UI must retain the coverage disclaimer.

---

# EXISTING OVERALL OPPORTUNITY SCORE

The existing VenueBite scoring engine should continue to own overall scoring.

Do not move overall scoring into competition_service.py.

When real competition data succeeds:

- population remains demo
- income remains demo
- rent remains demo
- competition becomes real

Then recalculate the overall VenueBite score using the existing scoring weights and the new real competition score.

Do not silently change population/income/rent weights.

Do not silently change the overall scoring formula.

---

# HYBRID ANALYSIS LABEL

Once Sprint 03 succeeds, the overall analysis is no longer purely demo and no longer fully real.

Clearly describe it as something like:

Hybrid analysis

REAL:
- geographic location
- nearby restaurant POIs
- competition factor

DEMO:
- population factor
- income factor
- rent factor

The UI must communicate this without cluttering the dashboard.

Do not label the entire VenueBite Opportunity Score as fully verified real-world analysis.

---

# PROVIDER FAILURE

If POI retrieval fails:

DO NOT silently replace it with fake competition data while pretending the factor is real.

Choose a transparent fallback.

Acceptable behavior:

- display competition data as unavailable
- explain that live competition data could not be retrieved

If preserving the previous mock overall score is necessary for application continuity, label it clearly:

"Demo analysis — live competition unavailable"

Never present a mock competition score as a successful real-data result.

---

# MAP INTEGRATION

Extend the Sprint 02 map.

Keep the primary candidate-site marker visually distinct.

Add nearby restaurant/competitor markers.

Differentiate at minimum:

- candidate location
- direct competitor
- other nearby restaurant

Markers must remain readable on:
- standard map
- satellite map

Clicking/tapping a competitor marker should provide useful information such as:

- restaurant name
- distance
- address where available
- category/concept relationship

Do not expose raw provider JSON.

---

# MAP PERFORMANCE

There may be up to roughly a few dozen nearby POIs.

Avoid unnecessary map re-renders.

Do not recreate the entire Mapbox instance for every small state change.

Update marker layers/data cleanly.

If clustering provides meaningful benefit and can be implemented simply, it may be used.

Do not overengineer clustering for fewer than a few dozen markers.

---

# NEARBY COMPETITION UI

Replace Sprint 02's fake competition cards/list with real POI results.

A useful section might show:

Nearby Competition

[4 direct] [18 nearby] [0.6 mi nearest]

Direct Competitors

1. Spice House
   Indian Restaurant
   0.6 mi

2. Bombay Kitchen
   Indian Restaurant
   1.2 mi

Nearby Restaurant Environment

...

Keep the design consistent with the Sprint 02 visual system.

Avoid giant cards for every competitor.

The dashboard should remain information-dense and usable.

---

# COMPETITOR SORTING

Default sorting should prioritize useful market context.

For direct competitors:

1. closest distance
2. stable secondary ordering

For general nearby restaurants:

distance is an appropriate initial sort.

Do not invent ranking based on business quality unless ratings/reviews are actually available and intentionally incorporated.

---

# RATINGS / REVIEWS / PRICING

Do not require ratings, reviews, popularity, or price-level information for Sprint 03.

If Mapbox provides a field reliably and within the current endpoint/product terms, it may be displayed conservatively.

Do not make scoring depend on fields that are inconsistently available.

Do not scrape external review platforms.

---

# CLOSED BUSINESSES

Prefer active/open POIs.

Do not intentionally include permanently closed competitors in the active competition score.

If provider status is unavailable, do not guess.

---

# FRONTEND STATE CONSISTENCY

Sprint 02 established that:

- search field
- normalized location
- result heading
- coordinates
- location card
- map marker

must refer to the same selected location.

Preserve that guarantee.

Sprint 03 must ensure competition data is always tied to the SAME candidate coordinates currently being analyzed.

Do not display stale competitor results when the user changes location.

When a new analysis begins:

- show loading state
- clear or visually invalidate stale competition data
- update competitor markers only when current analysis results arrive

---

# USER EXPERIENCE

When analysis is running, communicate that VenueBite is retrieving nearby competition.

Use clean loading states.

Examples:

"Analyzing nearby restaurant competition..."

Do not freeze the interface.

If POI analysis fails but geography works, the map should still work.

---

# DATA SOURCE LABELING

Display the source appropriately.

Examples:

"Live nearby-place data via Mapbox"

or:

"Competition snapshot powered by Mapbox"

Do not over-brand the interface.

Comply with required provider attribution.

---

# SECURITY

Continue the existing security baseline.

Use the existing:

MAPBOX_ACCESS_TOKEN

environment variable.

Do not add the real token to:

- source
- JavaScript literals
- templates as hardcoded content
- README
- tests
- prompts
- commits

Do not log access tokens.

Do not accept `sk.` server-secret tokens into browser-rendered configuration.

Continue validating all external provider data.

---

# API FAILURE HANDLING

Handle at least:

- request timeout
- connection failure
- HTTP error
- rate limiting
- malformed JSON
- missing feature collection
- malformed coordinates
- missing names
- unexpected provider fields
- empty result collection
- invalid category/query
- unavailable token/configuration

The application must fail gracefully.

Do not expose raw provider error bodies to users.

Development logging may contain sanitized diagnostic information.

Never log tokens.

---

# HTTP TIMEOUTS

All server-side external HTTP calls must have explicit timeouts.

Do not create requests that can hang Flask indefinitely.

Keep timeout values centralized/configurable.

---

# REQUEST VOLUME

Avoid wasteful provider calls.

Do not search on every character typed for competition.

Competition search happens after a user has selected a real candidate location and requests analysis.

Reuse the normalized selected location.

Do not geocode the same selected location again unnecessarily.

---

# TESTING

All previous tests must remain green.

Use:

python -m pytest

on this Windows project.

Do not rely on plain `pytest` if its import-path behavior differs.

Add meaningful tests for Sprint 03.

Tests must NOT make live Mapbox API requests.

Mock provider calls.

Test areas should include:

- normalized POI response
- malformed POI response
- duplicate POIs
- invalid coordinates
- distance calculation
- radius filtering
- direct-competitor classification
- concept normalization
- unknown concept fallback
- provider failure
- empty result handling
- competition score boundaries
- higher pressure produces lower competition score
- closer direct competitors increase pressure
- unrelated restaurants affect pressure less than direct competitors
- successful hybrid analysis
- competition unavailable state
- route behavior
- stale location/competition mismatch prevention where practical

Tests must remain deterministic.

---

# SCORING TEST REQUIREMENTS

Competition score must always remain in:

0 <= competition_score <= 100

Test extreme cases.

Test zero returned results.

Test many close competitors.

Test many distant competitors.

Test direct vs general restaurant weighting.

Do not optimize tests for one exact sample dataset unless necessary.

---

# MOCK DATA CLEANUP

Remove the fake nearby restaurant list from production analysis behavior once real POI data is functioning.

Do not delete mock provider infrastructure required by tests or future development unless it is genuinely obsolete.

Population, income, and rent should remain demo data for Sprint 03.

Ensure their UI labels still say demo.

---

# README

Update README with:

- Sprint 03 overview
- real competition functionality
- Mapbox POI/Search Box dependency
- architecture overview
- competition model v1 explanation
- real-vs-demo factor table
- provider limitations
- search-result coverage limitation
- environment setup
- how to run

  python app.py

- how to test

  python -m pytest

- known limitations
- no persistent POI storage
- future roadmap

Do not place real credentials in README.

---

# UI QUALITY

Preserve the strong Sprint 02 visual design.

Sprint 03 should look like an extension of the existing product, not another redesign.

Focus visual work on:

- competition metrics
- nearby competitor list
- competitor markers
- analysis explanation
- loading/error states

Do not redesign unrelated sections just because they can be redesigned.

---

# PERFORMANCE

Do not introduce unnecessary heavy dependencies.

Prefer existing dependencies and Python standard library utilities where appropriate.

If adding an HTTP dependency, first check whether the repository already uses an appropriate client.

Avoid unnecessary JavaScript frameworks.

No React.

---

# DO NOT BUILD IN SPRINT 03

Do not implement:

- Census demographics
- real population data
- real income data
- real rent/property-cost data
- property listings
- commercial real estate
- zoning
- permits
- regulations
- restaurant licensing
- traffic data
- foot-traffic data
- parking intelligence
- database persistence
- saved analyses
- authentication
- accounts
- AI recommendations
- LLM integration
- chatbot
- payments
- subscriptions
- Docker
- cloud deployment
- React
- Google Places

Keep Sprint 03 focused on REAL COMPETITION INTELLIGENCE.

---

# ACCEPTANCE SCENARIOS

Manually verify at least several materially different locations/concepts.

Examples:

Denver, CO
Indian restaurant

Miami, FL
Cuban restaurant

Chicago, IL
Pizza restaurant

New York, NY
Coffee shop

Greeley, CO
Mexican restaurant

Also test a less-common concept such as:

Denver, CO
Congolese restaurant

For every successful case verify:

- selected location remains correct
- map remains centered correctly
- candidate marker remains correct
- nearby POI data belongs to that location
- competitor markers appear
- direct competitors are distinguishable
- distances are plausible
- competition metrics update
- competition score updates
- score remains 0-100
- overall VenueBite score recalculates
- population/income/rent remain demo
- competition is labeled real
- no stale results from previous location remain

Do not hardcode expected business names because provider data can change.

---

# ACCEPTANCE CRITERIA

Sprint 03 is complete only when:

1. Sprint 01 functionality remains intact.

2. Sprint 02 location search/map remains intact.

3. Real restaurant POIs are retrieved around the selected candidate coordinates.

4. Nearby results are normalized through a provider abstraction.

5. Real competitor markers appear on the map.

6. Direct competitors are distinguished from general nearby restaurants.

7. Distances are calculated and displayed.

8. Nearby results are filtered to the configured radius.

9. Duplicate results are handled.

10. Competition score uses real observed competition data.

11. Higher observed pressure produces a lower competition score.

12. Existing overall score uses the real competition factor when available.

13. Population remains demo.

14. Income remains demo.

15. Rent remains demo.

16. The UI clearly labels the analysis as hybrid.

17. Provider failure does not silently turn into fake competition data.

18. Zero results are described accurately rather than treated as proof that no restaurants exist.

19. Mapbox result limitations are communicated.

20. External calls have explicit timeouts.

21. No real Mapbox token is committed.

22. No Search Box POI database/persistence is added.

23. Existing tests pass.

24. New tests pass.

25. Application runs with:

    python app.py

26. Full test suite runs with:

    python -m pytest

27. `git status` is shown at completion.

28. Codex does NOT commit or push.

---

# FINAL VERIFICATION

Before declaring Sprint 03 complete:

1. Run:

   python -m pytest

2. Run the application.

3. Check several locations and restaurant concepts.

4. Verify direct competitor markers.

5. Verify general restaurant markers.

6. Verify map and satellite modes.

7. Verify competition score changes between locations where returned data differs.

8. Verify the overall score recalculates.

9. Verify demo labels remain on population/income/rent.

10. Test missing Mapbox configuration.

11. Test provider failure handling.

12. Inspect browser console.

13. Inspect Flask/server logs.

14. Inspect `git diff`.

15. Inspect `git status`.

16. Confirm `.env` remains ignored.

17. Search staged/tracked files for accidental credentials.

18. Confirm no unrelated features were removed.

DO NOT COMMIT.

DO NOT PUSH.

---

# FINAL RESPONSE

When finished, report:

1. What was implemented.
2. Files created.
3. Files modified.
4. Provider architecture.
5. Competition model v1 design.
6. How direct competitors are classified.
7. How distance is calculated.
8. How provider-result limitations are handled.
9. How real vs demo data is labeled.
10. Test results.
11. Manual test results.
12. Known limitations.
13. Current `git status`.
14. Anything Chris must configure or manually verify.

Do not commit or push.