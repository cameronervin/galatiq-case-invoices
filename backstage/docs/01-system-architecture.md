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

FastAPI queues a new run after its durable record exists. A worker loads the run
by ID, executes or resumes the graph, and writes all business state to SQLite.
The UI polls the public detail endpoint until review or a terminal status.

## Component ownership

| Component | Owns | Does not own |
| --- | --- | --- |
| CLI and FastAPI routes | Input validation and transport translation | Workflow or persistence logic |
| `InvoiceProcessingService` | Runtime composition, staging, orchestration, cleanup | SQL statements or HTTP rendering |
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

Each `InvoiceProcessingService` owns one `Database`, three repositories, and one
`GraphProvider`. Repositories receive the bound `Database.session` callable. Each
method opens one short-lived SQLAlchemy `Session` with a context manager, commits
successful writes, rolls back exceptions, and always closes the session. Sessions
are never shared across requests, graph nodes, CLI calls, or Celery tasks.

The API lifespan constructs and closes its service. The CLI closes in `finally`.
Celery creates one service per worker process and closes it on process shutdown.
Service cleanup is idempotent and ordered: close the graph checkpoint connection,
then dispose the SQLAlchemy engine.

## Scope boundary

- **Implemented:** shared service orchestration, run-ID-only tasks, explicit API,
  CLI, worker, graph, repository, and lifecycle boundaries.
- **Take-home default:** synchronous SQLAlchemy, `NullPool`, one local SQLite file,
  and worker concurrency one for the documented demo.
- **Production follow-up:** independent web/worker deployments, managed queues,
  PostgreSQL connection pooling, tracing, and health/readiness dependencies.

See [data and persistence](03-data-and-persistence.md) for transaction details and
[interfaces and operations](04-interfaces-and-operations.md) for startup commands.
