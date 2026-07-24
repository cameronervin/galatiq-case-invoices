# Data and Persistence

## SQLAlchemy model

Application persistence uses SQLAlchemy 2.0 typed ORM models in
`backend/app/models/persistence.py`. `Base.metadata.create_all()` repeatably
creates six application tables; the seed uses the SQLite dialect's idempotent
insert construct. There is no Alembic layer or first-party handwritten SQL.

| Table | Responsibility |
| --- | --- |
| `schema_migrations` | Records the initial schema version |
| `inventory_items` | Canonical code, display name, stock, JSON aliases |
| `agent_runs` | Source metadata, provider profile, state, safe error, timestamps |
| `run_results` | Typed JSON invoice, findings, recommendation, review, loop counts |
| `payments` | One idempotent mock-payment record per run |
| `run_events` | Append-only sanitized timeline ordered by integer event ID |

Status and stage are constrained strings matching public enums. Money is stored
as integer cents. UTC timestamps remain ISO strings. Foreign keys cascade from a
run to its result, payment, and events. SQLAlchemy expressions define checks and
the partial unique index for active provider profiles.

## Session context and repository boundary

`Database` owns the engine and `sessionmaker`. Its
`session(write: bool = False)` context manager creates one session, commits a
successful write, rolls back an exception, and closes in all cases. The typed
`SessionContext` callable is injected into the inventory, run, and payment
repositories; repositories never receive a path or retain a session.

The engine uses one connection per unit of work with `NullPool`, a five-second
driver timeout, `check_same_thread=False`, and SQLite `IMMEDIATE` write locking.
Foreign keys are enabled through Python's SQLite connection configuration API.
Application reads and writes use ORM entities plus SQLAlchemy `select`, `insert`,
and `update` expressions.

## Transactions and invariants

- Non-failed runs are unique by content hash, provider name, and provider model.
  A failed run releases that profile so the content may create a new run.
- Concurrent creators handle the uniqueness race by returning the winning run.
- Review storage uses a conditional update, so the first decision wins; identical
  unresolved decisions can redispatch and conflicts remain conflicts.
- `payments.run_id` and `idempotency_key` are unique. Concurrent delivery returns
  the existing payment and cannot create a second record.
- Events append in the same transaction as their run transition and are read in
  autoincrementing event-ID order.
- Repositories return immutable DTOs and Pydantic domain models, never detached
  ORM entities.

## JSON artifacts

Invoice, findings, recommendation, and review are natural aggregate artifacts,
so they are stored as SQLAlchemy `JSON` and validated at the repository boundary.
This keeps the take-home schema small while preserving exact public types. Fields
needed for deduplication, lifecycle queries, ordering, and payment guarantees stay
relational and constrained.

## Checkpoints and source cleanup

LangGraph's `SqliteSaver` owns a separate raw SQLite connection and its internal
checkpoint schema. First-party code configures and closes that connection but
does not execute checkpoint SQL. Application tables remain repository-owned.

Uploaded sources are staged under generated names. They are deleted on completed,
rejected, or failed outcomes. A review-required source remains only until resume
reaches a terminal outcome. Public objects never expose its path or contents.

## Compatibility and scope

- **Implemented:** metadata creation preserves current table/column contracts and
  can open the existing local schema without destructive rewrite.
- **Take-home default:** JSON aggregates, SQLite default journal mode, metadata
  creation, and synchronous sessions keep local setup focused.
- **Production follow-up:** Alembic migrations, PostgreSQL, encrypted object
  storage/retention policy, backups, and broader concurrent-load testing.

See [system architecture](01-system-architecture.md) for lifecycle ownership.
