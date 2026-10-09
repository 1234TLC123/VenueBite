# Sprint 08 UI System

## Principles

VenueBite remains an analysis application, not a landing page. The visual hierarchy is location, Opportunity Score, Data Coverage, map, factors, review signals, market context, and property context. Decision metrics are visible; supporting methodology is disclosed on demand. Fictional, partial, unavailable and real evidence remain distinct.

Sections are unframed layouts separated by restrained rules. Only repeated factor items and genuinely framed tools such as the map use card-like surfaces. No backend model, weight, provider or provenance policy was changed in this sprint.

## Tokens

All shared colors live in the opening custom-property block of `static/css/style.css`.

- Page: near-black `--page`; surfaces: charcoal `--surface`, `--surface-elevated`, `--surface-glass`.
- Text: `--ink` and `--muted`; borders: `--line`, `--border-strong`.
- Commands/geography: cyan `--accent`, `--accent-soft`.
- Favorable evidence: green `--green`, `--green-light`.
- Review: amber `--amber`, `--amber-light`; challenging classification: muted coral `--red`, `--red-light`.
- Partial evidence and occupancy utilization: `--violet`.
- Corners: `--radius: 6px`. Spacing uses predominantly 8, 12, 16, 24 and 32px.
- System font stack; fixed-size typography, zero letter spacing, tabular numeric metrics. No remote font dependency.

## Layout

A compact sticky header keeps the brand and functioning Analyze navigation available. A single backdrop blur is limited to this header. The constrained workspace reaches 1480px with responsive gutters.

The main desktop grid pairs the score overview with a 500px map (480px on smaller laptops). Four factors occupy a separate row. Strengths/review signals use an unframed split layout. Demographics and competition, then site and occupancy, use paired columns.

The form gives location the largest track. Optional occupancy terms use native details, grouped fieldsets, explicit labels, and the existing input names. At narrower widths, the form, factors, and section grids collapse independently.

Fresh reports focus their location heading and move it below the sticky header immediately, without a theatrical animation. Persisted back-forward navigation does not re-run report arrival; existing analysis invalidation still clears stale evidence.

## Evidence Badges

The existing provider labels and statuses are preserved, not renamed into stronger claims. Real evidence uses muted green; partial user terms use violet; demo and fallback use amber, with an additional fallback border; unavailable uses neutral charcoal. Labels communicate the same information without color.

`data-factor-evidence` exposes the actual status for semantic regression tests. It does not create a new evidence model. Regrid remains outside both score and coverage. Rent stays demo unless Sprint 07's existing budget-fit requirements are satisfied.

## Score Visualization

The server-rendered numeric Opportunity Score is immediate and accessible. A decorative, aria-hidden SVG circle uses the same score, a 100-unit path, and a computed dash offset. Its color follows the existing classification. No rounding, weighting, classification or scoring threshold is modified.

The ring is not an animated counter. Classification, Score Model v2, and the non-prediction warning remain visible.

## Data Coverage

Coverage is separate from opportunity. Four segments have widths equal to the existing factor weights (30/30/20/20); inner fills use their existing real/partial/other credits (1/.5/0). A partial segment is additionally striped. The accessible native meter retains the exact server-calculated coverage value.

The numeric percentage, existing coverage label, and "not success probability" caution remain visible. Evidence quality details retain factor credits, unavailable-data explanations and model caveats.

## Factors and Contributions

Each factor shows score, weight, evidence, weighted points, and expandable source/model information. Factor meters show raw factor scores.

The separate contribution graphic shows weighted points on one common 0-30 point scale. This scale accommodates the largest factor weight and permits valid visual comparison. It is not a normalized raw-score graphic. All values also appear as text.

## Map and Market Context

Mapbox's existing configuration, authentication, SDK, map/satellite behavior, recentering, markers, popups and parcel layering are untouched. Controls receive consistent framing and minimum touch targets. Attribution stays visible. Actual Mapbox media supplies the primary visual asset.

Area metrics emphasize population/income values and retain real/demo/unavailable labels. Census geography, vintage and margins of error move into native source details; the tract/ACS interpretation caution stays visible.

Competition highlights observed restaurants, direct matches, radius and score. The pressure meter displays `100 - competition score` as a presentation index, not the raw provider pressure-points quantity. Model details retain raw pressure and the original formula. Direct matches are open by default; general restaurants are expandable. Tables keep names, addresses, match basis and distance, with bounded scrolling and sticky headers. Limited-sample coverage and Mapbox attribution remain visible.

## Property Context

No-parcel responses use a neutral unavailable state and the original explanation, including that parcel nonexistence is not established. When present, parcel facts and zoning cautions remain visible; source/match considerations are expandable. The separation from scoring, assessment/sale limitations, and missing-field interpretation are always visible rather than hidden in a disclosure.

Occupancy separates base, additional, known total and budget facts. A compact cost/budget strip emphasizes the known monthly total and the user's threshold. The utilization graphic has a 0-150% visual scale, a marked 100% budget line, and a clamped progress value. The true utilization remains visible and accessible even above 150%. No visual clamping changes scores. User-supplied status, excluded-cost warning, budget-relative limitation and fallback reason remain clear.

## Motion and Background

A small locally authored SVG supplies abstract contour lines and a grid, not a fake geographic map. A single CSS scan plane animates transform and opacity slowly. It is aria-hidden, pointer-inert, and behind the application. There is no video, particle loop, animation framework, gradient orb, or extra API.

`prefers-reduced-motion: reduce` disables animation, transitions and smooth scrolling, while preserving the backdrop. Existing Mapbox reduced-motion handling is unchanged. No motion is required to read scores or evidence.

## Accessibility and Responsive Strategy

- Semantic sections, fieldsets, legends, tables, labels and native details remain server-rendered.
- Skip navigation, visible focus, status/live regions, invalid-field focus and busy state are retained.
- Input wrappers provide the focus indicator without a second competing inner outline.
- Icons reuse the local Lucide assets. Unfamiliar icon controls retain accessible names and native title tooltips.
- Charts have numeric text/native meter or progress alternatives; color is never the only information channel.
- 1280px tightens gutters; 1000px adapts forms and market columns; 700px stacks score/map; 480px uses compact mobile controls and single-column lease groups.
- Mobile places the score and coverage before the map, followed by factors, review, market and property evidence.
- Long text wraps; tables scroll within their section. The map retains 340px height on narrow phones.

## Performance

No dependency was added. No heavy image/video/font download or chart library is involved. The only continuously animated decoration uses transform/opacity. The SVG is small, cached and local. Native details do not require JS. Form UI is isolated from map/provider code.

## Files

Created: `static/images/geospatial-field.svg`, `static/js/form-ui.js`, `templates/_score_overview.html`, `templates/_factor_intelligence.html`, `templates/_strengths_risks.html`, `tests/form-ui.test.mjs`, `tests/run-js-tests.mjs`, `tests/test_ui_modernization.py`, this document, and `docs/sprint08-engineering-report.md`.

Modified for Sprint 08: `static/css/style.css`, `static/js/main.js`, `templates/base.html`, `templates/index.html`, `templates/results.html`, `templates/_competition.html`, `templates/_demographics.html`, `templates/_site_intelligence.html`, the existing untracked Sprint 07 `templates/_occupancy.html` and `templates/_occupancy_form.html`, `tests/test_routes.py`, `tests/test_competition_routes.py`, `tests/test_demographic_integration.py`, and `README.md`.

Existing Sprint 07 backend changes and untracked files were preserved. Temporary preview/fixture helpers and logs are ignored under `.venv/`.

## Verification and Next UI Work

Run `python -m pytest` and `node tests/run-js-tests.mjs` in environments with Python and Node. The same JS exports can run in the provided JavaScript runtime without a terminal Node executable.

See the engineering report for live values, acceptance scenarios, security checks and limitations. Future improvements should include a screen-reader audit, cross-browser QA and user testing. Do not add unfinished navigation until its workflow exists.
