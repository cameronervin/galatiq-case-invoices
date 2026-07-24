# Data Model Specification

## Purpose

SQLite is the source of truth for inventory, application runs, normalized
invoices, findings, decisions, payments, and audit events. Valkey contains only
Celery queue/result metadata. LangGraph checkpoint tables are package-managed in
SQLite and are not application query models.

## Storage Rules

- Store UUIDs and ISO-8601 UTC timestamps as text.
- Store money as integer minor units (`*_cents`) plus an ISO currency code.
- Use parameterized queries, foreign keys, WAL mode, and a busy timeout.
- Never store raw model responses, hidden reasoning, prompts, API keys, or full
  invoice contents in application tables.
- `source_path` is internal and never appears in API/CLI response models.
- Inventory is reference data; payment does not decrement stock.
- Migrations are versioned and idempotent. Generated `.db` files are ignored.

## Enumerations

### Run status

`queued`, `extracting`, `validating`, `deciding`, `review_required`, `paying`,
`completed`, `rejected`, `failed`

Terminal statuses: `completed`, `rejected`, `failed`.

### Finding severity

`warning`, `blocking`

### Decision route

`approve`, `review`, `reject`

### Payment status

`pending`, `succeeded`, `failed`

## Application Schema

Implement equivalent versioned SQL. Table/column names below are the contract.

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory_items (
    item_code TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    stock INTEGER NOT NULL CHECK (stock >= 0),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS inventory_aliases (
    normalized_alias TEXT PRIMARY KEY,
    item_code TEXT NOT NULL REFERENCES inventory_items(item_code)
);

CREATE TABLE IF NOT EXISTS agent_runs (
    run_id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    source_filename TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_format TEXT NOT NULL CHECK (
        source_format IN ('pdf', 'txt', 'json', 'csv', 'xml')
    ),
    source_origin TEXT NOT NULL CHECK (source_origin IN ('cli', 'api')),
    source_size_bytes INTEGER NOT NULL CHECK (source_size_bytes > 0),
    source_retained INTEGER NOT NULL DEFAULT 1 CHECK (source_retained IN (0, 1)),
    provider_name TEXT NOT NULL,
    provider_model TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'queued', 'extracting', 'validating', 'deciding',
        'review_required', 'paying', 'completed', 'rejected', 'failed'
    )),
    current_stage TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 1 CHECK (attempt_count >= 1),
    error_code TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_created_at
    ON agent_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status
    ON agent_runs(status, updated_at DESC);

CREATE TABLE IF NOT EXISTS invoices (
    run_id TEXT PRIMARY KEY REFERENCES agent_runs(run_id) ON DELETE CASCADE,
    invoice_number TEXT,
    revision TEXT,
    vendor_name TEXT,
    invoice_date TEXT,
    due_date TEXT,
    currency TEXT,
    subtotal_cents INTEGER,
    tax_cents INTEGER,
    shipping_cents INTEGER,
    total_cents INTEGER,
    payment_terms TEXT,
    extraction_confidence TEXT CHECK (
        extraction_confidence IN ('high', 'medium', 'low')
    ),
    extracted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoice_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES invoices(run_id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL CHECK (line_number >= 1),
    source_name TEXT,
    normalized_item_code TEXT REFERENCES inventory_items(item_code),
    quantity INTEGER,
    unit_price_cents INTEGER,
    line_total_cents INTEGER,
    normalization_note TEXT,
    UNIQUE (run_id, line_number)
);

CREATE INDEX IF NOT EXISTS idx_invoice_items_run_id
    ON invoice_items(run_id, line_number);

CREATE TABLE IF NOT EXISTS validation_findings (
    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES agent_runs(run_id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL CHECK (sequence >= 1),
    code TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('warning', 'blocking')),
    field_path TEXT,
    item_line_number INTEGER,
    safe_message TEXT NOT NULL,
    expected_json TEXT,
    actual_json TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (run_id, sequence)
);

CREATE TABLE IF NOT EXISTS approval_decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES agent_runs(run_id) ON DELETE CASCADE,
    version INTEGER NOT NULL CHECK (version >= 1),
    proposed_route TEXT NOT NULL CHECK (proposed_route IN ('approve', 'review', 'reject')),
    final_route TEXT NOT NULL CHECK (final_route IN ('approve', 'review', 'reject')),
    reason_codes_json TEXT NOT NULL,
    safe_summary TEXT NOT NULL,
    reflection_count INTEGER NOT NULL CHECK (reflection_count BETWEEN 0 AND 2),
    decided_by TEXT NOT NULL CHECK (decided_by IN ('agent', 'policy', 'human')),
    reviewer_reason TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (run_id, version)
);

CREATE TABLE IF NOT EXISTS payment_attempts (
    payment_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE REFERENCES agent_runs(run_id) ON DELETE CASCADE,
    idempotency_key TEXT NOT NULL UNIQUE,
    vendor_name TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    currency TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'succeeded', 'failed')),
    mock_reference TEXT,
    error_code TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES agent_runs(run_id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL CHECK (sequence >= 1),
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    code TEXT NOT NULL,
    safe_message TEXT NOT NULL,
    duration_ms INTEGER CHECK (duration_ms IS NULL OR duration_ms >= 0),
    created_at TEXT NOT NULL,
    UNIQUE (run_id, sequence)
);

CREATE INDEX IF NOT EXISTS idx_run_events_run_id
    ON run_events(run_id, sequence);
```

## Seed Data

```sql
INSERT OR IGNORE INTO inventory_items (item_code, display_name, stock) VALUES
    ('WidgetA', 'Widget A', 15),
    ('WidgetB', 'Widget B', 10),
    ('GadgetX', 'Gadget X', 5),
    ('FakeItem', 'Fake Item', 0);

INSERT OR IGNORE INTO inventory_aliases (normalized_alias, item_code) VALUES
    ('widgeta', 'WidgetA'),
    ('widget a', 'WidgetA'),
    ('widgetb', 'WidgetB'),
    ('widget b', 'WidgetB'),
    ('gadgetx', 'GadgetX'),
    ('gadget x', 'GadgetX'),
    ('fakeitem', 'FakeItem'),
    ('fake item', 'FakeItem');
```

Alias keys are lowercase with surrounding whitespace collapsed. No fuzzy match
may silently convert an unknown item; uncertain matches remain unknown findings.

## Entity Relationships

```text
inventory_items 1 ── * inventory_aliases

agent_runs 1 ── 0..1 invoices 1 ── * invoice_items
agent_runs 1 ── * validation_findings
agent_runs 1 ── * approval_decisions
agent_runs 1 ── 0..1 payment_attempts
agent_runs 1 ── * run_events
```

## Repository Boundaries

| Repository | Responsibilities |
| --- | --- |
| `InventoryRepository` | Seed, normalize aliases, return stock snapshots; never mutate stock during runs |
| `AgentRunRepository` | Create/deduplicate runs, transitions, retries, source retention, recent/detail queries |
| `InvoiceRepository` | Atomically replace normalized invoice and items for a run |
| `FindingRepository` | Atomically replace ordered findings for validation attempts |
| `DecisionRepository` | Append versioned agent/policy/human decisions |
| `PaymentRepository` | Create-or-return idempotent payment attempt and update status |
| `RunEventRepository` | Append monotonic sanitized events |

Public services depend on repository protocols, not SQLite connections or rows.

## Transition Invariants

- Only the service/worker may advance run status.
- `review_required` can transition only to `paying` or `rejected` after a valid
  persisted human decision.
- `paying` can transition only to `completed` or `failed`.
- A blocking finding prevents all transitions to `paying`.
- `retry` is valid only from `failed`, increments `attempt_count`, appends an
  event, and returns to `queued` without deleting prior audit records.
- Exact content hashing is global across filenames and submission surfaces.

## Retention

- Stage source files beneath an ignored application directory with generated
  filenames, never user-controlled paths.
- Retain source while queued, processing, review-required, or retry-eligible.
- Delete source after completed/rejected and mark `source_retained=0`.
- Failed sources expire after 24 hours. Cleanup runs opportunistically at startup
  and before new uploads; expired retries return `SOURCE_UNAVAILABLE`.
- Retain normalized records and audit data for the lifetime of this prototype.

## LangGraph Checkpoints

Use the supported SQLite checkpointer package. Compile the worker graph with the
checkpointer and invoke it with `thread_id=run_id`. Treat checkpoint tables as an
internal LangGraph schema: application repositories must not query or modify them.

