# Sprint 05 — Scoring Model v2 + Explainability + Confidence

You are working inside the existing VenueBite repository.

VenueBite is a Flask/Jinja full-stack restaurant location-intelligence web application.

Current product state:

Sprint 01:
- full-stack Flask/Jinja foundation
- scoring architecture
- services
- tests

Sprint 02:
- Mapbox location search
- real coordinates
- interactive map
- satellite mode
- provider architecture
- redesigned dashboard

Sprint 03:
- real nearby restaurant POIs
- direct-competitor classification
- real competition intelligence
- competition map markers
- Competition Model v1

Sprint 04:
- U.S. Census geography resolution
- real ACS population
- real ACS median household income
- demographic provenance
- Population Model v1
- Income Model v1
- Census MOE metadata
- hybrid real/demo analysis

Sprint 04 is complete, committed, and pushed.

Sprint 05 must refine the intelligence layer without adding unrelated new providers or product areas.

---

# PRIMARY SPRINT GOAL

Upgrade VenueBite from a collection of factor scores into a transparent,
versioned, explainable scoring system.

The goal is NOT to pretend the model predicts restaurant success.

The goal is to make the existing opportunity score:

- deterministic
- understandable
- consistent
- provenance-aware
- coverage-aware
- inspectable
- easier to calibrate later

Sprint 05 should improve:

1. Factor scoring architecture
2. Overall score composition
3. Factor contribution visibility
4. Strength/risk explanations
5. Data coverage/confidence
6. Model versioning
7. Score transparency
8. UI presentation

Do not add AI.

Do not add new external data providers.

---

# CRITICAL STARTING PROCEDURE

Before changing anything:

1. Read `AGENTS.md`.
2. Read this complete Sprint 05 prompt.
3. Inspect the repository.
4. Run:

   git status
   git branch --show-current
   python -m pytest

5. Record baseline test count.

6. Inspect at minimum:

   venuebite/scoring.py
   venuebite/competition_scoring.py
   venuebite/demographic_scoring.py
   venuebite/services/analysis_service.py
   provider provenance structures
   templates/results.html
   factor-card templates
   strengths/risks logic
   README.md

Understand the current scoring semantics before editing.

---

# GIT RULES

Do NOT:

- commit
- push
- create branches
- reset
- rewrite Git history
- delete working Sprint 01–04 functionality

Chris will review changes manually.

---

# IMPORTANT MODEL PRINCIPLE

VenueBite must NOT claim:

- guaranteed restaurant success
- investment certainty
- scientific validation
- predictive accuracy that has not been established
- profitability forecasts

Use wording such as:

"Location Opportunity Score"

"market context"

"observed competition"

"demographic context"

"commercial rent remains demo"

The score is decision-support, not a guarantee.

---

# CURRENT FACTORS

VenueBite currently evaluates four major factors:

1. Population
2. Income
3. Rent / occupancy
4. Competition

Current provenance:

Population:
REAL Census data

Income:
REAL Census data

Competition:
REAL observed Mapbox POI data

Rent:
DEMO commercial occupancy factor

Preserve this distinction.

---

# FACTOR SEMANTICS

Keep explicit factor direction.

Population:
higher score = more favorable population context

Income:
higher score = stronger household purchasing-power context

Rent:
higher score = more favorable / more affordable occupancy context

Competition:
higher score = lower observed competition pressure

Do not invert these semantics accidentally.

---

# SCORING MODEL VERSION

Introduce explicit overall model versioning.

Example:

VENUEBITE_SCORE_MODEL_VERSION = "2.0"

Use a clean centralized constant or model metadata structure.

Do not identify model versions only through comments.

The results page should be able to display something subtle like:

VenueBite Score Model v2

---

# CENTRALIZED FACTOR CONFIGURATION

Centralize factor configuration.

Conceptually:

FACTOR_CONFIG = {
    "population": {
        "weight": 0.30,
        "direction": "higher_is_better",
        "provenance_expected": "census",
    },
    ...
}

Do not scatter weights through multiple modules/templates.

The existing overall weights should remain unchanged unless inspection reveals a verified inconsistency.

If weights are currently:

Population 30%
Income 30%
Rent 20%
Competition 20%

preserve them.

Do not change weights simply because a different combination "looks better."

---

# FACTOR CONTRIBUTIONS

Calculate how much each factor contributes to the final score.

Conceptually:

population score = 74
population weight = 30%

weighted contribution = 22.2 points

income score = 81
income weight = 30%

weighted contribution = 24.3 points

The backend should produce a structured breakdown.

Example:

{
    "population": {
        "score": 74,
        "weight": 0.30,
        "weighted_points": 22.2
    }
}

Do not calculate contributions in templates.

---

# FINAL SCORE

Overall score remains conceptually:

sum(factor_score × factor_weight)

Keep final score bounded:

0 <= opportunity_score <= 100

Round presentation consistently.

Do not silently change factor values based on data confidence.

Confidence and opportunity score must remain separate concepts.

---

# CONFIDENCE / COVERAGE

Introduce a separate VenueBite analysis coverage/confidence indicator.

IMPORTANT:

Confidence must NOT mean:

"probability this restaurant succeeds"

It should mean:

"how much of the VenueBite model is currently supported by real,
usable data."

Possible labels:

Data Coverage
Analysis Coverage
Evidence Coverage

Prefer one of these over predictive "confidence" if that reduces ambiguity.

---

# DATA COVERAGE MODEL

Create a deterministic coverage model.

Each factor can have a status such as:

real
demo
unavailable
partial

Example weights for coverage may align with factor weights.

If:

Population = real
Income = real
Competition = real
Rent = demo

Then overall coverage should reflect that most, but not all, of the model
is supported by real data.

Do NOT simply display 100%.

A reasonable conceptual approach:

real factor:
100% of its coverage weight

partial factor:
some bounded intermediate percentage

demo factor:
0% real-data coverage

unavailable:
0%

If existing factor weights are:

Population 30%
Income 30%
Rent 20%
Competition 20%

then:

real population = 30 coverage points
real income = 30
demo rent = 0
real competition = 20

Data Coverage = 80%

This is only a conceptual model.

Implement cleanly and centrally.

---

# COVERAGE LABELS

Create deterministic labels.

Example:

90–100:
Very high data coverage

70–89:
High data coverage

50–69:
Moderate data coverage

25–49:
Limited data coverage

0–24:
Very limited data coverage

Use sensible language.

Do not imply predictive accuracy.

---

# FACTOR PROVENANCE

Factor provenance must be structured backend data.

Example:

population:
    source_type: real
    provider: U.S. Census Bureau
    vintage: 2024
    model: Population Model v1

income:
    source_type: real
    provider: U.S. Census Bureau
    vintage: 2024
    model: Income Model v1

competition:
    source_type: real
    provider: Mapbox
    model: Competition Model v1

rent:
    source_type: demo

Do not derive provenance from UI text.

---

# STRENGTHS AND RISKS

Replace simplistic or generic strengths/risks with deterministic,
factor-driven explanations.

The explanation engine should use structured score/factor information.

Examples:

Strength:
"Household income is a relative strength in this tract."

Strength:
"Observed direct competition pressure is relatively low within the selected radius."

Risk:
"Commercial rent is still based on demo data and should be verified before making a site decision."

Risk:
"Several direct competitors were observed close to the candidate site."

Do NOT use AI.

Do NOT generate random prose.

Do NOT claim causal certainty.

---

# EXPLANATION ENGINE

Create a dedicated explanation layer.

Possible structure:

venuebite/
    services/
        explanation_service.py

or:

venuebite/explanations.py

Responsibilities:

- interpret factor scores
- identify top strengths
- identify top risks
- explain weighted contributions
- mention demo/unavailable factors
- generate concise structured explanations

The explanation engine must not fetch data.

It consumes analysis results only.

---

# TOP STRENGTHS

Determine strengths using transparent rules.

For example:

high factor score
+
meaningful weight
=
candidate strength

Do not automatically classify every score above 50 as a strength.

Use centralized thresholds.

Limit output to the most useful strengths.

Avoid repetitive statements.

---

# TOP RISKS

Risks should consider:

- low factor scores
- real competitive pressure
- unavailable data
- demo factors
- weak demographic context
- data-quality limitations

A demo factor itself may be a decision risk because the information
has not been verified.

Example:

"Commercial occupancy cost is not yet based on live market data."

That is more useful than pretending demo rent is real.

---

# SCORE CLASSIFICATION

Review the existing score classifications.

Examples may include:

Strong Opportunity
Promising
Mixed
Challenging

Use neutral professional language.

Avoid:

Guaranteed success
Excellent investment
Bad location
Do not open here

VenueBite informs decisions rather than making them.

Centralize score thresholds.

---

# SCORE EXPLANATION

Provide a short deterministic summary.

Example:

"VenueBite scores this location at 73.4/100. Income and population are
the strongest weighted factors. Competition is moderate, while commercial
rent remains unverified demo data."

Generate this from backend structured data.

No LLM.

---

# CONTRIBUTION VISUALIZATION

Improve the UI so users can understand the score.

For each factor show:

- factor score
- factor weight
- weighted contribution
- real/demo/unavailable badge
- source/model where appropriate

Example:

Population
74 / 100
Weight: 30%
Contribution: 22.2 points
REAL — Census ACS 2024

Do not overwhelm the dashboard.

Use compact expandable/detail behavior if necessary.

---

# OVERALL SCORE PANEL

Enhance the primary opportunity score panel.

Show:

Opportunity Score
73.4 / 100

Classification
Promising

Data Coverage
80%

Score Model
v2

Keep visually clean.

Opportunity Score and Data Coverage must be clearly separate.

---

# COVERAGE WARNING

If coverage is below a meaningful threshold, show a notice.

Example:

"Limited data coverage. Some factors are demo or unavailable."

Do not block the user from seeing the analysis.

---

# DATA QUALITY NOTES

Surface important limitations.

Examples:

Census:
ACS estimates are survey-based.

Competition:
Mapbox nearby results are an observed provider sample, not an exhaustive
business census.

Rent:
Demo only.

Keep detailed explanations in tooltips or expandable sections where
appropriate.

Do not clutter the main score card.

---

# POPULATION AND INCOME MODELS

Do NOT arbitrarily rewrite Population Model v1 or Income Model v1.

First inspect the Sprint 04 implementation.

Only fix:

- verified inconsistencies
- boundary bugs
- unclear constants
- duplicated logic
- provenance issues

If threshold recalibration is proposed, document why.

Do not tune thresholds merely to create visually attractive scores.

---

# COMPETITION MODEL

Do NOT rewrite Competition Model v1 unless a real bug is found.

Preserve:

higher competition score =
more favorable / lower observed competition pressure

Keep direct competitor proximity meaningful.

---

# RENT FACTOR

Rent remains demo.

Do not make it real.

Do not substitute:

- ACS residential rent
- Zillow rent
- residential housing cost

for restaurant commercial occupancy cost.

Because rent remains demo, Data Coverage should reflect this.

---

# SCORE TRACE / DEBUG VIEW

Create a structured scoring trace internally.

Conceptually:

{
    "model_version": "2.0",
    "factors": {
        ...
    },
    "raw_weighted_sum": 73.42,
    "final_score": 73.4,
    "coverage": 80
}

This may be useful for tests and future auditability.

Do not expose raw debugging objects directly in production UI.

---

# ANALYSIS SERVICE

The analysis service should orchestrate:

1. geography
2. demographics
3. competition
4. factor scoring
5. overall scoring
6. data coverage
7. explanation generation

Keep responsibilities separated.

Do not turn analysis_service.py into a massive untestable file.

Extract services/modules where appropriate.

---

# FAILURE BEHAVIOR

Support mixed availability.

Examples:

Census works
Competition fails
Rent demo

or:

Competition works
Census fails
Rent demo

The score and coverage behavior must be explicit.

Do not silently mark failed data as real.

If the existing system uses demo fallback values, provenance must clearly
say demo fallback.

Coverage must decrease accordingly.

---

# PARTIAL DATA

The system should support factor-level availability.

Example:

Population:
real

Income:
unavailable

Competition:
real

Rent:
demo

The score system must handle this according to current application policy.

Do not invent missing data.

If the overall scoring engine requires fallback values, mark them as
fallback/demo and reduce coverage.

---

# UI

Preserve Sprint 02–04 visual design.

Do NOT redesign VenueBite again.

Improve only:

- score transparency
- contribution display
- coverage indicator
- strengths
- risks
- model/source details

Keep map and competition UI intact.

---

# MOBILE

Verify score breakdown remains usable on mobile.

Avoid wide tables that require awkward horizontal scrolling.

Use stacked factor details where needed.

---

# ACCESSIBILITY

Maintain:

- semantic markup
- keyboard navigation
- focus states
- reduced motion
- sufficient contrast
- labels not based only on color

Score contribution and coverage meaning should be understandable by
screen readers.

---

# TESTING

Before changes:

python -m pytest

Preserve every Sprint 01–04 test.

Add tests for:

Overall scoring
- exact weighted contribution math
- factor weight total
- score clamping
- deterministic rounding
- model version

Coverage
- all real
- all demo
- mixed
- unavailable
- partial
- expected current hybrid coverage
- always 0–100

Provenance
- Census population
- Census income
- Mapbox competition
- demo rent
- fallback states

Explanation engine
- strong population
- weak population
- strong income
- competition pressure
- demo rent risk
- unavailable factor
- no duplicated strength/risk
- deterministic output

Score classification
- boundary values
- 0
- 100
- intermediate bands

Integration
- fully successful U.S. analysis
- Census failure
- competition failure
- partial Census data
- non-U.S. demographic unavailable
- stale analysis prevention

UI rendering
- coverage displayed
- contribution displayed
- source labels
- model version
- demo rent remains obvious

No automated test should require a live external API.

Use:

python -m pytest

---

# MANUAL ACCEPTANCE TESTS

Run several locations.

Examples:

Denver, CO
Indian Restaurant

Greeley exact address
Mexican Restaurant

Chicago, IL
Pizza Restaurant

Miami, FL
Cuban Restaurant

New York, NY
Coffee Shop

Verify:

- opportunity score changes
- factor contributions are correct
- coverage displays correctly
- population real
- income real
- competition real
- rent demo
- explanations reflect actual factor values
- no explanation contradicts score
- score model says v2
- map still works
- satellite still works
- competitor markers still work
- radius selector still works
- Census source/vintage still works

Also test provider failure states.

---

# MODEL DOCUMENTATION

Update README with:

VenueBite Score Model v2

Document:

- factors
- factor semantics
- weights
- contribution calculation
- coverage calculation
- model limitations
- real/demo provenance
- classification bands
- explanation rules
- why coverage is not predictive confidence
- rent limitation

Do not market the model as scientifically validated.

---

# OPTIONAL ENGINEERING DOCUMENT

If useful, create:

docs/scoring-model-v2.md

Document:

- architecture
- weights
- formulas
- thresholds
- provenance
- coverage
- examples
- limitations
- future calibration work

Do not create documentation merely to inflate file count.

---

# DO NOT BUILD IN SPRINT 05

Do not implement:

- new data providers
- commercial-property APIs
- commercial rent APIs
- zoning
- permits
- traffic APIs
- foot traffic
- database
- authentication
- Keycloak
- saved analyses
- accounts
- AI
- LLM
- chatbot
- Docker
- deployment
- payments
- subscriptions
- React

Keep Sprint 05 focused on SCORING + EXPLAINABILITY.

---

# ACCEPTANCE CRITERIA

Sprint 05 is complete only when:

1. Sprint 01 functionality remains intact.
2. Sprint 02 map/location remains intact.
3. Sprint 03 competition remains intact.
4. Sprint 04 Census demographics remain intact.
5. Score Model v2 is explicitly versioned.
6. Factor weights are centralized.
7. Factor contributions are computed backend-side.
8. Overall score remains deterministic.
9. Overall score remains bounded 0–100.
10. Data Coverage is computed separately.
11. Coverage is bounded 0–100.
12. Coverage does not imply success probability.
13. Provenance is structured.
14. Population remains real Census.
15. Income remains real Census.
16. Competition remains real observed data.
17. Rent remains demo.
18. Strengths are deterministic.
19. Risks are deterministic.
20. Explanations reflect actual factor data.
21. Demo/unavailable factors reduce coverage.
22. UI shows factor contribution.
23. UI shows Data Coverage.
24. UI shows Score Model v2.
25. UI clearly separates score from coverage.
26. Failure states remain transparent.
27. No new external provider is added.
28. No credential handling regresses.
29. Existing tests pass.
30. New tests pass.
31. App runs with:

    python app.py

32. Tests run with:

    python -m pytest

33. Git status is shown.
34. Codex does not commit.
35. Codex does not push.

---

# FINAL VERIFICATION

Before completion:

1. Run:

   python -m pytest

2. Start:

   python app.py

3. Test multiple locations/concepts.

4. Verify contribution calculations manually for at least one result.

5. Verify weights total 100%.

6. Verify Data Coverage manually for at least one result.

7. Verify rent remains demo.

8. Verify map/satellite.

9. Verify competitor markers.

10. Verify Census source/vintage.

11. Verify fallback states.

12. Inspect browser console.

13. Inspect Flask logs.

14. Inspect git diff.

15. Inspect git status.

16. Confirm `.env` remains ignored.

17. Confirm no credentials are exposed.

18. Confirm no unrelated architectural rewrite occurred.

DO NOT COMMIT.

DO NOT PUSH.

---

# FINAL RESPONSE

When finished, report:

1. What Sprint 05 implemented.
2. Files created.
3. Files modified.
4. Score Model v2 formula.
5. Factor weights.
6. Factor contribution design.
7. Coverage model.
8. Coverage labels.
9. Provenance structure.
10. Explanation engine design.
11. Strength/risk rules.
12. Score classifications.
13. Test count/result.
14. Manual test results.
15. Known limitations.
16. Git status.
17. Anything Chris should manually verify.

Do not commit.
Do not push.