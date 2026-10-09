# Sprint 07 — Commercial Occupancy + Candidate Property Analysis

You are working inside the existing VenueBite repository.

VenueBite is a Flask/Jinja full-stack restaurant location-intelligence web application.

Current product state:

Sprint 01
- Flask/Jinja foundation
- service architecture
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
- Competition Model v1
- competitor map markers

Sprint 04
- U.S. Census tract resolution
- real ACS population
- real median household income
- Population Model v1
- Income Model v1
- demographic provenance

Sprint 05
- VenueBite Score Model v2
- centralized factor weights
- weighted contributions
- Data Coverage
- structured provenance
- deterministic explanations
- strengths/risks
- internal score trace

Sprint 06
- real Regrid parcel/site intelligence
- parcel boundaries
- land-use/property context
- site provenance
- zoning/value/sale cautions
- parcel data intentionally isolated from Score Model v2

Sprint 06 is complete, committed, and pushed.

Sprint 07 adds:

COMMERCIAL OCCUPANCY + CANDIDATE PROPERTY ANALYSIS

No new external API is required for this sprint.

The user may enter terms from a legitimate commercial listing, broker package,
landlord quote, or other source they already have.

VenueBite must calculate and explain commercial occupancy costs without inventing
market facts.

======================================================================
PRIMARY SPRINT GOAL
======================================================================

Allow a user to attach commercial property / lease terms to the currently
selected VenueBite candidate location.

VenueBite should be able to answer:

- How large is the available space?
- What is the asking rent?
- What lease structure is being quoted?
- What is estimated monthly base rent?
- What is estimated annual base rent?
- What additional NNN/CAM charges were supplied?
- What is estimated monthly occupancy cost from the supplied terms?
- How does that cost compare with the user's own stated occupancy budget,
  if one is supplied?
- Is the rent factor still demo, or is it now supported by candidate-property
  evidence?
- What important lease-cost information is still missing?

The product must not invent commercial market rent.

======================================================================
CRITICAL PRODUCT PRINCIPLE
======================================================================

ASKING RENT IS NOT THE SAME THING AS AFFORDABILITY.

A quoted $30/SF/year rent cannot automatically be called favorable or
unfavorable without context.

A $30/SF rate can mean very different things in:

- Greeley
- Denver
- Chicago
- Manhattan

Therefore Sprint 07 must distinguish:

1. Occupancy calculation
2. Affordability scoring

VenueBite may calculate occupancy cost from supplied terms.

VenueBite must NOT convert a raw asking rent directly into a nationwide
"good/bad rent score" using arbitrary absolute thresholds.

======================================================================
RENT SCORE POLICY
======================================================================

The current VenueBite rent factor is:

20% of Score Model v2

Current state:

DEMO

Sprint 07 may replace the demo rent factor ONLY when enough user-supplied
evidence exists to calculate a defensible affordability score.

The preferred Sprint 07 approach is budget-relative affordability.

Required for a live/user-supported rent score:

- usable property space size
- usable commercial rent terms
- user-supplied monthly occupancy budget OR equivalent documented threshold

If a budget/threshold is not supplied:

- calculate occupancy costs
- show them clearly
- keep the rent factor DEMO
- do not invent a live rent score

This rule is mandatory.

======================================================================
DATA COVERAGE POLICY
======================================================================

Opportunity Score and Data Coverage remain separate.

Current typical successful U.S. analysis before Sprint 07:

Population      real    30%
Income          real    30%
Competition     real    20%
Rent            demo     0% real-data coverage

Total Data Coverage = 80%

User-supplied commercial listing terms are not independently verified provider
data.

Treat sufficiently complete user-supplied occupancy evidence as:

PARTIAL evidence

not fully verified REAL evidence.

Under the existing coverage model:

partial credit = 0.5

Therefore:

rent factor weight = 20%
partial evidence credit = 0.5

coverage contribution = 10 points

A complete user-supported occupancy analysis may raise Data Coverage:

80% → 90%

Do not raise coverage to 100% merely because the user typed listing terms.

Future verified commercial lease/property providers may support full evidence
credit.

======================================================================
CRITICAL STARTING PROCEDURE
======================================================================

Before editing anything:

1. Read AGENTS.md completely.
2. Read this full Sprint 07 prompt.
3. Inspect the repository.
4. Run:

   git status
   git branch --show-current
   python -m pytest

5. Record baseline test count.

6. Inspect at minimum:

   venuebite/scoring.py
   venuebite/data_coverage.py
   venuebite/services/analysis_service.py
   venuebite/services/explanation_service.py

   demographic scoring
   competition scoring
   site intelligence
   provider/provenance models

   templates/results.html
   search/analyze form
   parcel/site templates
   static JavaScript
   static CSS

   README.md
   docs/scoring-model-v2.md
   docs/site-intelligence-v1.md

Understand Sprints 01–06 before modifying architecture.

======================================================================
GIT RULES
======================================================================

DO NOT:

- commit
- push
- create a new branch
- reset
- rewrite Git history
- delete unrelated functionality

Chris will review and commit manually.

======================================================================
NO NEW EXTERNAL PROPERTY PROVIDER
======================================================================

Do not add:

- LoopNet
- Crexi scraping
- CoStar scraping
- Zillow
- Reonomy
- CompStak
- ATTOM
- brokerage scraping
- random listing APIs

Sprint 07 uses user-supplied candidate-property terms.

Architect the system so a licensed commercial-property provider can plug in later.

======================================================================
PROPERTY / OCCUPANCY ARCHITECTURE
======================================================================

Introduce clean commercial occupancy boundaries.

A reasonable structure:

venuebite/
    occupancy.py

venuebite/
    services/
        occupancy_service.py

or another clean equivalent that fits the repository.

Responsibilities:

Occupancy model/calculator
    deterministic lease math

Occupancy service
    input normalization
    validation
    affordability logic
    provenance
    missing-field handling

Analysis service
    orchestration

Routes
    request/response only

Templates
    rendering only

JavaScript
    form state / cost preview only if justified

Do not put lease formulas into templates.

Do not put scoring formulas into JavaScript.

======================================================================
NORMALIZED CANDIDATE PROPERTY INPUT
======================================================================

Create a normalized internal structure conceptually similar to:

{
    "status": "available",

    "source_type": "user_supplied",
    "source_label": "Commercial listing",
    "source_url": "...",

    "property_address": "...",

    "space_size_sqft": 2800,

    "asking_rent": {
        "value": 32.0,
        "basis": "per_sqft_per_year"
    },

    "lease_structure": "nnn",

    "additional_occupancy_rate": {
        "value": 8.50,
        "basis": "per_sqft_per_year"
    },

    "monthly_occupancy_budget": 10000,

    "notes": "..."
}

This is conceptual.

Use immutable/dataclass/domain objects if consistent with existing architecture.

======================================================================
FORM INPUTS
======================================================================

Add a commercial-property / occupancy section to the analysis workflow.

Recommended inputs:

Property / space address
- default to selected candidate address where appropriate
- allow user correction

Available space
- square feet

Asking rent
- numeric

Rent basis
Initial supported values:

- $ / SF / year
- $ / SF / month
- total monthly rent
- total annual rent

Lease structure
Initial values:

- NNN
- Gross
- Modified Gross
- Unknown / Not stated

Additional NNN / CAM / operating charges
Optional numeric field

Additional-charge basis:

- $ / SF / year
- $ / SF / month
- total monthly
- total annual

Monthly occupancy budget
Optional

Listing/source URL
Optional

Source label
Optional

Notes
Optional

Do not add dozens of fields.

Keep the workflow usable.

======================================================================
INPUT OPTIONALITY
======================================================================

The user must still be able to analyze a location WITHOUT providing
commercial-property terms.

If no occupancy information is supplied:

existing Sprint 06 behavior continues

Rent:
DEMO

Data Coverage:
normally 80% when other three factors are real

Do not make Sprint 07 inputs mandatory for normal location analysis.

======================================================================
LEASE STRUCTURE SAFETY
======================================================================

Lease structure changes what asking rent may include.

VenueBite must not pretend to know expenses that the user did not supply.

NNN:

asking base rent may exclude property taxes, insurance, maintenance/CAM, and
other pass-throughs.

Gross:

quoted rent may include more operating expenses, but exact inclusions vary.

Modified Gross:

expense responsibility depends on the lease.

Unknown:

do not assume.

Use cautious language.

Do not automatically invent NNN charges.

======================================================================
BASE RENT FORMULAS
======================================================================

Normalize all supported rent bases into:

monthly_base_rent

annual_base_rent

For:

$ / SF / year

annual_base_rent =
space_size_sqft × rate_per_sqft_per_year

monthly_base_rent =
annual_base_rent / 12


For:

$ / SF / month

monthly_base_rent =
space_size_sqft × rate_per_sqft_per_month

annual_base_rent =
monthly_base_rent × 12


For:

total monthly

monthly_base_rent =
provided monthly amount

annual_base_rent =
monthly_base_rent × 12


For:

total annual

annual_base_rent =
provided annual amount

monthly_base_rent =
annual_base_rent / 12


Do not infer missing space size when a per-SF basis requires it.

======================================================================
ADDITIONAL OCCUPANCY COST FORMULAS
======================================================================

Normalize supplied additional charges similarly.

Examples:

NNN / CAM / operating charges supplied as:

$ / SF / year

annual_additional_cost =
space_size_sqft × additional_rate

monthly_additional_cost =
annual_additional_cost / 12


If additional charges are not supplied:

do NOT set them to a fabricated amount.

Use:

unknown / not supplied

The estimated total occupancy cost must communicate whether it is complete or
partial.

======================================================================
TOTAL OCCUPANCY COST
======================================================================

If base rent is available:

estimated_monthly_base_rent
estimated_annual_base_rent

If additional occupancy charges are also supplied:

estimated_monthly_occupancy_cost =
monthly_base_rent + monthly_additional_cost

estimated_annual_occupancy_cost =
annual_base_rent + annual_additional_cost

If additional charges are missing:

show:

Estimated base rent

not:

Total occupancy cost

unless the lease structure reasonably establishes that base rent is total rent.

Use careful wording.

======================================================================
DO NOT INCLUDE UNSUPPLIED COSTS
======================================================================

Do not invent:

- utilities
- insurance
- taxes
- maintenance
- CAM
- repairs
- marketing fees
- percentage rent
- buildout
- tenant improvements
- deposits
- broker fees
- permits
- liquor license
- equipment
- payroll

unless explicitly entered by the user.

======================================================================
OCCUPANCY BUDGET
======================================================================

Allow an optional:

Monthly occupancy budget

This is the user's own operating threshold.

It is not market data.

If supplied:

occupancy_budget_ratio =
estimated_monthly_occupancy_cost / monthly_occupancy_budget

or:

monthly_base_rent / budget

when only base rent is known.

The model must distinguish:

complete occupancy estimate

vs

base-rent-only estimate

======================================================================
RENT MODEL V1
======================================================================

Create:

VenueBite Commercial Occupancy Model v1

This model should score BUDGET FIT, not nationwide market cheapness.

Semantic meaning remains compatible with Score Model v2:

HIGHER RENT SCORE =
more favorable / more affordable occupancy context

Use a deterministic bounded model.

Conceptually:

cost <= 70% of stated budget
    strong affordability

70–85%
    favorable

85–100%
    near budget

100–115%
    above budget

>115%
    materially above budget

Exact implementation thresholds may be refined, but they must be:

- centralized
- documented
- deterministic
- tested
- reasonable
- not tuned to make scores look attractive

Use interpolation or clearly defined bands rather than unexplained magic jumps.

Score must remain:

0 <= rent_score <= 100

======================================================================
IMPORTANT RENT MODEL LIMITATION
======================================================================

Commercial Occupancy Model v1 measures:

fit relative to the USER'S stated occupancy budget

It does NOT measure:

- whether rent is cheap for the submarket
- market rent
- fair market value
- expected profitability
- affordability relative to restaurant revenue
- landlord negotiability
- future escalations

The UI and README must state this clearly.

======================================================================
WHEN RENT SCORE MAY BECOME USER-SUPPORTED
======================================================================

A live/user-supported rent score requires:

1. valid candidate-property cost information
2. valid monthly occupancy budget

If either is missing:

keep current demo rent score

or mark rent unavailable according to the established scoring policy

Do not invent a score.

Preferred compatibility behavior:

keep the existing demo fallback score

but label:

Demo fallback — occupancy budget not supplied

or:

Demo fallback — insufficient lease terms

======================================================================
RENT PROVENANCE
======================================================================

When the user-supported model is active:

rent provenance should conceptually indicate:

status:
partial

provider:
user_supplied

source:
commercial listing / broker quote / user entry

model:
Commercial Occupancy Model v1

Do not label this:

REAL VERIFIED MARKET DATA

because VenueBite has not independently verified the listing.

======================================================================
DATA COVERAGE INTEGRATION
======================================================================

Existing coverage rules:

real = 1.0
partial = 0.5
demo = 0
fallback = 0
unavailable = 0

Therefore a user-supported rent score receives partial credit.

Example:

Population
30 × 1.0 = 30

Income
30 × 1.0 = 30

Competition
20 × 1.0 = 20

Rent
20 × 0.5 = 10

Total:
90%

Verify this mathematically in tests.

Do not special-case UI percentages.

======================================================================
OPPORTUNITY SCORE INTEGRATION
======================================================================

Score Model v2 remains authoritative.

Weights remain:

Population      30%
Income          30%
Rent            20%
Competition     20%

If Commercial Occupancy Model v1 successfully produces a supported rent score:

use that rent score in Score Model v2.

If not:

preserve established demo/fallback behavior.

Do not change any other factor model.

======================================================================
SCORE MODEL VERSION
======================================================================

Do not automatically rename Score Model v2 to v3.

The overall formula and weights are unchanged.

Instead document:

Score Model v2
+
Commercial Occupancy Model v1

If implementation changes the overall score formula itself, stop and justify the
need before doing so.

======================================================================
WEIGHT REGRESSION
======================================================================

Population:
30%

Income:
30%

Rent:
20%

Competition:
20%

Total:
100%

These weights must remain unchanged.

Add regression tests.

======================================================================
CANDIDATE PROPERTY STATUS
======================================================================

Create clear states such as:

not_provided
partial
complete
invalid

Do not infer completeness only from UI strings.

======================================================================
COST COMPLETENESS
======================================================================

Create structured cost completeness.

Possible states:

base_only

base_plus_additional

unknown_expenses

This helps VenueBite distinguish:

Estimated base rent
vs
Estimated occupancy cost

Do not overclaim precision.

======================================================================
PROPERTY SOURCE PROVENANCE
======================================================================

Allow user to optionally record:

source label

Example:

Crexi listing
Broker email
Landlord quote
Property flyer

and:

source URL

Do not fetch/scrape the URL in Sprint 07.

The URL is provenance metadata only.

Never imply VenueBite independently verified it.

======================================================================
SOURCE URL SECURITY
======================================================================

Validate source URLs.

Allow:

http
https

Reject unsafe schemes such as:

javascript:
data:
file:

Render external links with:

rel="noopener noreferrer"

Escape user text normally.

======================================================================
CANDIDATE PROPERTY UI
======================================================================

Add a polished section.

Example:

COMMERCIAL OCCUPANCY
User-supplied listing terms

Available space
2,800 SF

Asking rent
$32.00 / SF / year

Lease structure
NNN

Additional charges
$8.50 / SF / year

Estimated base rent
$7,467 / month
$89,600 / year

Estimated additional occupancy charges
$1,983 / month
$23,800 / year

Estimated occupancy cost
$9,450 / month
$113,400 / year

Your occupancy budget
$10,000 / month

Budget utilization
94.5%

Rent factor
68 / 100
PARTIAL EVIDENCE
Commercial Occupancy Model v1

Use compact formatting.

======================================================================
INCOMPLETE COST EXAMPLE
======================================================================

If:

NNN lease
$32/SF/year
2,800 SF

but no NNN/CAM charges supplied:

show:

Estimated base rent
$7,467 / month

Additional NNN/CAM charges
Not supplied

Do NOT show:

Total occupancy cost: $7,467

Instead:

"Base rent only. Total occupancy cost may be higher."

======================================================================
LEASE TERM / ESCALATIONS
======================================================================

Sprint 07 does not need full lease underwriting.

Do not implement complex:

- annual escalation schedules
- free rent
- tenant improvement amortization
- percentage rent
- renewal options
- discounted cash flow

Optional text notes may record them.

Future sprint can build advanced lease economics.

======================================================================
STRENGTHS / RISKS INTEGRATION
======================================================================

Extend deterministic explanations carefully.

Examples when budget-supported rent is favorable:

"Candidate base/occupancy cost is within the stated monthly occupancy budget."

Examples when above budget:

"Estimated occupancy cost exceeds the stated monthly occupancy budget."

Evidence risk:

"Commercial occupancy terms are user-supplied and have not been independently
verified."

Missing information:

"NNN/CAM charges were not supplied, so the estimate reflects base rent only."

Do not say:

"This lease is a good deal."

"Rent is below market."

"Take this property."

======================================================================
SITE + OCCUPANCY COMBINATION
======================================================================

Sprint 06 site intelligence and Sprint 07 occupancy intelligence should complement
each other.

Example:

SITE INTELLIGENCE
Regrid parcel data

COMMERCIAL OCCUPANCY
User-supplied listing terms

Do not merge Regrid assessment values into lease-cost formulas.

Do not infer asking rent from assessed values.

======================================================================
MAP BEHAVIOR
======================================================================

Sprint 07 should not substantially redesign the map.

Preserve:

- candidate marker
- competitor markers
- parcel boundary
- standard/satellite
- map controls

If candidate-property address differs from selected Mapbox location:

do not silently assume they are the same.

Either:

- validate consistency
- warn user
- or keep selected location authoritative

Do not geocode source/listing URL.

======================================================================
ADDRESS CONSISTENCY
======================================================================

The selected Mapbox candidate coordinates remain authoritative for the analysis.

The candidate-property address is contextual metadata.

If user enters a materially different address:

show a validation warning such as:

"Property address differs from the selected analysis location. Verify the
candidate site."

Do not silently move the analysis based only on free-text occupancy input.

======================================================================
MONEY NORMALIZATION
======================================================================

Use Decimal or another appropriate precise monetary strategy where practical.

Avoid unnecessary binary floating-point drift for currency calculations.

Round display currency normally to cents.

Keep score calculations consistent with existing scoring architecture.

======================================================================
NUMERIC VALIDATION
======================================================================

Reject:

- negative square footage
- zero square footage when required
- negative rent
- zero/negative occupancy budget
- unreasonable non-finite values
- NaN
- infinity
- malformed currency

Set sensible upper bounds to prevent absurd or malicious input from destabilizing
rendering/calculation.

Do not reject legitimately expensive commercial properties merely because the
number looks high.

======================================================================
CURRENCY
======================================================================

Sprint 07 may initially support USD only.

If so:

make that explicit.

Do not pretend international currency conversion exists.

Non-U.S. occupancy input should either:

- remain unsupported
- or be clearly treated as user-entered USD

Do not infer currency from Mapbox country automatically without a currency system.

======================================================================
ANALYSIS STATE
======================================================================

Preserve the existing stale-state rules.

If occupancy inputs change:

old opportunity score
old rent factor
old Data Coverage
old occupancy calculations
old explanations

must be invalidated until the user submits a new analysis.

Do not leave previous rent analysis attached to new form values.

======================================================================
OPTIONAL OCCUPANCY INPUT FLOW
======================================================================

Do not clutter the default location search experience.

Use an expandable section such as:

"Add commercial property terms"

or:

"Analyze a specific commercial space"

The existing user can still run normal VenueBite analysis without opening it.

======================================================================
FORM UX
======================================================================

Use clear helper text.

Example:

Asking rent
[ 32.00 ] [$ / SF / year ▼]

Available space
[ 2800 ] SF

Lease structure
[ NNN ▼ ]

Additional NNN/CAM
[ 8.50 ] [$ / SF / year ▼]

Monthly occupancy budget
[ 10000 ]

Do not require the user to understand hidden formulas.

======================================================================
RENT SCORE UI
======================================================================

When user-supported rent is active:

Rent
68 / 100

PARTIAL EVIDENCE

Commercial Occupancy Model v1

Budget utilization
94.5%

Weight
20%

Contribution
13.6 points

When not active:

Rent
55 / 100

DEMO

Commercial rent not yet supported by sufficient candidate-property evidence.

======================================================================
DATA COVERAGE UI
======================================================================

If rent becomes partial evidence:

show:

Data Coverage
90%

Do not call it:

90% accuracy

or:

90% confidence of success

Coverage still means evidence coverage only.

======================================================================
OCCUPANCY SUMMARY
======================================================================

Generate deterministic summary language.

Example:

"The candidate space is listed at $32/SF/year for 2,800 SF. Based on the supplied
NNN charges, estimated occupancy cost is approximately $9,450/month, representing
94.5% of the stated $10,000 monthly occupancy budget."

If additional charges are missing:

"The listed base rent is approximately $7,467/month. NNN/CAM charges were not
supplied, so total occupancy cost is not known."

No AI.

======================================================================
DO NOT CREATE MARKET BENCHMARKS
======================================================================

VenueBite does not yet know:

average rent in this submarket
median retail rent
restaurant rent comps
market lease rate
executed lease comps

Do NOT display any of these.

Do NOT compare asking rent to "market" unless a future legitimate data provider
supplies that evidence.

======================================================================
NO REVENUE FORECASTING
======================================================================

Do not calculate:

- projected restaurant revenue
- rent-to-sales ratio
- break-even revenue
- profitability
- ROI
- investment return

unless the user provides and a future sprint explicitly models the required
financial inputs.

Sprint 07 is occupancy-cost analysis only.

======================================================================
NO FINANCIAL RECOMMENDATION LANGUAGE
======================================================================

Avoid:

"affordable investment"

"profitable location"

"good lease"

"bad lease"

"you should sign"

Use:

"within stated occupancy budget"

"above stated occupancy budget"

"base-rent-only estimate"

"additional lease costs not supplied"

======================================================================
FAILURE BEHAVIOR
======================================================================

Bad occupancy input must not break:

- map
- Census
- competition
- Regrid
- existing score rendering

If occupancy section is invalid:

show field-specific validation errors.

The user may correct and resubmit.

Do not silently discard malformed values and pretend analysis succeeded.

======================================================================
SECURITY
======================================================================

Treat all candidate-property inputs as untrusted user input.

Maintain Jinja escaping.

Validate:

- numbers
- URLs
- enum-like fields
- notes length
- source labels

No HTML injection.

No JavaScript URLs.

No unsafe raw HTML.

======================================================================
PRIVACY / PERSISTENCE
======================================================================

Sprint 07 does not add database persistence.

Do not store:

- listing details
- budgets
- lease terms
- source URLs

beyond the current request/session behavior already established by the app.

Do not add a database.

Saved properties come later.

======================================================================
TESTING
======================================================================

Before changing code:

python -m pytest

Preserve all Sprint 01–06 tests.

No external APIs are required for Sprint 07 tests.

Add comprehensive tests for:

Base rent math
- $/SF/year
- $/SF/month
- monthly total
- annual total

Additional charge math
- per SF/year
- per SF/month
- monthly total
- annual total

Total occupancy math
- complete cost
- base-only cost
- missing additional charges

Validation
- negative SF
- zero SF
- malformed rent
- non-finite values
- invalid lease structure
- invalid rent basis
- invalid source URL
- negative budget
- zero budget

Commercial Occupancy Model v1
- far below budget
- below budget
- near budget
- exactly at budget
- slightly above
- materially above
- boundaries
- score always 0–100

Provenance
- no input = demo
- incomplete input = demo fallback
- complete cost but no budget = demo fallback
- sufficient cost + budget = partial
- provider/source metadata

Data Coverage
- prior normal case stays 80%
- supported rent case becomes 90%
- occupancy data must never produce 100% coverage
- failed Census + occupancy scenarios
- failed competition + occupancy scenarios

Score Model v2
- weights unchanged
- supported rent score changes only rent contribution
- population unchanged
- income unchanged
- competition unchanged
- contributions sum correctly

Explanations
- within budget
- above budget
- missing NNN/CAM
- user-supplied evidence caution
- demo fallback caution
- no "below market" claim
- no recommendation language

Integration
- location analysis without occupancy inputs
- complete occupancy input
- incomplete occupancy input
- invalid occupancy input
- Sprint 06 parcel remains intact
- Census remains intact
- competition remains intact
- map remains intact

State consistency
- editing occupancy field invalidates old report
- changing location invalidates old occupancy result
- stale rent score does not remain
- stale coverage does not remain

Security
- HTML escaping
- malicious source URL
- notes escaping

======================================================================
MANUAL ACCEPTANCE TESTS
======================================================================

Test at least:

Scenario A
No occupancy input

Expected:
- existing VenueBite behavior
- rent demo
- normal coverage remains 80%

Scenario B
2,800 SF
$32/SF/year
NNN
$8.50/SF/year additional
$10,000 monthly budget

Verify:
annual base rent
monthly base rent
additional cost
estimated total occupancy
budget ratio
Rent Model v1
partial evidence
Data Coverage = 90%
score recalculation

Scenario C
Same listing
no NNN/CAM amount

Expected:
- base rent calculated
- total occupancy NOT claimed
- missing-cost warning
- scoring policy follows documented completeness rule

Scenario D
Complete rent terms
no occupancy budget

Expected:
- occupancy cost calculated
- rent score remains demo fallback
- coverage remains 80%

Scenario E
Occupancy cost above budget

Expected:
- lower rent score
- risk explanation
- no "bad lease" language

Scenario F
Malformed/negative values

Expected:
- validation error
- no Flask 500

Also verify:

- Mapbox map
- satellite
- parcel boundary
- competitors
- Census demographics
- Site Intelligence
- Score Model v2
- mobile layout

======================================================================
README
======================================================================

Update README with:

- Sprint 07 overview
- candidate-property input
- supported rent bases
- lease-structure limitations
- commercial occupancy formulas
- Commercial Occupancy Model v1
- monthly occupancy budget concept
- partial evidence provenance
- Data Coverage 80% → 90% example
- why user-supplied listing data is not fully verified
- no market-rent comparison
- no revenue/profit forecast
- no listing scraping
- no property persistence
- how to run

  python app.py

- how to test

  python -m pytest

======================================================================
ENGINEERING DOCUMENT
======================================================================

Create if useful:

docs/commercial-occupancy-v1.md

Document:

- input schema
- normalization
- formulas
- completeness states
- provenance
- Rent Model v1
- coverage behavior
- score integration
- examples
- limitations

======================================================================
DO NOT BUILD IN SPRINT 07
======================================================================

Do NOT implement:

- LoopNet scraping
- Crexi scraping
- CoStar scraping
- CompStak API
- property discovery API
- asking-rent API
- market rent benchmarks
- executed lease comps
- saved properties
- database
- authentication
- Keycloak
- AI
- LLMs
- chatbot
- property recommendations
- profit forecasting
- revenue forecasting
- ROI
- advanced lease underwriting
- zoning verification
- permits
- restaurant licenses
- Docker
- deployment
- payment systems
- React/Vue/Angular

Keep Sprint 07 focused on COMMERCIAL OCCUPANCY + CANDIDATE PROPERTY ANALYSIS.

======================================================================
ACCEPTANCE CRITERIA
======================================================================

Sprint 07 is complete only when:

1. Sprint 01–06 functionality remains intact.
2. Commercial-property terms are optional.
3. User can enter space size.
4. User can enter asking rent.
5. Supported rent bases normalize correctly.
6. Lease structure is recorded.
7. Optional additional occupancy charges normalize correctly.
8. Monthly base rent is calculated.
9. Annual base rent is calculated.
10. Additional costs are calculated when supplied.
11. Total occupancy cost is only claimed when sufficiently supported.
12. Monthly occupancy budget is optional.
13. Commercial Occupancy Model v1 is implemented.
14. Budget-supported rent score remains 0–100.
15. Raw asking rent alone does not produce arbitrary nationwide affordability scoring.
16. User-supported rent provenance is partial.
17. Current successful evidence coverage can rise from 80% to 90%.
18. User-supplied rent can never create 100% real-data coverage.
19. Score Model v2 weights remain unchanged.
20. Population Model remains unchanged.
21. Income Model remains unchanged.
22. Competition Model remains unchanged.
23. Sprint 06 parcel intelligence remains separate.
24. Regrid assessment values are never used as asking rent.
25. Occupancy explanations are deterministic.
26. No market-rent claims are invented.
27. No revenue/profitability claims are invented.
28. No new external data provider is added.
29. Invalid occupancy data does not crash Flask.
30. Existing tests pass.
31. New tests pass.
32. App runs with:

    python app.py

33. Tests run with:

    python -m pytest

34. `.env` remains ignored.
35. Git status is shown.
36. Codex does not commit.
37. Codex does not push.

======================================================================
FINAL VERIFICATION
======================================================================

Before completion:

1. Run:

   python -m pytest

2. Start:

   python app.py

3. Verify normal analysis without occupancy input.

4. Verify complete NNN example.

5. Verify base-only example.

6. Verify no-budget example.

7. Verify above-budget example.

8. Verify invalid inputs.

9. Verify contribution math manually.

10. Verify Data Coverage manually.

11. Verify Score Model v2 weights.

12. Verify population unchanged.

13. Verify income unchanged.

14. Verify competition unchanged.

15. Verify parcel/site intelligence.

16. Verify Mapbox standard/satellite.

17. Verify stale-state clearing.

18. Verify mobile layout.

19. Inspect browser console.

20. Inspect Flask logs.

21. Inspect git diff.

22. Inspect git status.

23. Confirm no secret is tracked.

DO NOT COMMIT.

DO NOT PUSH.

======================================================================
FINAL REPORT
======================================================================

When finished, report:

1. What Sprint 07 implemented.
2. Files created.
3. Files modified.
4. Candidate-property input architecture.
5. Supported rent bases.
6. Lease structures supported.
7. Occupancy formulas.
8. Cost completeness states.
9. Commercial Occupancy Model v1 formula.
10. Rent-factor activation rules.
11. Rent provenance behavior.
12. Data Coverage behavior.
13. Score Model v2 regression result.
14. Population/Income/Competition regression result.
15. Explanation behavior.
16. Test count and result.
17. Manual acceptance results.
18. Known limitations.
19. Git status.
20. Anything Chris must manually verify.

Do not commit.
Do not push.