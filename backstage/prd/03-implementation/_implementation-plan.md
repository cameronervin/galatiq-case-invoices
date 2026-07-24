# Vertical Implementation Plan

This plan records the implemented vertical build. Each phase ends in a
demonstrable slice and passes focused checks plus `make verify`.

## Phase 1 — Offline CLI Vertical Slice (complete)

- Implement public/domain models, SQLAlchemy metadata and typed ORM models, three
  context-session-injected repositories, staging/deduplication/cleanup,
  deterministic loaders, offline provider, inventory/payment tools, typed
  LangGraph, and synchronous CLI.
- Prove clean payment, blocking rejection, review-required output, exact money,
  source cleanup, payment replay, and no path/content leakage.

## Phase 2 — Agentic and Fixture Completion (complete)

- Add explicit agent roles, one extraction repair, one approval revision,
  deterministic policy override, Grok adapter, provider registry, and complete
  fixture evaluation.
- Prove every fixture outcome, loop bound, threshold boundary, tool event,
  provider failure, and 300-second deadline behavior.

## Phase 3 — API and Worker (complete)

- Add create/list/detail/review routes, run-ID-only execute/resume tasks,
  idempotent review redispatch, minimal Celery results, and asynchronous smoke.
- Prove status codes, same-profile deduplication, queue failure, review conflict,
  duplicate delivery, and Valkey data minimization.

## Phase 4 — Workspace and Handoff (complete)

- Implement upload, recent runs, polling, detail, findings, timeline, review, and
  outcomes; mechanically validate frontend/API contracts; reconcile all docs.
- Prove accessibility, responsive states, offline CLI demo, optional Grok demo,
  full verification, and asynchronous worker smoke.

## Persistence Simplification (complete)

- Replace first-party `sqlite3` schema and repository code with SQLAlchemy 2.0
  typed ORM models while preserving table, JSON, enum, deduplication, event, and
  payment contracts.
- Inject a context-managed `SessionContext` into every repository operation;
  verify commit, rollback, closure, reuse, and concurrent uniqueness behavior.
- Keep LangGraph checkpointing on a separately owned framework connection and
  make service cleanup close the graph before disposing the engine.
- Add the canonical numbered interviewer documentation under `backstage/docs` and
  retain this PRD as the requirements and implementation-history source.

## Deviations

Record any deviation here with planned behavior, actual behavior, reason, and
impact before marking the affected phase complete.

No deviations recorded.

## Product Done

- Every canonical user story and fixture outcome has automated evidence.
- The documented offline CLI runs without broker/network access.
- Human review resumes durably and duplicate delivery cannot pay twice.
- API/UI flows are demonstrable when Valkey is running.
- Logs and public surfaces contain no forbidden data.
- `make verify` and the documented worker smoke pass.
