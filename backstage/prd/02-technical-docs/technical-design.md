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

Aggregate-focused SQLAlchemy 2.0 typed ORM modules under
`backend/app/infrastructure/db/models/` define `schema_migrations` and five domain
tables on one shared declarative base.
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
may create a new run. Staged files are deleted after every terminal outcome, and
an upload not durably owned by a run is removed when persistence fails.

The composition root at `backend/app/bootstrap/invoice_runtime.py` owns one
`Database` and injects its `SessionContext`
into the repositories used by the focused invoice intake, execution, review,
and query services behind `InvoiceProcessingService`. The API composition
root also binds queue dispatch to `RunApplicationService`, keeping HTTP routes
free of repository and Celery orchestration. Each repository method opens a
short-lived session, commits successful writes, rolls back exceptions, and
always closes. Repositories never receive database paths, create engines, or
retain sessions. The engine uses `NullPool`, a
five-second driver timeout, `IMMEDIATE` write locking, and Python's SQLite
connection configuration API for foreign keys.

Repository/provider/document/queue contracts live under `backend/app/ports`.
Business validation and approval policies live under `backend/app/domain`.
Validation rules are grouped under `domain.validation` by rule family:
extraction feedback, finding construction and ordering, invoice integrity and
reconciliation, and inventory normalization and stock checks.
Concrete database, document, model-provider, graph-checkpoint, and queue adapters
live under `backend/app/infrastructure`; services depend on ports rather than
those concrete modules.

LangGraph's `SqliteSaver` keeps its separately owned raw checkpoint connection;
first-party graph code does not execute checkpoint SQL. Queued execution is
atomically claimed once, and guarded transitions prevent a late writer from
regressing terminal state. Service cleanup closes the graph, cached live-provider
clients, and SQLAlchemy engine once.

## Extraction and Validation

- JSON, CSV, and XML use deterministic loaders.
- TXT and text-bearing PDF use the configured provider.
- Encrypted, empty, image-only, and over-limit PDFs fail explicitly.
- Missing values remain missing unless a documented normalization applies;
  JSON/XML missing currency is blocking rather than inferred.
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

Grok uses one cached client per provider/model profile, the OpenAI SDK Responses
API, strict Pydantic output, `store=False`, a 45-second request timeout, one
adapter-level transient retry, and SDK retries disabled. Provider-hosted tools are
disabled. Static policy stays in trusted instructions; document and repair values
are sent only as untrusted input. The runtime resolves the provider recorded on
each run through an owned provider registry backed by named provider factories.
Provider instances are cached per profile and any provider that exposes
`close()` is released idempotently.

Document ingestion lives under `infrastructure.documents`, with format-specific
adapters behind an immutable suffix registry. Its loader facade keeps file limits
and error contracts stable while JSON, CSV, XML, TXT, and PDF parsing remain
independently testable. Deterministic approval routing remains business logic
under `domain.policies`; it is not treated as a generic utility.

## Safety and Observability

Generated staging paths never use client filenames. Logs and events may include
run ID, stage, status, safe codes, counts, provider/model, and duration, but not
raw documents, paths, vendor/item/amount details, prompts, provider payloads, or
secrets. All payment and review transitions are server-owned and idempotent.

## Non-Goals

No failed-run retry, source-retention subsystem, OpenAI adapter, authentication,
cloud deployment, image OCR, live bank/inventory service, FX conversion, or
inventory mutation is included.
