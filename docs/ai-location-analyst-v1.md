# AI Location Analyst v1

Sprint 11 adds **SiteWise** to completed analyses, saved-site detail, and comparisons of 2-4 selected snapshots. It explains existing evidence, model outputs, uncertainty and verification steps. It is not a scoring engine, legal adviser, market-data provider, autonomous agent or success predictor.

The user-facing brand is **SiteWise**, subtitled "VenueBite's AI location intelligence analyst", with **Ask SiteWise** as the primary call to action. Branding is presentation only: internal technical names (`AIAnalystService`, `OpenAIProvider`, `AIContextBuilder`, `EvidenceRegistry`), the `venuebite-ai-analyst-v1` instruction version, module paths, evidence IDs, grounding rules and the security model are unchanged by the brand.

## Architecture

- `venuebite/ai.py`: provider protocol, errors, bounds, structured schema, evidence labels and versioned instructions.
- `providers/openai_provider.py`: official SDK Responses adapter; SDK objects and exceptions stay here.
- `services/ai_context.py`: signed temporary current contexts, signed saved references, server reconstruction and provenance compression.
- `services/ai_evidence.py`: deterministic normalized evidence registry and stored-value comparison deltas.
- `services/ai_response_validator.py`: fail-closed structural, citation, numeric and domain checks.
- `services/ai_analyst_service.py`: request validation, ephemeral history, provider orchestration and local request budget.
- `ai_routes.py`: CSRF-protected JSON transport, without SQL or scoring formulas.
- `_ai_analyst.html`, `ai-analyst.js`, `ai-analyst.css`: native modal drawer, plain-text answers and progressive evidence disclosures.

The existing provider and repository boundaries remain intact. No chat table, migration, authentication, alternate database, AI tools, web search or frontend framework was added.

## Verified OpenAI Integration

Official documentation and the installed SDK interface were checked October 11, 2026, before integration. The official Python SDK is pinned to `openai==3.29.0`. Requests use `client.responses.create`, `text.format` with a strict JSON schema, `store=False`, `stream=False`, an empty tool list and `tool_choice="none"`. No Assistants, Conversations, previous-response IDs, background mode or remote prompt storage are used.

The SDK client is initialized only when an enabled provider is explicitly asked a question. The base URL is fixed to `https://api.openai.com/v1`; redirects and ambient proxy configuration are disabled. Automatic SDK retries are disabled to avoid multiplying cost. Timeout, authentication, rate-limit, incomplete/refusal and malformed-output paths return fixed sanitized messages. Questions, requests, answers, SDK exception text and response IDs are not logged or persisted by VenueBite.

Configuration is server-side only:

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TIMEOUT_SECONDS=25
OPENAI_MAX_OUTPUT_TOKENS=1400
```

Leave the key blank for normal non-AI operation. Add a key privately to the server environment or ignored `.env`, never to chat, source, HTML or JavaScript. Restart Flask after environment changes. The default is a low-latency, non-reasoning model with structured-output support; model selection is configurable but must preserve Responses/strict-schema compatibility. Invalid model-name syntax falls back to the centralized default. The server timeout clamps to 1-45 seconds; output clamps to 256-2000 tokens. The timeout is the SDK's per-network-operation timeout, not a claim of a globally enforced wall-clock deadline. The client also stops waiting after 50 seconds.

Without a key, the drawer remains available to explain the unavailable state, but sending is disabled. Direct API requests receive `503 / not_configured`. Ordinary analysis, maps, persistence, deletion and comparison still work. Tests never inherit a real environment AI key unless explicitly configured by a test, and all AI tests use fakes or an SDK mock HTTP transport.

Verified references:

- [Responses Python API](https://developers.openai.com/api/reference/python/resources/responses/methods/create).
- [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
- [Responses migration guide](https://developers.openai.com/api/docs/guides/migrate-to-responses).
- [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini).
- [OpenAI API data controls](https://developers.openai.com/api/docs/guides/your-data).

## Trusted Context

Current context is built from the completed server report through the existing normalized snapshot builder. A narrowly scoped `allow_unresolved=True` option permits discussion of an honestly labeled demo analysis; the default resolved-location requirement for saving is unchanged. Geography, Search Box labels/IDs/coordinates and raw provider payloads never enter the AI whitelist.

Current tokens carry only minimized normalized evidence, not a full provider response. They use a separate `venuebite-ai-context-v1` signing salt, context version 1, a hash of the CSRF session nonce and a 30-minute expiry. Tokens are capped at 20,000 characters. A new completed analysis records the token hash in the signed Flask session and rejects the previous current token through the API. This is separate from snapshot persistence and is not an authorization model.

Saved tokens contain the context kind, requested site IDs and strict snapshot digests, not copied browser facts. Sending a question reloads the selected records through `SavedSiteService`. Deleted, corrupt, changed, invalid, expired or differently session-bound contexts fail closed with a stale-context response. Compare reloads exactly 2-4 unique selected records through the unchanged `ComparisonService`; unselected records never enter the AI request. Saved evidence remains historical, with original model versions and evidence/analysis dates. Reading or chatting does not update a snapshot or refresh an external data provider.

The client clears the token, history and pending response on location, concept, radius, occupancy or regulatory edits by listening to the existing analysis-invalidated event. Compare picker edits invalidate the old selection. Back-forward restoration invalidates a current context and resets saved/compare conversations. Generation guards discard late responses after reset/invalidation. A signed current token establishes the original report, not that the current browser form is still untouched: normal UI edits disable chat immediately. This local, cookie-based design is not server-side revocation against a malicious client replaying an older valid session cookie.

## Evidence Registry

Stable IDs are namespaced by selection order, such as `s1.score`, `s1.population.contribution`, `s1.occupancy.monthly_known_total`, `s1.regulatory.permission`, and `compare.s1_s2.score`. IDs are deterministic for the same supplied snapshots/order. Each canonical entry includes label, exact normalized value, readable display, units, evidence status, source, date, reviewed source URL where appropriate, and limitations.

Statuses remain distinct: model, real, partial, demo, fallback, unavailable, unsupported, user-supplied plans, official fact, government guidance, official confirmation required and unknown. Missing values remain `null`/unknown, not zero. Current timestamps describe analysis time; Census vintage and regulatory retrieval/effective-date fields retain their separate meanings.

The OpenAI request deduplicates origin/date and limitation metadata into reference lists and omits URLs entirely. The external evidence context is capped at 64 KiB of compact UTF-8 JSON; the richer internal citation context is capped at 192 KiB. Four regulatory snapshots fit this budget in regression tests. IDs refer to server-rendered evidence, so the model cannot author a source link. Canonical numbers are formatted for readability without changing their exact stored values.

Comparison score/coverage deltas are computed with `Decimal` from stored outputs. The existing neutral highlights and compatibility warnings are provided with registry IDs. Different concepts, radii, models, factor evidence, lease structures or space sizes retain their warnings; deltas do not establish a best-site recommendation.

## Response Contract And Grounding

The model returns only:

```json
{
  "answer_blocks": [
    {
      "text": "The stored score is {{s1.score}}; this is not a success prediction.",
      "evidence_ids": ["s1.score"]
    }
  ],
  "limitations": ["Confirm missing evidence before making a lease decision."]
}
```

Every block must cite 1-6 unique existing IDs. The server allows 1-5 blocks, at most 1,000 characters of model prose per block, and at most three extra 300-character limitations. Unsupported keys, missing/unknown IDs, malformed placeholders, uncited placeholders, duplicate JSON keys, non-finite JSON values, refusal/incomplete output or oversized output are rejected. Raw response text is capped at 16 KiB.

All quantities, dates, versions and district codes use `{{evidence_id}}` placeholders. Literal digits, HTML and model-authored links are prohibited in model prose. The server substitutes exact canonical values, units and readable evidence labels. Unknown-value citations require explicit missing/unavailable/unknown language. Domain guards reject approval, success guarantees, fabricated market rent, invented traffic/revenue/demand, replacement scores and confidence/probability reinterpretations. Every response includes fixed server-authored score, coverage, occupancy and permission limitations; suggested questions are server-authored too.

These are layered controls, not a formal proof that unrestricted natural-language interpretation is correct. Rule-based semantic guards are intentionally conservative and can reject a benign answer. A plausible unsupported qualitative statement can still evade lexical checks. Evidence disclosures and user review remain necessary; future work should strengthen domain-specific claim typing and adversarial evaluation rather than claiming infallible grounding. Rejected responses show a safe error, never a silent unsupported answer.

## Prompt Injection And Rendering

The versioned instructions are `venuebite-ai-analyst-v1`, checked into source. Questions, recent history, concepts, user labels, provider strings and comparison text are serialized inside a single user JSON data message, never concatenated into privileged instructions. History roles are restricted to user/assistant and remain data, not model system messages. Freeform listing notes, source labels/URLs and property addresses are omitted from the external context. Known configured credentials and credential-like tokens are blocked in questions, history, context, output and saving; the active CSRF nonce is blocked in conversational input.

No tool definitions, function execution, URL fetching or autonomous actions are available to the model. There is no browser OpenAI connection and no OpenAI addition to the CSP. The browser uses `textContent`, never model `innerHTML` or Markdown. Citations are rebuilt from trusted registry entries. Links require reviewed server URLs, HTTPS, no embedded credentials and official hosts on the client. Questions are untrusted content too.

## Domain Safeguards

**Scoring:** Score Model v2, classification, weights and contributions are read verbatim. Population/income/rent/competition remain 30/30/20/20. The AI cannot update official model outputs, parameters, records or Data Coverage. Parcel/regulatory facts stay outside the score and coverage.

**Coverage:** Existing credits stay real 1, partial 0.5, demo/fallback/unavailable 0. Coverage is weighted usable model evidence, not probability, confidence, statistical accuracy, permission or freshness. Partial evidence does not halve the factor score.

**Occupancy:** User rates, bases, lease structure, space size, known base/additional/total costs, budget and utilization are included as partial evidence. Missing inputs/costs remain unknown. A known base cost is not an all-in total. Budget fit is relative to the supplied threshold, not national affordability, market rent or profitability. Demo rent factor outputs stay demo. Notes, listing URLs and addresses are not transmitted.

**Parcel:** Only VenueBite's match outcome and withholding limitations are shared. Exact/nearby/ambiguous/restricted/not-found/unavailable outcomes remain distinguishable; they do not establish ownership, lease availability, suitability or asking value. Direct Regrid attributes, identifiers, values and geometry are deliberately withheld until external-sharing permission is verified. Missing premium attributes are not negative facts. The existing Site Intelligence UI and saved facts remain unchanged.

**Regulatory:** Normalized official Denver district/framework/overlay/version/date facts, reviewed checklist status and user project plans retain their different evidence classes. All checklist items remain available. Restaurant-use permission is always not verified in the current model. Guidance is not site-specific approval, code-family flags are not amendment/effective dates, and unsupported jurisdictions/unknown legal requirements stay unsupported/unknown. No invented fees, timelines, exemptions or approval probability are supplied.

## Privacy And Third-Party Transmission

Only explicit Send transmits the question, a maximum of six recent messages and the selected minimized evidence to OpenAI. Opening a drawer, starter selection, reset, page loads and compare selection do not call AI. No system path, environment/config, secret, SQL/raw row, raw provider payload, unrelated saved record, geometry or unnecessary user note is transmitted. Exact addresses and provider-derived location names are omitted; current contexts say Current analysis. Saved names are explicit user-owned labels, treated as untrusted data.

Transmission decisions are conservative:

- VenueBite-owned scores, coverage, model contributions, match outcomes and deterministic comparisons: shared.
- Public normalized Census estimates, MOEs, GEOID and vintage: shared with their tract/survey limitations.
- Explicit user occupancy/project values: shared only upon Send, as partial/user evidence; users should avoid entering personal or confidential material into chat.
- Normalized Denver official facts/guidance: shared with source/agency attribution and historical dates; not permission conclusions.
- Mapbox Search Box coordinates, IDs, result labels, POI names/details, raw rows/counts/distances, response payloads and directories: not shared with OpenAI or placed in AI tokens/persistence. Existing VenueBite competition factor outputs remain available. This sprint grants no new storage or redistribution permission.
- Regrid direct parcel data: withheld because the available plan documentation does not establish permission for this external AI-sharing use. No guess about account licensing is made.

See [Search Box restrictions](https://docs.mapbox.com/api/search/search-box/) and [Regrid plan documentation](https://support.regrid.com/reference/plan-options). The Regrid documentation could not be retrieved during the final research attempt; no external-sharing permission is inferred from that failure. The conservative withholding policy is implemented rather than depending on guessed terms.

VenueBite has **no permanent chat storage**. Browser history is RAM-only; reset/navigation discards it. Signed current evidence tokens expire and are never written to SQLite. Request-budget memory retains only session nonces, request IDs, counters and timestamps, not messages. Operational access logs may show the `/api/ai/chat` path/status, not message bodies. `store=False` disables OpenAI response application-state storage; it is **not** a guarantee of zero retention. OpenAI's normal abuse-monitoring policy may retain API content for up to 30 days unless an eligible account has appropriate approved data controls. Review account policies before sending confidential information; no Zero Data Retention claim is made.

## Cost And Failure Controls

Question length is 1-1,200 characters. History is at most six user/assistant entries, each at most 1,200 characters. The JSON endpoint accepts at most 32 KiB; existing form body limits remain 16 KiB. Context, response size, output tokens and network waits are bounded as above. Only one request can be in flight per local session; duplicate request IDs and more than eight attempts per minute are rejected. The in-process budget stores at most 1,024 session entries and expires idle entries after a minute. Failed provider requests still count, preventing rapid retry amplification.

This is a development safeguard, not a distributed quota, global spend limit, authentication or robust abuse prevention. It resets on process restart, is not shared across workers, and a client can obtain new sessions. Production needs authentication/ownership controls, global quotas, account billing alerts/limits and distributed throttling. No such systems were added in this sprint.

The API uses sanitized JSON errors: 400 validation, 403 session/CSRF, 409 stale/duplicate, 413 oversized request, 429 local/provider limit, 502 unsupported/malformed/incomplete answer, 503 unavailable/configuration and 504 provider timeout. Errors do not replace the dashboard or alter saved evidence. A failed answer is not appended to the bounded successful-turn history.

## UI And Accessibility

The Sprint 08 palette/type/icons are retained in a right-side native `<dialog>`. It displays the context kind and historical status, suggested starters, user/analyst turns, progressive evidence disclosures, loading/error/unavailable states, reset and close. Sending requires an explicit action after a disclosure of OpenAI sharing. No fabricated progress meter, permanent-memory promise or dark-pattern auto-send is used.

Native modality plus bounded Tab/Shift-Tab wrapping keeps focus in the drawer; Escape and close restore trigger focus. Controls have accessible names and 44px targets; textarea has a label and character limit. Conversation/log, loading/status and error/alert semantics are explicit. Evidence has textual statuses, not only colors. The message area scrolls independently while the composer remains visible. CSS disables animation for reduced motion. Desktop, tablet, 390px phone and 320px narrow-phone layouts were reviewed. Screen-reader certification and an OS-level reduced-motion preference change were not performed.

## Local Use And Future Work

Install `requirements.txt`, configure the optional private AI key, and restart Flask. Run `python -m pytest` and `node tests/run-js-tests.mjs`. Automated tests use temporary databases and mocked AI, never paid APIs or live Regrid.

Current Saved Sites are shared local records without account ownership; chat is not account-isolated. Production deployment must add authentication and authorize every context/reference. Future work may add authenticated budgets, stronger typed claim validation, redaction/consent policies for user labels, approved provider-sharing licenses and carefully sanitized streaming. These are not current Sprint 11 features.

See [Sprint 11 engineering report](sprint11-engineering-report.md) for actual test counts, manual observations, storage/provider audits and the accurately labeled live AI result.
