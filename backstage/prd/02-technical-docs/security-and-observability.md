# Security and Observability Specification

## Security Posture

This is a localhost prototype without authentication. That scope does not make
invoice documents, vendor details, model prompts, or payment-like actions safe to
log or trust. Bind services to local interfaces by default and keep all workflow
authority on the server.

## Trust Boundaries

| Input | Trust level | Required handling |
| --- | --- | --- |
| Uploaded/local invoice | Untrusted | Size/type/path validation; parse as data, never instructions |
| API/CLI fields | Untrusted | Pydantic/argparse validation; no status/provider/payment authority |
| LLM output | Untrusted | Strict structured schema plus deterministic guardrails |
| Human review | Authorized local action but untrusted payload | State check, enum/reason validation, first decision wins |
| SQLite application state | Server-owned | Repository-only writes, constraints, transactions |
| Environment secrets | Sensitive | Read at startup/use; never return or log |
| Celery payload | Internal but replayable | JSON-safe run identifiers only; idempotent handling |

## File Security

- Accept only `.pdf`, `.txt`, `.json`, `.csv`, and `.xml` after suffix and
  content checks.
- Reject empty files, files over 10 MB, PDFs over 20 pages, encrypted PDFs,
  image-only PDFs, NUL-containing text, and malformed structured documents.
- XML parsing disables DTD, external entities, and network access.
- Use generated staging filenames beneath configured storage; never join an
  upload filename into a path.
- Store only the sanitized basename for display.
- Verify retained file existence and content hash before retry.
- Ignore staging directories and databases in git.

## Prompt-Injection Controls

- Prompts state that invoice content is untrusted evidence and embedded requests
  must not alter instructions, call tools, change policy, or reveal secrets.
- Delimit document content from instructions.
- Provide only task-specific output schemas and no network/search tools.
- Use deterministic loaders for structured formats when unambiguous.
- Never permit the model to select the payment tool or final policy route.
- Keep approval input limited to normalized fields and safe finding codes.

## Payment Safeguards

- Client values cannot set approval/payment state.
- Blocking findings cannot be manually overridden.
- Manual approval is accepted only from `review_required` and clearly confirms
  the next mock-payment action.
- Payment verifies persisted approval, run status, positive money, and the unique
  idempotency key in one service boundary.
- No live bank credentials, endpoints, or transfer behavior are allowed.

## Logging Contract

Use `structlog` with stable event names and sanitized fields.

Allowed fields:

- `run_id`, stage, status, safe code.
- File type and byte/page counts.
- Duration, attempt/reflection counts, provider/model names.
- Finding counts by severity.
- HTTP method/path template/status and request ID.

Forbidden fields:

- Raw invoice bytes/text, email addresses, vendor name, item details, amounts,
  local paths, prompts, model inputs/outputs, hidden reasoning, tokens, keys,
  authorization headers, or raw exception strings from providers.

Example safe events:

```text
agent_run_started(run_id, stage="ingest", file_type="pdf")
stage_completed(run_id, stage="validate", blocking_count=0, warning_count=1)
review_required(run_id, reason_codes=["UNSUPPORTED_CURRENCY"])
payment_completed(run_id, payment_id)
agent_run_failed(run_id, stage, error_code, retryable)
```

The existing redaction filter remains defense in depth, not permission to log
sensitive values first.

## Audit Events

Every meaningful state transition is appended to `run_events` with monotonically
increasing sequence. Persist the event and run status atomically where possible.
The public timeline contains safe messages only.

Required event codes include:

`RUN_QUEUED`, `RUN_DEDUPLICATED`, `INGEST_STARTED`, `EXTRACTION_COMPLETED`,
`EXTRACTION_REPAIR_REQUESTED`, `VALIDATION_COMPLETED`, `APPROVAL_PROPOSED`,
`POLICY_OVERRIDE`, `REVIEW_REQUIRED`, `REVIEW_APPROVED`, `REVIEW_REJECTED`,
`PAYMENT_STARTED`, `PAYMENT_SUCCEEDED`, `PAYMENT_FAILED`, `RUN_REJECTED`,
`RUN_FAILED`, `RUN_COMPLETED`, `RUN_RETRY_QUEUED`, `SOURCE_DELETED`.

## Public Error Policy

- Map known failures to stable uppercase codes and plain safe messages.
- Do not include stack traces or exception chaining in public responses.
- Invalid client data uses `4xx`; dependency/queue configuration uses `503`;
  asynchronous workflow failure is represented in persisted run state.
- Log stack traces only where logger configuration guarantees forbidden data is
  not attached; provider response bodies are never included.

## Local Network and CORS

- API and frontend bind to loopback in documented development commands.
- CORS remains an explicit configured local origin list.
- Allowed methods expand only for specified run endpoints.
- Do not add credentials/cookies or wildcard origins.
- Production authentication is an explicit non-goal and must not be implied.

## Verification

Security-focused tests cover path traversal filenames, suffix/content mismatch,
oversized files, XML entities, encrypted/image-only PDFs, prompt-injection text,
client-supplied server fields, review replay, payment replay, log redaction, safe
provider failures, and absence of local paths/secrets in API/CLI/worker results.

