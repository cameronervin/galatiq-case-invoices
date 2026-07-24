# System Architecture

## Runtime paths

The synchronous path is the evaluation baseline:

```text
CLI -> InvoiceProcessingService -> repositories -> LangGraph -> SQLite
```

The optional asynchronous path adds delivery and presentation layers without
changing workflow behavior:

```text
Next.js -> FastAPI -> SQLite -> Celery/Valkey -> InvoiceProcessingService
                                               -> LangGraph -> SQLite
```

FastAPI queues a new run after its durable record exists. A worker atomically
claims a queued run by ID before it executes the graph; guarded transitions keep
late writers from regressing terminal state. The UI polls the selected public
detail until review or a terminal status, and keeps polling while a persisted
review is waiting for worker resume.

## Component ownership

| Component | Owns | Does not own |
| --- | --- | --- |
| CLI and FastAPI routes | Input validation and transport translation | Dispatch, workflow, or persistence logic |
| `RunApplicationService` | API run commands, queries, and queue dispatch | HTTP rendering or infrastructure construction |
| `InvoiceProcessingService` | Stable facade over focused invoice use cases | Business implementation, SQL statements, or infrastructure construction |
| Invoice intake, execution, review, and query services | Staging/deduplication; workflow execution/resume; review persistence; run reads | Concrete infrastructure construction or transport rendering |
| `bootstrap.ApplicationRuntime` / `bootstrap.InvoiceProcessingRuntime` | Composition roots, concrete adapter wiring, ordered shutdown | Business routing or HTTP rendering |
| Ports | Repository, provider, document, queue, and runtime contracts | Concrete I/O or use-case orchestration |
| Pydantic schemas | Focused invoice, workflow, review, payment, error, and run/API data contracts | Business rules, persistence, or orchestration |
| Domain policies | Deterministic approval/payment routing rules | I/O, model calls, or persistence |
| Domain validation | Focused, deterministic extraction-feedback, finding-ordering, invoice-integrity, and inventory rule modules | I/O, model calls, persistence, or workflow orchestration |
| Infrastructure document adapters | Bounded PDF/text reads and JSON/CSV/XML parsing | Workflow orchestration or routing decisions |
| Infrastructure adapters | SQLAlchemy, LangGraph checkpoints, LLM clients, and Celery dispatch | Use-case or domain decisions |
| LangGraph | Typed workflow order, interrupt, and node state | Durable business-record queries |
| Repositories | Inventory, run/result/event, and payment persistence | Provider or routing decisions |
| Celery | Execute/resume delivery by `run_id` | Invoice, review, or payment state |
| Next.js | Upload, polling, inspection, and review interaction | Authoritative workflow state |

## SQLite and Valkey boundary

SQLite is the only application source of truth. It stores the provider profile,
workflow status, typed artifacts, review, payment, and sanitized timeline.
LangGraph also owns checkpoint tables in the same file through its separate
framework-managed connection.

Valkey is queue infrastructure. Task payloads contain only `run_id`; task results
contain run ID, status, and an optional safe error code. Losing result-backend
data does not lose the invoice run.

## Service lifecycle and sessions

`bootstrap.InvoiceProcessingRuntime` owns a `Database`, repository adapters, a
profile-caching provider registry, bounded document loaders, and one
checkpoint-backed `GraphProvider`. The bootstrap layer injects those ports into
separate intake, execution, review, and query services, then exposes their small
`InvoiceProcessingService` facade to the existing CLI/API/worker entrypoints.
The API lifespan owns a
`bootstrap.ApplicationRuntime` that composes that processor with
the queue-backed `RunApplicationService`. Repositories receive the bound
`Database.session` callable. Each
method opens one short-lived SQLAlchemy `Session` with a context manager, commits
successful writes, rolls back exceptions, and always closes the session. Sessions
are never shared across requests, graph nodes, CLI calls, or Celery tasks.

The API lifespan constructs and closes its service. The CLI closes in `finally`.
Celery creates one service per worker process and closes it on process shutdown.
Service cleanup is idempotent and ordered: close the graph checkpoint connection,
close any owned live-model clients, then dispose the SQLAlchemy engine.

Public Pydantic contracts are defined in focused modules under `app/schemas`.
The original `schemas.domain` module is a compatibility-only export surface;
definitions live with their invoice, workflow, review, payment, error, or run
aggregate so persistence and transport consumers share one canonical type.

## Scope boundary

- **Implemented:** shared service orchestration, run-ID-only tasks, explicit API,
  CLI, worker, graph, repository, and lifecycle boundaries.
- **Take-home default:** synchronous SQLAlchemy, `NullPool`, one local SQLite file,
  and worker concurrency one for the documented demo.
- **Production follow-up:** independent web/worker deployments, managed queues,
  PostgreSQL connection pooling, tracing, and health/readiness dependencies.

See [data and persistence](03-data-and-persistence.md) for transaction details and
[interfaces and operations](04-interfaces-and-operations.md) for startup commands.
