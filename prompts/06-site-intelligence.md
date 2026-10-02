# Sprint 06 — Real Parcel + Site Intelligence

You are working inside the existing VenueBite repository.

VenueBite is a Flask/Jinja full-stack restaurant location-intelligence web application.

Current product state:

Sprint 01
- Flask/Jinja full-stack foundation
- application/services architecture
- testing foundation

Sprint 02
- real Mapbox location search
- normalized coordinates
- interactive map
- satellite mode
- geographic provider architecture

Sprint 03
- real nearby restaurant POIs
- direct-competitor classification
- competition scoring
- competitor map markers

Sprint 04
- U.S. Census geography resolution
- real ACS population
- real ACS median household income
- demographic provenance
- demographic scoring

Sprint 05
- VenueBite Score Model v2
- centralized factor definitions
- weighted contributions
- deterministic explanations
- strengths/risks
- structured provenance
- Data Coverage
- internal scoring trace

Sprint 05 is complete, committed, and pushed.

Sprint 06 adds a new evidence layer:

REAL PARCEL + SITE INTELLIGENCE.

This sprint must extend the existing architecture rather than rebuild it.

======================================================================
PRIMARY SPRINT GOAL
======================================================================

Use Regrid parcel data to identify and describe the actual parcel associated
with a selected VenueBite candidate location.

Sprint 06 should answer questions such as:

- What parcel contains or most closely corresponds to this candidate site?
- What is the parcel boundary?
- How large is the parcel?
- What land-use information is available?
- Is there evidence of existing structures?
- What property/site attributes are available?
- When was the underlying county parcel data refreshed?
- What assessor/property context is available?
- Is zoning information present in the current provider entitlement?
- Does the site appear developed, vacant, commercial, mixed, or unknown based
  only on supported structured data?

The output must help a user understand the physical/property context of a
candidate restaurant site.

Do NOT pretend this sprint determines whether a restaurant can legally open
on the parcel.

Do NOT claim that zoning codes alone prove restaurant use is permitted.

Do NOT create real commercial-rent data from parcel values.

======================================================================
IMPORTANT SCORE POLICY
======================================================================

Sprint 06 MUST NOT silently alter VenueBite Score Model v2.

Current score factors remain:

Population      30%
Income          30%
Rent            20%
Competition     20%

Parcel/site intelligence is a new decision-support layer.

It does NOT become a fifth score factor in Sprint 06.

Commercial rent remains DEMO.

Current VenueBite Data Coverage for a normal successful U.S. analysis should
therefore remain 80% unless existing factor provenance changes.

Do NOT increase Data Coverage merely because parcel data becomes available.

Data Coverage measures the evidence behind the four current score factors.

Site Intelligence should have its own availability/provenance status.

======================================================================
CRITICAL STARTING PROCEDURE
======================================================================

Before editing anything:

1. Read AGENTS.md completely.
2. Read this entire Sprint 06 prompt.
3. Inspect the current repository structure.
4. Run:

   git status
   git branch --show-current
   python -m pytest

5. Record the baseline test count.

6. Inspect at minimum:

   venuebite/__init__.py
   venuebite/routes.py
   venuebite/scoring.py
   venuebite/data_coverage.py
   venuebite/services/analysis_service.py
   existing provider abstractions
   existing Mapbox geography provider
   demographic provider/service
   competition provider/service
   explanation service
   results templates
   map-viewer JavaScript
   competition marker logic
   README.md

Understand Sprints 01–05 before changing architecture.

======================================================================
GIT RULES
======================================================================

DO NOT:

- commit
- push
- create another branch
- reset the repository
- rewrite history
- delete unrelated working functionality

Chris will review and commit manually.

======================================================================
DATA PROVIDER
======================================================================

Use Regrid for Sprint 06 parcel/site intelligence.

Before implementing API behavior, verify current endpoint, authentication,
schema fields, limits, and account/trial behavior against official Regrid
documentation.

Do not guess provider fields.

Use official Regrid API/schema documentation as the authority.

Primary parcel lookup should use the official point / latitude-longitude parcel
lookup capability.

At the time of this sprint the documented endpoint is conceptually:

GET https://app.regrid.com/api/v2/parcels/point

with selected candidate:

lat
lon

Do not hardcode this endpoint in multiple files.

Centralize provider base URL and configuration.

======================================================================
REGRID AUTHENTICATION
======================================================================

Read the Regrid credential from:

REGRID_API_TOKEN

Server-side only.

Never expose it to:

- JavaScript
- HTML
- templates
- data attributes
- browser network requests
- README
- tests
- prompt files
- logs

Prefer a supported authorization header where documented.

Do not place the real token into query strings if an official secure header
mechanism is supported by the endpoint.

Never print or log the token.

Missing Regrid configuration must NOT prevent Flask from starting.

======================================================================
ENVIRONMENT CONFIGURATION
======================================================================

Update `.env.example` safely with placeholders only:

MAPBOX_ACCESS_TOKEN=your_mapbox_access_token_here
CENSUS_API_KEY=your_census_api_key_here
REGRID_API_TOKEN=your_regrid_api_token_here

Optionally add centrally parsed configuration such as:

REGRID_HTTP_TIMEOUT_SECONDS=8
REGRID_POINT_FALLBACK_RADIUS_METERS=25

if justified.

Do not overwrite Chris's existing `.env`.

`.env` must remain ignored.

======================================================================
PROVIDER ARCHITECTURE
======================================================================

Introduce a clean site/parcel provider abstraction.

A reasonable architecture is:

venuebite/
    providers/
        site_provider.py
        regrid_provider.py

venuebite/
    services/
        site_intelligence_service.py

The exact filenames may differ if the repository already has a cleaner pattern.

Required separation:

Regrid provider
    HTTP/API behavior
    authentication
    provider parsing
    normalized parcel records

Site intelligence service
    candidate parcel resolution
    ambiguity handling
    derived site facts
    safe interpretation
    availability state

Analysis service
    orchestration only

Routes
    request/response only

Templates
    presentation only

JavaScript
    parcel map visualization only

Do not parse Regrid responses in Flask routes.

Do not put parcel interpretation logic in templates.

======================================================================
NORMALIZED PARCEL MODEL
======================================================================

Never pass raw Regrid API JSON throughout VenueBite.

Create a normalized parcel/site model.

Conceptually:

{
    "status": "available",
    "provider": "regrid",
    "provider_name": "Regrid",

    "regrid_id": "...",
    "parcel_number": "...",

    "display_address": "...",

    "parcel_area_sqft": 24000,
    "parcel_area_acres": 0.55,

    "land_use_code": "...",
    "land_use_description": "...",

    "zoning_code": "...",
    "zoning_type": "...",

    "building_count": 1,
    "building_area_sqft": 6200,
    "building_footprint_sqft": 5800,
    "year_built": 1998,

    "assessed_land_value": 500000,
    "assessed_improvement_value": 750000,

    "last_sale_price": 1100000,
    "last_sale_date": "...",

    "county_fips": "...",

    "parcel_geometry": {...},

    "provider_refresh_date": "...",

    "source_url": "...",

    "field_availability": {...}
}

This is conceptual.

Only normalize fields that:

- actually exist in the documented schema
- are returned by the current account
- can be interpreted accurately

Do not invent missing values.

======================================================================
OFFICIAL FIELD USAGE
======================================================================

Before coding, verify every Regrid field against current official schema
documentation.

Likely useful documented fields include concepts such as:

- ll_uuid
- parcelnumb
- usedesc
- usecode
- zoning
- zoning_type
- ll_gisacre
- ll_gissqft
- ll_bldg_count
- ll_bldg_footprint_sqft
- area_building
- yearbuilt
- landval
- improvval
- saleprice
- saledate
- geoid
- ll_last_refresh
- sourceurl

Do NOT assume every account/county populates every field.

Do NOT fail an entire parcel analysis because one optional field is absent.

Field coverage varies geographically.

======================================================================
PARCEL LOOKUP FLOW
======================================================================

Reuse the exact selected candidate coordinates already resolved by Mapbox.

Do NOT geocode again.

Conceptually:

selected VenueBite candidate
        ↓
latitude / longitude
        ↓
Regrid point lookup
        ↓
parcel candidate(s)
        ↓
normalize
        ↓
determine exact / nearby / ambiguous / unavailable
        ↓
site intelligence
        ↓
map parcel overlay + property context

Do not call Regrid during autocomplete.

Do not call Regrid merely because the map moves.

Parcel lookup should happen when VenueBite analyzes the selected site.

======================================================================
EXACT POINT LOOKUP
======================================================================

First attempt an exact point lookup with a zero/smallest appropriate radius.

Request only a small result limit.

Do not retrieve hundreds of parcels.

When exactly one clear parcel contains the candidate point:

status should indicate an exact/strong match.

When no parcel is returned:

do NOT immediately claim:

"No parcel exists."

The Mapbox coordinate may lie:

- in a road
- at a building entrance
- near a parcel boundary
- at a centroid offset
- outside Regrid entitlement coverage

Handle this carefully.

======================================================================
SMALL-RADIUS FALLBACK
======================================================================

If exact point lookup returns no usable parcel, optionally perform one small,
bounded nearby lookup using a centrally configured radius such as approximately
20–30 meters.

Purpose:

handle points returned near streets/parcel edges.

Do not use a giant radius.

Do not automatically pick a random nearby parcel.

Do not generate multiple wasteful calls.

At most:

1 exact lookup
+
1 small-radius fallback

for a normal analysis.

======================================================================
PARCEL MATCH QUALITY
======================================================================

Represent parcel match quality explicitly.

Suggested internal states:

exact
nearby
ambiguous
not_found
restricted
unavailable

The exact naming may differ.

The UI must distinguish these states.

Example:

Parcel match
Exact

or:

Parcel match
Nearby parcel — verify before relying on site facts

Do not pretend a nearby fallback match is equivalent to exact containment.

======================================================================
MULTIPLE PARCELS / STACKED PARCELS
======================================================================

A point may map to:

- multiple parcels
- stacked condominium parcels
- overlapping property records
- multiple parcels within fallback radius

Do not silently choose one when the match is materially ambiguous.

If multiple plausible parcels exist:

status = ambiguous

Show a useful message such as:

"Multiple parcel records correspond to this location. Site details require
parcel-level verification."

Preserve the map and all other VenueBite intelligence.

Do not crash the analysis.

======================================================================
PARCEL GEOMETRY
======================================================================

Retrieve parcel geometry when available.

Preserve valid GeoJSON Polygon and MultiPolygon geometry.

Validate structure before passing it to frontend map code.

Do not allow malformed provider geometry to crash Mapbox rendering.

The browser receives parcel geometry only.

The Regrid API token must never reach the browser.

======================================================================
MAP INTEGRATION
======================================================================

Extend the existing Mapbox Location Explorer.

Display the selected parcel boundary when available.

The existing map already contains:

- candidate-site marker
- direct competitor markers
- general restaurant markers
- map/satellite modes

Preserve all of them.

Add a parcel boundary overlay that is visually distinguishable without obscuring
restaurants or the base map.

Requirements:

- parcel outline
- subtle parcel fill
- works on standard map
- works on satellite
- responsive
- removed/replaced when a new analysis starts
- does not remain stale after location changes

Do not recreate the entire Mapbox instance.

Use a GeoJSON source/layer or another clean Mapbox-native approach.

======================================================================
PARCEL FIT / CAMERA BEHAVIOR
======================================================================

Do not aggressively zoom the map every time site data arrives if it creates a
poor experience.

If a parcel boundary is small, preserve useful surrounding competitor context.

The selected location and nearby market environment should remain visible.

Do not zoom so tightly that the map becomes only a parcel polygon.

======================================================================
SITE FACTS
======================================================================

Create a clear "Site Intelligence" section.

Potential useful metrics:

Parcel size
0.55 acres
23,958 sq ft

Land use
Commercial / Retail
(provider description)

Existing structures
1 observed structure

Building area
6,200 sq ft

Year built
1998

Zoning
C-MX-5
Data available — legal use not verified

Assessed land value
$500,000

Assessed improvements
$750,000

Last recorded sale
$1.1M · 2022

Source refresh
2026-xx-xx

Only show facts actually available.

Do not render empty rows for dozens of missing values.

======================================================================
ASSESSMENT VALUE SAFETY
======================================================================

Assessment values are NOT automatically:

- market value
- asking sale price
- lease rate
- restaurant buildout cost

Clearly label values based on what they actually represent.

Example:

Assessed land value

not:

Land price

Example:

Assessed improvement value

not:

Building market value

======================================================================
SALE DATA SAFETY
======================================================================

A recorded historical sale is not:

- current asking price
- current market value
- current availability
- current lease economics

If sale price/date is shown, label it historically.

Example:

Last recorded sale
$1.1M · 2022

Do not say:

Property currently worth $1.1M

unless another provider explicitly supports that claim.

======================================================================
COMMERCIAL RENT REMAINS DEMO
======================================================================

This requirement is mandatory.

Regrid parcel values do NOT replace VenueBite's rent/occupancy factor.

Do not derive restaurant lease cost from:

- assessed land value
- assessed building value
- last sale price
- residential rent
- property tax data
- parcel acreage

Rent remains:

DEMO

Therefore Score Model v2 still uses the existing demo rent contribution.

The UI should continue to warn:

Commercial occupancy cost is not yet backed by live lease-market evidence.

======================================================================
LAND USE INTERPRETATION
======================================================================

Display Regrid land-use information carefully.

Use provider descriptions where available.

Do not convert vague local use codes into claims that are not supported.

Allowed:

"Provider land-use description: Retail"

Not automatically allowed:

"This parcel is approved for a restaurant."

The latter belongs to future zoning/regulatory verification.

======================================================================
ZONING SAFETY
======================================================================

If zoning fields are available, they are useful context.

However:

ZONING CODE ≠ VERIFIED RESTAURANT PERMISSION.

Display:

Zoning context
C-MX-5

with language such as:

"Parcel zoning data is informational. VenueBite has not yet verified restaurant
use permissions, overlays, conditional-use requirements, or local approvals."

Do NOT say:

"Restaurant allowed"

"Restaurant prohibited"

"Ready to build"

unless a future authoritative regulation system establishes that.

======================================================================
OPTIONAL / PLAN-DEPENDENT DATA
======================================================================

Some Regrid data or matched datasets may depend on:

- plan
- entitlement
- county coverage
- dataset availability

Examples may include:

- standardized zoning
- matched building footprints
- enhanced ownership
- secondary addresses

Treat these as optional enhancements.

Do not make Sprint 06 depend on paid premium add-ons.

Detect missing fields cleanly.

Use:

"Not available from current parcel data"

rather than:

"None"

when absence may reflect provider coverage.

======================================================================
OWNERSHIP DATA
======================================================================

Do NOT emphasize personal property-owner data in Sprint 06.

VenueBite is analyzing restaurant sites, not profiling private individuals.

Do not display:

- private owner mailing addresses
- unnecessary personal owner information

Ownership is not required for Sprint 06 acceptance.

If owner/entity information happens to exist, do not surface it unless there is
a clear legitimate product reason and the data is handled appropriately.

======================================================================
BUILDING DATA
======================================================================

If standard parcel/building fields are available, normalize useful physical-site
information.

Examples:

- building count
- assessor building area
- Regrid calculated footprint size
- year built

Keep semantics explicit.

Building area and building footprint are different measurements.

Do not treat them as interchangeable.

If provider documentation supplies a field definition, preserve that distinction.

======================================================================
VACANT / DEVELOPED SITE SIGNAL
======================================================================

VenueBite may derive a conservative deterministic site-development state.

Examples:

Existing structures observed
No structure fields observed
Unknown

Do not confidently label:

"Vacant land"

unless available structured data supports that interpretation.

A missing building count is not proof of vacant land.

Possible internal states:

developed_evidence
no_structure_evidence
unknown

Avoid overclaiming.

======================================================================
SITE INTELLIGENCE EXPLANATIONS
======================================================================

Generate deterministic site notes.

No AI.

Examples:

"Regrid reports a 0.55-acre parcel with one existing structure."

"Commercial land-use context is present, but restaurant-use eligibility has not
been verified."

"Parcel geometry was resolved through a nearby fallback rather than exact point
containment; verify the parcel before relying on property facts."

"Building attributes are unavailable for this parcel."

"Historical assessment values are available; current asking rent is not."

No random prose.

No provider calls in the explanation layer.

======================================================================
SITE STRENGTHS / FLAGS
======================================================================

Do not merge site notes directly into Score Model v2 strengths/risks unless the
current score model explicitly supports the new evidence.

Instead create a dedicated:

Site considerations

section.

Potential deterministic considerations:

- usable parcel size information available
- existing structure evidence available
- commercial/mixed-use land-use context
- parcel match is nearby rather than exact
- zoning available but legal-use verification pending
- building attributes missing
- parcel record refresh is old
- multiple parcels ambiguous

Do not call these investment recommendations.

======================================================================
PROPERTY DATA PROVENANCE
======================================================================

Create structured site-data provenance.

Conceptual example:

{
    "status": "real",
    "provider": "Regrid",
    "match_quality": "exact",
    "refresh_date": "...",
    "parcel_id": "...",
    "coverage_notes": [...]
}

Do not derive provenance from rendered strings.

======================================================================
SOURCE FRESHNESS
======================================================================

Where Regrid provides source/refresh metadata, retain it.

Display something concise such as:

Parcel data refreshed:
June 2026

or the exact available date.

Do not call parcel data "live" or "real-time."

County assessor parcel information may update periodically.

======================================================================
REGRID TRIAL / ACCOUNT COVERAGE
======================================================================

This requirement is critical.

Regrid API tokens may have geographic or dataset restrictions depending on the
account or trial plan.

Current official documentation indicates that some API trial tokens are limited
to sample counties.

Do NOT interpret:

403
empty response
or missing premium fields

as proof that the parcel does not exist.

Distinguish:

not_found

from:

provider_restricted / outside_current_coverage

where possible.

Sanitize provider error messages before showing them.

======================================================================
TRIAL TOKEN MANUAL TESTING
======================================================================

Before calling a geographic lookup bug, determine the capabilities of the current
Regrid token.

If the token is a restricted trial token, use documented sample counties for live
acceptance testing.

Current official Regrid trial documentation lists sample coverage including:

- Dallas County, Texas
- Marion County, Indiana
- Wilson County, Tennessee
- Durham County, North Carolina
- Fillmore County, Nebraska
- Clark County, Wisconsin
- Gurabo Municipio, Puerto Rico

Verify the current list against official Regrid documentation rather than relying
solely on this prompt.

If the current token has nationwide/self-serve access, also test Colorado sites.

Do not hardcode these counties into production product logic.

They are manual-test guidance only.

======================================================================
PROVIDER USAGE EFFICIENCY
======================================================================

Regrid usage may be measured based on returned parcel records.

Minimize unnecessary returned records.

Do not:

- perform parcel lookup on autocomplete keystrokes
- request large radius searches
- request hundreds of parcels
- refetch parcel data for map/satellite switches
- call provider once per field
- make unnecessary duplicate requests

Use a small result limit.

Fetch fields in one parcel response where practical.

======================================================================
HTTP CLIENT BEHAVIOR
======================================================================

All Regrid calls must have explicit timeouts.

Handle:

- missing token
- invalid token
- unauthorized response
- entitlement restriction
- rate/usage limit
- timeout
- connection failure
- HTTP error
- malformed JSON
- missing FeatureCollection
- empty feature list
- malformed geometry
- malformed field values
- multiple parcel results
- missing optional attributes

Do not expose raw provider responses to users.

Do not expose token values.

======================================================================
FIELD VALIDATION
======================================================================

Validate normalized values.

Examples:

Latitude:
-90 through 90

Longitude:
-180 through 180

Parcel acres:
must not be negative

Parcel square feet:
must not be negative

Building counts:
must not be negative

Year built:
reasonable integer or unavailable

Assessment/sale values:
nonnegative numeric or unavailable

Geometry:
valid supported GeoJSON structure

Do not blindly trust provider data.

======================================================================
RAW DATA POLICY
======================================================================

Do not create a persistent Regrid parcel database in Sprint 06.

Do not persist raw API responses.

Do not add PostgreSQL.

Do not add SQLite.

Do not introduce filesystem caches.

Request-scope processing is sufficient.

A small process-local cache may only be introduced if clearly allowed,
bounded, deterministic, and useful, but it is not required.

Prefer no cache unless necessary.

======================================================================
ANALYSIS SERVICE INTEGRATION
======================================================================

Existing VenueBite analysis flow roughly includes:

geography
demographics
competition
factor scoring
overall scoring
coverage
explanations

Add:

site intelligence

without turning analysis_service.py into a monolith.

Conceptually:

selected location
      ↓
geography
      ├── Census demographics
      ├── competition
      └── parcel/site intelligence
               ↓
normalized analysis report
               ↓
Score Model v2 remains unchanged
               ↓
UI

Site intelligence may run independently of Census/competition where practical.

A Regrid failure must NOT destroy:

- map
- demographics
- competition
- opportunity score

======================================================================
FAILURE ISOLATION
======================================================================

Example:

Mapbox works
Census works
Competition works
Regrid fails

Expected:

Opportunity Score still works.

Data Coverage remains based on score-factor provenance.

Site Intelligence says:

"Parcel data unavailable."

Do not fail the whole report.

======================================================================
MAP STATE CONSISTENCY
======================================================================

Preserve the critical invariant:

search selection
candidate coordinates
map candidate marker
competitor markers
Census tract
competition results
parcel boundary
parcel facts

must belong to the SAME submitted analysis.

When a user changes:

- location
- restaurant concept
- radius

invalidate stale analysis state appropriately.

A new location must immediately clear the old parcel boundary.

Do not leave a previous site's polygon visible while a new location is selected.

======================================================================
FRONTEND JAVASCRIPT
======================================================================

Keep parcel visualization modular.

A reasonable new module could be:

static/js/parcel-layer.js

Responsibilities:

- add/update parcel GeoJSON source
- render parcel fill/outline
- clear stale parcel
- gracefully handle missing geometry
- optionally provide parcel popup/context

Do not put Regrid network calls in JavaScript.

All provider requests remain server-side.

======================================================================
SITE INTELLIGENCE UI
======================================================================

Preserve Sprint 02–05 design.

Do NOT redesign VenueBite again.

Add a polished section such as:

SITE INTELLIGENCE
Real parcel data · Regrid

Parcel
0.55 acres
23,958 sq ft

Land use
Commercial / Retail

Structures
1 observed

Building area
6,200 sq ft

Year built
1998

Zoning context
C-MX-5
Restaurant permissions not yet verified

Assessment context
Land: $500K
Improvements: $750K

Last recorded sale
$1.1M · 2022

Parcel match
Exact

Provider refresh
June 2026

Only show fields actually available.

Use compact cards/rows.

======================================================================
SITE INTELLIGENCE STATUS
======================================================================

Possible user-facing states:

Real parcel data

Nearby parcel match — verify

Multiple parcels — verification needed

Outside current provider coverage

Parcel data unavailable

No matching parcel returned

Do not conflate these.

======================================================================
EMPTY/MISSING FIELD UX
======================================================================

Do not fill the interface with:

N/A
N/A
N/A
N/A

Prefer:

- omit low-value unavailable rows
- group unavailable optional data
- display one concise provider-coverage note

Important missing information such as zoning may say:

"Zoning data not available from current parcel record."

======================================================================
PARCEL SOURCE LINK
======================================================================

If a documented county source URL is supplied and safe to display, VenueBite may
offer a source-record link.

Treat it as external.

Use secure link behavior:

rel="noopener noreferrer"

Do not manufacture county URLs.

Do not make source URL availability an acceptance requirement.

======================================================================
NO LEGAL CONCLUSIONS
======================================================================

Sprint 06 must not state:

- restaurant use is legal
- restaurant use is illegal
- zoning approval guaranteed
- liquor license possible/impossible
- building permit guaranteed
- parcel is shovel-ready
- ADA compliance
- fire-code compliance
- parking requirement compliance

Those belong to future regulatory feasibility work using authoritative local
sources.

======================================================================
NO COMMERCIAL LISTINGS YET
======================================================================

Sprint 06 does not implement:

- properties for sale search
- properties for lease search
- asking rents
- listing inventory
- broker contact data
- LoopNet scraping
- Crexi scraping
- CoStar scraping

Sprint 06 analyzes the parcel at the already-selected candidate site.

Commercial-property discovery belongs in a later sprint with licensed data.

======================================================================
NO SCORE CHANGES
======================================================================

Run regression tests proving that for identical four-factor inputs:

Sprint 05 Score Model v2 output is unchanged.

Parcel/site availability must not alter:

- factor scores
- factor weights
- weighted contributions
- Opportunity Score
- Data Coverage

unless a separate verified pre-existing bug is discovered.

If a score changes because of Sprint 06, treat it as a regression until proven
otherwise.

======================================================================
TESTING
======================================================================

Before changes:

python -m pytest

Preserve all Sprint 01–05 tests.

No automated test may make a real Regrid network request.

Mock provider calls.

Add comprehensive tests for:

Configuration
- missing REGRID_API_TOKEN
- token never exposed client-side
- environment loading
- timeout parsing

Provider
- exact parcel response
- empty result
- 401/403
- restricted/coverage response
- timeout
- connection failure
- malformed JSON
- missing parcels object
- missing features
- malformed fields

Normalization
- parcel ID
- parcel number
- parcel acres
- parcel square feet
- land use
- zoning
- building count
- building area
- footprint
- year built
- assessment values
- sale data
- refresh date
- source URL

Geometry
- valid Polygon
- valid MultiPolygon
- missing geometry
- malformed coordinates
- unsupported geometry
- geometry safely omitted rather than crashing

Parcel resolution
- exact single match
- exact multiple matches
- zero exact + one nearby match
- zero exact + several nearby matches
- total not found
- ambiguous
- provider restricted

Validation
- negative sizes
- invalid year
- malformed money values
- invalid coordinates

Analysis integration
- successful parcel
- Regrid unavailable
- restricted trial
- ambiguous parcel
- no parcel found
- Census still works
- competition still works
- Score Model v2 unchanged
- Data Coverage unchanged
- rent remains demo

State consistency
- new location clears old parcel
- old polygon does not remain
- parcel coordinate corresponds to current analysis
- stale parcel results do not render

Templates
- site intelligence available state
- unavailable state
- nearby match warning
- ambiguous warning
- zoning disclaimer
- assessment labels
- historical sale labels
- source provenance

Security
- HTML escaping
- token isolation
- sanitized provider errors

Map/frontend behavior should be tested where current project test architecture
makes that practical without brittle CSS tests.

======================================================================
LIVE MANUAL ACCEPTANCE TESTS
======================================================================

First determine current Regrid token scope.

If nationwide/current-plan coverage permits, test:

Denver exact address
Greeley exact address
Chicago exact address
Miami exact address
New York exact address

Prefer full addresses rather than city centroids because this sprint analyzes
specific parcels.

Also test materially different parcel types where practical.

If current token is geographically restricted, use official Regrid trial counties.

Good trial examples should come from:

Dallas County, TX
Marion County, IN
Durham County, NC

Use real complete street addresses that Mapbox resolves.

Do not invent a provider problem simply because the trial token cannot access
Colorado.

For each successful parcel verify:

- current selected location is correct
- parcel belongs to current location
- boundary appears
- candidate marker remains
- competitor markers remain
- standard map works
- satellite works
- parcel size plausible
- land use displayed when available
- building fields displayed when available
- assessment values labeled correctly
- sale history labeled historically
- zoning does not claim legal restaurant eligibility
- rent remains demo
- score remains unchanged by parcel data
- Data Coverage remains based on four scoring factors
- provider attribution shown
- refresh information shown where available

Also manually test:

- point on/near a street
- no parcel result
- restricted geographic result if applicable
- changed location clears old polygon

======================================================================
REGRID USAGE CHECK
======================================================================

Because returned records may count toward Regrid usage:

Do not repeatedly run dozens of unnecessary manual parcel searches.

Use only enough live acceptance tests to verify behavior.

Do not write automated tests against live Regrid.

If practical and officially supported, document how Chris can review API usage
in his Regrid account.

Do not query usage on every application request.

======================================================================
README
======================================================================

Update README with:

- Sprint 06 overview
- Regrid dependency
- REGRID_API_TOKEN setup
- server-side credential rules
- parcel lookup flow
- exact vs nearby parcel matching
- parcel geometry behavior
- normalized parcel fields
- optional field/provider coverage
- trial geographic limitations
- assessment-value disclaimer
- historical-sale disclaimer
- zoning disclaimer
- commercial-rent limitation
- Score Model v2 unchanged
- Data Coverage unchanged
- no parcel persistence
- how to run:

  python app.py

- how to test:

  python -m pytest

- known limitations
- future site/regulatory/property roadmap

Do not put a real Regrid token in README.

======================================================================
OPTIONAL ENGINEERING DOCUMENT
======================================================================

If useful, create:

docs/site-intelligence-v1.md

Document:

- provider architecture
- parcel resolution algorithm
- normalized schema
- match-quality states
- field semantics
- map overlay behavior
- trial limitations
- legal/zoning limitations
- score isolation
- known gaps

Do not create documentation simply to inflate file count.

======================================================================
DO NOT BUILD IN SPRINT 06
======================================================================

Do NOT implement:

- commercial asking rent
- commercial listing search
- land-for-sale search
- properties-for-lease discovery
- LoopNet scraping
- Crexi scraping
- CoStar scraping
- residential rent substitution
- zoning legal conclusions
- permitted-use verification
- permit research
- restaurant licensing
- liquor licensing
- building-code compliance
- parking compliance
- utilities analysis
- construction cost estimates
- traffic API
- foot-traffic API
- database
- persistence
- saved analyses
- authentication
- Keycloak
- AI
- LLMs
- chatbot
- Docker
- deployment
- payments
- subscriptions
- React/Vue/Angular

Keep Sprint 06 focused on REAL PARCEL + SITE INTELLIGENCE.

======================================================================
ACCEPTANCE CRITERIA
======================================================================

Sprint 06 is complete only when:

1. Sprint 01 functionality remains intact.
2. Sprint 02 map/location functionality remains intact.
3. Sprint 03 competition functionality remains intact.
4. Sprint 04 Census functionality remains intact.
5. Sprint 05 Score Model v2 remains numerically stable.
6. Regrid parcel provider is implemented behind an abstraction.
7. Candidate coordinates can resolve a parcel where provider coverage exists.
8. Exact parcel matches are distinguishable from nearby fallback matches.
9. Multiple/ambiguous parcels are handled safely.
10. Parcel boundary renders on Mapbox.
11. Old parcel boundaries clear when location changes.
12. Parcel size is shown when available.
13. Land-use context is shown when available.
14. Building/site context is shown when available.
15. Zoning context may be shown when available but does not claim legal permission.
16. Assessment values are not mislabeled as market values.
17. Historical sale values are not mislabeled as current asking prices.
18. Commercial rent remains demo.
19. Opportunity Score weights remain unchanged.
20. Parcel data does not alter Opportunity Score.
21. Parcel data does not inflate Score Model Data Coverage.
22. Regrid failure does not destroy the rest of the analysis.
23. Missing Regrid token does not prevent Flask startup.
24. Trial/provider restrictions are distinguished from parcel nonexistence.
25. Regrid token never reaches browser code.
26. Regrid token never appears in logs.
27. `.env` remains ignored.
28. Existing tests pass.
29. New tests pass.
30. App starts with:

    python app.py

31. Full suite runs with:

    python -m pytest

32. Git status is shown at completion.
33. Codex does not commit.
34. Codex does not push.

======================================================================
FINAL SECURITY CHECK
======================================================================

Before completion:

- verify `.env` is ignored
- search changed/tracked files for accidental Regrid credentials
- do not print the real token during scanning
- verify Mapbox token handling remains intact
- verify Census key handling remains intact
- verify Regrid token is server-only
- verify no raw provider error contains credentials

======================================================================
FINAL VERIFICATION
======================================================================

Before declaring Sprint 06 complete:

1. Run:

   python -m pytest

2. Start:

   python app.py

3. Determine current Regrid token geographic entitlement.

4. Perform a small set of live parcel tests in supported coverage.

5. Verify exact parcel behavior.

6. Verify nearby fallback behavior where practical.

7. Verify parcel boundary.

8. Verify map/satellite.

9. Verify candidate marker.

10. Verify competitor markers.

11. Verify Census demographics.

12. Verify Opportunity Score regression stability.

13. Verify Data Coverage regression stability.

14. Verify rent remains demo.

15. Verify zoning disclaimer.

16. Verify assessment-value labeling.

17. Verify historical-sale labeling.

18. Verify provider refresh/source metadata.

19. Change locations and confirm old polygon disappears.

20. Inspect browser console.

21. Inspect sanitized Flask logs.

22. Inspect git diff.

23. Inspect git status.

24. Confirm no secrets are tracked.

DO NOT COMMIT.

DO NOT PUSH.

======================================================================
FINAL REPORT
======================================================================

When finished, report:

1. What Sprint 06 implemented.
2. Files created.
3. Files modified.
4. Regrid provider architecture.
5. Exact API endpoint(s) used.
6. Authentication method used.
7. Current token entitlement/coverage observed.
8. Parcel resolution algorithm.
9. Exact/nearby/ambiguous behavior.
10. Normalized parcel fields.
11. Parcel geometry/map implementation.
12. Site Intelligence UI behavior.
13. How optional/plan-dependent fields are handled.
14. Zoning disclaimer behavior.
15. Assessment/sale-value safety behavior.
16. Score Model v2 regression results.
17. Data Coverage regression results.
18. Rent-factor status.
19. Test count/result.
20. Live manual test results.
21. Regrid usage considerations.
22. Known limitations.
23. Current git status.
24. Anything Chris must manually verify.

Do not commit.
Do not push.