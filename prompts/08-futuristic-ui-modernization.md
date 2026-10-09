# Sprint 08 — Futuristic UI Modernization + Product Experience

You are working inside the existing VenueBite repository.

VenueBite is a Flask/Jinja full-stack restaurant location-intelligence web application.

The application now has substantial working product functionality:

Sprint 01
- Flask/Jinja application foundation
- analysis workflow
- scoring foundation
- tests

Sprint 02
- real Mapbox location search
- real coordinates
- interactive map
- satellite mode
- geographic context

Sprint 03
- real nearby restaurant competition
- direct competitor classification
- Competition Model v1
- competitor map markers

Sprint 04
- real U.S. Census demographics
- tract population
- household income
- demographic provenance

Sprint 05
- VenueBite Score Model v2
- weighted factor contributions
- Data Coverage
- deterministic explanations
- strengths and risks

Sprint 06
- Regrid parcel/site intelligence
- parcel boundaries
- site provenance
- zoning/value/sale cautions

Sprint 07
- commercial occupancy input
- lease/rent normalization
- monthly and annual occupancy calculations
- Commercial Occupancy Model v1
- partial user-supplied evidence
- Data Coverage integration
- occupancy warnings and provenance

The backend/product intelligence is now significantly stronger than the current visual experience.

SPRINT 08 IS A PRODUCT EXPERIENCE AND VISUAL DESIGN SPRINT.

Do not redesign the underlying business logic.

Do not break existing analysis functionality.

======================================================================
PRIMARY SPRINT GOAL
======================================================================

Transform VenueBite from a functional prototype into a polished, futuristic,
premium location-intelligence web application.

The desired impression should be:

- modern
- sophisticated
- cinematic
- intelligent
- data-driven
- futuristic
- trustworthy
- premium SaaS
- visually impressive without becoming distracting

VenueBite should feel like a real technology startup product rather than a
school project or prototype dashboard.

The redesign must improve:

- first impression
- visual hierarchy
- navigation
- workspace organization
- score visualization
- factor visualization
- evidence visualization
- map presentation
- commercial occupancy presentation
- strengths/risks presentation
- mobile responsiveness
- accessibility
- perceived product quality

======================================================================
DESIGN PHILOSOPHY
======================================================================

VenueBite should feel like a futuristic location-intelligence command center.

Think:

location intelligence
+
restaurant strategy
+
modern geospatial analytics
+
premium SaaS dashboard

Avoid:

- generic Bootstrap appearance
- large blocks of plain text
- excessive borders
- random gradients
- overly bright neon everywhere
- childish gaming UI
- excessive animation
- clutter
- fake futuristic effects
- heavy video that makes the product slower or harder to read

Use motion and graphics deliberately.

======================================================================
CRITICAL STARTING PROCEDURE
======================================================================

Before editing anything:

1. Read AGENTS.md completely.
2. Read this Sprint 08 prompt completely.
3. Inspect the repository.
4. Run:

   git status
   git branch --show-current
   python -m pytest

5. Record baseline Python test count.

6. Run existing JavaScript tests.

7. Inspect:

   templates/base.html
   templates/results.html
   templates/_search_form.html
   templates/_map_workspace.html
   templates/_site_intelligence.html
   templates/_occupancy.html
   templates/_occupancy_form.html

   static/css/style.css
   static/js/analysis-state.js
   static/js/map-viewer.js
   static/js/parcel-layer.js

   venuebite/routes.py
   venuebite/services/analysis_service.py

8. Inspect current desktop and mobile application visually.

Understand existing functionality before changing presentation.

======================================================================
GIT RULES
======================================================================

DO NOT:

- commit
- push
- reset
- rewrite history
- create another branch
- remove working functionality

Chris will review and commit manually.

======================================================================
NO BACKEND REWRITE
======================================================================

This sprint is primarily UI/UX.

Preserve:

- Mapbox location search
- map/satellite modes
- competitor markers
- Census demographics
- Competition Model v1
- Site Intelligence
- parcel boundaries
- Score Model v2
- Commercial Occupancy Model v1
- Data Coverage
- provenance
- explanations
- validation
- existing forms
- current routes

Do not change scoring simply to make the UI look better.

======================================================================
NAVIGATION CLEANUP
======================================================================

The current navigation includes unfinished product items such as:

Compare
Coming soon

Saved Locations
Coming soon

Find an Area
Coming soon

These repeated "Coming soon" elements make VenueBite feel unfinished.

For Sprint 08:

HIDE unfinished navigation features from the primary navigation.

The main navigation should show only functioning product areas.

At minimum:

VenueBite logo / brand
Analyze

Do not delete future functionality architecture if any exists.

Simply remove or hide unfinished navigation entries from normal user-facing
navigation until those features are implemented.

Do not show repeated "Coming soon" badges in the primary application shell.

If a future-feature location must remain visible for technical reasons, use one
subtle disabled treatment rather than repeated promotional placeholders.

======================================================================
APPLICATION SHELL
======================================================================

Redesign the overall shell.

Suggested structure:

LEFT / TOP BRAND AREA
VenueBite
Location Intelligence

PRIMARY NAV
Analyze

UTILITY AREA
optional lightweight status/help/about controls if already useful

MAIN CONTENT
futuristic analysis workspace

The shell should feel intentional and spacious.

Desktop may use:

- compact sidebar
or
- premium top navigation

Choose the approach that best fits the current architecture.

Do not waste large amounts of horizontal space.

======================================================================
FUTURISTIC BACKGROUND
======================================================================

Chris wants VenueBite to feel futuristic with a visually rich background.

Create an elegant animated environmental background.

Preferred implementation:

- dark deep-space / midnight gradient
- subtle moving gradient mesh
- animated glow fields
- faint geospatial grid
- very subtle data lines / map-coordinate motifs
- soft blurred light sources
- optional particle/data-point motion
- optional animated map-network effect

The background must remain subordinate to the application content.

Do not make the page look like a nightclub.

======================================================================
VIDEO-LIKE EXPERIENCE
======================================================================

The desired feeling is similar to a high-end cinematic animated/video
background.

However:

Do NOT depend on a remote stock video.

Do NOT download copyrighted footage.

Do NOT add a huge video file merely for decoration.

Prefer creating a "video-like" visual experience using:

- CSS animation
- gradients
- SVG
- Canvas
- lightweight native JavaScript

If there is already an appropriate locally owned video asset in the repository,
it may be considered.

Otherwise use performant generated animation.

The visual effect should resemble a moving digital geospatial environment.

======================================================================
BACKGROUND PERFORMANCE
======================================================================

The futuristic background must:

- not block interaction
- not consume excessive CPU
- not interfere with Mapbox
- not reduce text contrast
- not significantly slow first render
- not trigger constant unnecessary layout recalculation

Honor:

prefers-reduced-motion

When reduced motion is enabled:

- stop decorative animation
- preserve visual appearance

======================================================================
COLOR SYSTEM
======================================================================

Create a coherent design system.

Suggested direction:

Background:
near-black / midnight navy

Surfaces:
deep navy
charcoal glass
translucent dark panels

Primary accent:
electric blue / cyan family

Secondary accent:
subtle violet / indigo

Positive:
restrained green

Warning:
amber

Risk:
muted coral/red

Evidence:
distinct but tasteful badges

Do not use ten unrelated accent colors.

Do not hard-code inconsistent colors throughout templates.

Use CSS custom properties.

Example conceptual tokens:

--bg-primary
--bg-secondary
--surface
--surface-elevated
--surface-glass
--border-soft
--text-primary
--text-secondary
--text-muted
--accent-primary
--accent-secondary
--positive
--warning
--risk

======================================================================
GLASS / SURFACE DESIGN
======================================================================

Use premium glass-like surfaces where appropriate:

- translucent backgrounds
- subtle backdrop blur
- restrained borders
- soft shadows
- subtle internal highlights

Do not overdo blur.

Cards should have clear hierarchy.

Primary information cards should look more important than secondary metadata.

======================================================================
TYPOGRAPHY
======================================================================

Improve typography hierarchy.

Use existing fonts or safe high-quality web/system font stacks.

Avoid adding large third-party font dependencies unless clearly justified.

Hierarchy:

Product brand
Page title
Section title
Metric value
Metric label
Supporting explanation
Provenance metadata

Large numeric values should be easy to scan.

Long explanatory paragraphs should not dominate the screen.

======================================================================
ANALYZE PAGE HERO
======================================================================

Redesign the top analysis area.

It should immediately communicate:

VenueBite helps evaluate restaurant locations using real geographic,
demographic, competition, site, and occupancy evidence.

Create a compact but premium hero/workspace header.

Possible visual:

VENUEBITE
LOCATION INTELLIGENCE

Analyze a restaurant location

Search any city, neighborhood, ZIP, intersection, or address and evaluate the
location using multiple layers of evidence.

Do not make the hero excessively tall.

The actual application should remain visible quickly.

======================================================================
SEARCH / ANALYSIS FORM
======================================================================

Redesign the search controls to feel premium.

Current important controls:

- Location
- Restaurant concept
- Radius
- Commercial property terms

Present the primary three controls clearly.

Recommended desktop layout:

Location
large dominant input

Concept
secondary input/select

Radius
compact control

Analyze Location
prominent CTA

Use modern focus states.

Use real labels.

Do not rely on placeholders alone.

======================================================================
COMMERCIAL OCCUPANCY FORM
======================================================================

Keep commercial property terms optional.

Use a polished expandable section:

"Analyze a specific commercial space"

or:

"Add commercial property terms"

Collapsed by default.

When expanded:

organize fields into meaningful groups:

SPACE
- property address
- available SF

LEASE
- asking rent
- rent basis
- lease structure

ADDITIONAL COSTS
- NNN/CAM
- charge basis

BUSINESS THRESHOLD
- monthly occupancy budget

SOURCE
- label
- URL
- notes

Avoid making the section look like one huge form.

======================================================================
MAIN RESULTS WORKSPACE
======================================================================

The current results page is too vertically stacked.

Redesign into a structured intelligence workspace.

Desktop target:

----------------------------------------------------------
|                     MAP / LOCATION                     |
----------------------------------------------------------
| SCORE OVERVIEW            | FACTOR INTELLIGENCE        |
|                           |                            |
----------------------------------------------------------
| DEMOGRAPHICS              | COMPETITION                |
----------------------------------------------------------
| SITE INTELLIGENCE         | OCCUPANCY                  |
----------------------------------------------------------
| STRENGTHS & RISKS / EVIDENCE QUALITY                  |
----------------------------------------------------------

Exact layout may differ if a stronger solution emerges.

The important point:

Users should visually understand the analysis before reading paragraphs.

======================================================================
MAP EXPERIENCE
======================================================================

Make the map feel like the centerpiece of a location-intelligence platform.

Improve:

- map card framing
- map header
- map controls
- candidate location presentation
- legend
- coordinate display
- standard/satellite toggle

Preserve all existing map behavior.

Possible map header:

GEOGRAPHIC EXPLORER

Aurora, Colorado, United States
39.74033, -104.83067

LIVE LOCATION

Use subtle visual status indicators.

======================================================================
MAP HEIGHT
======================================================================

On desktop:

give the map a substantial height.

It should not feel compressed.

Suggested visual target:

approximately 480–620px depending on viewport

Do not hard-code a layout that breaks smaller laptops.

Use responsive CSS.

======================================================================
OPPORTUNITY SCORE VISUAL
======================================================================

The Opportunity Score should become one of the strongest visuals in VenueBite.

Create a premium circular score visualization.

Example:

        46.1
       / 100

   CHALLENGING

VenueBite Score Model v2

Potential implementation:

- SVG circular progress
- CSS conic-gradient
- accessible numeric text

Do not use a heavy charting library solely for this.

Color should reflect classification carefully:

Strong
Promising
Mixed
Challenging

Do not make low scores look like application errors.

======================================================================
SCORE ANIMATION
======================================================================

Optional:

animate score ring from zero to result when a new analysis completes.

Only if lightweight.

Honor prefers-reduced-motion.

Do not delay result readability.

======================================================================
DATA COVERAGE VISUAL
======================================================================

Data Coverage should have its own distinct visualization.

Examples:

coverage ring
or
horizontal evidence meter

Show:

80%
High data coverage

and clearly maintain:

"Evidence coverage — not success probability."

Do not visually confuse Opportunity Score with Data Coverage.

======================================================================
FACTOR INTELLIGENCE
======================================================================

Current factors:

Population
Income
Rent
Competition

Redesign them into premium factor cards.

Each factor should clearly show:

Factor name

Score

Weight

Contribution

Evidence type

Source/model

Example:

POPULATION

36.8 / 100

30% weight
11.04 points

REAL CENSUS ESTIMATE

Use concise badges.

======================================================================
FACTOR CONTRIBUTION GRAPHIC
======================================================================

Add a visual contribution graphic.

Example:

Population     ███████████          11.04
Income         █████████████        13.35
Rent           ███████████          11.00
Competition    ███████████          10.70

Use native CSS/SVG where possible.

The bars should represent weighted contribution, not raw score.

Include accessible text.

Do not introduce a charting library solely for four bars.

======================================================================
EVIDENCE BADGES
======================================================================

Create visually consistent evidence badges.

Examples:

REAL
PARTIAL
DEMO
UNAVAILABLE
FALLBACK

Possible display:

REAL · CENSUS
REAL · MAPBOX
PARTIAL · USER SUPPLIED
DEMO
REAL · REGRID

Do not make badges excessively bright.

======================================================================
PROVENANCE DISCLOSURE
======================================================================

The current "Source & model" information is important but should not dominate.

Create expandable provenance details.

Example:

[ View source & model ]

When opened:

Provider
Model
Vintage
Evidence status
Limitations

Maintain accessibility and server-rendered fallback.

======================================================================
AREA INSIGHTS
======================================================================

Redesign Census / area insights as a visual intelligence panel.

Highlight:

Tract population
Median household income
Population growth availability
Commercial rent state
Observed restaurants
Schools/universities

Real/demo/unavailable status must remain obvious.

Do not hide data limitations.

======================================================================
DEMOGRAPHIC VISUALS
======================================================================

Create simple elegant visuals where they genuinely help.

Possible:

Population
large number + score indicator

Income
large currency number + score indicator

Margins of error
subtle secondary detail

Avoid meaningless charts with only one number.

======================================================================
COMPETITION EXPERIENCE
======================================================================

Nearby competition is a major product feature.

Redesign its top summary.

Example:

COMPETITION INTELLIGENCE

53.5 / 100

26
restaurants observed

1
direct competitor

2.62 mi
nearest direct match

3 mi
search radius

Then show:

Competition pressure
Moderate

Use a visual pressure bar.

======================================================================
COMPETITOR TABLE
======================================================================

Improve the competitor tables.

Current content must remain:

Restaurant
Match
Distance
Address

Use:

- better spacing
- sticky header if useful
- badges for match type
- visually distinct distance
- responsive layout
- horizontal overflow handling where necessary

Do not remove provider limitations.

======================================================================
SITE INTELLIGENCE UI
======================================================================

Improve Sprint 06 presentation.

When no parcel is returned:

do not show an alarming error-style empty block.

Instead display a calm state:

SITE INTELLIGENCE

Parcel data unavailable for this point

No matching parcel was returned by the current Regrid entitlement/search.
This does not establish that no parcel exists.

When parcel data exists:

highlight:

- parcel area
- land-use
- building area if available
- zoning code
- assessment information
- sale information
- source

Keep legal/value cautions.

======================================================================
COMMERCIAL OCCUPANCY RESULTS
======================================================================

When Sprint 07 occupancy information exists:

create a premium occupancy card.

Example:

COMMERCIAL OCCUPANCY

2,800 SF
NNN

$7,467
monthly base rent

$1,983
additional charges

$9,450
estimated known occupancy cost

$10,000
monthly budget

94.5%
budget utilization

Rent factor
66 / 100

PARTIAL · USER SUPPLIED

Use clear separation between:

base rent
additional charges
known occupancy cost
budget

Do not imply unknown expenses are included.

======================================================================
OCCUPANCY BUDGET GAUGE
======================================================================

Add a clean budget-utilization visual.

Example:

0% ---------------- 94.5% ---- 100% --------

or a polished progress meter.

Important:

Going above 100% must not visually break the component.

Support values >100%.

======================================================================
STRENGTHS & RISKS
======================================================================

Redesign the Strengths & Risks section.

Use cards with icons or subtle indicators.

Example:

STRENGTHS
No fully real-data factors meet the current strength threshold.

RISKS / REVIEW ITEMS

Population
36.8
Tract population context needs review.

Income
44.5
Purchasing-power context needs review.

Rent
Demo
Commercial rent requires verification.

Competition
53.5
Moderate observed pressure.

Do not make the section feel like a wall of text.

======================================================================
SMART INFORMATION DENSITY
======================================================================

A core Sprint 08 goal is reducing visible text density.

Do not delete important disclaimers.

Instead use hierarchy:

Primary:
decision metrics

Secondary:
short explanation

Tertiary:
expandable methodology / provenance / limitations

Users should not need to read everything to understand the result.

======================================================================
PROGRESSIVE DISCLOSURE
======================================================================

Use expandable sections for:

- methodology
- evidence details
- source/model details
- provider limitations
- advanced lease notes

Important disclaimers should still remain visible where legally/analytically
necessary.

Do not bury critical facts.

======================================================================
ANALYSIS SUMMARY
======================================================================

Create a concise high-level summary near the score.

Example:

Aurora, Colorado
Indian Restaurant

46.1 / 100
Challenging

Evidence coverage
80%

Key review areas
Population
Income
Commercial rent verification

This gives users immediate understanding.

======================================================================
STATUS LANGUAGE
======================================================================

Use professional labels.

Prefer:

Live data
Real evidence
Partial evidence
Demo
Unavailable
Needs verification

Avoid excessive technical wording in the primary UI.

Technical detail can remain in methodology sections.

======================================================================
MICROINTERACTIONS
======================================================================

Add subtle premium interaction states:

- hover elevation
- button glow
- card focus
- accordion transitions
- score reveal
- loading shimmer/skeleton where appropriate
- selected map mode states

Keep them quick.

No slow theatrical animations.

======================================================================
ANALYSIS LOADING STATE
======================================================================

Improve perceived quality when analysis runs.

The Analyze button should clearly transition into a loading state.

Example:

Analyzing location...

Optionally show compact steps such as:

Resolving geography
Reading demographics
Observing competition
Checking parcel context
Calculating score

Only if implementation reflects actual flow reasonably.

Do not fabricate percentage completion.

======================================================================
EMPTY STATE
======================================================================

Before analysis:

show an intentional workspace rather than large blank space.

Example:

READY FOR ANALYSIS

Search a location and select a restaurant concept to begin.

Visual:
subtle animated map-grid / location pulse graphic.

Do not show fake score results.

======================================================================
ERROR STATES
======================================================================

Improve errors visually.

Provider failures should look like data-state messages, not application crashes.

Examples:

Map temporarily unavailable

Census context unavailable

Parcel data unavailable

Commercial terms incomplete

Use calm language.

======================================================================
MAPBOX ERRORS
======================================================================

Do not alter the working Mapbox authentication merely for visual changes.

The Mapbox account has now been upgraded from demo access.

Preserve current working token loading behavior.

Never print or expose MAPBOX_ACCESS_TOKEN.

======================================================================
RESPONSIVE DESIGN
======================================================================

Sprint 08 must work at:

large desktop
normal laptop
tablet
mobile

Desktop can use multi-column dashboards.

Tablet should collapse gracefully.

Mobile should become a single readable flow.

Map must remain usable on mobile.

Tables must not destroy the page width.

======================================================================
MOBILE PRIORITY ORDER
======================================================================

On mobile, prioritize:

1. search
2. location
3. opportunity score
4. Data Coverage
5. map
6. factor intelligence
7. strengths/risks
8. demographics
9. competition
10. site intelligence
11. occupancy

Exact ordering may be adjusted based on implementation.

======================================================================
ACCESSIBILITY
======================================================================

Maintain good accessibility.

Requirements:

- semantic HTML
- keyboard navigability
- visible focus states
- adequate contrast
- labels for inputs
- ARIA labels where appropriate
- chart values available as text
- motion reduction
- buttons not represented only by icons
- no information communicated only through color

======================================================================
PERFORMANCE
======================================================================

Do not make VenueBite visually impressive at the cost of performance.

Avoid:

- giant videos
- giant background images
- excessive blur layers
- huge JS animation libraries
- multiple chart libraries
- expensive constant repaint loops

Prefer:

- CSS
- SVG
- small native JS components

======================================================================
DEPENDENCY RULE
======================================================================

Do not add React.

Do not add Vue.

Do not add Angular.

Do not migrate away from Flask/Jinja.

Do not add a full UI framework solely for Sprint 08.

Do not add a charting library unless there is a substantial documented reason.

Native SVG/CSS is preferred for current metrics.

======================================================================
NO MARKETING-LANDING-PAGE TAKEOVER
======================================================================

VenueBite is an application.

Do not turn the project into primarily a marketing landing page.

A concise hero is fine.

The analysis workspace must remain the product focus.

======================================================================
NO BACKEND FEATURE CREEP
======================================================================

Sprint 08 must not implement:

- saved locations
- comparison engine
- property discovery
- database
- authentication
- payments
- AI assistant
- zoning verification
- permit engine
- Docker
- new APIs

Those belong to later sprints.

======================================================================
CSS ORGANIZATION
======================================================================

Refactor CSS enough to create a maintainable design system.

Use sections such as:

tokens
reset/base
layout
navigation
hero
forms
buttons
cards
map
metrics
score
coverage
factors
competition
site intelligence
occupancy
strengths/risks
utilities
responsive
motion

Do not create arbitrary duplicated rules.

======================================================================
TEMPLATE ORGANIZATION
======================================================================

If results.html is becoming unwieldy:

extract focused partials.

Possible:

_score_overview.html
_factor_intelligence.html
_demographic_intelligence.html
_competition_intelligence.html
_evidence_quality.html
_strengths_risks.html

Only refactor if it improves maintainability.

Do not create dozens of tiny partial files unnecessarily.

======================================================================
JAVASCRIPT
======================================================================

Keep JavaScript modular.

If needed add modules for:

- UI animation
- accordions
- score visuals
- progress visuals
- loading state

Do not mix these responsibilities into Mapbox code.

Do not break analysis-state.js.

======================================================================
DESIGN CONSISTENCY
======================================================================

Every major section should share:

same spacing scale
same border system
same card radius family
same typography hierarchy
same badge system
same evidence system

Avoid creating each section as a separate visual style.

======================================================================
BRANDING
======================================================================

Strengthen the VenueBite identity.

Potential visual motif:

location pin
+
signal/radar
+
restaurant intelligence

Do not introduce a completely new brand name.

Keep:

VenueBite

Possible secondary descriptor:

Location Intelligence

======================================================================
OPTIONAL LOGO MARK
======================================================================

If useful, create a small CSS/SVG brand mark.

No external copyrighted logo.

Do not spend the entire sprint designing a logo.

======================================================================
VISUAL QUALITY BAR
======================================================================

The final result should look appropriate for:

- portfolio screenshots
- internship/job interviews
- startup demo
- investor/product demo
- software engineering portfolio
- desktop application presentation

It should not look like default class-project HTML.

======================================================================
SCREENSHOTS / MANUAL REVIEW
======================================================================

Manually inspect at minimum:

Desktop:
1440px or similar

Laptop:
approximately 1280px

Tablet:
approximately 768px

Mobile:
approximately 390px

Check:

- no overlap
- no clipping
- no unreadable text
- no broken cards
- no giant empty space
- map remains usable
- forms remain usable
- tables remain usable

======================================================================
LIVE ACCEPTANCE LOCATION
======================================================================

Use a real successful analysis during visual verification.

Example:

Aurora, Colorado
Indian Restaurant
3-mile radius

Verify:

- Mapbox
- Census
- competition
- score
- evidence
- Site Intelligence state
- occupancy UI

Also test an occupancy-supported scenario:

Space:
2800 SF

Lease:
NNN

Asking rent:
$32 / SF / year

Additional:
$8.50 / SF / year

Budget:
$10,000/month

Expected approximate:

Base:
$7,466.67/month

Additional:
$1,983.33/month

Known occupancy:
$9,450/month

Budget utilization:
94.5%

Rent:
66/100

Partial evidence

Data Coverage:
approximately 90% when other required evidence is available

Do not modify calculations merely to match visual expectations.

======================================================================
TESTING
======================================================================

Run all existing tests.

python -m pytest

Run JavaScript tests.

Add UI-related tests where meaningful.

Do not create brittle tests that assert exact decorative CSS.

Test functional UI behavior instead:

- unfinished nav links absent
- analysis inputs still submit
- occupancy accordion works
- source details toggles work
- loading state clears
- score output exists
- evidence labels remain correct
- map container remains present
- accessibility labels exist where important
- stale analysis behavior remains intact

======================================================================
REGRESSION REQUIREMENTS
======================================================================

Sprint 08 must not change:

Score Model v2 factor weights

Population:
30%

Income:
30%

Rent:
20%

Competition:
20%

Commercial Occupancy Model v1 calculations

Competition Model v1

Census scoring

Regrid behavior

Data Coverage evidence semantics

Provider provenance semantics

======================================================================
MANUAL ACCEPTANCE CHECKLIST
======================================================================

Scenario A — No analysis

Verify:

- futuristic empty state
- clean navigation
- no repeated Coming soon
- search controls clearly visible
- no fake score

Scenario B — Standard live analysis

Verify:

- map
- satellite
- score ring
- Data Coverage
- factor visualization
- contribution visualization
- demographics
- competition
- strengths/risks

Scenario C — Occupancy analysis

Verify:

- optional form
- lease inputs
- cost summary
- utilization visualization
- partial evidence
- score integration

Scenario D — No parcel result

Verify:

- calm unavailable state
- no alarming pseudo-error
- correct Regrid explanation

Scenario E — Provider partial failure

Verify:

- remaining product remains usable
- visual state communicates unavailable evidence cleanly

Scenario F — Mobile

Verify all core controls and result sections.

======================================================================
COMING-SOON CLEANUP ACCEPTANCE
======================================================================

The primary application navigation must NOT display:

Compare — Coming soon
Saved Locations — Coming soon
Find an Area — Coming soon

unless those features are actually implemented.

Their removal must not create dead links.

Future functionality can remain in code/roadmap.

======================================================================
DOCUMENTATION
======================================================================

Create:

docs/sprint08-ui-system.md

Document:

- visual design principles
- design tokens
- layout system
- evidence badge system
- score visualization
- Data Coverage visualization
- motion behavior
- responsive strategy
- accessibility behavior
- performance considerations
- files changed
- future UI considerations

======================================================================
FINAL VERIFICATION
======================================================================

Before completion:

1. Run:

   python -m pytest

2. Run JavaScript tests.

3. Start the application.

4. Perform desktop analysis.

5. Perform occupancy analysis.

6. Verify Mapbox standard mode.

7. Verify Mapbox satellite mode.

8. Verify competition markers.

9. Verify Census.

10. Verify Site Intelligence.

11. Verify score math unchanged.

12. Verify Data Coverage unchanged except where Sprint 07 already defines
    occupancy evidence behavior.

13. Verify hidden unfinished navigation.

14. Test tablet.

15. Test mobile.

16. Test keyboard navigation.

17. Test reduced-motion behavior where practical.

18. Inspect browser console.

19. Inspect Flask logs.

20. Inspect git diff.

21. Inspect git status.

22. Verify `.env` remains ignored.

23. Verify no tokens or secrets entered repository files.

DO NOT COMMIT.

DO NOT PUSH.

======================================================================
FINAL REPORT
======================================================================

When complete, provide a detailed report containing:

1. Overall visual redesign summary
2. Navigation changes
3. Application-shell changes
4. Background/motion implementation
5. Search experience changes
6. Results workspace changes
7. Opportunity Score visualization
8. Data Coverage visualization
9. Factor intelligence changes
10. Contribution visualization
11. Map UI changes
12. Demographic UI changes
13. Competition UI changes
14. Site Intelligence UI changes
15. Commercial Occupancy UI changes
16. Strengths/Risks UI changes
17. Responsive/mobile work
18. Accessibility work
19. Performance work
20. Files created
21. Files modified
22. Python test count
23. JavaScript test result
24. Manual browser verification
25. Known limitations
26. Git status
27. Anything Chris should manually inspect

Do not commit.
Do not push.