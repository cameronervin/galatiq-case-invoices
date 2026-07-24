# Quality, Security, and Roadmap

## Verification strategy

`make verify` checks generated API artifacts without rewriting them, runs backend
branch coverage with an 85% floor and lint, then runs frontend tests, lint, type
checking, and a production build. GitHub Actions runs the same target from frozen
Python and pnpm lockfiles.
The documented Valkey/Celery smoke test exercises real execute and review/resume
delivery after the local suite.

| Area | Evidence |
| --- | --- |
| Persistence | Repeatable metadata, constraints/FKs/indexes, seed idempotency, JSON round trips, session commit/rollback/close |
| Concurrency | Same-profile creation, execution claims, terminal transitions, and payment delivery are guarded |
| Workflow | Every route, repair/revision bound, policy override, interrupt/resume, timeout, and replay path |
| Providers | Offline fixtures and mocked Grok success, refusal, auth, timeout, retry, structured output, `store=False` |
| Interfaces | CLI exit codes, API status/contracts, queue failure, review conflict/redispatch, JSON-safe Celery |
| Frontend | Selection races, polling recovery, queue-error reconciliation, review redispatch, accessibility, type contract, production build |
| Architecture | Static source guard rejects raw SQL escape hatches and repository `sqlite3` use |
| Documentation | Required numbered files, headings, and relative links |

## Fixture matrix

| Expected route | Fixtures | Core evidence |
| --- | --- | --- |
| Pay | INV-1001, INV-1004, revised INV-1004, INV-1006, INV-1010, INV-1011, INV-1015 | Valid, in-stock USD at or below threshold |
| Review | INV-1012, INV-1014 | OCR warning or preserved non-USD currency |
| Reject | INV-1002, INV-1003, INV-1005, INV-1007, INV-1008, INV-1009, INV-1013, INV-1016 | Blocking inventory, date, quantity, identity, or reconciliation finding |

## Observability and sanitization

Run events expose stage, status, stable code, safe message, duration, and time.
Provider/tool/payment transitions are visible, including separate validation,
inventory, approval, and critic outcomes, bounded repairs/revisions, policy
overrides, review, and payment. Public results,
logs, events, and Celery values exclude local paths, raw documents, review text in
queue data, prompts, provider payloads, credentials, vendor/item/amount logging,
and hidden reasoning.

Errors cross boundaries as stable codes and safe messages. Setup and workflow
exceptions mark the run failed, delete staged sources, and preserve sanitized
audit state; persistence failures remove unowned staged uploads. Missing Grok
credentials fail explicitly. Queue failure never pretends a run is executing;
review queue failure preserves the decision for idempotent redispatch.

## Security posture

- Generated staging names prevent client filename path control.
- Upload type, size, and empty-content checks happen before execution.
- XML uses a hardened parser; PDF handling is bounded and rejects encrypted,
  empty, image-only, and oversized inputs.
- Inventory is read-only and payment is mock, deterministic, and server-owned.
- SQLAlchemy binds values; first-party backend code has no executable raw SQL.
- Secrets and generated databases/sources are excluded from source control.

## Known limitations and non-goals

This is not a production accounts-payable platform. It has no authentication,
tenant isolation, authorization, cloud deployment, high-availability database,
image OCR, virus scanning, vendor master, purchase-order matching, FX conversion,
inventory mutation, live payment, source-retention service, or failed-run retry.
SQLite concurrency and local filesystem staging are appropriate only for this
prototype's workload.

## Production evolution

1. Add identity, reviewer authorization, audit policy, and managed secrets.
2. Move relational state to PostgreSQL and introduce Alembic migrations.
3. Store encrypted source documents in managed object storage with explicit
   retention, malware scanning, and access logs.
4. Integrate vendor/PO/inventory systems and a payment service behind the existing
   repository/tool boundaries.
5. Add OCR, evaluation datasets, prompt/model versioning, distributed tracing,
   queue monitoring, SLOs, backups, and disaster recovery.

## Interviewer talking points

- The project optimizes first for a one-command, evidence-backed vertical demo.
- Agent reasoning is bounded by deterministic validation and payment policy.
- SQLite holds durable business facts; Valkey failure cannot erase a run.
- Context-managed session injection gives CLI, API, graph, and worker the same
  repository semantics without global sessions.
- Deduplication and database uniqueness make duplicate mock payment impossible.
- Above-and-beyond UI/worker scope is isolated from the required broker-free path.

## Scope boundary

- **Implemented:** the verification, safeguards, fixture coverage, and failure
  behavior described above.
- **Take-home default:** local infrastructure and mock integrations prioritize
  reproducibility and explainability.
- **Production follow-up:** the ordered roadmap above addresses scale, compliance,
  integration, and operational maturity.

Start with the [application overview](00-application-overview.md) or run the
commands in [interfaces and operations](04-interfaces-and-operations.md).
