# Decisions and Tradeoffs

## Decision record

| Decision | Why it fits this take-home | Cost or rejected alternative |
| --- | --- | --- |
| Offline provider by default | Evaluator gets deterministic, keyless, network-free behavior | Live model variability is demonstrated only in optional Grok mode |
| One shared workflow | CLI and workspace prove the same behavior | Separate per-surface orchestration was rejected as drift-prone |
| SQLite owns state; Valkey only queues | Durable results do not depend on broker retention | Valkey-as-database was rejected |
| SQLAlchemy 2.0 typed ORM | Typed models, generated statements, testable constraints, and injected sessions | Direct `sqlite3` reduced dependencies but spread transaction/SQL details |
| Context-managed session injection | Repository unit of work is explicit and always closed | Global/scoped sessions and FastAPI-owned sessions do not fit CLI/graph/worker reuse |
| No first-party handwritten SQL | One persistence abstraction and enforceable review boundary | Raw DDL, pragmas, cursors, `text()`, and driver SQL were removed |
| Metadata creation, not Alembic | One initial local schema keeps evaluation setup small | Migration history is deferred until schema evolution exists |
| Typed JSON workflow artifacts | Aggregate artifacts round-trip cleanly without many thin tables | Fully normalized invoice/finding/history tables add queryability not needed here |
| Deterministic policy after critique | Model contributes reasoning but cannot bypass business controls | Model-owned routing/payment was rejected |
| Server-owned idempotent payment | Duplicate worker delivery cannot pay twice | Model-selected tools and live banking are out of scope |
| No failed-run retry endpoint | Resubmitting failed content is simpler and avoids attempt/history state | Retry command, attempt counter, and retry UI were removed |
| Delete terminal staged sources | Minimizes sensitive local residue | A retention/replay subsystem was rejected for V1 |

## Why SQLAlchemy without repository leakage

ORM entities stay inside the persistence implementation. Repositories return
Pydantic models or immutable DTOs, so services and graph nodes do not depend on a
database mapping strategy. The injected `SessionContext` supplies transaction
scope without making FastAPI, Celery, or LangGraph own sessions.

SQLite locking is configured through the driver, foreign keys through Python's
connection API, and constraints/indexes through SQLAlchemy expressions. The
application uses short `IMMEDIATE` write transactions and `NullPool` instead of
first-party WAL statements or process-shared connections.

## Complexity deliberately avoided

There are only five run endpoints including health, three repositories, six
application tables, two worker tasks, one provider registry, and one graph. The
design omits authentication, retry/history tables, provider-per-surface rules,
offset pagination, retained-source policies, live integrations, and generalized
workflow/plugin infrastructure.

## Scope boundary

- **Implemented:** each decision above is reflected in code, tests, or public
  behavior; static tests enforce the SQL-free boundary.
- **Take-home default:** favor a small demonstrable vertical slice over a
  production-shaped platform.
- **Production follow-up:** revisit choices using measured load, compliance,
  retention, integration, and operator requirements rather than adding speculative
  abstractions now.

See [data and persistence](03-data-and-persistence.md) for concrete invariants and
[quality and roadmap](06-quality-security-and-roadmap.md) for evolution paths.
