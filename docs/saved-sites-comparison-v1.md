# Saved Sites and Comparison v1

## Scope

Local, single-instance Flask/Jinja persistence, not accounts or cloud sharing. Sprint 01-08 providers, scoring, occupancy semantics and visual system remain unchanged. SQLite uses the Python standard library; no dependencies, provider switches, charts framework or frontend framework were added.

## Architecture

`db.py` owns connection lifecycle, transactions, idempotent initialization and the small versioned schema migration. `SavedSiteRepository` owns parameterized SQL and validated JSON reconstruction. `SavedSiteService` owns completed-analysis validation, input fingerprinting, naming, explicit user location metadata and saving. `ComparisonService` reads stored snapshots, formats missing-aware metrics and generates deterministic gated highlights. `saved_routes.py` owns HTTP validation, scoped CSRF, feedback and rendering. Analysis services have no database dependency.

SQLite defaults to `instance/venuebite.db`; `VENUEBITE_DATABASE_PATH` may override it. Database and journal/WAL/SHM sidecars under `instance/` are ignored, not all instance source/config files. Custom paths need explicit protection. `flask --app app init-db` initializes safely; otherwise the first saved operation initializes lazily. Ordinary live analysis does not create database records.

## Schema and Initialization

Schema version 3, `PRAGMA user_version`, one `saved_sites` table:

- `id`: stable integer primary key.
- `analysis_id`: unique completed-analysis identifier, not a provider ID.
- `display_name`, `location_label`: bounded user metadata.
- `restaurant_concept`, `search_radius_miles` (1/3/5).
- `opportunity_score`, `opportunity_classification`, `score_model_version`.
- `data_coverage`, `coverage_label`.
- `analysis_timestamp`, `created_at`: separate timezone-aware UTC times.
- `snapshot_version`, `snapshot_json`: explicit normalized format.

There are deliberately **no coordinate columns**. An index orders newest save timestamp/id first. Score/coverage/radius/name constraints supplement service validation. Initialization never empties saved analyses. Unsupported future schemas fail safely. Prototype version 1 migrates transactionally: old geography columns and JSON fields are removed, provider-derived location labels become `Saved candidate`, auto-filled property addresses matching those labels are cleared, and model outputs/IDs/timestamps/user names remain unchanged. Version 2 metadata migrates to an application-owned source note instead of retaining Search Box response attribution text. Secure deletion plus VACUUM removes old free-page copies. Invalid legacy JSON aborts and rolls back; repair is explicit, never an automatic database reset. Back up permitted data before future migrations; do not retain unauthorized geography in backups.

## Snapshot Format 2

Explicit whitelists permit identity/analysis context, stored score and raw weighted sum, four factors (scores/weights/contributions/status/provenance/version), Data Coverage/credits, normalized Census facts/MOEs/GEOID/vintage, aggregate VenueBite competition outputs, normalized permitted parcel summary, occupancy inputs/results/Decimal strings and deterministic explanations. Census vintage and county refresh dates remain separate from analysis/save timestamps.

JSON is UTF-8, finite-number-only, size/depth/list/string bounded, duplicate-key rejecting and version checked. Scalar fields, exact section keys, evidence statuses, IDs/timestamps and safe source URLs are validated on write and read. Duplicated scalar columns must agree with JSON. No pickle, arbitrary object reconstruction, debug dumps or raw provider payloads. Corrupt current-format records are omitted from browsing with an explicit unreadable count, not deleted. Detail returns a sanitized unreadable state. Stored scores are never recalculated with current scoring code.

## Search Box Retention Boundary

Search Box is temporary-use data for the live analysis session. SQLite never receives Search Box coordinates, Mapbox IDs, provider result labels/place types, POI names/addresses/categories/business details, raw Search Box/POI payloads, polygons or business directories. There is no retention override flag or automatic API switch. Future saved maps require a reviewed permanent-storage-capable source; no such source is introduced here.

Saving requires the user to type a location label. It is not prefilled from a Search Box result. The default name uses the user concept, not provider geography. Only a genuinely supplied occupancy property address is stored, never the live model's automatic Mapbox-label fallback. Census region metadata is from Census, not copied from Search Box. VenueBite-generated competition count/distance/pressure/score summaries and model explanations remain stored as historical aggregate model context, not a reconstructable business directory. They retain capped-sample/provenance limitations. Further commercial deployment still requires reviewing provider terms for the intended use; this sprint does not grant additional provider rights.

## Saved Lifecycle

After successful resolved analysis, the service prepares a two-hour signed normalized snapshot token bound to a canonical hash of every location/concept/radius/selection/occupancy input. Live geography is used only for validation and the hash; it is not persisted. Save submits the same analysis form via its explicit Save action. Changed inputs are rejected server-side even with JavaScript disabled; JS also hides stale output and invalidates the token. Unresolved/demo-only analyses do not offer saving.

Save requires a trimmed name (1-140 characters), explicit location label (1-200), no control characters or configured credentials. Unicode and normal punctuation are accepted; HTML-like strings remain escaped text, never rendered markup. Signed payloads cannot upgrade evidence or change outputs. A duplicate submission of one analysis ID returns the existing record. Fresh analyses of the same place/concept, or different assumptions, receive distinct IDs and can be compared.

Saved list/detail clearly say historical snapshot; no provider calls or map initialization occur. Analyze again prefills user label/concept/radius/occupancy only. The selection token and coordinates are empty; a fresh suggestion and explicit Analyze submission are required. Originals are not overwritten. Deletion is confirmed, CSRF-protected POST; destructive GET is unavailable. Missing/deleted IDs receive clear feedback, including comparison selection containing a deleted record.

## Comparison Rules

GET form/query carries ordered `site_id` values. Exactly 2-4 unique valid existing IDs are accepted, with server validation and client maximum selection controls. No permanent comparison session. The matrix displays score/classification/coverage/version, four factor bars/evidence/contributions, Census metrics/MOEs/geography/source, aggregate competition context, parcel fields/status, and occupancy rates/cost/budget/utilization/model. Missing values stay unavailable/not supplied/unknown total; real zero remains zero.

- Highest stored score: only equal model versions/weights, concept/radius and full factor-evidence vectors.
- Highest Data Coverage: only equal score-model versions/weights; never success probability.
- Strongest competition factor: same concept/radius and same real competition model.
- Lowest known occupancy: all partial user terms, known total, equal numeric size and lease structure. Not verified market rent.
- Mixed rent evidence: explicit partial-vs-demo/fallback warning; no rent winner based on unequally supported evidence.

Ties identify all tied names in selection order. Highlights are deterministic, not recommendations. Different context/models/evidence generate limitations. No source refetching, score recalculation, mutation, AI or automatic best-site advice.

## UX and Accessibility

Functional Analyze/Saved Sites/Compare navigation; Find an Area hidden. Sprint 08 colors, glass surfaces, restrained motion, score ring and evidence badges retained. Saved cards stack; mobile comparison scrolls within a keyboard-focusable region with sticky metric labels. Exact numbers accompany graphics. Semantic table headers/caption, named checkboxes, real labels, native details, focus states, 44px action targets, status feedback and explicit deletion confirmation. Existing reduced-motion rules apply to new elements too.

## Security and Testing

Parameterized SQL only in the repository/database boundary. New mutations require session CSRF tokens, HttpOnly/SameSite=Lax cookies and constant-time comparisons; existing analysis remains separate. Saved responses are no-store. Source URLs must be safe HTTP(S), credential-free and remain escaped with noopener links. Known server secrets/token-like values are rejected before persistence. Errors/logs never include SQL parameters, provider payloads or credentials. This is not comprehensive production security: no authentication/authorization, no encryption at rest, no per-user privacy, no encrypted backups. Keep development loopback-only and protect the local file.

All automated provider tests use fakes; test apps without explicit DATABASE allocate a temporary directory, ignoring the development database environment. Repository/service/route tests cover CRUD, reconstruction, safe migration, invalid JSON/IDs/SQL-like names, escape/CSRF, stale/tampered/expired tokens, exact occupancy/score/evidence preservation, ordered 2-4 comparisons, missing/zero/model/evidence gates and zero provider calls when browsing/mutating. JS tests cover stale save actions and 2-4 selection controls in addition to existing UI tests.

## Future Migrations

Add owner/user IDs through an explicit versioned migration and authorize every read/delete/compare; never invent ownership of pre-account records. PostgreSQL can implement the same repository contract, replacing SQLite connection/upsert/version migration mechanics. Retain normalized versioned historical snapshots and idempotency. Before public deployment add production session/CSRF policy, encryption/backups, authorization, pagination, operational logging, migrations and retention controls. A permitted permanent geocoder needs explicit source provenance and schema evolution; do not silently repurpose Search Box coordinates.
