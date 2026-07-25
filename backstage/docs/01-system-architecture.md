# System Architecture

## Runtime paths

The evaluation baseline runs without queue infrastructure:

```text
CLI -> InvoiceProcessingService -> use cases -> LangGraph -> SQLite
```

The optional workspace adds delivery and presentation around the same service:

```text
Next.js -> FastAPI -> SQLite -> Celery/Valkey -> InvoiceProcessingService
                                               -> LangGraph -> SQLite
```

FastAPI persists a run before queuing it. A worker claims the queued run by ID,
and guarded transitions prevent late writers from regressing terminal state. The
UI polls the selected run through review or a terminal outcome.

## Boundaries

| Boundary | Responsibility |
| --- | --- |
| CLI and FastAPI | Validate transport input and render public contracts |
| Application services | Intake, deduplication, execution, review, queries, and dispatch |
| LangGraph | Typed workflow order, bounded loops, interrupt, and node state |
| Domain policy and validation | Deterministic findings, ordering, and final routing |
| Repositories | Inventory, run, result, event, review, and payment persistence |
| Infrastructure adapters | Documents, SQLAlchemy, checkpoints, providers, and queue delivery |
| Celery | Execute or resume a run by `run_id` |
| Next.js | Upload, polling, inspection, and review interaction |

HTTP routes and the root CLI remain thin. Composition roots build concrete
adapters; services depend on ports and public Pydantic contracts rather than ORM
entities or framework state.

## State and delivery

SQLite is the only business source of truth. It stores provider profile, run
status, typed artifacts, review, payment, sanitized events, and LangGraph
checkpoints. Valkey is queue infrastructure: task payloads contain only `run_id`,
and results contain run ID, status, and an optional safe error code.

Each repository operation uses one short-lived SQLAlchemy session. Successful
writes commit, failures roll back, and sessions always close. Sessions are never
shared across requests, graph nodes, CLI calls, or Celery tasks.

The API lifespan owns its runtime. The CLI closes in `finally`; Celery builds one
runtime per worker process and closes it at process shutdown. Cleanup closes graph
checkpoints and provider clients before disposing the SQLAlchemy engine.

## Scope boundary

- **Implemented:** shared service orchestration, explicit ports, run-ID-only
  tasks, guarded state transitions, and owned runtime lifecycles.
- **Take-home default:** synchronous SQLAlchemy, `NullPool`, one SQLite file, and
  Celery concurrency one for the documented local workspace.
- **Production follow-up:** independent deployments, managed queues, PostgreSQL
  pooling, tracing, health dependencies, and horizontal worker recovery.

See [agent workflow](02-agent-workflow.md), [data and persistence](03-data-and-persistence.md),
and [interfaces and operations](04-interfaces-and-operations.md).
