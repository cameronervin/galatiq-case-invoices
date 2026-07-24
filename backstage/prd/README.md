# Invoice Processing Automation PRD

## Purpose

This is the first structured product harness for the Galatiq invoice-processing
case study. It specifies the product to be built on top of the existing scaffold;
it does not describe implemented business behavior.

The product is a local-first accounts-payable workspace that accepts invoice
documents, extracts structured data, validates them against mock inventory,
routes them through bounded LangGraph approval logic, and records either a mock
payment or an explainable rejection.

## Users

- **Accounts-payable processor:** submits invoices and monitors processing.
- **VP reviewer:** resolves high-value, warning, and non-USD exceptions.
- **Local operator/developer:** configures the model provider and runs the local
  API, worker, CLI, and frontend.
- **Case-study evaluator:** verifies correctness, safety, agentic behavior, and
  usability using the supplied fixtures.

## Goals

- Process PDF, TXT, JSON, CSV, and XML invoices through an observable workflow.
- Complete clean USD invoices at or below $10,000 with an idempotent mock payment.
- Reject blocking validation failures before payment.
- Pause high-value, warning, and non-USD cases for an auditable human decision.
- Make exact duplicates idempotent while treating changed revisions as new runs.
- Keep model providers replaceable and require Grok for CLI-created runs.
- Preserve missing and uncertain data rather than inventing values.

## Non-Goals

- Production authentication or authorization.
- Live email ingestion, inventory services, banking, or payment settlement.
- Currency conversion or exchange-rate lookup.
- Cloud deployment or additional persistent services.
- Image-only PDF OCR.
- Inventory reservation or stock decrement after payment.

## Success Criteria

- The documented CLI command processes a clean fixture end to end using Grok.
- API and workspace users can submit, track, review, retry, and inspect runs.
- All supplied fixtures produce the outcomes in the acceptance matrix.
- Graph retries, resumes, and duplicate worker delivery cannot pay twice.
- Logs and public responses contain no secrets, raw provider payloads, raw
  invoice contents, or local filesystem paths.
- The full repository verification and asynchronous worker smoke test pass.

## Locked Product Decisions

| Decision | Direction | Source |
| --- | --- | --- |
| Delivery surface | CLI, FastAPI, Celery worker, and Next.js workspace | Product owner |
| Orchestration | Typed LangGraph workflow with bounded repair/reflection loops | Product owner and README |
| Approval policy | Clean USD `<= $10,000` auto-pays; high-value, warnings, and non-USD require review; blockers reject | Product owner |
| CLI provider | Grok only; missing `XAI_API_KEY` is a configuration error | Product owner |
| Development provider | OpenAI adapter behind the same provider contract | Product owner |
| Duplicate policy | Exact content reuses the existing run; changed content creates a new run | Product owner |
| Foreign currency | Preserve original currency and require review; never invent FX | Product owner |
| Human review surface | API and workspace; CLI reports `review_required` with the run ID | Product owner |
| Priority | End-to-end correctness before extra agentic or visual polish | Product owner |
| Deadline | No hard deadline | Product owner |

## Documentation Map

### User stories

- [Master user stories](01-user-stories/_master-user-stories.md)
- [Submission and tracking](01-user-stories/epic-1-submission-and-tracking.md)
- [Extraction and validation](01-user-stories/epic-2-extraction-and-validation.md)
- [Approval and payment](01-user-stories/epic-3-approval-and-payment.md)
- [Operations and workspace](01-user-stories/epic-4-operations-and-workspace.md)

### Technical specifications

- [Data model](02-technical-docs/data-model.md)
- [API specification](02-technical-docs/api-specification.md)
- [Agentic framework](02-technical-docs/agentic-framework.md)
- [Integration specification](02-technical-docs/integration-specification.md)
- [Security and observability](02-technical-docs/security-and-observability.md)
- [Workspace UX](02-technical-docs/workspace-ux.md)

### Implementation

- [Master implementation plan](03-implementation/_implementation-plan.md)
- Phase 1: contracts and persistence
- Phase 2: ingestion and providers
- Phase 3: validation and workflow
- Phase 4: API, worker, and CLI
- Phase 5: workspace and readiness

## Phase Workflow

Each phase file contains tasks with status, goal, user-story references,
assertion-chain validation, and linked PRD documents. Tasks are ordered by
dependency and sized for one coding-agent thread. Mark tasks with:

- `☐` — not started
- `◐` — partial; state what remains in the goal
- `☑` — complete, reviewed, tested, and committed

When implementation differs from a task, record **Planned**, **Actual**,
**Reason**, and **Impact on later phases** in the matching deviations file.
Reconcile the specifications at phase boundaries before starting the next phase.

## Fixture Acceptance Matrix

| Expected outcome | Invoices | Reason |
| --- | --- | --- |
| Automatic mock payment | INV-1001, INV-1004, revised INV-1004, INV-1006, INV-1010, INV-1011, INV-1015 | Clean, supported USD invoices within stock and threshold |
| Human review | INV-1012 | OCR-like normalization warnings |
| Human review | INV-1014 | EUR is preserved but unsupported for automatic payment |
| Rejection | INV-1002, INV-1005, INV-1007, INV-1013 | Aggregated quantities exceed stock; INV-1013 also has a total discrepancy |
| Rejection | INV-1003 | Zero-stock item, invalid relative due date, and suspicious urgency language |
| Rejection | INV-1008, INV-1016 | Unknown inventory items |
| Rejection | INV-1009 | Missing required fields, negative quantity, and invalid amount |

## Assumptions

- Supplied fixtures are immutable and contain mock data only.
- PDFs are text-bearing; image OCR is deferred.
- Due dates are validated relative to invoice dates, not the current system date.
- The inventory table is reference data and is never decremented by this workflow.
- Valkey is queue infrastructure only; SQLite is the application source of truth.
- Raw documents may be staged locally for processing and retry, but are never
  stored in graph state, logs, or public API responses.

