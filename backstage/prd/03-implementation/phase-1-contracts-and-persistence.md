# Phase 1 — Contracts and Persistence

## Objective

Establish the typed domain, versioned SQLite source of truth, repositories, and
safe run lifecycle required by every later workflow slice. Do not implement file
parsing, LLM calls, graph business nodes, new run routes, or frontend behavior yet.

## Dependencies

- Existing scaffold and approved PRD documents.
- No prior implementation phase.

## Task Plan

| Status | Goal | User Stories | Validation | PRD Docs |
| --- | --- | --- | --- | --- |
| ☐ | **[feature] Define public/domain contracts** — Add Pydantic enums and models for run summaries/details, money, invoice/items, findings, decisions, payments, events, review commands, and safe errors without exposing paths or provider payloads. | US-03, US-06, US-08–US-14 | Contract tests construct every status/finding/decision → Decimal money serializes as exact strings → forbidden internal fields are absent → `uv run pytest backend/tests/schemas -v` passes. | `data-model.md`, `api-specification.md`, `agentic-framework.md` |
| ☐ | **[migration] Add versioned SQLite schema and seed** — Implement repeatable migrations, connection PRAGMAs, required tables/indexes/constraints, and exact inventory/alias seed data. | US-04, US-05, US-08, US-12, US-14 | Empty temp DB migrates to latest → second migration is a no-op → foreign keys/WAL/busy timeout are active → seed values/aliases match spec → invalid status/money/stock constraints fail → focused DB tests pass. | `data-model.md`, `security-and-observability.md` |
| ☐ | **[feature] Implement persistence repositories** — Add protocol-conforming SQLite repositories for inventory, runs, invoices/items, findings, decisions, payments, and ordered events with short parameterized transactions. | US-03–US-05, US-08, US-12–US-14 | Repository tests save/read each aggregate → repeated invoice/finding replacements are atomic → event/decision versions stay ordered → inventory remains unchanged → no persistence rows cross public boundaries. | `data-model.md`, `security-and-observability.md` |
| ☐ | **[feature] Implement source staging and run creation** — Validate safe generated staging, SHA-256 content deduplication, source metadata, origin/provider assignment, and cleanup/expiry services behind a protocol. | US-01, US-02, US-04, US-05 | New content creates queued run → same bytes/different filename returns same run with deduplicated flag → changed revision creates new run → traversal filename cannot escape staging → terminal cleanup deletes source → expired failed source becomes unavailable. | `data-model.md`, `api-specification.md`, `security-and-observability.md` |
| ☐ | **[feature] Implement run transitions and retry service** — Enforce the status transition table, append safe events, increment attempts, and make failed retry conditional on retained/hash-matching source. | US-03, US-05, US-14 | Valid transitions update status/event atomically → invalid transition raises typed conflict → failed retry returns queued with incremented attempt → non-failed/expired/tampered source rejects → previous decisions/payments remain intact. | `data-model.md`, `api-specification.md`, `security-and-observability.md` |
| ☐ | **[feature] Implement idempotent payment repository primitive** — Create-or-return a unique per-run payment attempt without adding the payment tool or graph route. | US-04, US-12 | First key creates one attempt → repeated key/run returns same attempt → conflicting key cannot create second payment → success/failure updates are transactional → no vendor/amount is logged. | `data-model.md`, `security-and-observability.md` |

## Definition of Done

- [ ] All Phase 1 tasks are `☑` or deviations explicitly re-scope them.
- [ ] Migrations are repeatable on temporary databases.
- [ ] Inventory seed and aliases match supplied fixtures.
- [ ] Run, event, retry, deduplication, retention, and payment invariants are tested.
- [ ] No parser, model provider, graph workflow, API run route, or frontend behavior is introduced early.
- [ ] Relevant backend tests and lint pass.
- [ ] `make verify` passes.

