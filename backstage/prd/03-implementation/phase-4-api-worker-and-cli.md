# Phase 4 — API, Worker, and CLI

## Objective

Expose the proven workflow through thin FastAPI routes, JSON-safe Celery tasks,
and the required Grok-backed CLI while preserving SQLite as the source of truth.

## Dependencies

- Complete in-process workflow from Phase 3.

## Task Plan

| Status | Goal | User Stories | Validation | PRD Docs |
| --- | --- | --- | --- | --- |
| ☐ | **[feature] Refactor worker execution and resources** — Remove per-task `asyncio.run`, initialize one synchronous graph/checkpointer/provider/repository context per worker process, set local concurrency one, and send only run IDs in tasks. | US-05, US-11, US-14, US-15 | Worker registers execute/resume tasks → payload/result JSON serialization passes → lifecycle init/shutdown is idempotent → duplicate execute/resume is safe → task never receives source path/content/review text → focused worker tests pass. | `agentic-framework.md`, `integration-specification.md`, `security-and-observability.md` |
| ☐ | **[feature] Implement run creation/list/detail API** — Add multipart upload and bounded list/detail routes over services and public Pydantic models, including new-vs-deduplicated response status. | US-02–US-04, US-14 | Valid upload returns `202` and queues by run ID → exact duplicate returns `200`/same run → invalid/oversized/type mismatch maps to documented `4xx` → list pagination/filter works → detail matches staged workflow state → no path/internal/provider payload leaks. | `api-specification.md`, `security-and-observability.md` |
| ☐ | **[feature] Implement review and retry API** — Validate review reason/state, persist first-wins human decision, dispatch resume, and expose failed retry with retained source/hash checks and typed conflicts. | US-05, US-11, US-13 | Review approve/reject returns `202` and resumes correct branch → duplicate/out-of-state review returns `409` → queue failure leaves review state recoverable → eligible retry increments attempt/queues → ineligible/expired/tampered retry maps to documented `409`. | `api-specification.md`, `data-model.md`, `agentic-framework.md` |
| ☐ | **[feature] Implement Grok-required CLI lifecycle** — Preserve required invoice command, validate Grok key/model before queueing, create through shared service, poll SQLite by default, add no-wait/timeout options, and print one safe JSON result. | US-01, US-03, US-15 | Exact README command reaches terminal/review state with mocked worker → missing Grok key exits 3 before dispatch → invalid input/dispatch/failed/timeout exit codes match spec → `--no-wait` returns queued → stdout/stderr contain no resolved path/key/raw invoice. | `api-specification.md`, `integration-specification.md`, `security-and-observability.md` |
| ☐ | **[feature] Harden queue/status failure handling and logging** — Persist safe queue failures, use stable API/CLI/worker codes, expand explicit CORS methods, and emit sanitized structured transition logs. | US-03, US-05, US-14 | Broker failure cannot leave falsely queued run → public error envelope is stable → CORS allows configured local origin/methods only → log capture excludes vendor/amount/path/prompt/key/provider body → transient polling can still read last persisted state. | `api-specification.md`, `security-and-observability.md` |
| ☐ | **[eval] Add API/CLI/worker integration tests and smoke path** — Exercise upload-to-worker-to-terminal and review resume with real SQLite, mocked providers/payment, and Valkey only in the documented smoke test. | US-01–US-05, US-11–US-15 | API create→GET terminal assertion chain passes → review create→interrupt→approve/reject passes → retry passes → CLI clean/review/failure paths pass → Celery eager tests remain JSON-safe → Docker worker smoke completes when available. | `api-specification.md`, `integration-specification.md` |

## Definition of Done

- [ ] All Phase 4 tasks are `☑` or deviations explicitly re-scope them.
- [ ] API endpoints and CLI behavior match exact public contracts.
- [ ] Celery payloads contain only JSON-safe identifiers/commands specified by the PRD.
- [ ] Valkey is not used to answer run APIs.
- [ ] CLI cannot run without Grok configuration.
- [ ] Structured errors/logs pass leakage tests.
- [ ] Focused integration checks and `make verify` pass.
- [ ] Docker/Valkey asynchronous worker smoke test passes when Docker is available.

