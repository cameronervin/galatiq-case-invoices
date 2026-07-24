# Master User Stories

This file is the canonical story catalog for the first implementation. Every
story must appear in the master implementation plan and in at least one detailed
phase.

## Epic 1 — Submission and Tracking

### US-01 — Submit an invoice from the CLI

**As a** member of accounts payable  
**I want** to submit a local invoice with the documented command  
**So that** I can receive a structured processing result without using the UI.

Acceptance criteria:

1. `--invoice_path` accepts existing PDF, TXT, JSON, CSV, or XML files.
2. Unsupported, missing, or oversized files fail before queueing with structured errors.
3. CLI-created runs require valid Grok configuration and never silently select OpenAI.
4. The default command waits for `completed`, `rejected`, `review_required`, `failed`, or timeout.
5. Output is one JSON-safe result containing the run ID and public run state.
6. Public output exposes the original filename but not the resolved local path.

### US-02 — Upload an invoice in the workspace

**As a** member of accounts payable  
**I want** to upload a supported invoice in the browser  
**So that** I can start processing without terminal access.

Acceptance criteria:

1. The upload control accepts PDF, TXT, JSON, CSV, and XML.
2. The client shows type and size errors before submission when detectable.
3. The API revalidates the file and creates the authoritative run ID.
4. A new run returns `202`; an exact duplicate returns `200` with `deduplicated=true`.
5. The UI moves immediately to the queued run state after a successful response.

### US-03 — Track current and recent runs

**As a** member of accounts payable  
**I want** to see current progress and recent runs  
**So that** I know what needs attention and what has finished.

Acceptance criteria:

1. Recent runs are ordered newest first with bounded pagination.
2. Each run shows filename, status, current stage, and timestamps.
3. Active runs refresh every two seconds and stop polling in terminal or review states.
4. Run detail includes normalized invoice data, findings, decision, payment, and events when present.
5. Unknown run IDs return an explicit not-found state.

### US-04 — Deduplicate exact submissions

**As a** member of accounts payable  
**I want** to avoid processing an identical invoice twice  
**So that** retries and accidental resubmissions cannot duplicate payment.

Acceptance criteria:

1. A SHA-256 content hash is computed before run creation.
2. Identical content reuses the original run regardless of filename.
3. Changed content, including the revised INV-1004 fixture, creates a new run.
4. Deduplicated responses identify that reuse occurred.
5. Payment idempotency remains enforced when a run is replayed or redelivered.

### US-05 — Retry a failed run

**As a** member of accounts payable  
**I want** to retry a failed run while its source remains available  
**So that** a transient provider or worker failure does not require re-entry.

Acceptance criteria:

1. Only `failed` runs may be retried.
2. Retry returns `409` when the run state or retained source is ineligible.
3. The same run ID is reused and an attempt counter is incremented.
4. Payment idempotency prevents a repeated payment if failure occurred after payment.
5. Retry activity appears in the run event timeline.

## Epic 2 — Extraction and Validation

### US-06 — Extract a normalized invoice

**As a** member of accounts payable  
**I want** to extract consistent fields from every supported format  
**So that** downstream rules do not depend on document layout.

Acceptance criteria:

1. Output includes invoice number, revision when present, vendor, invoice date, due date, currency, items, subtotal, tax, shipping, and total.
2. Money is normalized without binary floating-point arithmetic.
3. JSON, CSV, and XML use deterministic loaders; TXT and PDF use extracted text plus the configured model.
4. PDF handling supports text-bearing documents and rejects encrypted, image-only, or over-page-limit inputs explicitly.
5. Structured model output is validated against Pydantic schemas before use.
6. Raw source text and raw model responses are not placed in graph state or logs.

### US-07 — Surface missing or uncertain extraction

**As a** member of accounts payable  
**I want** to see missing and corrected fields explicitly  
**So that** the system never hides assumptions in financial data.

Acceptance criteria:

1. Missing required values remain `null` and generate coded findings.
2. OCR-like corrections and item alias normalizations generate visible warnings.
3. Extraction assessment may request at most two repair attempts.
4. Repair receives only bounded feedback and cannot invent unsupported values.
5. Exhausted repair transitions to a sanitized failure or blocking finding.

### US-08 — Validate inventory availability

**As a** member of accounts payable  
**I want** to validate invoice items against mock inventory  
**So that** unknown, unavailable, or excessive quantities are stopped.

Acceptance criteria:

1. Item aliases normalize before lookup, including `Widget A` and `Gadget X`.
2. Repeated lines for the same normalized item are aggregated before stock comparison.
3. Unknown items, zero-stock items, and quantities above stock are blocking findings.
4. Findings include stable codes, affected fields/items, expected values, and actual values.
5. Validation never decrements inventory.

### US-09 — Validate integrity and suspicious data

**As a** member of accounts payable  
**I want** to detect malformed totals, dates, quantities, and payment language  
**So that** invalid or suspicious invoices cannot reach payment.

Acceptance criteria:

1. Vendor, due date, at least one item, positive quantities, positive prices, and positive total are required.
2. Due date must be an absolute date on or after the invoice date.
3. Line totals, subtotal, tax, shipping, and total reconcile within one cent when supplied.
4. Relative or unparseable dates are blocking findings.
5. Urgent wire/payment language creates a coded risk finding without persisting the raw text.
6. Validation results are deterministic and do not depend on the approval model.

## Epic 3 — Approval and Payment

### US-10 — Produce and critique an approval recommendation

**As a** VP reviewer  
**I want** to receive a reasoned and self-checked recommendation  
**So that** the system demonstrates judgment without bypassing policy.

Acceptance criteria:

1. The approval proposal uses normalized invoice data and coded findings only.
2. A critique checks completeness, rule consistency, and unsupported claims.
3. Proposal revision is bounded to two attempts and a graph recursion limit.
4. Stored output contains a concise summary, route, reason codes, and iteration count.
5. Raw reasoning traces and provider payloads are never stored or returned.
6. Deterministic policy overrides any model recommendation that violates a blocking rule.

### US-11 — Review an exception

**As a** VP reviewer  
**I want** to approve or reject invoices requiring judgment  
**So that** high-risk decisions remain human-controlled and auditable.

Acceptance criteria:

1. Clean USD totals above $10,000 enter `review_required`.
2. Warning findings and non-USD currency enter `review_required`.
3. Blocking findings reject directly and cannot be manually overridden.
4. LangGraph pauses with a durable, JSON-safe interrupt keyed by run ID.
5. Review requires `approve` or `reject` plus a 3–500 character reason.
6. Approval clearly confirms that mock payment is the next action.
7. Repeated or out-of-state review requests return `409`.

### US-12 — Execute an idempotent mock payment

**As a** member of accounts payable  
**I want** to record payment only after valid approval  
**So that** the workflow completes safely without touching a real bank.

Acceptance criteria:

1. Only a server-owned approved state may call the payment tool.
2. The tool records vendor, original amount, currency, timestamp, status, and mock reference.
3. A unique per-run idempotency key prevents duplicate payment attempts.
4. Automatic payment applies only to clean USD totals at or below $10,000.
5. A reviewed non-USD invoice retains its original currency; no FX value is created.
6. Payment failure results in `failed` with a sanitized code and retry-safe record.

### US-13 — Record rejection with reasoning

**As a** member of accounts payable  
**I want** to see why an invoice was rejected  
**So that** I can correct the source or explain the outcome.

Acceptance criteria:

1. Blocking validation failures route to `rejected` without payment.
2. Human rejection routes to `rejected` without payment.
3. The result includes stable reason codes and a concise safe summary.
4. Rejection events record whether the source was policy or human review.
5. Terminal rejection removes the staged source according to retention policy.

## Epic 4 — Operations and Workspace

### US-14 — Inspect an audit timeline

**As a** local operator  
**I want** to inspect sanitized workflow events  
**So that** I can diagnose progress and explain outcomes.

Acceptance criteria:

1. Events record sequence, run ID, stage, status, safe code, timestamp, and duration when available.
2. Stage transitions are persisted before public status changes are reported.
3. Logs use the same stable codes but omit document content and financial details.
4. Celery result storage is never treated as run history.
5. Events remain ordered after retry and review resume.

### US-15 — Configure a replaceable model provider

**As a** local operator  
**I want** to configure Grok or OpenAI behind one contract  
**So that** development can switch providers without changing workflow rules.

Acceptance criteria:

1. Provider selection, model, keys, timeouts, and retry limits come from environment settings.
2. CLI-created runs always select Grok and require `XAI_API_KEY`.
3. API/UI development may select OpenAI and require `OPENAI_API_KEY`.
4. Provider selection cannot be supplied by an untrusted API client.
5. Requests disable provider-side storage where supported.
6. Tests use a fake provider and never need network access or paid credentials.

### US-16 — Use an accessible processing workspace

**As a** member of accounts payable or a VP reviewer  
**I want** to understand every workflow state and action  
**So that** I can operate the prototype confidently.

Acceptance criteria:

1. Empty, uploading, queued, processing, review, rejected, failed, and completed states are visually distinct.
2. Upload and review controls have accessible names, keyboard operation, and visible focus.
3. Findings and reasons use plain language alongside stable codes.
4. Payment approval requires an explicit confirmation step.
5. Layout remains usable on narrow and desktop viewports.
6. Reduced-motion preferences are respected.
7. No raw prompts, provider payloads, local paths, or unnecessary sensitive details are displayed.

## Cross-Epic Edge Cases

| Case | Required behavior |
| --- | --- |
| Exact file resubmitted under another filename | Return the existing run with `deduplicated=true` |
| Changed INV-1004 revision | Create a new run because content hash changed |
| Worker delivers the same task twice | Reuse persisted state and payment idempotency key |
| Provider times out | Bound retries, mark sanitized failure, permit eligible retry |
| Review submitted twice | First valid decision wins; later request returns `409` |
| Clean total exactly $10,000.00 | Automatic mock payment |
| Clean total $10,000.01 | Human review |
| Current date is after fixture due date | Do not reject solely for being overdue relative to the system clock |
