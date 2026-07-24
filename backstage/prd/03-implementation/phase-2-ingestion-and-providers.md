# Phase 2 — Ingestion and Providers

## Objective

Turn retained files into normalized typed invoices through safe format loaders
and replaceable model adapters. Implement bounded extraction assessment/repair
behavior without yet approving, reviewing, or paying invoices.

## Dependencies

- Phase 1 contracts, repositories, staging, and run transitions.

## Task Plan

| Status | Goal | User Stories | Validation | PRD Docs |
| --- | --- | --- | --- | --- |
| ☐ | **[feature] Implement bounded structured loaders** — Add JSON, both CSV shapes, and hardened XML loaders with deterministic mapping, size/depth/entity defenses, and typed malformed-document errors. | US-06, US-07 | Supplied JSON/CSV/XML load into common candidate shape → malformed/ambiguous CSV and JSON fail safely → XML DTD/entity input is rejected → raw content never reaches logs → focused loader tests pass. | `agentic-framework.md`, `integration-specification.md`, `security-and-observability.md` |
| ☐ | **[feature] Implement TXT and PDF loaders** — Add bounded UTF-8 text loading and PyMuPDF text extraction with encryption, page-count, image-only, empty-text, and content checks. | US-06, US-07 | Supplied TXT/PDF text is extracted → over-page/encrypted/image-only/empty PDFs return `UNSUPPORTED_PDF` → oversized/NUL text rejects → loader result is transient and no graph/public object contains full text. | `integration-specification.md`, `security-and-observability.md` |
| ☐ | **[feature] Define provider-neutral structured model boundary** — Replace the free-text LLM protocol with extraction, repair, approval proposal, and critique methods plus neutral timeout/refusal/schema/auth exceptions and a deterministic fake. | US-06, US-07, US-10, US-15 | Fake implements every typed method → invalid outputs cannot construct domain models → exception mapping is provider-neutral → tests use no key/network → factory rejects unknown/unconfigured providers. | `agentic-framework.md`, `integration-specification.md` |
| ☐ | **[feature] Implement Grok and OpenAI adapters** — Use the OpenAI SDK Responses API, strict Pydantic schemas, `store=False`, explicit model/timeout, and at most two transient retries; Grok uses the xAI base URL. | US-06, US-10, US-15 | Mocked SDK verifies base URL/key/model/schema/`store=False` → timeout/429/5xx retries are bounded → refusal/schema/auth failures map safely → Grok/OpenAI selection follows server settings → no raw response is logged. | `integration-specification.md`, `security-and-observability.md` |
| ☐ | **[feature] Implement extraction and assessment services** — Map deterministic candidates or provider output to canonical invoice/items, exact money, nullable missing fields, confidence, normalization findings, and repair feedback. | US-06, US-07 | Every supported fixture produces canonical types or explicit failure → missing values remain null with codes → arithmetic/date assessment detects defects → alias/OCR evidence produces warnings → no unsupported correction is silent. | `data-model.md`, `agentic-framework.md` |
| ☐ | **[feature] Implement extraction graph slice** — Replace the placeholder with ingest, extract, assess, repair, and fail/stop nodes using runtime context and a maximum of two repairs; persist invoice/findings/events idempotently. | US-06, US-07, US-14 | Graph reaches extraction-complete state for clean input → repair route executes at most twice → exhausted/unrecoverable input fails safely → replay does not duplicate rows/events → topology/loop tests pass. | `agentic-framework.md`, `data-model.md`, `security-and-observability.md` |

## Definition of Done

- [ ] All Phase 2 tasks are `☑` or deviations explicitly re-scope them.
- [ ] All five formats have positive and negative loader coverage.
- [ ] Provider adapters are replaceable and tests remain key/network-free.
- [ ] Extraction state is typed and contains no raw document/model payload.
- [ ] Repair behavior terminates after two attempts.
- [ ] No validation, approval, review, or payment behavior is introduced early.
- [ ] Relevant backend tests and lint pass.
- [ ] `make verify` passes.

