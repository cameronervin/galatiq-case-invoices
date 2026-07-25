# Decisions and Tradeoffs

## Decision record

| Decision | Take-home value | Deferred cost |
| --- | --- | --- |
| Offline provider by default | Deterministic, keyless, network-free evaluation | Live model variability is optional |
| One workflow for every surface | CLI and workspace prove identical behavior | Surfaces cannot customize orchestration independently |
| SQLite owns state; Valkey only queues | Broker loss cannot erase a run | SQLite limits scale and concurrency |
| SQLAlchemy repositories | Typed constraints and isolated persistence | More structure than direct `sqlite3` |
| Metadata creation, not Alembic | Fresh checkout needs no migration step | Schema evolution is deferred |
| Typed JSON workflow artifacts | Small schema with exact public round trips | Less ad hoc SQL queryability |
| Deterministic policy after critique | Models cannot bypass routing controls | Policy changes require code changes |
| Server-owned idempotent payment | Duplicate delivery cannot pay twice | No model-selected or live banking tool |
| Delete terminal staged sources | Minimizes sensitive local residue | Replay requires resubmission |
| No failed-run retry endpoint | Avoids attempt/history complexity | A failed file must be resubmitted |

## Boundary rationale

ORM entities remain inside persistence adapters. Repositories return Pydantic
models or immutable DTOs, and injected session contexts own commit, rollback, and
close behavior. This lets CLI, API, graph, and worker reuse the same services
without framework-owned or global sessions.

The model contributes extraction, recommendation, and critique, while trusted
validation and policy own blocking findings, review thresholds, rejection, and
payment eligibility. This keeps agent behavior observable without delegating
financial control to generated output.

## Complexity deliberately omitted

The prototype has five API routes including health, six application tables, two
worker tasks, one provider registry, and one graph. It intentionally omits auth,
tenancy, retry/history tables, retained-source replay, live integrations, offset
pagination, and generalized workflow/plugin infrastructure.

## Scope boundary

- **Implemented:** the decisions above are enforced by code, contracts, tests, or
  documented behavior.
- **Take-home default:** favor one demonstrable vertical slice over speculative
  platform infrastructure.
- **Production follow-up:** revisit choices using measured scale, compliance,
  retention, integration, and operator requirements.

See [data and persistence](03-data-and-persistence.md) and
[quality, security, and roadmap](06-quality-security-and-roadmap.md).
