# Phase 3 — Validation and LangGraph Workflow

## Objective

Complete deterministic validation, bounded approval/critique, policy routing,
durable human review, rejection, and idempotent mock payment inside LangGraph.
This phase proves the business workflow in-process before exposing new API/CLI
contracts.

## Dependencies

- Phase 1 persistence and idempotency primitives.
- Phase 2 loaders, provider boundary, canonical invoices, and extraction graph.

## Task Plan

| Status | Goal | User Stories | Validation | PRD Docs |
| --- | --- | --- | --- | --- |
| ☐ | **[feature] Implement inventory validation tool and rules** — Normalize only explicit aliases, aggregate repeated items, perform read-only inventory lookup, and emit ordered blocking findings for unknown, zero, or excessive stock. | US-08 | `Widget A`/`Gadget X` normalize explicitly → repeated lines aggregate → unknown/zero/excess stock map to stable codes with expected/actual values → inventory rows never change → fixture-focused tests pass. | `data-model.md`, `agentic-framework.md` |
| ☐ | **[feature] Implement integrity and risk validation** — Enforce required fields, integral positive quantities, positive money, absolute/date ordering, one-cent arithmetic reconciliation, and bounded suspicious-payment-language detection. | US-07, US-09 | Missing/negative/relative-date/total-mismatch cases emit documented blockers → current system date alone does not reject fixtures → suspicious urgency creates safe code without storing source text → deterministic results are provider-independent. | `agentic-framework.md`, `security-and-observability.md` |
| ☐ | **[feature] Add validation graph node and persistence** — Advance status/events, combine extraction and business findings deterministically, persist one ordered set, and make node replay idempotent. | US-08, US-09, US-14 | Extraction-complete graph reaches deciding with findings → blocking/warning counts match persisted rows → node replay replaces rather than duplicates findings → safe event/status transaction is observable. | `agentic-framework.md`, `data-model.md` |
| ☐ | **[feature] Implement approval proposal and critique loop** — Add typed provider calls, proposal/critique schemas, decision versions, maximum two revisions, and recursion protection without persisting raw reasoning. | US-10, US-14, US-15 | Accepted proposal proceeds once → critique-requested revisions stop after two → invalid/unsupported claims are surfaced → decisions record safe summary/codes/count → provider failures terminate safely → no raw reasoning stored. | `agentic-framework.md`, `integration-specification.md` |
| ☐ | **[feature] Implement deterministic decision gate** — Compute blocker/review/automatic routes from persisted invoice/findings and override noncompliant model recommendations with an auditable policy decision. | US-10, US-11, US-13 | Any blocker always rejects → warning/non-USD/`> $10K` always reviews → clean USD `<= $10K` approves → exact threshold boundary tests pass → model disagreement records `POLICY_OVERRIDE`. | `agentic-framework.md`, `security-and-observability.md` |
| ☐ | **[feature] Add SQLite checkpointing and human-review interrupt** — Compile the worker graph with synchronous SQLite saver, use `thread_id=run_id`, interrupt with safe review data, and resume from persisted first-wins human decision. | US-11, US-14 | Review route persists `review_required` and interrupt → restart/recompile can inspect/resume thread → approve resumes to payment route → reject resumes to rejection → duplicate/out-of-state decision is rejected → pre-interrupt side effects are idempotent. | `agentic-framework.md`, `data-model.md`, `api-specification.md` |
| ☐ | **[feature] Implement guarded idempotent mock payment** — Add payment tool/adapter and node that verifies persisted approval, positive original-currency money, paying status, and unique idempotency key before recording a simulated result. | US-04, US-11, US-12 | Clean approved run pays once → graph/task replay returns same payment → unapproved/rejected/blocking run cannot call adapter → non-USD reviewed approval retains currency → scripted failure persists retry-safe failed attempt/run. | `integration-specification.md`, `data-model.md`, `security-and-observability.md` |
| ☐ | **[feature] Implement rejection, finalize, and failure nodes** — Persist safe terminal outcomes/events, distinguish policy/human rejection, clean up eligible sources, and retain failed sources for retry. | US-05, US-12–US-14 | Blocking/human rejection never creates payment → completed records payment and cleanup → failed records safe code/retryability and retained source → terminal replay does not duplicate events/cleanup → full graph route tests pass. | `agentic-framework.md`, `data-model.md`, `security-and-observability.md` |
| ☐ | **[eval] Automate workflow acceptance matrix** — Drive supplied and synthetic invoices through the graph with a deterministic fake provider and assert expected automatic/review/rejection outcomes. | US-06–US-13 | Supplied fixture matrix matches `prd/README.md` → clean `$10K` auto-pays → `$10,000.01` reviews → both review outcomes pass → duplicate payment/replay tests pass → no fixture is modified. | `prd/README.md`, `agentic-framework.md` |

## Definition of Done

- [ ] All Phase 3 tasks are `☑` or deviations explicitly re-scope them.
- [ ] Every graph route and both bounded loops are tested.
- [ ] Deterministic policy wins over model recommendations.
- [ ] Durable review resumes after graph recreation.
- [ ] Payment is guarded and idempotent under replay/redelivery.
- [ ] Supplied fixture outcomes match the PRD matrix.
- [ ] No API run routes, CLI wait behavior, or frontend implementation is introduced early.
- [ ] Relevant backend tests and lint pass.
- [ ] `make verify` passes.

