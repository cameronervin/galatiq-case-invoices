# Data and Persistence

## SQLite model

SQLAlchemy 2.0 typed models and focused repositories own the application schema.
`Base.metadata.create_all()` automatically creates six application tables, and
the inventory seed is repeatable. No manual database setup, Alembic migration, or
first-party handwritten SQL is required.

| Table | Responsibility |
| --- | --- |
| `schema_migrations` | Initial schema version |
| `inventory_items` | Canonical item, display name, stock, and aliases |
| `agent_runs` | Source metadata, provider profile, state, and timestamps |
| `run_results` | Typed invoice, findings, recommendation, review, and loop counts |
| `payments` | One idempotent simulated payment per run |
| `run_events` | Append-only sanitized timeline |

Money is stored as integer cents, UTC timestamps as ISO strings, and workflow
aggregates as validated JSON. Fields used for lifecycle, deduplication, ordering,
and payment guarantees remain relational and constrained.

## Transactions and invariants

- Each operation opens one injected SQLAlchemy session and commits or rolls back
  as one unit of work.
- Non-failed content is unique by content hash, provider, and model; concurrent
  creators return the winning run.
- Conditional review writes make the first decision authoritative while allowing
  identical unresolved redispatch.
- Unique run and idempotency keys prevent duplicate payments under repeated
  worker delivery.
- Events are written with their state transition and read by integer event ID.
- Repositories return immutable DTOs or Pydantic models, never ORM entities.

SQLite uses `NullPool`, a five-second driver timeout, foreign keys, and
`IMMEDIATE` write locking. This supports the local concurrency target; it is not
presented as a horizontally scaled database design.

## Checkpoints and source cleanup

LangGraph's `SqliteSaver` manages its own checkpoint tables in the same file.
First-party code configures that connection but does not query checkpoint tables.

Uploads are staged under generated names. Completed, rejected, and failed runs
delete their staged source. A review-required source remains only until resume
reaches a terminal state. Public contracts never expose source paths or content.

## Scope boundary

- **Implemented:** automatic schema/seed setup, typed SQLAlchemy repositories,
  guarded state, validated JSON artifacts, checkpoints, and terminal cleanup.
- **Take-home default:** one local SQLite file, metadata creation, synchronous
  sessions, and local transient staging.
- **Production follow-up:** PostgreSQL, Alembic, encrypted object storage and
  retention, backups, and broader concurrency testing.

See [system architecture](01-system-architecture.md) for lifecycle ownership and
[decisions](05-decisions-and-tradeoffs.md) for persistence tradeoffs.
