# Commercial Occupancy Model v1

## Scope and Architecture

Sprint 07 separates occupancy calculations from affordability context. Quoted rent is not a nationwide good/bad price. Model `commercial-occupancy-v1` measures fit relative to the user's own monthly USD occupancy budget; it is not market rent, fair market value, revenue-relative affordability, profitability or a lease recommendation.

`occupancy.py` contains frozen candidate/rate/cost/model contracts and pure Decimal calculators. `services/occupancy_service.py` normalizes untrusted fields, validates them, determines cost completeness, generates candidate facts/cautions, and invokes the budget model. `AnalysisService` replaces only rent before existing Score Model v2, coverage, explanations and trace calculation. Routes only validate/orchestrate/render. Templates contain no lease or scoring formulas; JavaScript only invalidates report state. There are no new dependencies, providers or network requests.

## Input Contract

The normalized `CandidateProperty` contains:

- `source_type`: always `user_supplied` for this workflow; request attempts to supply other status/provider fields are ignored.
- `source_label`, `source_url`: optional provenance metadata; default label `Commercial listing / user entry`.
- `property_address`: optional contextual address; when other terms are supplied and this is blank, the selected analysis label is attached in the report.
- `space_size_sqft`: optional positive Decimal square feet, never inferred from a parcel/building.
- `asking_rent`: optional `OccupancyRate(value, basis)`.
- `lease_structure`: `nnn`, `gross`, `modified_gross`, or `unknown`.
- `additional_occupancy_rate`: optional `OccupancyRate(value, basis)`.
- `monthly_occupancy_budget`: optional positive Decimal, the user's operating threshold, not market data.
- `notes`: optional text, submitted as `occupancy_notes`.
- `provided`: distinguishes untouched optional form defaults from actual candidate input.

Form fields for rate bases are `asking_rent_basis` and `additional_occupancy_basis`. Valid bases are `per_sqft_per_year`, `per_sqft_per_month`, `total_monthly`, and `total_annual`. Defaults are per-SF/year and unknown lease structure, visibly selected in the form; these defaults alone do not constitute evidence.

## Normalization and Validation

Plain decimal numbers and correctly grouped comma amounts are supported. Monetary inputs may include a leading dollar sign. Up to six decimal places are retained. No exponent notation, NaN, infinity, malformed grouping/currency, negative rent/charges, zero/negative size or budget is accepted. Explicit zero base rent/additional charges is an allowed user assertion. Missing fields remain `None`, never zero.

Size is bounded to 10,000,000 SF and each monetary input to $100,000,000. These are safety limits, not affordability thresholds. Inputs are limited to 48 characters for numbers/enums; address 300, label 120, source URL 2,000 and notes 1,000. Duplicate values for any occupancy field, invalid enums and control characters are rejected. Notes may contain ordinary newlines/tabs. The existing 16-KiB request bound remains in place.

Validation returns immutable values/errors and an `invalid` input status. Routes return HTTP 400 with field-specific errors, retained bounded values and any matching signed geographic selection, before any Census/POI/Regrid request. Invalid input is never silently accepted as a successful report. A too-large whole request returns the existing HTTP 413 handler.

## Lease and Currency Policy

All entered money is explicitly USD, including non-U.S. selections; no automatic currency inference or conversion occurs. NNN may exclude tax, insurance, maintenance/CAM and other pass-throughs. Gross inclusions vary; Modified Gross depends on the agreement; Unknown assumes nothing. Recording a lease type never invents operating expenses or guarantees exclusions.

The selected Mapbox coordinates remain authoritative. Property address is metadata only. Case/punctuation/whitespace-normalized address text is compared; different text produces a conservative verification warning, never a geocode or moved point. Abbreviations or a less complete address can also warn; this is not a postal-address verification engine. A source URL is not a geocoding input.

## Cost Formulas

Both base rent and additional charges normalize independently:

```text
per_sqft_per_year: annual = size * rate; monthly = annual / 12
per_sqft_per_month: monthly = size * rate; annual = monthly * 12
total_monthly: monthly = amount; annual = monthly * 12
total_annual: annual = amount; monthly = annual / 12

estimated_monthly_occupancy = monthly_base + monthly_additional
estimated_annual_occupancy = annual_base + annual_additional
```

Per-SF amounts cannot be calculated without size. Flat totals can be calculated without size, but model activation still requires size. Decimal calculations retain precision; display currency uses cents with `ROUND_HALF_UP`. Display rounding never feeds calculations, budget ratios or scoring. Components displayed at cents may occasionally differ from a displayed total by a cent because the total uses retained precision.

## Completeness and Activation

Candidate states are structured:

- `not_provided`: untouched/empty optional fields; no occupancy panel and unchanged demo rent/provenance.
- `partial`: some valid input, but size or complete calculable costs are missing.
- `complete`: usable size and calculable base plus explicit additional charges. Budget may still be missing.
- `invalid`: normalization errors; shown only in the input-validation result, not a successful analysis.

Cost completeness is independently structured:

- `unknown_expenses`: no calculable base rent; no total inferred.
- `base_only`: calculable base, no calculable additional charges; show base rent, not total occupancy.
- `base_plus_additional`: both supplied components calculated; show their combined estimate with an exclusions caution.

**Conservative v1 policy:** all lease structures require explicit additional charges, including a supplied zero, to claim a combined estimate or activate rent scoring. A Gross label alone does not establish that base rent is total occupancy. Missing NNN/CAM charges therefore keeps demo rent even if a budget exists. The estimate is complete only for the entered components, not complete lease underwriting.

Activation requires usable size, calculable base and additional charges, plus a valid positive monthly budget. Complete costs with no budget are calculated and displayed but retain demo rent 55/100 with `Demo fallback - occupancy budget not supplied`. Insufficient costs/size retain 55 with an insufficient-terms reason. Raw rate, source label, address, Regrid assessments and building area cannot activate the model.

## Budget Model

Let `r = estimated_monthly_occupancy / monthly_occupancy_budget`. Anchors are centralized in `BUDGET_ANCHORS`:

```text
r <= .70: 100
.70 -> 100; .85 -> 85; 1.00 -> 55; 1.15 -> 25; 1.50 -> 0
r >= 1.50: 0
between (a, sa) and (b, sb): score = sa + (r-a)/(b-a) * (sb-sa)
```

Scores are monotonic, bounded 0-100 and rounded to one decimal with Decimal half-up. Within-budget bands are well within at <=70%, within at <=85%, near at <=100%, above at <=115%, materially above beyond 115%. Thresholds are transparent product heuristics, not externally calibrated research and not tuned to produce appealing Opportunity Scores. At 100% the score is 55: being exactly at a chosen budget leaves no headroom in this heuristic. The model cannot judge whether the user's budget itself is realistic.

## Provenance, Score and Coverage

An active rent factor uses status `partial`, provider `user_supplied`, label `PARTIAL EVIDENCE`, version `commercial-occupancy-v1`, budget-relative description and the supplied source label. Source text cannot upgrade it to real. An inactive factor keeps the existing demo score/provider/status, adding only a reason when terms were provided. None of the other factor statuses or numerical models changes.

Score Model v2 remains `2.0`, with 30/30/20/20 weights. Rent contribution is `rent_score * .20`; the existing overall formula sums full-precision contributions and rounds the total once to one decimal. The immutable trace records actual rent source/model/status, score, contribution and coverage credit. The original expected-source field retains the default demo expectation for compatibility; actual fields show the optional supported model.

```text
without supported rent: 30*1 + 30*1 + 20*0 + 20*1 = 80%
with partial rent:      30*1 + 30*1 + 20*.5 + 20*1 = 90%
Census failed, supported rent and competition: 10 + 20 = 30%
competition failed, Census and supported rent: 30 + 30 + 10 = 70%
both providers failed, supported rent only: 10%
```

Coverage is usable evidence support, not accuracy, statistical confidence, demand or success probability. User terms never produce 100% coverage. Regrid remains separate and cannot change these values. Unavailable Census factors retain independent fallback, and real zero estimates remain usable.

## Explanations and Presentation

The optional form starts collapsed. When expanded, Analyze moves after the terms; no duplicate command or new workflow is introduced. The separate full-width occupancy section renders supplied rates/size, base/additional/combined estimates, budget utilization, score/model/status, source and notes. Calculable supplied base rent suppresses the fictional area asking-rent metric, even when budget is absent; it does not falsely label the new terms real.

Deterministic explanations state within or above the stated monthly budget, with a user-evidence verification risk. Partial rent never qualifies as a fully real global strength, preserving Sprint 05 semantics. Missing extras and budget get explicit cautions. No cheap/below-market, good/bad lease, sign/invest, revenue or profitability claim is generated. Editing any occupancy field, location, concept or radius hides all old output, clears provider/map snapshot metadata and marks occupancy stale until resubmission. Back-forward restoration also invalidates the report.

## Security and Limitations

Source URLs accept safe HTTP(S) links only, rejecting unsafe schemes, credentials, invalid ports, local-host links and credential-style query parameters. Links use `rel="noopener noreferrer"`; user text/notes are Jinja-escaped. No source URL is fetched. Occupancy has no logging, storage, database, browser persistence or API credential requirement. Responses use the existing `Cache-Control: no-store` policy.

No property availability or independently verified lease evidence exists. Excluded costs, concessions, percentage rent, recurring escalations and buildout underwriting are not inferred. A future licensed provider could supply normalized commercial terms through these calculator/service boundaries, but would need its own verified-evidence and completeness policy; it is not implemented here. Model anchors need outcome-independent calibration before consequential use.

See [Sprint 07 engineering report](sprint07-engineering-report.md) for test counts, all acceptance scenarios, startup, Git/security verification and any outstanding live-provider checks.
