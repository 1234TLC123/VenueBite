# Sprint 11 Engineering Report

Implementation and acceptance verification: **October 11, 2026, America/Denver**. Analyst instruction version used during development: `venuebite-ai-analyst-v1`. User-facing brand finalized during this sprint: **SiteWise** ("VenueBite's AI location intelligence analyst"), with **Ask SiteWise** as the primary call to action. Branding is presentation only; internal technical names were not renamed.

## 1. Sprint Objective

Add a grounded AI location analyst that converses about the current completed analysis, one saved snapshot, or 2-4 compared snapshots using only trusted server-built VenueBite evidence. Preserve all Sprint 01-10 behavior, Score Model v2, Data Coverage semantics, occupancy/parcel/regulatory evidence meanings, saved-page zero-provider isolation and Mapbox storage restrictions. The model explains evidence; it is not a scoring engine, fact source, legal adviser or autonomous agent.

## 2. Baseline

Read `AGENTS.md` and `prompts/11-ai-analyst-chatbot.md` before implementation, then prior design docs (`scoring-model-v2`, `site-intelligence-v1`, `commercial-occupancy-v1`, `zoning-regulatory-feasibility-v1`, Sprint 09/10 reports) and the existing routes, services, providers, repositories, templates, static JS, snapshot/signing utilities, comparison system, configuration and tests. Branch: `1234tlc123-probable-succotash`; starting HEAD: `5fca56b` (clean worktree). Baseline suites from the verified Sprint 10 state: **1,191 Python tests** and **70 JavaScript tests** passing. The existing signed-snapshot/token architecture (`itsdangerous` serializer used by Saved Sites) was identified for reuse as the trusted AI context mechanism.

## 3. Deliverables

Provider-abstracted OpenAI Responses integration; deterministic evidence registry; signed/session-bound trusted contexts for current, saved and compare; structured grounded response contract with server-side citation validation and canonical-value substitution; versioned analyst instructions; prompt-injection and credential guards; CSRF-protected JSON chat endpoint; SiteWise drawer UI with evidence disclosures, starters and full state handling; invalidation on analysis-input changes; cost/rate bounds; 111 new Python tests and 32 new JavaScript tests; design/privacy documentation; README section; this report. No database migration, no chat persistence, no new frontend framework, no Assistants API, no web search or tools.

## 4. Changed Files

New application files (7): `venuebite/ai.py`, `venuebite/ai_routes.py`, `venuebite/providers/openai_provider.py`, `venuebite/services/ai_analyst_service.py`, `venuebite/services/ai_context.py`, `venuebite/services/ai_evidence.py`, `venuebite/services/ai_response_validator.py`.

New frontend files (3): `templates/_ai_analyst.html`, `static/js/ai-analyst.js`, `static/css/ai-analyst.css`.

New tests/docs (4): `tests/test_ai_analyst.py`, `tests/ai-analyst.test.mjs`, `docs/ai-location-analyst-v1.md`, `docs/sprint11-engineering-report.md`. The sprint prompt `prompts/11-ai-analyst-chatbot.md` is also present as an untracked worktree file.

Modified files (10): `.env.example`, `README.md`, `requirements.txt` (adds `openai==3.29.0`), `templates/base.html`, `tests/run-js-tests.mjs`, `tests/test_routes.py`, `venuebite/__init__.py`, `venuebite/routes.py`, `venuebite/saved_routes.py`, `venuebite/services/saved_site_service.py` (`allow_unresolved` snapshot option and an `sk-` credential pattern added to the existing save guard).

`scoring.py`, `data_coverage.py`, demographic/competition scoring, occupancy, snapshots, repositories and the comparison service are untouched.

## 5. Architecture

Routes stay transport-only: `ai_routes.py` handles CSRF/session, content type, body limits and JSON decode, then delegates to `AIAnalystService`. `venuebite/ai.py` centralizes the provider protocol, bounds, errors, response schema and versioned instructions. Services own orchestration (`ai_analyst_service`), trusted context construction/resolution (`ai_context`), the evidence whitelist (`ai_evidence`) and fail-closed output validation (`ai_response_validator`). The OpenAI SDK is confined to `providers/openai_provider.py`; no other module imports or receives SDK objects. `create_app` wires an injectable `ai_provider`, so tests use fakes and future providers need no service rewrite.

## 6. AI Provider Design

`AIProvider` is a one-method protocol (`answer(context, question, history)`) plus an `enabled` flag. `OpenAIProvider` adapts it to the official SDK; `FakeAI` (tests) injects deterministic outputs/errors. The provider receives the compact model context, never raw snapshots, raw provider payloads or secrets beyond its own key. Provider exceptions are caught at the boundary and replaced with fixed sanitized `AIError`s; arbitrary exception text is never logged or returned (regression-tested).

## 7. OpenAI API Integration

Current official documentation and the installed SDK were verified before coding (references in `docs/ai-location-analyst-v1.md`). Integration uses `client.responses.create` with `instructions`, a single user JSON input message, `text.format` strict JSON schema, `store=False`, `stream=False`, `tools=[]`, `tool_choice="none"`, bounded `max_output_tokens` and timeout, `max_retries=0`, fixed `https://api.openai.com/v1` base URL, no redirects and no ambient proxy trust. No Assistants, Conversations, previous-response IDs or provider-side prompt storage (asserted by tests, including a real-SDK mock-transport test confirming a single `/v1/responses` request). Refusal/incomplete status, malformed JSON, duplicate keys, non-finite values and oversized output are rejected with safe errors.

## 8. Model / Configuration

One configuration value, `OPENAI_MODEL`, defaults to `gpt-4.1-mini`: a cost-conscious, low-latency non-reasoning model with strict structured-output support, sufficient for explanation over pre-computed evidence; the most expensive models were deliberately not assumed. `OPENAI_API_KEY`, `OPENAI_TIMEOUT_SECONDS` (clamped 1-45) and `OPENAI_MAX_OUTPUT_TOKENS` (clamped 256-2000) are environment-only; `.env.example` contains placeholders. Invalid model syntax falls back to the central default. Changing models requires no code change. Without a key the app runs normally and SiteWise reports itself unavailable.

## 9. Trusted Context Model

Browser-supplied analytical facts are never trusted: the chat request carries only a server-signed context token, the question, bounded user/assistant history and a request ID; any extra key (score, facts, model, tools...) is rejected with 400 before any provider call. Tokens use a dedicated `venuebite-ai-context-v1` salt, context version, SHA-256 binding to the session CSRF nonce, 30-minute expiry and a 20,000-character cap. Tampered, expired, foreign-session, wrong-version or wrong-kind tokens fail closed as stale context (409). Chat never triggers Census, Mapbox, competition, Regrid or Denver zoning calls.

## 10. Current-Analysis Context

A completed analysis builds a normalized snapshot server-side (via the existing snapshot builder, with a narrowly scoped `allow_unresolved=True` so honestly labeled demo analyses are discussable; save semantics unchanged) and signs the minimized evidence into the token. The session stores the current token's hash; a newer completed analysis invalidates the previous token (409, regression-tested). Client-side, the existing `venuebite:analysis-invalidated` event (location, concept, radius, occupancy, regulatory edits) clears token, history and pending replies; back/forward restoration invalidates; generation guards discard late responses.

## 11. Saved-Site Context

Saved-detail tokens store only the site ID and a strict snapshot digest. Sending a question reloads the record through `SavedSiteService` and rejects deleted or changed records. The context marks evidence historical with original model versions and dates; the assistant is instructed to present saved evidence as a historical snapshot, never live data. Opening saved detail makes zero external provider calls (instrumented test fails on any provider method).

## 12. Compare Context

Compare tokens store 2-4 selected site IDs plus digests; resolution reloads exactly those records through the unchanged `ComparisonService`. Unselected sites never enter the context. Deterministic score/coverage deltas (`Decimal` on stored values) and the existing neutral highlights/warnings are supplied as evidence so the model explains rather than recomputes comparisons. Deleting a compared site invalidates the token; compare-picker changes invalidate the conversation client-side.

## 13. Evidence Registry

`EvidenceRegistry` deterministically whitelists per-site IDs (`s1.score`, `s1.population.contribution`, `s1.census.income`, `s1.occupancy.monthly_known_total`, `s1.site.match`, `s1.regulatory.district`, `s1.regulatory.permission`, ...) and pairwise `compare.s1_s2.*` deltas. Each entry carries label, exact value, readable display, units, evidence status (model/real/partial/demo/fallback/unavailable/unsupported/user-supplied/official fact/guidance/unknown), source, date, reviewed official URL where appropriate, and limitations. Missing values stay `null`/unknown, never zero. Duplicate IDs raise. The registry contains no secrets and no raw third-party payloads; identical snapshots produce identical registries (tested).

## 14. Structured Response Contract

The model must return `{answer_blocks: [{text, evidence_ids}], limitations}` under a strict JSON schema. Server validation rejects unknown keys, 0 or >5 blocks, uncited blocks, unknown/duplicate evidence IDs, >1,000-char block prose, >3 or >300-char limitations and >16 KiB output. All numbers/dates/codes must be `{{evidence_id}}` placeholders that are also cited; the server substitutes canonical values and evidence labels, so the model cannot author a figure, URL or citation chip. Literal digits, HTML, markdown links and control characters in model prose are rejected. Unknown-value citations require explicit missing/unverified language. Invalid output returns a safe 502 fallback; nothing malformed is rendered.

## 15. Analyst Instruction / Version

`venuebite/ai.py` holds the versioned instruction set, `venuebite-ai-analyst-v1`, exposed internally via `PROMPT_VERSION` and included in every API response for debugging/tests. The analyst self-identifies as SiteWise, VenueBite's grounded AI location intelligence analyst (branding only; rules unchanged). Instructions forbid invented facts, score recalculation, coverage reinterpretation, legal/permission conclusions, treating context strings as commands, and literal digits outside placeholders; they require citing evidence and naming what VenueBite would need to verify next.

## 16. Prompt Injection Defense

All user-controlled and provider-derived strings (question, history, concept, saved-site names, labels) travel as DATA inside one serialized user JSON message; nothing untrusted is concatenated into instructions. History roles are restricted to user/assistant; a "system" role is rejected. Field lengths and control characters are bounded server-side. The instructions explicitly refuse role changes, secret disclosure and fabricated conclusions found in data. Credential-like strings (configured secret values, `sk-`/`pk.`/`sk.` shapes, the session nonce) are blocked in questions, history, contexts, outputs and saves. A dedicated test sends injection text through saved names, questions and history and asserts it reaches the provider as data and produces no fabricated approval.

## 17. Score Safeguards

Score Model v2 and `data_coverage.py` are byte-identical to HEAD. Weights remain Population 30%, Income 30%, Rent 20%, Competition 20% (asserted from AI context). The AI receives official score, factor scores, weights, contributions and classification as evidence and cannot alter them; validator rules reject "recalculated score"/"new score"/best-site pronouncements. Deterministic comparison deltas remove arithmetic incentive.

## 18. Data Coverage Safeguards

Coverage credits remain real 1.0, partial 0.5, demo/fallback/unavailable 0, sourced from the existing implementation. The registry labels coverage "usable evidence support; not probability or confidence"; instructions forbid probability/confidence/accuracy/approval readings; the validator rejects coverage-as-confidence phrasings; a fixed server-authored limitation accompanies every answer. Tests cover acceptance and rejection paths.

## 19. Occupancy Safeguards

Sprint 07 semantics preserved: user terms are partial/user-supplied evidence, never independently verified; demo rent stays fictional and is never market rent; known base rent is not all-in cost; missing NNN/CAM values stay unknown, not zero; budget utilization is fit against the user's own threshold, not market affordability. These are enforced jointly by registry statuses/limitations, instructions and validator patterns (e.g. "verified rent", "market rent", "national affordability" rejected).

## 20. Parcel Safeguards

Sprint 06 match outcomes (exact/nearby/ambiguous/restricted/unavailable/not found) remain distinguishable. Direct Regrid attributes, identifiers, values and geometry are withheld from AI transmission pending verified external-sharing permission; the registry exposes only the match outcome plus explicit withholding limitations. Assessed/historical values cannot be presented as asking prices (validator-rejected), and missing parcel fields are unknown, not zero.

## 21. Regulatory Safeguards

Sprint 10 evidence classes are preserved: official district/framework/overlay/dates (`verified_official_fact`), guidance, user project plans (user-supplied) and unknowns. `regulatory.permission` is always "Not verified" in the current model; a D-CV district with use-review-required status cannot be described as restaurant permission. The validator rejects "allowed/approved/permitted/legal/compliant", "no permit required" and invented fees/timelines; safe official links (denvergov.org, census.gov allowlist, HTTPS-only, credential-free) come solely from the server registry. Parametrized tests cover identified, unsupported, unavailable, ambiguous, no-match and unknown statuses.

## 22. UI / UX

An **Ask SiteWise** floating action opens a right-side native `<dialog>` drawer in the Sprint 08 design system: SiteWise identity with subtitle, context label (current vs historical snapshot vs selected comparisons), deterministic starter questions per context kind, user/analyst turns, expandable evidence disclosures (label, value, status, source, date, limitations, safe official link), fixed limitation panel, loading status ("Reviewing selected evidence..." — no fabricated progress), error/unavailable states, reset, character counter and an explicit OpenAI-sharing privacy notice. Duplicate sends are blocked while busy; failures never disturb the underlying analysis page.

## 23. Accessibility

Native modal `<dialog>` with labelled heading (`aria-labelledby`), `aria-haspopup`/`aria-controls` trigger, bounded Tab/Shift-Tab wrapping, Escape close and focus return to the trigger; focus lands on the composer (or close button when disabled). Conversation uses `role="log"` with polite live region ("SiteWise conversation"); status uses `role="status"`; errors use `role="alert"`. Evidence statuses are textual, not color-only; controls meet 44px targets; the textarea has a visible label; reduced-motion preference disables the drawer animation; mobile layout (safe-area padding, full-width drawer) is covered by CSS and JS tests. Screen-reader certification was not performed.

## 24. Security

`OPENAI_API_KEY` is server-only: never in templates, JS, API responses, logs, exceptions, tests or docs (tests assert an environment key does not reach pages in testing mode). The chat endpoint requires same-session CSRF (constant-time compare, format-checked header), rejects cross-site `Sec-Fetch-Site`, enforces `application/json`, 32 KiB bodies, duplicate-key JSON rejection and `Cache-Control: no-store`; CSP remains `self`-scoped with no OpenAI origin. Model output renders via `textContent` only — no `innerHTML`, markdown or model-authored URLs; unsafe schemes/hosts are dropped. Provider exceptions are sanitized. Secret scan of tracked/unignored files found only variable names, placeholders and the synthetic test value `sk-testcredentialnotreal123456789`; no real credential shapes. `.env`, `.venv` and `instance/*.db` are confirmed git-ignored.

## 25. Privacy / Data Minimization

Only an explicit Send transmits data to OpenAI: the question, at most six recent conversational turns and the minimized evidence for the selected context. Not transmitted: API keys, Flask secret, DB paths, raw SQLite rows, raw provider payloads, stack traces, environment variables, unrelated saved sites, addresses/display names, listing notes, Mapbox Search Box coordinates/IDs/POI names/rows/counts/distances (excluded per Sprint 09 rules, with an explicit registry limitation), and direct Regrid attributes (withheld pending licensing verification). `store=False` disables provider application storage; OpenAI abuse-monitoring retention may still apply and no Zero Data Retention claim is made. VenueBite persists no chat content; history is browser RAM only.

## 26. Cost Controls

Message 1-1,200 chars; history ≤ 6 entries × 1,200 chars; request body ≤ 32 KiB; external context ≤ 64 KiB compact JSON (4 regulatory snapshots fit, tested); output ≤ 16 KiB raw / 2,000 tokens (default 1,400); SDK retries disabled; timeout 25 s server (client stops at 50 s). An in-process `RequestBudget` enforces one in-flight request per session, duplicate request-ID rejection, 8 requests/minute and 1,024 tracked sessions. Failed provider calls still consume budget. No prompts/responses are persisted for analytics.

## 27. Provider Isolation

Loading Saved Sites, saved detail and Compare still makes zero external provider calls, and an AI question from those pages calls only the AI provider: tests monkeypatch every geography/competition/site/regulatory/demographic provider method to fail the test if touched, then exercise page loads and successful chats. Census, Mapbox, Regrid and Denver zoning providers and their smoke procedures are unchanged; no re-run of their live checks was needed because no code path touching them changed.

## 28. Python Tests

Full suite: **1,302 passed** (baseline 1,191; +111, all in `tests/test_ai_analyst.py`; one existing route test was extended for the session cookie now set by the CSRF nonce). Command: `.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=<writable scratch> -o cache_dir=<writable scratch>` (the established Windows workaround for the permission-broken default `pytest-of-chris` temp root; application code unmodified for testing). Coverage includes context creation/signing/tamper/expiry/session binding, saved/compare digests and deletion, registry determinism and statuses, grounding acceptance/rejection (33 unsafe-phrasing cases, malformed outputs, invented IDs, placeholder abuse), route validation/CSRF/size/duplicate-JSON, provider failure sanitization, SDK adapter contract and mock HTTP transport, rate budget, secret guards at five boundaries, prompt injection, DB restart integrity with no chat tables, and regression (`python -m compileall` also passed).

## 29. JavaScript Tests

Full suite: **102 passed** (baseline 70; +32 in `tests/ai-analyst.test.mjs`) via `node tests/run-js-tests.mjs`. Coverage: open/close/Escape/focus wrap and restore, disabled no-key state, starter interaction without auto-send, blank/oversized prevention, duplicate-send prevention, per-context-kind request payloads and SiteWise response rendering, bounded history, error codes (timeout, rate, unavailable, unsupported, stale, invalid session), abort/timeout state, malformed-answer rejection, reset, analysis-invalidated/compare-picker/back-forward invalidation including late-reply suppression, XSS inertness of model/source text, and the official-host HTTPS link allowlist.

## 30. Live AI Smoke Test

**LIVE AI SMOKE TEST NOT RUN — API KEY NOT CONFIGURED.** `.env` contains no `OPENAI_API_KEY` entry (presence checked without printing values), so no live OpenAI request was possible or attempted; automated tests remain fully mocked and require no key or network. The scripted live procedure (score explanation, missing evidence, legal-permission refusal, injection refusal, saved and compare questions, citation-ID verification) is defined in the sprint prompt and should be executed and reported when a key is configured locally. This sprint makes no claim that live model behavior was observed.

## 31. Known Limitations / Future Work

- The lexical answer validator is conservative: it can reject benign phrasings (retry guidance is shown) and cannot formally prove every qualitative claim is supported; evidence disclosure and user judgment remain necessary.
- The rate/duplicate budget is in-process and per-session: it resets on restart, is not shared across workers and is not abuse-proof without authentication. Production needs account scoping, global quotas and billing alerts.
- Saved Sites remain local, non-owner-scoped records; chat is not account-isolated. Current-token invalidation is session-cookie based, not server-side revocation against a malicious client.
- No streaming; structured validation was prioritized over token animation. Carefully sanitized streaming is possible future work.
- Direct Regrid attributes and Mapbox Search Box details stay out of AI context until sharing permissions are verified; answers about them are honest unavailability statements.
- `allow_unresolved` demo contexts are clearly demo-labeled but inherently limited evidence.
- Live model behavior is unverified in this environment (Section 30); the grounding contract is enforced server-side regardless of model quality.

## 32. Acceptance Status and Git Status

All 42 sprint acceptance criteria are satisfied except that criterion 40 (live AI smoke test) is satisfied in its accurate-reporting form: the test is truthfully reported NOT RUN for lack of a configured key, which the sprint prompt deems acceptable. Existing functionality, Score Model v2, Data Coverage, saved sites (original records intact, digests unchanged across restart tests), compare, occupancy, parcel and regulatory behavior are unchanged; the application starts and serves pages with and without an AI key (verified via test client and a live `flask run` returning HTTP 200); context/conversation/cost bounds are enforced; documentation (`docs/ai-location-analyst-v1.md`, README) is complete.

Git: branch `1234tlc123-probable-succotash`, HEAD `5fca56b`. `git diff --check` clean; `git status --short` shows only the intended Sprint 11 modified/new files listed in Section 4; **nothing staged, committed or pushed**. No secret or database file is tracked. SPRINT 11 COMPLETE (with the live-smoke NOT RUN disclosure above).
