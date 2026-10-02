# VenueBite Score Model v2

## Purpose and Architecture

Model `2.0` makes the existing four-factor opportunity heuristic auditable. It
does not recalibrate the factors, predict restaurant outcomes, or introduce new
data providers. Flask/Jinja, signed Mapbox selections, live competition and Census
orchestration remain in place.

`AnalysisService` assembles independent provider results and per-factor
`FactorProvenance`. It then calls the pure overall calculator, coverage calculator,
explanation function, and trace builder. Routes and templates do not implement
formulas or request additional data. The report carries immutable score, coverage,
explanation and trace objects; the trace is internal, not frontend debug JSON.

The original numeric-only `ScoreResult.strengths` / `risks` remain compatible with
Sprint 01 callers. The application renders `report.explanations`, which adds
provenance, real metrics, weighted ranking and evidence-gap interpretation.

## Formulas and Direction

Population and income weigh 30% each; rent and competition weigh 20% each. The
weights total 100% and are defined only in `scoring.FACTOR_DEFINITIONS`. Every
factor direction is `higher_is_better`; expected sources are Census, Census,
demo fixture, and Mapbox, respectively.

- Population: more favorable tract population context, not density or demand.
- Income: stronger household purchasing-power context, not restaurant spending.
- Rent: more favorable commercial occupancy affordability; still fictional.
- Competition: lower observed pressure; direct and nearby matches matter more.

```text
weighted_points = score * weight
raw_weighted_sum = math.fsum(weighted_points)
opportunity_score = round(clamp(raw_weighted_sum, 0, 100), 1)
```

Invalid inputs remain errors rather than silently clamped factor scores.
Contributions retain full precision and display two decimals. The unrounded
total is rounded once to one decimal before classification; unusual arbitrary
input precision can make summed displayed points differ slightly from that total.
Population Model v1, Income Model v1 and Competition Model v1 are unchanged.

Classifications remain Strong at 80+, Promising at 65+, Mixed at 50+, and
Challenging below 50. They describe heuristic model context, not investment advice.

## Separate Data Coverage

Coverage uses the same weights but only structured factor evidence statuses:

```text
real credit = 1.0
explicit factor-level partial credit = 0.5
demo, fallback, unavailable credit = 0.0
coverage = round(sum(weight * credit * 100), 1)
```

Coverage is bounded 0-100. Labels: Very high at 90+, High at 70+, Moderate at 50+,
Limited at 25+, Very limited below 25. Below 70%, a nonblocking verification
notice appears. Coverage never changes the Opportunity Score or factor scores.

A successful current hybrid is 30 + 30 + 0 + 20 = **80%**. Census failure leaves
20%; competition failure leaves 60%; both failures/demo-only leave 0%. One usable
Census factor with live competition gives 50%. Genuine zero Census estimates
receive full coverage even though their factor scores are zero.

An aggregate partial Census response still gives full credit to each usable
estimate and no credit to the missing estimate's demo fallback. The explicit
`partial` credit is supported for factor-level incomplete inputs; current provider
results are not newly assigned that status. Missing MOEs do not invalidate usable
estimates. Capped Mapbox samples can be usable without being exhaustive. Coverage
does not measure discovery completeness, precision, accuracy, statistical
confidence, or success probability. It cannot reach 100% real support while rent
remains demo.

## Provenance and Trace

Each factor retains status, provider, source label, optional ACS vintage/GEOID,
factor-model version, description and sanitized fallback reason. Coverage never
guesses provenance from a source label. Trace entries add direction, expected
source, score, weight, weighted points, evidence credit and coverage points; the
trace also retains overall model version, raw sum, final score and coverage.

No keys, raw provider bodies, or transport URLs are added to the trace. Private
Census configuration stays server-side; existing public Mapbox rendering behavior
is unchanged. No data is persisted or cached.

## Explanation Rules

The explanation engine has no I/O, AI or randomness.

- Fully real factors scoring 75+ are strength candidates, ranked by weighted
  contribution; the top two appear. Stable ties use centralized factor order.
- Real factors below 65 are review risks. At least two observed direct competitors
  within 0.5 mile also flag a proximity risk. Wording retains the actual Competition
  Model v1 pressure level instead of relabeling moderate pressure as high.
- Demo, fallback, unavailable and explicit partial inputs are verification risks
  regardless of their numeric score. Rent is unverified commercial occupancy
  context, not proof of expensive rents. No residential rent substitutes are used.
- Real risks rank by weighted score deficit; evidence gaps rank by missing
  coverage weight. At most four items appear, one per factor; a factor cannot be
  both a strength and a risk.
- Each item explains the contribution and weight. Actual ACS estimates and
  observed counts/distances are used where available. Empty POI samples are never
  evidence that no competitors exist. Summaries and expandable quality notes use
  those same normalized results.

## Verification on 2026-10-02

Baseline: **487 tests**. Sprint 05 adds **91 tests**, for **578 passing tests**
using `python -m pytest`; no automated test needs an external API.

Live browser reports at a 3-mile radius:

- Denver, CO + Indian: 42.6 opportunity, 80% coverage, 37 observed restaurants;
  GEOID 08031002604. Contributions 14.64 + 11.04 + 11.00 + 5.88 = 42.56 -> 42.6.
- 701 10th Avenue, Greeley, CO + Mexican: 39.8, 80%, 42 restaurants;
  GEOID 08123000100. Contributions 16.71 + 8.64 + 11.00 + 3.40 = 39.75 -> 39.8.
- Chicago, IL + Pizza: 69.8, 80%, 50 restaurants; GEOID 17031839100.
  Contributions 28.14 + 27.87 + 11.00 + 2.74 = 69.75 -> 69.8.
- Miami, FL + Cuban: 36.8, 80%, 49 restaurants; GEOID 12086003704.
  Contributions 9.12 + 12.90 + 11.00 + 3.76 = 36.78 -> 36.8.
- New York, NY + Coffee: 61.0, 80%, 50 restaurants; GEOID 36061003100.
  Contributions 17.52 + 30.00 + 11.00 + 2.44 = 60.96 -> 61.0.

All five reports showed real Census population/income, real observed Mapbox
competition, demo rent and Model v2. Chicago listed its stronger demographic
factors while identifying high observed competition pressure. Denver/Miami did
not invent strengths for weak demographics. New York listed income, not its
below-threshold population, as a strength. POIs and scores can change per request.

Independent live-provider diagnostics confirmed 20% coverage with Census disabled
and usable Mapbox competition; an injected competition failure with actual Census
data preserved 60% coverage and rent verification risk. Mocked integration tests
also cover both failures, partial estimates, genuine zero values, non-U.S. skips,
signed coordinates, stale reports, template escaping and credential isolation.

A live Paris + Indian browser report scored 63.8 with 20% coverage and 50 observed
POIs. Population/income were explicitly demo fallback, Census was U.S.-only
unavailable, and the nonblocking evidence-gap notice was visible. Editing the
concept hid the whole old analysis and removed all restaurant markers. Demo-only
route verification retained 72.5 with 0% coverage, not invented real-data support.

Browser checks covered map and satellite imagery, competitor popups, 1/3/5-mile
reports with unchanged Census tract, stale score/coverage/Census/marker clearing,
keyboard-expanded source details, and 390x844 / 1366x900 / normal desktop layouts
without horizontal page overflow. No browser warning/error entries were observed
in the live U.S. acceptance session. The normal `python app.py` entry point started
successfully and was stopped after checking startup; the separate preview on port
5004 does not replace the user's preexisting servers.

## Limitations and Calibration Work

Neither opportunity nor coverage is a validated probability or forecast. ACS is
survey-based, pooled over five years and subject to margins of error; containing
tracts are proxies, not trade areas. Shared-boundary points can legitimately fail
as ambiguous. Mapbox discovery is capped, incomplete and category/matching
dependent. Rent is still demo and can materially influence the score. No traffic,
commercial-property cost, profitability or concept-demand data has been added.

Future calibration should use documented, outcome-independent research on factor
normalization, comparable geographic context, missing-data policies, sample
uncertainty and trustworthy commercial occupancy evidence. Any changed anchors
or weights need an explicit model version and evidence; do not tune them to make
scores look attractive. Persistence, provider licensing, new APIs and other
roadmap product areas remain separate work.

Chris should review the live reports and decision-support language in his normal
browser, including keyboard/reduced-motion preferences and provider outages. No
new API keys, dependencies or manual data migrations are required. Restart an
older local server to load the new Python modules/templates, or use the port-5004
preview. No commit or push was performed.
