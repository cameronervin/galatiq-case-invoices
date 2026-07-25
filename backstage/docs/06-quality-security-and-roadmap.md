# Quality, Security, and Roadmap

## Verification

```bash
make verify
```

The target checks generated API artifacts without rewriting them, runs backend
tests with branch coverage and an 85% floor, applies Python lint, then runs
frontend tests, lint, type checking, and a production build. GitHub Actions runs
the same target from frozen Python and pnpm lockfiles. The
[worker smoke test](04-interfaces-and-operations.md#execute-and-review-worker-smoke-test)
adds real Valkey execute and review/resume delivery.

| Area | Evidence |
| --- | --- |
| Persistence | Repeatable setup, constraints, JSON round trips, and session lifecycle |
| Concurrency | Guarded creation, execution, review, terminal state, and payment |
| Workflow | Routes, repair/revision bounds, interrupt/resume, timeout, and replay |
| Providers | Offline fixtures and mocked Grok success/failure paths |
| Interfaces | CLI exits, API contracts, queue failure, review conflict, JSON-safe tasks |
| Frontend | Selection races, polling recovery, review redispatch, accessibility, and build |
| Architecture | Static guard against raw SQL escape hatches |
| Documentation | Required files, headings, links, and upstream contract markers |

## Fixture matrix

| Route | Fixtures | Reason |
| --- | --- | --- |
| Pay | INV-1001, INV-1004, revised INV-1004, INV-1006, INV-1010, INV-1011, INV-1015 | Valid, in-stock USD at or below threshold |
| Review | INV-1012, INV-1014 | OCR-like warning or preserved non-USD currency |
| Reject | INV-1002, INV-1003, INV-1005, INV-1007, INV-1008, INV-1009, INV-1013, INV-1016 | Blocking inventory, date, quantity, identity, or reconciliation finding |

## Observability and security

Events expose stage, status, stable code, safe message, duration, and time. Public
results, logs, events, and queue values exclude local paths, raw documents,
prompts, provider payloads, credentials, vendor/payment details, and hidden
reasoning. Queue failure does not pretend execution started; review queue failure
preserves the decision for identical redispatch.

- Generated staging names prevent client filename path control.
- Type, size, empty-content, XML, PDF, and workflow bounds are enforced.
- Inventory is read-only and payment is deterministic, mock, and server-owned.
- SQLAlchemy binds values; first-party backend code contains no executable raw
  SQL.
- Secrets, generated databases, and staged sources are ignored by version control.

## Known limitations

This is not a production accounts-payable system. It has no authentication,
tenant isolation, reviewer authorization, cloud deployment, high-availability
database, image OCR, malware scanning, vendor master, purchase-order matching,
FX conversion, inventory mutation, live payment, source-retention service, or
failed-run retry. SQLite and local staging fit only this prototype workload.

## Production roadmap

1. Add identity, reviewer authorization, audit policy, and managed secrets.
2. Move relational state to PostgreSQL and add Alembic migrations.
3. Store encrypted documents with explicit retention, scanning, and access logs.
4. Integrate vendor, PO, inventory, and payment services behind existing ports.
5. Add OCR, evaluations, prompt/model versioning, tracing, queue monitoring,
   service objectives, backups, and disaster recovery.

## Scope boundary

- **Implemented:** the verification, safeguards, fixture behavior, and failure
  handling described above.
- **Take-home default:** local infrastructure and mock integrations prioritize
  reproducibility, safety, and explainability.
- **Production follow-up:** the roadmap addresses identity, scale, compliance,
  integrations, retention, and operations.

Start with the [application overview](00-application-overview.md) or use the
[operations guide](04-interfaces-and-operations.md) to run the system.
