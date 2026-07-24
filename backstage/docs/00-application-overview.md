# Application Overview

## What this application solves

Acme's manual invoice process is slow, error-prone, and difficult to audit. This
prototype turns supplied invoice documents into structured data, validates line
items against local inventory, records an explainable approval recommendation,
routes exceptions to a reviewer, and creates an idempotent mock payment for clean
invoices.

**Implemented** means behavior exists and is covered by the repository's test or
demo paths. **Take-home default** identifies a deliberate scope choice made for a
reliable local evaluation. **Production follow-up** identifies work intentionally
left outside this prototype.

## Primary demo

The required path is local, deterministic, synchronous, and broker-free:

```bash
uv sync
uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
```

It initializes SQLite, executes the typed LangGraph, deletes the staged source at
the terminal outcome, and prints one safe `RunDetail` JSON object. No API key,
Valkey process, web server, or network connection is needed.

## Business value demonstrated

- Straight-through processing for clean invoices with no duplicate mock payment.
- Explainable exception routing through stable finding and event codes.
- Human control over warning, non-USD, and high-value cases.
- A timestamped audit trail without exposing raw documents or hidden reasoning.
- One workflow implementation shared by the CLI and asynchronous workspace.

## Supplied-fixture outcomes

| Outcome | Fixtures |
| --- | --- |
| Automatic mock payment | INV-1001, INV-1004, revised INV-1004, INV-1006, INV-1010, INV-1011, INV-1015 |
| Human review | INV-1012, INV-1014 |
| Rejection | INV-1002, INV-1003, INV-1005, INV-1007, INV-1008, INV-1009, INV-1013, INV-1016 |

Missing CSV currency defaults to configured USD with an informational finding.
Exact aliases and parenthetical descriptors also produce informational findings.
OCR-like normalization produces a warning and requires review. Informational
findings never alter routing.

## Architecture snapshot

```text
CLI ------------------------> InvoiceProcessingService ----> LangGraph
                                      |                         |
Next.js -> FastAPI -> Celery ---------+                         +-> providers
              |                       |                         +-> inventory tool
              +-> Valkey: run IDs     +-> SQLAlchemy/SQLite     +-> mock payment
```

SQLite owns application state. Valkey only transports run identifiers and small
task results. The payment tool is deterministic and server-owned; a model cannot
select or invoke it directly.

## Scope boundary

- **Implemented:** offline and optional Grok providers, five explicit graph roles,
  human resume, API/worker/UI surfaces, audit events, and SQLAlchemy persistence.
- **Take-home default:** SQLite, typed JSON workflow artifacts, metadata schema
  creation, deterministic offline inference, and simulated payment.
- **Production follow-up:** authentication, durable object storage, PostgreSQL,
  live inventory/banking integrations, image OCR, and operational deployment.

## Document index

1. [System architecture](01-system-architecture.md)
2. [Agent workflow](02-agent-workflow.md)
3. [Data and persistence](03-data-and-persistence.md)
4. [Interfaces and operations](04-interfaces-and-operations.md)
5. [Decisions and tradeoffs](05-decisions-and-tradeoffs.md)
6. [Quality, security, and roadmap](06-quality-security-and-roadmap.md)

The [PRD](../prd/README.md) remains the requirements and implementation-history
source; this numbered set is the concise interviewer narrative.
