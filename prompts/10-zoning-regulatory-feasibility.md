Continue VenueBite from the current clean worktree and implement Sprint 10 completely.

PROJECT: VenueBite
SPRINT: 10 — Zoning & Regulatory Feasibility Intelligence
LATEST CHECKPOINT: 5ca4bcb — Complete VenueBite Sprints 07-09
BRANCH: 1234tlc123-probable-succotash

IMPORTANT:
- DO NOT COMMIT.
- DO NOT PUSH.
- DO NOT STAGE FILES.
- Preserve all existing working functionality.
- Do not recreate previous sprint work.
- Implement the sprint end to end, not just scaffolding or a plan.

==================================================
1. STARTUP / BASELINE
==================================================

Before making any changes:

1. Read AGENTS.md.
2. Read the existing architecture and README.
3. Read:
   - docs/sprint09-engineering-report.md
   - docs/saved-sites-comparison-v1.md
   - docs/scoring-model-v2.md
   - docs/site-intelligence-v1.md
4. Inspect:
   - git status
   - git log --oneline -10
   - current routes/services/providers/repositories/templates/static/tests
5. Run the full Python test suite.
6. Run the full JavaScript test suite.
7. Record the baseline test counts.
8. Identify existing extension points before editing.
9. Create:
   prompts/10-zoning-regulatory-feasibility.md
   containing the finalized Sprint 10 specification.

VenueBite is a Flask/Jinja full-stack application.

Do NOT create a React app.
Do NOT create a separate frontend directory.
Do NOT add Docker, Keycloak, PostgreSQL, AI chat, or commercial property discovery in this sprint.

==================================================
2. SPRINT OBJECTIVE
==================================================

Add a new evidence-aware:

ZONING & REGULATORY FEASIBILITY

feature to VenueBite.

The feature should help restaurant entrepreneurs investigate whether a proposed restaurant location may face zoning, permitting, licensing, land-use, or regulatory issues.

The application should help answer:

- Which jurisdiction governs the site?
- Which zoning district applies?
- Which zoning framework/code appears applicable?
- What official evidence supports that result?
- Is restaurant-use permission actually verified?
- Which important conditions remain unresolved?
- Which permits/licenses/reviews may apply?
- Which official government sources should the user review?
- What should the user verify before signing a lease?

This is decision-support intelligence.

It is NOT:
- legal advice
- zoning approval
- permit approval
- confirmation that a business can legally operate

Never fabricate regulatory conclusions.

==================================================
3. CRITICAL SAFETY RULE
==================================================

Never claim:

- "Restaurant approved"
- "Restaurant use is legal"
- "This property is approved for restaurant use"
- "No permit required"
- "You can open here"
- "Zoning approved"
- "This site is compliant"

unless an exact authoritative, current, machine-verifiable rule supports the precise claim and all applicable conditions have been evaluated.

A zoning district lookup alone does NOT prove a restaurant is permitted.

Preferred language:

- Official zoning district identified
- Official use review required
- Restaurant-use permission not yet verified
- Additional review may apply
- Jurisdiction confirmation recommended
- Government guidance indicates this may apply
- Data unavailable
- Unsupported jurisdiction
- Requires official confirmation

Missing evidence must stay missing.

Do not convert unknowns into guesses.

==================================================
4. INITIAL LIVE JURISDICTION
==================================================

Implement Denver, Colorado as the first supported live zoning jurisdiction.

Use official City and County of Denver sources only.

Investigate and verify the current official Denver GIS zoning service before implementation.

Candidate official ArcGIS zoning layer:

https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_ZONE_ZONING_A/FeatureServer/209

Also research current official Denver government sources for:

- Denver Zoning Code
- Former Chapter 59
- zoning/use permits
- restaurant/commercial kitchen permitting
- building/change-of-use permits
- food establishment licensing
- health review/inspection
- fire/building systems
- kitchen ventilation/mechanical work
- signage
- outdoor seating
- drive-through conditions
- parking/transportation requirements
- accessibility
- alcohol licensing where applicable

Use official denvergov.org or other authoritative government sources.

Before relying on any source:

- confirm it still exists
- confirm it is official
- inspect live metadata/schema
- confirm the relevant fields
- assess whether normalized data may be retained
- do not assume public access automatically means unlimited storage rights

Do not scrape websites when a documented API or official structured source exists.

==================================================
5. PROVIDER ARCHITECTURE
==================================================

Preserve VenueBite separation of concerns:

- routes = HTTP request/response
- providers = external data retrieval
- services = orchestration/business logic
- repositories = persistence
- templates = presentation
- JS = frontend interaction
- scoring = existing deterministic scoring only

Build an extensible zoning/regulatory provider architecture.

Use existing project conventions where appropriate.

Possible files:

venuebite/regulatory.py
venuebite/providers/zoning_provider.py
venuebite/providers/denver_zoning_provider.py
venuebite/services/regulatory_service.py
templates/_regulatory_feasibility.html

Do not force these exact filenames if the current architecture suggests something cleaner.

The architecture must allow future jurisdictions without rewriting the core regulatory service.

DO NOT implement:

if city == "Denver":
    ...

throughout the application.

Jurisdiction-specific behavior belongs behind provider/service abstractions.

==================================================
6. DENVER GIS LOOKUP
==================================================

Use the official Denver ArcGIS REST service.

Perform point-in-polygon zoning lookup using latitude/longitude from the active analysis session.

Do NOT infer zoning from a city name or formatted address.

Investigate the live schema and normalize useful authoritative fields such as, if actually present:

- zone code
- zoning description
- neighborhood context
- district group
- use/form classification
- applicable code version
- jurisdiction identifiers

Do not use field names until the live schema confirms them.

Provider requirements:

- HTTPS only
- fixed allowlisted official hostname
- fixed service endpoint
- server-side request
- reasonable timeout
- bounded query
- explicit requested fields
- strict JSON parsing
- controlled response size
- safe handling of ArcGIS errors
- no secret leakage
- no arbitrary redirects
- no arbitrary user-supplied provider URL
- no SSRF
- no raw exception text in user-facing HTML

Tests must mock provider calls.

Live API availability must not be required for automated tests.

==================================================
7. JURISDICTION VALIDATION
==================================================

Do not assume an address containing "Denver" is governed by Denver zoning.

The zoning lookup itself or another authoritative geographic mechanism must confirm coverage.

Handle explicitly:

- supported Denver point
- outside supported jurisdiction
- unsupported U.S. jurisdiction
- unsupported country
- no matching zoning polygon
- more than one matching polygon
- boundary ambiguity
- malformed provider response
- timeout
- provider outage
- invalid latitude/longitude
- incomplete response

Never silently choose a nearby zoning district.

Unsupported jurisdictions must remain fully analyzable in the rest of VenueBite.

Regulatory section should say that live regulatory coverage is not yet available.

==================================================
8. DENVER CODE FRAMEWORK
==================================================

Denver may have more than one zoning framework.

The system must distinguish, based on authoritative evidence, between:

- Denver Zoning Code
- Former Chapter 59
- other special/site-specific zoning situations if encountered

Do not assume every Denver parcel falls under the modern Denver Zoning Code.

Support honest handling of:

- Former Chapter 59
- planned unit developments
- overlays
- site-specific conditions
- special review districts
- ambiguous code context

If an exact interpretation cannot be safely made:

show the known zoning facts
+
show an "official review required" state.

Do not fabricate code interpretation.

==================================================
9. RESTAURANT PROJECT PROFILE
==================================================

Add an extensible restaurant regulatory profile.

Possible normalized project attributes:

- full-service restaurant
- quick-service restaurant
- café / coffee shop
- takeout-focused restaurant
- commercial kitchen
- alcohol service
- outdoor seating / patio
- drive-through
- major interior renovation
- change of use

Do NOT assume existing VenueBite marketing concept labels map directly to statutory land-use categories.

Keep:

VenueBite business concept
and
government land-use classification

separate.

Where an exact mapping is not authoritative, mark it as requiring official use classification review.

Avoid overloading the existing analysis form.

Use progressive disclosure for optional regulatory project details.

==================================================
10. REGULATORY RESULT MODEL
==================================================

Create a normalized regulatory result structure.

It should support fields such as:

- support status
- jurisdiction name
- jurisdiction identifier
- responsible agency
- zoning district/code
- zoning description
- zoning framework
- source title
- source URL
- source type
- retrieved timestamp
- effective/publication date if actually known
- project concept
- restaurant-use verification status
- accessory-use questions
- known findings
- unresolved findings
- missing information
- permit/review checklist
- recommended next actions
- provenance/evidence status

Clearly distinguish:

1. VERIFIED_OFFICIAL_FACT
2. USER_SUPPLIED
3. INTERPRETATION_REQUIRES_CONFIRMATION
4. GENERAL_GUIDANCE
5. UNKNOWN
6. UNSUPPORTED

Use names compatible with existing code conventions.

Do not invent a confidence percentage.

==================================================
11. RESTAURANT USE FEASIBILITY
==================================================

Do NOT create a fake "restaurant permitted" engine.

If exact, authoritative zoning-use tables can safely be modeled and all relevant conditions can be evaluated, build narrowly scoped rules with:

- source citation
- zoning code version
- rule version
- applicable conditions
- explicit limitations

Otherwise the correct output is:

"Official use review required"

A strong zoning identification + verification workflow is preferable to a wrong automated legal conclusion.

Examples of questions the system may surface:

- Is the restaurant use classified as primary, accessory, conditional, or prohibited?
- Is a zoning permit needed?
- Is there a change of occupancy/use?
- Is outdoor seating proposed?
- Is alcohol service proposed?
- Is a drive-through proposed?
- Is there a special zoning overlay?
- Is parking review triggered?
- Does an older zoning code apply?

Do not answer these affirmatively without supporting evidence.

==================================================
12. PERMIT / LICENSE CHECKLIST
==================================================

Build a concise Denver-specific regulatory research checklist using official government sources.

Potential categories:

- zoning/use review
- zoning permit
- building permit
- change of use / occupancy
- commercial kitchen
- retail food establishment licensing
- health review / inspection
- fire/life safety
- hood / ventilation / mechanical work
- plumbing/electrical work where applicable
- accessibility
- signage
- outdoor seating
- drive-through
- alcohol licensing
- parking/transportation
- other site-specific review

Each item must have a status such as:

- Government guidance identifies this topic
- May apply depending on project details
- Requires official confirmation
- Not evaluated
- Not applicable based on verified user input

Do NOT invent:

- application costs
- approval times
- guaranteed required permits
- guaranteed exemptions
- approval probability

Each jurisdiction-specific item should link to an official source.

==================================================
13. DETERMINISTIC NEXT STEPS
==================================================

Create deterministic next-step guidance.

Examples:

- Confirm official restaurant land-use classification
- Verify whether zoning permit is required
- Confirm outdoor seating rules
- Confirm drive-through allowance
- Confirm alcohol-license path
- Review change-of-occupancy implications
- Confirm accessibility requirements
- Contact Denver zoning staff for special district review

Order next steps by materiality where possible.

Do not use an LLM to generate these findings.

No AI chatbot in Sprint 10.

==================================================
14. RESULTS PAGE INTEGRATION
==================================================

Add a premium:

Zoning & Regulatory Feasibility

section to analysis results.

It should visually match the Sprint 08 futuristic design.

Show:

- jurisdiction
- regulatory coverage status
- official zoning district
- applicable zoning framework
- restaurant-use verification status
- known findings
- unresolved questions
- permit/review checklist
- recommended next steps
- official source links
- retrieval/source dates
- limitations

Use progressive disclosure.

Do not dump long legal text onto the page.

Clearly separate:

Verified
Needs verification
Unknown

The section must degrade gracefully if the provider fails.

Core VenueBite analysis must still complete.

==================================================
15. MAP INTEGRATION
==================================================

If reasonably supported:

- indicate zoning context on the existing map
- label it distinctly from parcel and competition layers

Do NOT add decorative or misleading zoning polygons.

Do NOT confuse:

parcel geometry
with
zoning geometry

A reliable evidence card is more important than adding a polygon layer.

Preserve existing map/satellite behavior.

==================================================
16. SCORE MODEL SEPARATION
==================================================

DO NOT MODIFY LOCATION OPPORTUNITY SCORE V2.

Weights remain:

Population: 30%
Income: 30%
Rent: 20%
Competition: 20%

Do not add zoning to that score.

Do not change its thresholds.

Do not recalculate historical scores.

DO NOT MODIFY DATA COVERAGE calculation.

Regulatory intelligence gets its own independent status.

Do not increase VenueBite Data Coverage because zoning data exists.

==================================================
17. SAVED SITES
==================================================

Integrate Sprint 10 with Sprint 09 persistence safely.

Existing saved records must remain readable.

Requirements:

- old snapshots load unchanged
- existing scores remain exact historical values
- saved detail uses persisted snapshot only
- loading saved details makes zero providers calls
- regulatory information preserves its own provenance
- regulatory retrieval timestamp is retained where allowed
- missing data remains missing
- unsupported jurisdiction state can be persisted
- no automatic reinterpretation of old regulatory snapshots
- schema evolution is backward compatible
- restart persistence works

Persist only normalized regulatory data that is legally appropriate to retain.

Do not store raw provider responses.

Do not store unnecessary third-party data.

If storage rights are unclear:

do not persist the questionable data
and document the limitation.

==================================================
18. MAPBOX STORAGE RESTRICTION
==================================================

Sprint 09 Mapbox rules remain mandatory.

DO NOT persist Mapbox Search Box:

- coordinates
- IDs
- POI names/details
- raw responses
- business-directory records

Mapbox Search Box remains session-only.

Do not silently switch to another Mapbox API.

Do not introduce permanent geocoding storage unless explicitly licensed and intentionally designed.

==================================================
19. COMPARE SITES
==================================================

Extend Compare to display regulatory context when a saved snapshot legitimately contains it.

Possible rows:

- Jurisdiction
- Zoning district
- Zoning framework
- Restaurant-use review status
- Major unresolved conditions
- Source / retrieval date

Do NOT rank a site higher merely because it has better regulatory coverage.

Missing zoning data does not mean bad zoning.

Compare must use persisted snapshots only.

Opening Compare must trigger zero provider calls.

==================================================
20. REGULATORY STATUS
==================================================

Create a clear deterministic regulatory review state.

For example:

VERIFIED_ZONING_ONLY
USE_REVIEW_REQUIRED
PARTIAL_REVIEW
UNSUPPORTED_JURISDICTION
PROVIDER_UNAVAILABLE
AMBIGUOUS
UNKNOWN

Use project-appropriate names.

Do not create a fake numeric regulatory score.

Do not call it probability or confidence.

==================================================
21. SOURCE TRACEABILITY
==================================================

Every official claim must be traceable.

Capture when available:

- agency
- dataset/document title
- official URL
- retrieved timestamp
- source version
- applicable code version
- effective/publication date

Important:

retrieval date != legal effective date

publication date != proof that the rule remains current

If current legal status cannot be verified, say so.

All user-visible regulatory links must be safe HTTPS official links.

==================================================
22. SECURITY
==================================================

Preserve and extend the project's security posture.

Required:

- no arbitrary fetch URLs
- allowlisted regulatory provider hosts
- HTTPS
- safe timeouts
- safe JSON handling
- safe redirects
- response size control
- HTML escaping
- no tokens in browser code
- no secret values in logs
- no provider payloads in exceptions shown to users
- no SQL injection
- no provider calls from Saved Sites/Compare
- safe source URL rendering
- no unsafe javascript: links
- no path traversal

Do not expose any credential.

==================================================
23. ACCESSIBILITY / MOBILE
==================================================

Keep the Sprint 08 UI quality.

Verify:

- responsive layout
- keyboard navigation
- proper heading structure
- accessible links
- status is not color-only
- visible focus states
- screen-reader-friendly labels
- reduced-motion compatibility
- no horizontal overflow at mobile widths
- regulatory cards remain usable on small screens

==================================================
24. TESTING
==================================================

Add comprehensive automated tests.

At minimum cover:

PROVIDER
- valid Denver response
- schema normalization
- no result
- malformed result
- multiple results
- boundary ambiguity
- timeout
- upstream error
- invalid coordinates
- unsafe endpoint prevention

REGULATORY SERVICE
- supported jurisdiction
- unsupported jurisdiction
- Denver code version handling
- Former Chapter 59 handling
- unknown framework
- no fabricated permitted-use result
- accessory project inputs
- permit checklist generation
- deterministic next steps
- evidence provenance

INTEGRATION
- existing Analyze works
- zoning appears on supported analysis
- unsupported locations remain analyzable
- provider failure does not crash analysis
- Score Model v2 unchanged
- Data Coverage unchanged
- saved snapshots remain backward compatible
- regulatory snapshots restore after restart
- saved detail makes zero provider calls
- Compare makes zero provider calls
- Compare uses exact persisted data
- Mapbox Search Box data is not persisted
- no raw regulatory payload persisted

SECURITY
- safe URL behavior
- HTML escaping
- malformed IDs
- SQL injection-resistant repository behavior
- provider exception sanitization

UI
- section renders
- unsupported state renders
- unavailable state renders
- evidence labels render
- accessible headings/labels
- mobile-friendly HTML/CSS structure

Automated tests must not call live external services.

Use mocks/fixtures.

==================================================
25. LIVE SMOKE TESTING
==================================================

After automated tests pass, perform separately labeled live smoke checks if network/API availability allows.

Use official Denver government sources.

Test at least:

- one valid Denver point with a zoning result
- one unsupported/non-Denver point
- one provider failure/unavailable path if practical

Do NOT modify user data unnecessarily.

Clearly distinguish:

AUTOMATED TESTS
from
LIVE SMOKE TESTS

If a live service cannot be reached, say so rather than marking it passed.

==================================================
26. DATABASE INSPECTION
==================================================

After implementation:

Inspect the development SQLite database.

Verify it contains no:

- Mapbox Search Box coordinates
- Mapbox IDs
- raw Mapbox payloads
- POI directories
- raw Denver GIS responses
- API credentials
- secret tokens

Verify regulatory snapshot persistence stores only intended normalized fields.

Verify existing saved sites still load after app restart.

==================================================
27. DOCUMENTATION
==================================================

Create:

docs/zoning-regulatory-feasibility-v1.md

Document:

- purpose
- architecture
- initial jurisdiction coverage
- Denver provider
- official data sources
- source schema
- jurisdiction detection
- Denver Zoning Code vs Former Chapter 59
- regulatory status model
- restaurant-use safeguards
- permit checklist approach
- evidence/provenance model
- persistence/storage decisions
- licensing/retention considerations
- Saved Sites behavior
- Compare behavior
- scoring separation
- known limitations
- future jurisdiction strategy

Update README as appropriate.

Do not make unsupported legal claims in documentation.

==================================================
28. ENGINEERING REPORT
==================================================

Create:

docs/sprint10-engineering-report.md

Write a complete 32-part engineering report.

Include at minimum:

1. Sprint objective
2. Baseline state
3. Deliverables
4. Files changed
5. Architecture
6. Data flow
7. Provider design
8. Official sources
9. Source/licensing assessment
10. Jurisdiction handling
11. Denver zoning lookup
12. Denver code-framework handling
13. Regulatory evidence model
14. Restaurant-use safeguards
15. Project-specific attributes
16. Permit/license checklist
17. Deterministic next steps
18. UI integration
19. Map integration
20. Saved Sites integration
21. Snapshot migration/backward compatibility
22. Compare integration
23. Scoring separation
24. Data Coverage separation
25. Security controls
26. Data retention/database inspection
27. Python test results
28. JavaScript test results
29. Live smoke test results
30. Accessibility/mobile review
31. Known limitations / manual checks
32. Final acceptance status and Git status

Do not claim tests/checks you did not actually perform.

==================================================
29. ACCEPTANCE CRITERIA
==================================================

Sprint 10 is complete only if:

1. Existing VenueBite analyses still work.
2. Existing Score Model v2 output remains unchanged.
3. Existing Data Coverage behavior remains unchanged.
4. A supported Denver location can obtain authoritative zoning information.
5. Unsupported jurisdictions return an honest unsupported state.
6. The app never claims restaurant permission without sufficient evidence.
7. Denver code/framework distinctions are handled honestly.
8. Regulatory findings have provenance.
9. Official source links are displayed safely.
10. Permit/review checklist is evidence-aware.
11. Missing requirements remain missing.
12. Provider outage cannot break analysis.
13. Existing Saved Sites still load.
14. Existing historical snapshots remain unchanged.
15. Regulatory snapshot migration is backward compatible.
16. Saved detail makes zero provider calls.
17. Compare makes zero provider calls.
18. Compare uses persisted snapshots only.
19. No unauthorized Mapbox data is persisted.
20. No raw regulatory provider responses are persisted.
21. No credentials are persisted or rendered.
22. Database remains ignored by Git.
23. .env remains ignored by Git.
24. Regulatory UI matches existing futuristic design.
25. Mobile layout is usable.
26. Accessibility behavior is preserved/improved.
27. Full Python suite passes.
28. Full JavaScript suite passes.
29. Live Denver smoke test is performed if technically available.
30. Documentation is complete.
31. Git diff contains only intended Sprint 10 changes.
32. Nothing is staged, committed, or pushed.

If any acceptance item is incomplete:

- list it explicitly
- explain the blocker
- DO NOT call Sprint 10 complete

==================================================
30. FINAL SAFETY CHECKS
==================================================

Before finishing:

1. Run full Python tests.
   On Windows, if pytest temp permissions fail, use a controlled basetemp rather than modifying application code.

2. Run full JavaScript tests.

3. Run:
   git status --short

4. Confirm:
   - nothing staged
   - nothing committed
   - nothing pushed

5. Verify:
   .env is ignored

6. Verify:
   SQLite development database is ignored

7. Search the worktree/staged state for:
   MAPBOX_ACCESS_TOKEN
   CENSUS_API_KEY
   REGRID_API_TOKEN

8. Verify no real credentials are present.

9. Inspect database storage.

10. Restart Flask and confirm:
    - existing saved sites survive
    - regulatory saved data survives as designed

11. Verify loading:
    - Saved Sites
    - saved detail
    - Compare

    causes ZERO external provider calls.

12. Verify the app works with regulatory provider unavailable.

==================================================
31. GIT DISCIPLINE
==================================================

DO NOT:

- git add
- git commit
- git push

Leave all Sprint 10 changes uncommitted for review.

The final report must state:

- Python test count
- JavaScript test count
- live smoke-test status
- files changed
- database/storage inspection result
- provider-call verification result
- acceptance criteria status
- git status

==================================================
32. IMPLEMENTATION STANDARD
==================================================

Work like a senior software engineer.

Do not stop at placeholders.

Do not leave obvious TODO implementations.

Do not make sweeping unrelated refactors.

Prefer the smallest clean architecture that supports future jurisdictions.

Preserve all existing behavior.

Never invent zoning or legal facts.

Use real government evidence where available.

If the source cannot support a conclusion, VenueBite must say that it cannot verify it.

Start Sprint 10 now.