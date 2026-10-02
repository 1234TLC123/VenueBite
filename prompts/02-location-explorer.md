# Sprint 02 — VenueBite Location Explorer + Product UI Redesign

You are working inside the existing VenueBite repository.

VenueBite is a full-stack restaurant location-intelligence application built with Flask and Jinja.

Sprint 01 is complete and already committed. Do not rebuild the application from scratch.

Your job in Sprint 02 is to transform the current MVP into a polished location-intelligence product with real geographic search and a real interactive Mapbox map while preserving the existing VenueBite scoring and analysis architecture.

## CRITICAL RULES

Before changing any code:

1. Read `AGENTS.md` completely.
2. Inspect the current repository structure.
3. Run:
   - `git status`
   - `git branch --show-current`
   - existing tests
4. Understand the Sprint 01 implementation before editing it.

Do NOT:
- commit
- push
- create branches
- rewrite working architecture unnecessarily
- migrate to React
- add a database
- add authentication
- add Docker
- add AI features
- add commercial property APIs
- add Census/demographic APIs
- add real restaurant competition APIs yet
- hardcode Denver, Colorado, Aurora, or any specific region

This sprint must work with the existing Flask/Jinja architecture.

---

# PRODUCT GOAL

VenueBite should feel like a professional geographic intelligence application.

The user should be able to:

1. Enter a city, neighborhood, ZIP/postcode, landmark, or exact address.
2. Receive real location suggestions.
3. Select a location.
4. See that real location on an interactive Mapbox map.
5. See a marker at the selected location.
6. Switch between a standard VenueBite map and satellite imagery.
7. Choose a restaurant concept.
8. Run VenueBite analysis.
9. See the existing opportunity score, factors, strengths, risks, insights, and competition demo data alongside the real map.

The geographic information should be real.

The existing business-analysis factors may remain mock/demo data for Sprint 02.

Never present mock demographic/business data as verified real-world information.

---

# MAP PROVIDER

Use Mapbox.

Primary technologies:

- Mapbox GL JS for map rendering.
- Mapbox Search / Search Box functionality for user-facing geographic search/autocomplete where practical.
- Mapbox geographic services for resolving locations.
- Existing Flask backend for application logic.

Do not tightly couple the entire application to Mapbox.

Build a provider abstraction so another provider can eventually replace Mapbox without rewriting VenueBite.

---

# PROVIDER ARCHITECTURE

Create or adapt an architecture similar to:

venuebite/
    providers/
        __init__.py
        location_provider.py
        mapbox_provider.py

The exact names may change if the current repository architecture suggests something cleaner.

Responsibilities:

## location_provider.py

Define the interface/contract used by VenueBite for geographic location information.

The rest of the application should work with normalized VenueBite location objects rather than raw Mapbox responses.

## mapbox_provider.py

Implement Mapbox-specific behavior.

Normalize provider responses into something conceptually similar to:

{
    "display_name": "Greeley, Colorado, United States",
    "latitude": 40.4233,
    "longitude": -104.7091,
    "place_type": "place",
    "provider": "mapbox"
}

Include useful fields only when supported.

Do not spread raw Mapbox response parsing throughout routes and templates.

---

# REAL LOCATION SUPPORT

Location search must support broad geographic queries.

Examples that should work where supported by Mapbox:

- Denver, CO
- Greeley, CO
- Miami, FL
- Chicago, IL
- Dallas, TX
- New York, NY
- 10001
- Green Valley Ranch, Denver
- Times Square
- complete street addresses
- intersections where supported

VenueBite must not be Colorado-specific.

Structure the application so international support can be added or enabled later without redesigning the entire location system.

---

# LOCATION SEARCH EXPERIENCE

Replace the primitive location input with a polished geographic search experience.

Requirements:

- location autocomplete/suggestions
- keyboard accessible suggestions
- mouse selection
- loading state
- no-results state
- clear error state
- selected-location state
- ability to change the location
- preserve restaurant concept when changing location where appropriate
- prevent accidental submission when no usable location exists
- graceful fallback if Mapbox fails

Do not make a malformed Mapbox response crash the application.

---

# MAPBOX MAP

Replace the Sprint 01 placeholder map with a real interactive Mapbox map.

Required features:

- real map centered on selected location
- visible candidate-site marker
- zoom controls
- responsive resizing
- smooth camera/fly-to transition
- standard map mode
- satellite mode
- clear selected-location state
- sensible initial/default view before selection
- loading state
- useful error state if map initialization fails

The map should be one of the most visually important parts of the dashboard.

Do not create an oversized empty map with the analysis pushed far below the fold.

---

# MAP STYLE

Create a custom VenueBite map experience.

The product should feel:

- modern
- professional
- geographic
- analytical
- premium
- clean
- futuristic without looking like a game or crypto dashboard

Preferred visual direction:

- deep navy / charcoal surfaces
- restrained accent highlights
- subtle glow only where useful
- strong typography
- clear hierarchy
- compact information density
- sophisticated map styling
- polished hover/focus states
- tasteful transitions
- minimal visual clutter

Do not cover the application in excessive gradients or glassmorphism.

Do not sacrifice readability for aesthetics.

---

# PRODUCT LAYOUT

Redesign the application into an application-first dashboard.

Desktop should conceptually feel similar to:

-------------------------------------------------------------
VenueBite             Analyze     Discover     Compare
-------------------------------------------------------------

Search city, neighborhood, ZIP, address...
Restaurant concept...

-------------------------------------------------------------
Opportunity Score    |                                      |
72.5                 |                                      |
Strong Potential     |            MAPBOX MAP                |
                     |                                      |
Population 85        |            Candidate Site            |
Income 80            |                                      |
Rent 55              |            Map | Satellite           |
Competition 60       |                                      |
-------------------------------------------------------------

Area Insights

Strengths                         Risks

Nearby Competition
DEMO DATA

The exact implementation should be improved beyond this ASCII layout.

Use the existing Sprint 01 information architecture where appropriate rather than deleting useful functionality.

---

# SCORE DISPLAY

Keep the existing scoring engine.

Do not silently change the existing scoring formula just for the redesign.

Make the score visually stronger.

Potential implementation:

- circular score indicator
- progress ring
- animated value
- classification badge
- factor bars

Animations should be restrained and accessible.

Respect `prefers-reduced-motion`.

---

# REAL DATA VS DEMO DATA

This distinction is mandatory.

Real geographic data may include:

- resolved location name
- latitude
- longitude
- map
- Mapbox geographic information

Existing mock data may include:

- population factor
- income factor
- rent factor
- competition factor
- nearby competitor demo records
- opportunity score derived from mock factors
- strengths/risks based on mock factors

The interface must clearly communicate this.

Use wording such as:

"Real location data"

and

"Demo market analysis"

or another polished equivalent.

Do not make the user believe mock demographics or competition values are verified facts.

---

# ENVIRONMENT CONFIGURATION

Add Mapbox configuration safely.

`.env` should support:

MAPBOX_ACCESS_TOKEN=

Do NOT commit `.env`.

Update `.env.example` with:

MAPBOX_ACCESS_TOKEN=your_mapbox_access_token_here

Never place a real token in:

- Python source
- JavaScript source
- templates
- tests
- README examples
- AGENTS.md
- prompt files

A browser Mapbox token may be visible client-side by nature.

Use an appropriately scoped public Mapbox token for browser map rendering.

Document that production tokens should use URL/domain restrictions and minimum required scopes.

Do not expose secret Mapbox tokens intended for server-only operations.

---

# CONFIGURATION FAILURE

If MAPBOX_ACCESS_TOKEN is absent:

- Flask must still start.
- The rest of VenueBite must not crash.
- Show a clear development/configuration message in the map area.
- Tests must continue to work.

Do not require developers to have a real Mapbox token just to run the test suite.

---

# FLASK ARCHITECTURE

Preserve the existing application structure.

Keep concerns separated:

Routes:
- request/response handling

Services:
- analysis orchestration

Providers:
- external geographic provider behavior

Scoring:
- score calculation/classification

Templates:
- presentation

JavaScript:
- map and UI interaction

Do not put all logic into `app.py`.

Do not move scoring logic into templates or frontend JavaScript.

---

# INPUT VALIDATION

Continue server-side validation.

Validate:

- location
- restaurant concept
- latitude if submitted
- longitude if submitted
- provider-generated identifiers where relevant

Latitude must remain within valid geographic bounds.

Longitude must remain within valid geographic bounds.

Do not blindly trust hidden form values sent by the browser.

Handle unexpected provider data safely.

---

# FRONTEND JAVASCRIPT

Organize JavaScript cleanly.

Do not create one giant script containing unrelated functionality.

Use clear functions/modules for things such as:

- map initialization
- map style switching
- selected-location updates
- search behavior
- loading/error states
- score animation if applicable

Avoid unnecessary frontend dependencies.

Use vanilla JS unless the existing project already has a justified dependency.

---

# RESPONSIVE DESIGN

VenueBite must work on:

- desktop
- laptop
- tablet
- mobile

Desktop:
Map and analytical information can appear side by side.

Mobile:
Stack intelligently.

Do not simply shrink the desktop layout.

Map controls and search suggestions must remain usable on touch devices.

---

# ACCESSIBILITY

Include:

- semantic HTML
- keyboard navigation
- visible focus states
- proper labels
- sufficient contrast
- appropriate ARIA where necessary
- reduced-motion support
- buttons instead of clickable divs when appropriate

Autocomplete must be keyboard usable.

---

# ERROR HANDLING

Handle:

- missing Mapbox configuration
- bad location query
- zero search results
- network/API failure
- invalid provider response
- invalid latitude/longitude
- map initialization failure
- unexpected JavaScript error where practical

The user should receive an understandable message.

Do not expose stack traces or provider credentials.

---

# SECURITY

Maintain the existing security baseline.

Do not:

- interpolate unsafe user input into HTML
- disable Jinja escaping
- expose secrets
- log access tokens
- commit `.env`
- trust client-provided geographic values without validation

Review external links/scripts and use official Mapbox resources.

---

# TESTING

Run all existing tests before changes.

Preserve all Sprint 01 tests.

Add meaningful tests for new backend behavior, including where appropriate:

- normalized location data
- valid location provider response
- malformed provider response
- missing configuration
- coordinate validation
- route validation
- provider failure handling

Do not make unit tests depend on live Mapbox requests.

Mock external provider calls.

Avoid brittle tests tied to cosmetic CSS details.

At completion:

pytest

must pass.

If the repository uses another established test command, run that too.

---

# README

Update README with:

- what Sprint 02 added
- Mapbox requirement
- how to obtain/configure a Mapbox token
- environment variable setup
- how to run VenueBite
- how to run tests
- distinction between real geographic data and demo market data
- architecture overview
- known Sprint 02 limitations
- next logical development areas

Do not place real credentials in README.

---

# DO NOT BUILD YET

Do not implement these in Sprint 02:

- authentication
- user accounts
- database persistence
- saved locations
- comparison persistence
- AI-generated explanations
- LLM APIs
- real Census demographics
- real population/income datasets
- commercial-property listings
- zoning
- permits
- regulations
- restaurant licensing
- real nearby restaurant intelligence
- Google Places
- payment systems
- subscriptions
- Docker
- cloud deployment
- React
- Vue
- Angular

Keep Sprint 02 focused.

---

# FUTURE-PROOFING

Design Sprint 02 so future providers can plug into VenueBite.

Future systems may include:

- business/POI provider
- demographics provider
- economic-data provider
- property/listings provider
- regulation provider
- street-level imagery provider
- AI explanation service

Do not implement these now.

Just avoid architecture that would prevent them.

---

# ACCEPTANCE CRITERIA

Sprint 02 is complete only when:

1. VenueBite starts normally using:

   python app.py

2. Existing functionality remains intact.

3. A configured Mapbox token produces a real interactive map.

4. Location search supports broad U.S. geographic input.

5. Selecting/searching a location yields real coordinates.

6. The map centers on that location.

7. A candidate-site marker appears.

8. Standard and satellite modes work.

9. The selected restaurant concept is included in the analysis.

10. Existing VenueBite scoring works.

11. Real geographic information is distinguished from demo market-analysis information.

12. Missing Mapbox configuration does not crash the application.

13. Invalid inputs produce user-friendly errors.

14. Mobile layout works.

15. Existing and new tests pass.

16. No secrets are committed.

17. No real Mapbox token appears anywhere in tracked source.

18. No existing working features are unnecessarily removed.

19. The UI is substantially improved over Sprint 01.

20. `git status` is shown at the end.

---

# FINAL VERIFICATION

Before declaring completion:

1. Run the full test suite.
2. Inspect the app for obvious runtime errors.
3. Review console/server errors.
4. Review `git diff`.
5. Review `git status`.
6. Check that `.env` is ignored.
7. Search tracked files for accidental Mapbox credentials.
8. Confirm no unrelated files were changed unnecessarily.

Do not commit.

Do not push.

---

# FINAL RESPONSE

When finished, report:

1. What was implemented.
2. Major files created or modified.
3. Architecture decisions.
4. Test results.
5. Any setup Chris must perform.
6. Any limitations still present.
7. Recommended manual test cases.
8. Current `git status`.

Do not commit or push anything.