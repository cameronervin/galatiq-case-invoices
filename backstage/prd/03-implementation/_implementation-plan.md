# Invoice Processing Phased Implementation Plan

## Purpose

This is a planning artifact for coding agents. It defines the intended product
and implementation order; the invoice workflow is not yet implemented. Agents
should work through phase tasks in order, use TDD for non-trivial behavior, update
task status, and record deviations before moving between phases.

Primary specifications:

- [Master user stories](../01-user-stories/_master-user-stories.md)
- [Data model](../02-technical-docs/data-model.md)
- [API specification](../02-technical-docs/api-specification.md)
- [Agentic framework](../02-technical-docs/agentic-framework.md)
- [Integration specification](../02-technical-docs/integration-specification.md)
- [Security and observability](../02-technical-docs/security-and-observability.md)
- [Workspace UX](../02-technical-docs/workspace-ux.md)

## Current State

- The root CLI validates supported local paths and publishes a Celery task.
- Celery and Valkey are configured with JSON serializers.
- FastAPI exposes only `GET /api/v1/health`.
- The typed LangGraph contains a single placeholder node.
- SQLite connection, repository, LLM, guardrail, and tool interfaces are scaffolded
  but have no business implementation.
- The Next.js page is a static foundation status card.
- Scaffold verification passes, but no case-study workflow behavior is covered.

## Target Architecture

```text
CLI ───────────────┐
                   ├─> run service -> repositories -> SQLite
FastAPI -> upload ─┘         │
                             └─> Celery/Valkey -> worker
                                                  │
                                                  └─> typed LangGraph
                                                       ├─ provider adapters
                                                       ├─ inventory tool
                                                       └─ mock payment tool

Next.js -> FastAPI run/status/review/retry APIs
```

The CLI and routes remain thin; services own use cases, repositories own SQLite,
the worker alone executes the graph, and public clients never choose server-owned
workflow decisions.

## Locked Decisions

| Decision | Direction |
| --- | --- |
| Framework | LangGraph with typed state, conditional edges, bounded loops, SQLite checkpoints, and interrupts |
| Approval | Blockers reject; warnings/non-USD/`> $10K` review; clean USD `<= $10K` auto-pays |
| CLI model | Grok required; default model configurable from `grok-4.5` |
| API development model | OpenAI supported; default configurable from `gpt-5.6-sol` |
| Persistence | SQLite application source of truth; Valkey queue metadata only |
| Execution | Synchronous graph within Celery; local worker concurrency one |
| Idempotency | SHA-256 deduplication and unique per-run payment key |
| Retention | Terminal success/rejection deletes source; failed retry source expires after 24 hours |
| UI | Accessible upload, progress, findings, review, retry, rejection, and completion workspace |

## Phase Overview

| Phase | Outcome | Stories | Detailed plan |
| --- | --- | --- | --- |
| 1 | Typed contracts, SQLite schema/repositories, and safe run lifecycle | US-01–US-05, US-08, US-12, US-14 | [Phase 1](phase-1-contracts-and-persistence.md) |
| 2 | Safe loaders, replaceable providers, typed extraction, and bounded repair | US-06, US-07, US-15 | [Phase 2](phase-2-ingestion-and-providers.md) |
| 3 | Deterministic validation and complete approval/review/payment LangGraph | US-08–US-13 | [Phase 3](phase-3-validation-and-workflow.md) |
| 4 | JSON-safe worker integration plus complete API and CLI contracts | US-01–US-05, US-11, US-14, US-15 | [Phase 4](phase-4-api-worker-and-cli.md) |
| 5 | Operational workspace, fixture evaluation, docs, and demo readiness | US-02, US-03, US-05, US-11–US-16 | [Phase 5](phase-5-workspace-and-readiness.md) |

## Cross-Phase Test Matrix

| Area | Required scenarios |
| --- | --- |
| Contracts | Pydantic and TypeScript enums/shapes agree; money serializes exactly |
| Persistence | Migration repeatability, constraints, deduplication, retry, ordering, source lifecycle |
| Formats | Valid/malformed PDF, TXT, JSON, CSV, XML; size/page/entity defenses |
| Providers | Grok/OpenAI configuration, strict schemas, refusal, timeout, retry, fake provider |
| Validation | Required fields, dates, totals, aliases, aggregation, unknown/zero/excess stock, suspicious text |
| Graph | Every branch, two loop bounds, recursion limit, policy override, interrupt approve/reject |
| Idempotency | Duplicate upload, duplicate Celery task, graph replay, payment redelivery |
| API/CLI | Safe errors, status codes, wait/timeout, review/retry conflicts, no local paths |
| Frontend | Accessible empty/active/review/rejected/failed/completed states and responsive layouts |
| Security/logging | No secrets, source content, vendor/amount details, prompts, provider payloads, or paths in logs |
| Fixtures | The acceptance matrix in `prd/README.md` is automated and passes |

## Phase Completion Rules

1. A phase is complete only when every task is `☑`, focused checks pass, relevant
   docs reflect actual behavior, and deviations are reconciled.
2. If a task is only partly implemented, mark `◐` and state the exact remainder
   in the Goal cell.
3. Do not mark docs as implemented before runtime behavior exists.
4. Run `make verify` at every phase boundary. Run the Valkey/worker smoke test at
   Phases 4 and 5 when Docker is available.
5. Preserve supplied fixtures and never commit secrets, generated databases,
   staged documents, caches, or build output.

## Explicit Non-Goals

- Authentication, authorization roles, multi-tenancy, or production deployment.
- Live email, bank, inventory, FX, or OCR services.
- Image-only PDF OCR.
- Client-selected provider, approval, validation, or payment state.
- Inventory mutation or procurement accounting.
- Unbounded autonomous agents or model-selected external tools.

## Definition of Product Done

- [ ] All US-01 through US-16 acceptance criteria are implemented and tested.
- [ ] Supplied and synthetic fixture evaluation matches the documented matrix.
- [ ] Clean CLI and UI/API flows are demonstrable locally.
- [ ] Human review resumes a durable graph and payment remains idempotent.
- [ ] Full backend coverage over `backend/app` is at least 90%.
- [ ] `make verify` passes.
- [ ] Docker/Valkey asynchronous worker smoke test passes when Docker is available.
- [ ] README, architecture, setup, security, and PRD docs match implemented behavior.

