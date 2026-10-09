# Sprint 09 — Saved Sites + Location Comparison + Persistence

You are working inside the existing VenueBite repository.

VenueBite is a Flask/Jinja full-stack restaurant location-intelligence application.

Completed product areas now include:

Sprint 01
- Flask/Jinja application foundation
- scoring foundation
- testing

Sprint 02
- real Mapbox location search
- map
- satellite
- geography normalization

Sprint 03
- real nearby restaurant competition
- direct competitor classification
- Competition Model v1

Sprint 04
- real Census population and household income
- demographic provenance

Sprint 05
- VenueBite Score Model v2
- weighted factor contributions
- Data Coverage
- deterministic explanations
- strengths / risks

Sprint 06
- Regrid parcel / site intelligence
- parcel boundaries
- normalized site context

Sprint 07
- commercial occupancy inputs
- Commercial Occupancy Model v1
- budget-relative rent scoring
- user-supplied partial evidence
- occupancy cost calculations

Sprint 08
- futuristic UI modernization
- modern application shell
- improved map presentation
- score / coverage visualizations
- responsive intelligence dashboard
- hidden unfinished navigation

Sprint 09 introduces:

SAVED SITES
+
LOCATION COMPARISON
+
DATABASE PERSISTENCE

======================================================================
PRIMARY SPRINT GOAL
======================================================================

Allow users to save analyzed candidate restaurant locations and compare them
side-by-side later.

VenueBite should begin functioning like a serious location-decision workspace.

A user should be able to:

1. Analyze a location normally.
2. Save that analyzed site.
3. Give it a useful name.
4. View previously saved sites.
5. Open a saved site.
6. Compare multiple saved sites.
7. Understand why one site differs from another.
8. Delete a saved site.
9. Preserve important analysis evidence without pretending a stored snapshot is
   live forever.

======================================================================
CORE PRODUCT PRINCIPLE
======================================================================

Saved analysis is a SNAPSHOT.

It is not automatically current data.

Population, income, competition, parcel information, commercial occupancy terms,
and scores may change in the future.

Therefore:

- preserve when the analysis was created
- preserve provider/source provenance
- clearly label saved analysis as a snapshot
- provide a future path for re-analysis
- do not silently represent historical saved values as freshly retrieved data

======================================================================
CRITICAL STARTING PROCEDURE
======================================================================

Before editing anything:

1. Read AGENTS.md completely.
2. Read this Sprint 09 prompt completely.
3. Inspect the repository.
4. Run:

   git status
   git branch --show-current
   python -m pytest

5. Run all existing JavaScript tests.

6. Record baseline test counts.

7. Inspect at minimum:

   venuebite/__init__.py
   venuebite/routes.py
   venuebite/scoring.py
   venuebite/occupancy.py

   venuebite/services/analysis_service.py
   venuebite/services/explanation_service.py
   venuebite/services/occupancy_service.py
   venuebite/services/site_intelligence_service.py

   templates/base.html
   templates/index.html
   templates/results.html
   existing dashboard partials

   static/css/style.css
   static/js/analysis-state.js
   static/js/map-viewer.js

   README.md
   docs/scoring-model-v2.md
   docs/commercial-occupancy-v1.md
   docs/sprint08-ui-system.md

Understand the current Sprint 01–08 architecture before implementation.

======================================================================
GIT RULES
======================================================================

DO NOT:

- commit
- push
- reset
- rewrite history
- create another branch
- discard existing Sprint 08 changes

Chris will review and commit manually.

======================================================================
DATABASE CHOICE
======================================================================

Use SQLite for Sprint 09 unless the existing repository already contains a
better justified persistence strategy.

SQLite is appropriate because:

- VenueBite is still local/single-instance development
- no production multi-user architecture exists yet
- it requires minimal infrastructure
- it enables a clean repository/service persistence boundary
- migration to PostgreSQL can happen later

Do NOT add PostgreSQL, Redis, Docker, or another infrastructure dependency in
Sprint 09.

======================================================================
DATABASE ARCHITECTURE
======================================================================

Introduce a clean persistence layer.

Prefer architecture conceptually similar to:

venuebite/
    db.py

venuebite/
    repositories/
        saved_site_repository.py

venuebite/
    services/
        saved_site_service.py
        comparison_service.py

Routes should not contain SQL.

Templates should not contain persistence logic.

Analysis services should remain responsible for analysis, not database access.

======================================================================
DATABASE LOCATION
======================================================================

Store the development SQLite database somewhere safe and clearly ignored by Git.

Example:

instance/venuebite.db

or equivalent Flask instance path.

The database file MUST NOT be committed.

Update .gitignore if necessary.

======================================================================
NO ORM REQUIREMENT
======================================================================

Do not add a heavy ORM unless the current architecture strongly justifies it.

For this sprint:

- Python sqlite3 is acceptable
- lightweight repository code is preferred
- parameterized SQL is mandatory

If SQLAlchemy is added, document why it is materially beneficial.

Do not add dependencies just because they are common.

======================================================================
DATABASE INITIALIZATION
======================================================================

Database initialization should happen safely.

Provide an idempotent schema creation strategy.

Possible:

init_db()

CREATE TABLE IF NOT EXISTS

Avoid destructive recreation.

Do not delete saved data every time Flask starts.

======================================================================
SAVED SITE DATA MODEL
======================================================================

Create a saved_site model capable of preserving a useful analysis snapshot.

At minimum persist:

Identity
- id
- display_name

Location
- location_label
- latitude
- longitude
- city if available
- state / region if available
- country if available

Restaurant analysis
- restaurant_concept
- search_radius_miles

Score
- opportunity_score
- opportunity_classification
- score_model_version

Coverage
- data_coverage
- coverage_label

Factors
- population_score
- income_score
- rent_score
- competition_score

Factor evidence
- population evidence status
- income evidence status
- rent evidence status
- competition evidence status

Weighted contributions
- population contribution
- income contribution
- rent contribution
- competition contribution

Important area facts
- tract population when available
- median household income when available
- tract GEOID if available
- Census vintage if available

Competition summary
- nearby restaurant count
- direct competitor count
- nearest direct competitor distance if available
- competition model version

Site summary
- parcel status
- parcel identifier where permitted
- parcel area if available
- land-use description/code if available
- building area if available
- zoning code if available
- Regrid source status / provenance

Commercial occupancy
- whether occupancy terms existed
- space size
- asking rent
- asking rent basis
- lease structure
- additional charges
- additional-charge basis
- monthly base rent
- monthly known occupancy cost
- monthly budget
- budget utilization
- occupancy model version
- occupancy evidence status

Snapshot metadata
- created_at
- updated_at if needed
- analysis_timestamp
- schema_version / snapshot_version

Do not persist unnecessary raw provider payloads.

======================================================================
RAW PROVIDER DATA POLICY
======================================================================

Do NOT store complete raw:

- Mapbox search payloads
- Mapbox POI payloads
- Census responses
- Regrid responses

Persist normalized facts necessary for comparison and saved-site display.

This keeps storage focused and reduces unnecessary provider-data retention.

======================================================================
PROVIDER LICENSING
======================================================================

Respect existing provider restrictions.

Mapbox nearby restaurant data should not be turned into a permanent raw POI
database.

Persist summary values needed to understand the saved analysis.

Do not build a historical Mapbox business directory.

======================================================================
SAVING A SITE
======================================================================

After a successful analysis, provide:

SAVE SITE

Opening the action should allow:

Saved site name

Default suggestion can be based on:

location + concept

Example:

Aurora — Indian Restaurant

Allow user editing.

Do not force a saved site name to equal the Mapbox result.

======================================================================
SAVE VALIDATION
======================================================================

A site must have a valid completed analysis before it can be saved.

Do not save:

- blank location
- unresolved analysis
- invalid score
- stale form state after the user changed inputs
- failed analysis with no meaningful candidate location

The saved snapshot must correspond to the currently displayed analysis.

======================================================================
DUPLICATES
======================================================================

Do not silently create endless accidental duplicates.

A user may intentionally save the same physical location multiple times when:

- concept differs
- radius differs
- occupancy assumptions differ
- analysis date differs

Therefore do not enforce uniqueness merely by coordinates.

If an apparent duplicate exists:

allow save

but optionally warn:

"A similar saved analysis already exists."

Do not block legitimate scenario comparison.

======================================================================
SAVED LOCATIONS NAVIGATION
======================================================================

Sprint 08 intentionally hid:

Saved Locations
Compare

because they were unfinished.

Once Sprint 09 implements them successfully:

restore functional navigation links:

Analyze
Saved Sites
Compare

Do NOT restore:

Find an Area

until that feature exists.

No "Coming soon" labels for implemented features.

======================================================================
SAVED SITES PAGE
======================================================================

Create a premium Saved Sites page matching Sprint 08 visual design.

Route conceptually:

/saved

or:

/sites

Use whichever naming best fits the application.

Each card/row should show:

- saved site name
- location
- restaurant concept
- Opportunity Score
- classification
- Data Coverage
- snapshot date
- evidence summary
- key metrics
- compare-selection action
- open/details action
- delete action

======================================================================
SAVED SITE CARD DESIGN
======================================================================

Example:

---------------------------------------------------
Aurora — Indian Restaurant
Aurora, Colorado

48.3 / 100
Mixed

90% evidence coverage

Population        36.8
Income            44.5
Rent              66.0
Competition       53.5

2,800 SF · NNN
$9,450/mo known occupancy

Saved Oct 2026

[ View ]   [ Compare ]   [ Delete ]
---------------------------------------------------

Match Sprint 08 design system.

======================================================================
SAVED SITE DETAIL
======================================================================

Allow opening one saved snapshot.

It should resemble the existing analysis dashboard but clearly indicate:

SAVED SNAPSHOT

Analyzed:
<timestamp>

Do not imply provider data was just fetched.

Possible actions:

- Compare
- Delete
- Analyze again

"Analyze again" may re-populate the current analysis workflow or trigger a fresh
analysis only if architecture supports it cleanly.

Do not fabricate freshness.

======================================================================
DELETE
======================================================================

Users must be able to delete saved sites.

Deletion must:

- use POST or DELETE-like server semantics
- not use a destructive GET route
- validate the site ID
- handle already-deleted/nonexistent records gracefully

Use a confirmation UI.

No raw SQL IDs exposed in unsafe query construction.

======================================================================
COMPARISON FEATURE
======================================================================

Create a true side-by-side comparison workflow.

Users should be able to select:

minimum:
2 sites

maximum:
4 sites

for comparison.

Do not create a layout optimized for 20 sites.

======================================================================
COMPARE PAGE
======================================================================

Create a premium comparison screen.

Recommended structure:

SITE HEADER ROW

Aurora
Denver
Greeley

Then comparison categories:

OPPORTUNITY
- overall score
- classification
- Data Coverage

FACTORS
- population
- income
- rent
- competition

DEMOGRAPHICS
- population
- household income
- tract information

COMPETITION
- observed nearby restaurants
- direct competitors
- nearest direct competitor

SITE
- parcel availability
- parcel area
- building area
- land use
- zoning code

OCCUPANCY
- space size
- lease structure
- known occupancy cost
- occupancy budget
- budget utilization

EVIDENCE
- real / partial / demo / unavailable

======================================================================
COMPARISON PRINCIPLE
======================================================================

Comparison must compare FACTS and MODEL OUTPUTS.

Do not declare:

"This is definitely the best site."

Do not turn the largest Opportunity Score into an automatic recommendation.

You may visually identify:

Highest score
Highest evidence coverage
Lowest known occupancy cost
Lowest observed competition pressure

but use neutral language.

======================================================================
COMPARISON HIGHLIGHTS
======================================================================

Generate deterministic comparison highlights.

Examples:

"Aurora has the highest Opportunity Score among the selected saved snapshots."

"Greeley has the strongest competition factor."

"Denver has the highest Data Coverage."

"Aurora's occupancy estimate is lower than Denver's based on the saved
user-supplied terms."

Include context.

Avoid:

"Choose Aurora."

======================================================================
MISSING DATA IN COMPARISON
======================================================================

Saved snapshots will not always contain the same fields.

Comparison must handle:

- no parcel
- demo rent
- no occupancy terms
- unavailable Census
- provider failure
- missing direct competitor

Show:

Unavailable
Not supplied
Demo
Not available in saved snapshot

Do not convert missing values to zero.

======================================================================
SCORE VISUALIZATION
======================================================================

Reuse Sprint 08 visual language.

For comparison:

use compact score rings or bars.

Do not duplicate giant full-dashboard cards for every site.

The comparison should remain readable.

======================================================================
FACTOR COMPARISON VISUAL
======================================================================

A useful design could be:

Population

Aurora    36.8  ███████
Denver    61.2  ████████████
Greeley   54.1  ██████████

Income

...

Use native CSS/SVG.

Do not introduce a charting library only for comparison bars.

======================================================================
RADAR CHART
======================================================================

A radar chart may look attractive but is optional.

Only implement one if:

- it is accessible
- it is lightweight
- it clearly adds value

Do not hide precise values behind the graphic.

Factor tables/bars are still required.

======================================================================
COMPARE SELECTION STATE
======================================================================

Comparison selections may be carried using:

- query parameters
- form POST
- lightweight session

Choose the cleanest current architecture.

Do not require user accounts yet.

Do not permanently store "comparison sessions" unless justified.

======================================================================
NO AUTHENTICATION YET
======================================================================

Sprint 09 database is local application persistence.

Do not build:

- login
- signup
- password reset
- OAuth
- Keycloak
- teams
- organizations

Saved sites are application-level local records for now.

Future authentication can associate saved sites with users later.

Design schema so adding owner/user_id later is possible without forcing it now.

======================================================================
FUTURE USER OWNERSHIP
======================================================================

Document the future migration path.

Example:

saved_site

id
future user_id nullable / migration later

Do not add fake user IDs.

======================================================================
DATABASE SECURITY
======================================================================

All SQL must use parameterized queries.

Never interpolate user values into SQL strings.

Validate:

- saved-site name
- IDs
- selected comparison IDs

Escape output using normal Jinja behavior.

======================================================================
CSRF / DESTRUCTIVE ACTION SAFETY
======================================================================

If the existing application has CSRF protection, use it.

If not:

do not introduce a half-built authentication/security framework.

At minimum:

- destructive actions must be POST
- use confirmation
- validate IDs
- do not expose deletion through GET links

Document that comprehensive CSRF protection belongs with the broader security /
auth sprint if not already present.

======================================================================
NAME VALIDATION
======================================================================

Saved site names:

- required
- trim whitespace
- reasonable max length
- no raw HTML
- Unicode allowed
- normal punctuation allowed

Do not create arbitrary restrictive name rules.

======================================================================
SNAPSHOT SERIALIZATION
======================================================================

Avoid storing an opaque Python pickle.

Do not use pickle for application persistence.

Prefer explicit columns and/or safe JSON for structured normalized snapshot
sections.

If JSON is used:

- store JSON text
- validate before decoding
- version the snapshot structure

======================================================================
SCHEMA VERSIONING
======================================================================

Introduce a simple schema/snapshot version concept.

Example:

snapshot_version = 1

This will allow future sprints to evolve saved-site structure.

Do not build an elaborate migration framework yet unless necessary.

======================================================================
DATABASE MIGRATION SAFETY
======================================================================

Do not destroy an existing dev DB to change schema.

If the schema changes during implementation:

provide a clean migration / ALTER strategy

or clearly document rebuilding only if no user data existed yet.

By final implementation, initialization must be repeatable and safe.

======================================================================
ANALYSIS TIMESTAMP
======================================================================

Store the timestamp of the actual analysis.

Use timezone-aware UTC internally where practical.

Display in a user-friendly format.

Do not represent save time as provider-data publication date.

======================================================================
CENSUS VINTAGE
======================================================================

Retain the Census vintage separately from analysis timestamp.

Example:

Analysis:
Oct 2026

Census source:
ACS 2024 5-year

Do not conflate them.

======================================================================
LIVE VS SAVED STATE
======================================================================

Use visually distinct labels:

LIVE ANALYSIS

SAVED SNAPSHOT

Avoid ambiguity.

======================================================================
RE-ANALYSIS
======================================================================

If implementing "Analyze again":

prefer a fresh analysis through the existing provider workflow.

Do not overwrite the original saved snapshot automatically.

A user may choose to save the new result separately.

This makes historical comparison possible later.

======================================================================
MAP ON SAVED DETAIL
======================================================================

If feasible, show the saved coordinates on Mapbox.

However:

the map is a visualization of saved coordinates.

Do not automatically re-fetch all providers merely to display a saved snapshot.

A saved detail page should remain a snapshot.

======================================================================
MAPBOX COST AWARENESS
======================================================================

Avoid unnecessary Mapbox initialization.

Do not load a map on every saved card.

Only initialize a map where it materially helps:

- saved-site detail
- comparison map if intentionally implemented

A Saved Sites list should not generate one map per card.

======================================================================
OPTIONAL COMPARISON MAP
======================================================================

If useful, Comparison may show one map containing markers for selected sites.

Do not create multiple maps.

Use saved coordinates.

Candidate markers must be distinguishable.

Do not require provider re-analysis.

======================================================================
SAVED SITE COUNT
======================================================================

Show a useful count.

Example:

Saved Sites
6 candidate analyses

No artificial maximum is required for saved records.

Comparison remains limited to 2–4.

======================================================================
EMPTY SAVED STATE
======================================================================

When no saved sites exist:

show a premium empty state.

Example:

NO SAVED SITES YET

Analyze a restaurant location and save the result to build your candidate
workspace.

[ Analyze a location ]

Do not show blank tables.

======================================================================
EMPTY COMPARE STATE
======================================================================

When fewer than two saved sites exist:

show:

SAVE AT LEAST TWO SITES TO COMPARE

with a path back to Analyze / Saved Sites.

======================================================================
COMPARE PICKER
======================================================================

Create a clean selection UI.

Example:

Select up to 4 saved analyses

☐ Aurora — Indian Restaurant
☐ Greeley — Indian Restaurant
☐ Denver — Coffee
☐ Chicago — Pizza

[ Compare selected ]

Disable or reject selections above 4.

Provide server-side validation too.

======================================================================
COMPARISON SORTING
======================================================================

Preserve selection order where practical.

Do not silently reorder sites only by score unless clearly indicated.

======================================================================
COMPARISON METRIC HIGHLIGHTING
======================================================================

Use subtle highlight badges:

Highest score
Highest coverage
Lowest known occupancy
Strongest competition factor

Only when data are actually comparable.

Do not highlight a demo value against real values without a warning.

======================================================================
EVIDENCE-AWARE COMPARISON
======================================================================

Evidence quality matters.

Example:

Site A
Rent 70
PARTIAL

Site B
Rent 55
DEMO

Do not present 70 vs 55 as equally supported facts.

The comparison UI must display evidence status near the value.

======================================================================
DETERMINISTIC INSIGHTS
======================================================================

Comparison insights must be rules-based.

No AI/LLM in Sprint 09.

Examples:

"If only fully real factors are considered, Denver has stronger demographic
evidence."

"Aurora's rent factor uses partial user-supplied evidence while Greeley's rent
factor remains demo."

Do not hallucinate causal explanations.

======================================================================
NO SCORE RECALCULATION FOR SAVED SNAPSHOTS
======================================================================

Saved snapshots preserve their score at analysis time.

Do not recalculate historical saved scores using future changed scoring code unless
the user explicitly re-analyzes.

Store:

score_model_version

This is essential.

======================================================================
MODEL VERSION DISPLAY
======================================================================

Saved details should indicate:

VenueBite Score Model v2

Competition Model v1

Commercial Occupancy Model v1

where applicable.

======================================================================
SAVED SITE SERVICE
======================================================================

SavedSiteService responsibilities should include:

- validate save request
- normalize display name
- construct snapshot from completed analysis
- save snapshot
- retrieve site
- list sites
- delete site

Repository handles persistence.

Service handles domain logic.

======================================================================
COMPARISON SERVICE
======================================================================

ComparisonService should:

- load selected snapshots
- validate 2–4 IDs
- preserve evidence states
- calculate comparison display structures
- generate deterministic highlights
- handle missing metrics safely

It must not mutate saved snapshots.

======================================================================
ROUTES
======================================================================

Possible routes:

GET /
Analyze

POST /analyze

POST /saved
Save current analysis

GET /saved
Saved site list

GET /saved/<id>
Saved snapshot detail

POST /saved/<id>/delete
Delete

GET or POST /compare
Select/compare saved snapshots

Choose routes consistent with current project architecture.

======================================================================
FLASH / USER FEEDBACK
======================================================================

Provide polished feedback:

Site saved

Site deleted

Unable to save stale analysis

Select at least two sites

Maximum four sites can be compared

Avoid raw exception messages.

======================================================================
ERROR HANDLING
======================================================================

Database failures must not expose stack traces in normal UI.

Handle:

- missing database directory
- missing record
- invalid site ID
- malformed JSON if structured JSON is used
- failed insert
- failed delete

Log sanitized developer information.

======================================================================
DATABASE FILE PROTECTION
======================================================================

Make sure:

instance/
or database-specific path

is ignored correctly where appropriate.

Do NOT accidentally ignore source files in instance/ if Flask uses any.

Target the database file or safe directory intentionally.

======================================================================
SPRINT 08 DESIGN SYSTEM
======================================================================

Saved and Compare pages must match the existing futuristic design:

- midnight background
- glass surfaces
- consistent accent colors
- typography
- badge system
- motion
- spacing
- responsive behavior

Do not create plain white CRUD pages.

======================================================================
MOTION
======================================================================

Use subtle motion only:

- card hover
- selection state
- comparison transitions

Honor prefers-reduced-motion.

======================================================================
MOBILE SAVED SITES
======================================================================

Saved cards should stack naturally.

Primary actions remain usable.

Do not create tiny table columns.

======================================================================
MOBILE COMPARISON
======================================================================

A 4-column comparison cannot reasonably fit on 390px.

Implement a mobile strategy such as:

- horizontally scrollable comparison matrix
- sticky metric-name column
or
- site-by-site comparison cards

Ensure users can still compare exact values.

======================================================================
ACCESSIBILITY
======================================================================

Requirements:

- semantic navigation
- keyboard usable save actions
- keyboard usable compare selection
- proper form labels
- delete confirmation accessible
- table headers where tables are used
- no color-only distinction
- clear focus states
- screen-reader labels on icon buttons

======================================================================
TESTING
======================================================================

Preserve all Sprint 01–08 tests.

Run:

python -m pytest

and all JS tests.

Add comprehensive persistence tests.

======================================================================
DATABASE TESTING
======================================================================

Tests must use isolated temporary databases.

Never write test data into the developer's real:

instance/venuebite.db

Use temp directories or test DB configuration.

======================================================================
REPOSITORY TESTS
======================================================================

Test:

- schema initialization
- insert
- retrieve
- list
- delete
- nonexistent ID
- multiple records
- data survives repository/service reconstruction
- SQL injection-like input remains harmless

======================================================================
SAVED SITE SERVICE TESTS
======================================================================

Test:

- valid analysis saves
- stale analysis rejected
- blank name rejected
- trimmed name
- long name validation
- snapshot timestamp
- score/model versions preserved
- evidence statuses preserved
- occupancy fields preserved
- missing parcel handled
- demo rent handled
- partial rent handled

======================================================================
COMPARISON TESTS
======================================================================

Test:

- two sites
- three sites
- four sites
- one site rejected
- five sites rejected
- invalid ID
- duplicate ID behavior
- mixed real/demo evidence
- unavailable fields
- partial occupancy
- comparison highlights
- score order
- coverage order
- no false "best site" recommendation

======================================================================
ROUTE TESTS
======================================================================

Test:

- save route
- saved list
- saved detail
- delete POST
- destructive GET unavailable
- compare selection
- invalid selections
- database error handling
- no saved records
- single saved record

======================================================================
SECURITY TESTS
======================================================================

Test:

- HTML saved-site name escaping
- SQL injection-style saved name
- invalid IDs
- deletion cannot use arbitrary SQL
- malformed snapshot data
- source URLs remain safely rendered if stored

======================================================================
REGRESSION TESTS
======================================================================

Confirm unchanged:

Population weight 30%
Income weight 30%
Rent weight 20%
Competition weight 20%

Score Model v2

Competition Model v1

Commercial Occupancy Model v1

Data Coverage semantics

Mapbox integration

Census integration

Regrid integration

Sprint 08 UI functionality

======================================================================
MANUAL ACCEPTANCE SCENARIO A
======================================================================

Analyze:

Aurora, Colorado
Indian Restaurant
3 miles

Save as:

Aurora — Indian Restaurant

Verify:

- save succeeds
- saved-site card appears
- location correct
- concept correct
- score correct
- coverage correct
- snapshot time present

======================================================================
MANUAL ACCEPTANCE SCENARIO B
======================================================================

Analyze another location such as:

Greeley, Colorado
Indian Restaurant

Save it.

Verify two records exist.

======================================================================
MANUAL ACCEPTANCE SCENARIO C
======================================================================

Compare Aurora and Greeley.

Verify:

- scores displayed
- coverage displayed
- factor values displayed
- evidence status displayed
- competition differences displayed
- demographic differences displayed
- missing parcel states handled
- deterministic comparison insight

======================================================================
MANUAL ACCEPTANCE SCENARIO D
======================================================================

Save Aurora with Sprint 07 occupancy inputs:

2,800 SF
NNN
$32/SF/year
$8.50/SF/year additional
$10,000 monthly budget

Verify saved snapshot preserves approximately:

$7,466.67 monthly base rent
$1,983.33 monthly additional
$9,450 monthly known occupancy
94.5% budget utilization
66 rent score
PARTIAL rent evidence
90% coverage when other factors are real

======================================================================
MANUAL ACCEPTANCE SCENARIO E
======================================================================

Compare:

Aurora occupancy-supported snapshot

against:

a demo-rent snapshot

Verify:

the UI clearly identifies evidence differences.

Do not present the factors as equally verified.

======================================================================
MANUAL ACCEPTANCE SCENARIO F
======================================================================

Delete a saved site.

Verify:

- confirmation
- POST deletion
- record disappears
- comparison gracefully handles previously selected deleted record

======================================================================
MANUAL ACCEPTANCE SCENARIO G
======================================================================

Restart Flask.

Verify saved records remain.

This proves actual persistence.

======================================================================
NO PROVIDER CALLS ON SAVED LIST
======================================================================

Opening Saved Sites should not automatically call:

Mapbox search
Mapbox POI search
Census
Regrid

Saved Sites is snapshot browsing.

Confirm this.

======================================================================
NO PROVIDER CALLS ON COMPARE
======================================================================

Comparison should use saved normalized snapshot data.

Do not silently trigger fresh provider calls.

======================================================================
DATABASE INSPECTION
======================================================================

Inspect SQLite schema after implementation.

Confirm:

- expected fields
- no plaintext API tokens
- no raw provider payload dump
- no unnecessary sensitive information

======================================================================
README
======================================================================

Update README with:

- Sprint 09 overview
- SQLite persistence
- database location
- saved-site workflow
- comparison workflow
- snapshot semantics
- model-version preservation
- evidence-aware comparison
- how to initialize/run
- how to test
- database not committed
- future authentication/PostgreSQL path

======================================================================
ENGINEERING DOCUMENT
======================================================================

Create:

docs/saved-sites-comparison-v1.md

Document:

- persistence architecture
- database schema
- snapshot model
- repository/service responsibilities
- saved-site lifecycle
- comparison rules
- evidence handling
- model versioning
- provider-data retention policy
- security
- limitations
- migration path to accounts/PostgreSQL

======================================================================
DO NOT BUILD IN SPRINT 09
======================================================================

Do NOT implement:

- authentication
- signup/login
- Keycloak
- PostgreSQL
- Redis
- Docker
- AI chatbot
- OpenAI API
- zoning
- permitting
- commercial listing discovery
- market rent provider
- payments
- teams
- collaboration
- sharing links
- cloud sync
- email

Keep Sprint 09 focused.

======================================================================
ACCEPTANCE CRITERIA
======================================================================

Sprint 09 is complete only when:

1. SQLite persistence exists.
2. Database is ignored by Git.
3. Schema initializes safely.
4. Completed live analyses can be saved.
5. Stale analyses cannot be saved as current.
6. Saved names are validated.
7. Saved snapshot records preserve location.
8. Saved snapshot records preserve concept/radius.
9. Scores are preserved.
10. model version is preserved.
11. Data Coverage is preserved.
12. factor scores are preserved.
13. factor evidence statuses are preserved.
14. weighted contributions are preserved.
15. demographic summaries are preserved.
16. competition summaries are preserved.
17. site summaries are preserved where available.
18. occupancy summaries are preserved where available.
19. raw provider payloads are not unnecessarily persisted.
20. Saved Sites page exists.
21. Saved-site detail exists.
22. deletion works via non-GET destructive route.
23. records survive Flask restart.
24. Compare page exists.
25. 2–4 sites can be compared.
26. comparison supports missing data.
27. comparison is evidence-aware.
28. deterministic comparison highlights exist.
29. no automatic "best site" recommendation exists.
30. saved pages do not trigger fresh provider analysis.
31. comparison does not trigger provider analysis.
32. Saved Sites nav is functional.
33. Compare nav is functional.
34. Find an Area remains hidden.
35. Sprint 08 visual language is preserved.
36. desktop layout works.
37. mobile layout works.
38. accessibility basics work.
39. existing tests pass.
40. new tests pass.
41. no secrets are persisted.
42. `.env` remains ignored.
43. database remains untracked.
44. no commit is made.
45. no push is made.

======================================================================
FINAL VERIFICATION
======================================================================

Before completion:

1. Run python -m pytest.
2. Run all JavaScript tests.
3. Start VenueBite.
4. Analyze Aurora.
5. Save Aurora.
6. Analyze another location.
7. Save it.
8. Open Saved Sites.
9. Open each saved detail.
10. Compare both sites.
11. Save an occupancy-supported scenario.
12. Compare partial rent vs demo rent.
13. Delete a test site.
14. Restart Flask.
15. Confirm remaining sites persist.
16. Verify Saved Sites generates no fresh provider calls.
17. Verify Compare generates no fresh provider calls.
18. Verify Mapbox live analysis still works.
19. Verify Census live analysis still works.
20. Verify Competition live analysis still works.
21. Verify Regrid behavior remains unchanged.
22. Verify Score Model v2 unchanged.
23. Verify Commercial Occupancy Model v1 unchanged.
24. Check mobile layout.
25. Check browser console.
26. Check Flask logs.
27. Inspect SQLite schema.
28. Verify no API tokens in database.
29. Inspect git diff.
30. Inspect git status.
31. Verify database file is ignored.
32. Verify `.env` remains ignored.

DO NOT COMMIT.

DO NOT PUSH.

======================================================================
FINAL REPORT
======================================================================

When complete, provide a detailed report containing:

1. Sprint 09 summary
2. Persistence architecture
3. Database path
4. Database schema
5. Schema initialization behavior
6. Repository architecture
7. SavedSiteService behavior
8. Snapshot contents
9. Snapshot versioning
10. Saved Sites UX
11. Saved detail UX
12. Delete behavior
13. Compare selection UX
14. Comparison architecture
15. Metrics compared
16. Evidence-aware comparison behavior
17. Deterministic highlights
18. Provider-data retention behavior
19. Provider-call behavior on saved pages
20. Security controls
21. Mobile behavior
22. Accessibility work
23. Files created
24. Files modified
25. Python test count
26. JavaScript test count
27. Manual acceptance results
28. Persistence restart verification
29. Known limitations
30. Future PostgreSQL/auth migration considerations
31. Git status
32. Anything Chris should manually inspect

Do not commit.
Do not push.