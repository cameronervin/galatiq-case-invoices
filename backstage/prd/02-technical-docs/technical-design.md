# Technical Design

## Architecture

The required CLI executes the typed LangGraph synchronously and does not require
Valkey. FastAPI, Celery, and Next.js expose the same services as an optional
asynchronous workspace.

```text
CLI -> run service -> SQLite -> LangGraph -> local tools

Next.js -> FastAPI -> run service -> SQLite -> Celery/Valkey -> LangGraph
```

SQLite is the application source of truth. Celery messages and results contain
only run identifiers, status, and a safe error code.

## Workflow

Explicit roles are implemented as graph nodes:

```text
ingest -> extraction agent -> validation agent -> approval agent
       -> critic agent -> policy gate
          | blocker                         -> reject
          | warning/non-USD/total > 10000  -> review interrupt
          | otherwise                       -> payment agent -> finalize
```

Extraction permits one repair. Approval permits one revision after critique.
The policy gate, not the model, owns the final route. Validation invokes the
read-only inventory tool; only the payment node may invoke mock payment.

Graph state is typed and contains no source path, raw document, prompt, provider
payload, API key, or hidden reasoning. These dependencies live in runtime
context. The overall workflow deadline is 300 seconds.

## Public Types

- `RunStatus`: `queued`, `running`, `review_required`, `completed`, `rejected`,
  `failed`.
- `RunStage`: `ingest`, `extract`, `validate`, `recommend`, `review`, `pay`,
  `finalize`.
- Finding severity: `info`, `warning`, `blocking`.
- Money uses an exact decimal string and ISO currency.
- Review decisions are `approve` or `reject` with a 3-500 character reason.

## SQLAlchemy and SQLite

SQLAlchemy 2.0 typed ORM models define `schema_migrations` and five domain tables.
`Base.metadata.create_all()` is repeatable, and SQLite dialect inserts seed
inventory idempotently. There is no first-party handwritten SQL or Alembic layer.

| Table | Responsibility |
| --- | --- |
| `inventory_items` | Item code, display name, non-negative stock, JSON aliases |
| `agent_runs` | Source metadata, provider profile, status/stage, safe error, timestamps |
| `run_results` | Typed JSON invoice, findings, recommendation, review, loop counts |
| `payments` | One idempotent mock payment per run |
| `run_events` | Append-only sanitized timeline ordered by event ID |

Three repositories own persistence: inventory; runs/results/events; payments.
Non-failed runs are unique by content hash, provider, and model. Failed content
may create a new run. Staged files are deleted after every terminal outcome.

`InvoiceProcessingService` owns one `Database`. Its injected `SessionContext`
opens a short-lived session per repository method, commits successful writes,
rolls back exceptions, and always closes. Repositories never receive database
paths, create engines, or retain sessions. The engine uses `NullPool`, a
five-second driver timeout, `IMMEDIATE` write locking, and Python's SQLite
connection configuration API for foreign keys.

LangGraph's `SqliteSaver` keeps its separately owned raw checkpoint connection;
first-party graph code does not execute checkpoint SQL. Service cleanup closes
that graph connection before disposing the SQLAlchemy engine and is safe twice.

## Extraction and Validation

- JSON, CSV, and XML use deterministic loaders.
- TXT and text-bearing PDF use the configured provider.
- Encrypted, empty, image-only, and over-limit PDFs fail explicitly.
- Missing values remain missing unless a documented normalization applies.
- The supplied CSV dialect defaults missing currency to configured USD and emits
  `DEFAULT_CURRENCY_APPLIED` as `info`.
- Exact aliases and parenthetical item descriptors emit
  `ITEM_ALIAS_NORMALIZATION` as `info`.
- OCR-like corrections emit `OCR_NORMALIZATION` as `warning`.
- Repeated normalized items are aggregated before inventory comparison.
- Unknown, zero-stock, excessive, missing, negative, invalid-date, suspicious
  payment language, and total-mismatch findings are blocking.

## Providers

`APP_LLM_PROVIDER=offline` is the default. It is deterministic, network-free,
and supports every supplied fixture. `grok` is the optional live provider and
requires `XAI_API_KEY`; it never silently falls back.

Grok uses the OpenAI SDK Responses API, strict Pydantic output, `store=False`, a
45-second request timeout, one adapter-level transient retry, and SDK retries
disabled. Provider-hosted tools are disabled. The runtime resolves the provider
recorded on each run through a provider registry.

## Safety and Observability

Generated staging paths never use client filenames. Logs and events may include
run ID, stage, status, safe codes, counts, provider/model, and duration, but not
raw documents, paths, vendor/item/amount details, prompts, provider payloads, or
secrets. All payment and review transitions are server-owned and idempotent.

## Non-Goals

No failed-run retry, source-retention subsystem, OpenAI adapter, authentication,
cloud deployment, image OCR, live bank/inventory service, FX conversion, or
inventory mutation is included.
