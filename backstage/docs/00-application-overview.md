# Application Overview

## Purpose

This prototype turns supplied invoice documents into typed data, checks line
items against local inventory, records an explainable decision, routes exceptions
to a reviewer, and creates one idempotent simulated payment for an approved run.
It demonstrates a complete local workflow without presenting prototype choices
as production capabilities.

## Reviewer path

The required demo is synchronous, deterministic, and broker-free:

```bash
uv sync
uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
```

The command creates and seeds SQLite automatically, executes the typed LangGraph,
removes the staged source at a terminal outcome, and prints a safe result. It
needs no API key, network connection, Docker, Valkey, API, worker, or frontend.
Use `--format json` for the compact public `RunDetail` contract.

The optional workspace adds upload, recent-run triage, polling, findings and
decision-history inspection, human review, and terminal outcomes through Next.js,
FastAPI, Celery, and Valkey. Approval requires a second-step confirmation before
simulated payment.

## Workflow and value

```text
ingest -> extract -> validate -> approve -> critic -> policy
                                                   | blocking -> reject
                                                   | exception -> review
                                                   | clean -> payment -> finalize
```

- Clean invoices demonstrate straight-through processing and one mock payment.
- Stable findings and events make exception routing observable.
- Human review controls warning, non-USD, and high-value cases.
- Content/profile deduplication and payment uniqueness prevent duplicate payment.
- The CLI and asynchronous workspace share one workflow implementation.

## Architecture snapshot

```text
CLI ------------------------> InvoiceProcessingService ----> LangGraph
                                      |                         |
Next.js -> FastAPI -> Celery ---------+                         +-> providers
              |                       |                         +-> inventory tool
              +-> Valkey: run IDs     +-> SQLAlchemy/SQLite     +-> mock payment
```

SQLite owns application state and LangGraph checkpoints. Valkey transports run
IDs and small task results only. Deterministic policy—not the model—owns final
routing, and the payment tool is server-owned.

## Scope boundary

- **Implemented:** offline and Grok providers, typed LangGraph roles, bounded
  repair/reflection, API/worker/UI paths, human resume, audit events, and
  SQLAlchemy persistence.
- **Take-home default:** deterministic offline inference, SQLite, local files,
  metadata-based schema creation, and simulated payment.
- **Production follow-up:** identity and authorization, PostgreSQL and migrations,
  managed document storage, OCR, live integrations, monitoring, and deployment.

## Document index

1. [System architecture](01-system-architecture.md)
2. [Agent workflow](02-agent-workflow.md)
3. [Data and persistence](03-data-and-persistence.md)
4. [Interfaces and operations](04-interfaces-and-operations.md)
5. [Decisions and tradeoffs](05-decisions-and-tradeoffs.md)
6. [Quality, security, and roadmap](06-quality-security-and-roadmap.md)

The [consolidated PRD](../prd/README.md) retains requirements and implementation
history; this numbered set is the concise reviewer narrative.
