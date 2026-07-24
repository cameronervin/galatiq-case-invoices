# Invoice Processing Automation PRD

## Purpose

Build a local-first invoice-processing prototype that demonstrates extraction,
deterministic validation, bounded agent critique, human review, and idempotent
mock payment. This PRD defines intended behavior; implemented behavior is
described by the root README and developer guides.

## README Requirements

- Process the supplied PDF, TXT, JSON, CSV, and XML fixtures.
- Validate invoice items against local SQLite inventory.
- Apply the $10,000 approval threshold and explain rejection.
- Demonstrate structured output, local tool use, and a bounded critique loop.
- Provide the required CLI command and structured results.
- Keep external inventory and payment behavior local and simulated.

## Implementation Defaults

- The required CLI executes synchronously without Valkey.
- Offline deterministic inference is the default; Grok is an optional live mode.
- FastAPI, Celery, and Next.js provide an optional asynchronous workspace.
- SQLite stores typed JSON workflow artifacts rather than independently queryable
  invoice, finding, and decision tables.
- SQLAlchemy 2.0 typed ORM models own application persistence. Repositories receive
  a context-managed session callable and contain no handwritten SQL.
- Blocking findings reject; warnings, non-USD, and totals above $10,000 require
  review; informational findings do not alter routing.
- Exact duplicates reuse a non-failed run only within the same provider/model
  profile. Changed content, provider/model changes, and resubmission after failure
  create new runs.

## Users

- Accounts-payable processor: submits and inspects invoices.
- VP reviewer: approves or rejects exceptions.
- Evaluator/operator: runs the local demo and verifies behavior.

## Success Criteria

- `python main.py --invoice_path=data/invoices/invoice_1001.txt` completes offline
  without Valkey or a network connection.
- Every supplied fixture matches the acceptance matrix.
- The workflow exposes extraction, inventory-tool validation, approval, critique,
  policy, review, rejection, and mock-payment events.
- Duplicate worker delivery cannot create a second payment.
- API, CLI, logs, Celery, and UI expose no local paths, raw invoice content,
  prompts, provider payloads, keys, or hidden reasoning.
- `make verify` and the documented asynchronous worker smoke test pass.

## Fixture Acceptance Matrix

| Outcome | Invoices | Reason |
| --- | --- | --- |
| Automatic mock payment | INV-1001, INV-1004, revised INV-1004, INV-1006, INV-1010, INV-1011, INV-1015 | Valid inventory and totals; clean USD at or below threshold |
| Human review | INV-1012 | OCR-like corrections are visible warnings |
| Human review | INV-1014 | EUR is preserved and requires review |
| Rejection | INV-1002, INV-1005, INV-1007, INV-1013 | Aggregated quantity exceeds stock; INV-1013 also has a total mismatch |
| Rejection | INV-1003 | Zero stock, invalid relative date, and suspicious payment language |
| Rejection | INV-1008, INV-1016 | Unknown inventory items |
| Rejection | INV-1009 | Missing fields, negative quantity, and invalid amount |

## Normalization Provenance

- The supplied CSV dialect has configured default currency USD. Applying it emits
  `DEFAULT_CURRENCY_APPLIED` with `info` severity.
- Exact aliases, including parenthetical item descriptions, emit
  `ITEM_ALIAS_NORMALIZATION` with `info` severity.
- Evidence-backed OCR corrections emit `OCR_NORMALIZATION` with `warning`
  severity and require review.
- No other missing invoice value is guessed.

## Business Demonstration

The demo reports straight-through fixture outcomes, exceptions needing human
attention, elapsed processing time, stable reason codes, and the invariant that
each run records at most one simulated payment.

## Documentation Map

- [Canonical user stories](01-user-stories/_master-user-stories.md)
- [Technical design](02-technical-docs/technical-design.md)
- [API specification](02-technical-docs/api-specification.md)
- [Workspace UX](02-technical-docs/workspace-ux.md)
- [Implementation plan](03-implementation/_implementation-plan.md)

## Assumptions and Non-Goals

Fixtures are immutable and contain mock data. PDFs are text-bearing. Inventory is
reference data and is not decremented. No retry endpoint, retained-source retry,
OpenAI adapter, authentication, cloud deployment, OCR service, live payment,
live inventory, or FX conversion is included.
