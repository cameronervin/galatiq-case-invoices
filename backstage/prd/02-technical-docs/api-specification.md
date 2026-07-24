# API Specification

## Conventions

- Base path: `/api/v1`.
- JSON keys use `snake_case` to match Pydantic models.
- UUIDs and timestamps are strings; timestamps are ISO-8601 UTC.
- Money is returned as `{ "amount": "5000.00", "currency": "USD" }`.
- Routes are thin and call services; clients cannot provide status, findings,
  approval route, provider, payment state, or local file paths.
- No authentication is required for this local-only prototype.

## Common Types

```text
RunStatus = queued | extracting | validating | deciding |
            review_required | paying | completed | rejected | failed

FindingSeverity = warning | blocking
ReviewDecision = approve | reject
```

### Money

```json
{
  "amount": "5000.00",
  "currency": "USD"
}
```

### Error response

```json
{
  "error": {
    "code": "RUN_NOT_FOUND",
    "message": "The requested run was not found.",
    "request_id": "optional-request-id"
  }
}
```

Messages are safe for display. Internal exceptions, paths, provider payloads,
prompts, secrets, and invoice contents are never returned.

## Endpoint Summary

| Method | Path | Success | Purpose |
| --- | --- | --- | --- |
| GET | `/health` | `200` | Existing service health check |
| POST | `/runs` | `202` or `200` | Upload and queue, or return exact duplicate |
| GET | `/runs` | `200` | List recent runs |
| GET | `/runs/{run_id}` | `200` | Read complete public run state |
| POST | `/runs/{run_id}/review` | `202` | Resume a review-required graph |
| POST | `/runs/{run_id}/retry` | `202` | Retry an eligible failed run |

## POST `/runs`

Content type: `multipart/form-data`

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `file` | binary | Yes | Non-empty, maximum 10 MB, supported suffix/content |

The server sanitizes the original basename, writes to a generated internal path,
computes SHA-256, resolves the server-configured API provider, and calls the run
creation service.

New run response: `202 Accepted`

```json
{
  "run_id": "11111111-1111-4111-8111-111111111111",
  "status": "queued",
  "current_stage": "queued",
  "source_filename": "invoice_1001.txt",
  "deduplicated": false,
  "created_at": "2026-01-30T12:00:00Z",
  "updated_at": "2026-01-30T12:00:00Z"
}
```

Exact duplicate response: `200 OK`, same shape with `deduplicated=true` and the
existing run's current state.

Errors:

| Status | Code | Condition |
| --- | --- | --- |
| 400 | `EMPTY_FILE` | Upload contains no bytes |
| 400 | `UNSUPPORTED_FILE_TYPE` | Suffix/content is unsupported or inconsistent |
| 413 | `FILE_TOO_LARGE` | File exceeds 10 MB |
| 422 | `INVALID_UPLOAD` | Multipart field is missing or invalid |
| 503 | `PROVIDER_NOT_CONFIGURED` | Server-selected API provider lacks required configuration |
| 503 | `QUEUE_UNAVAILABLE` | Run is persisted as failed if dispatch cannot complete |

## GET `/runs`

Query parameters:

| Name | Default | Bounds | Meaning |
| --- | --- | --- | --- |
| `limit` | 20 | 1–100 | Maximum results |
| `offset` | 0 | 0+ | Pagination offset |
| `status` | omitted | RunStatus | Optional exact filter |

Response: `200 OK`

```json
{
  "items": [
    {
      "run_id": "11111111-1111-4111-8111-111111111111",
      "status": "completed",
      "current_stage": "finalize",
      "source_filename": "invoice_1001.txt",
      "created_at": "2026-01-30T12:00:00Z",
      "updated_at": "2026-01-30T12:00:05Z"
    }
  ],
  "limit": 20,
  "offset": 0,
  "total": 1
}
```

## GET `/runs/{run_id}`

Response: `200 OK`

```json
{
  "run_id": "11111111-1111-4111-8111-111111111111",
  "status": "review_required",
  "current_stage": "human_review",
  "source_filename": "invoice_1014.xml",
  "attempt_count": 1,
  "created_at": "2026-01-30T12:00:00Z",
  "updated_at": "2026-01-30T12:00:05Z",
  "invoice": {
    "invoice_number": "INV-1014",
    "revision": null,
    "vendor_name": "TechParts International",
    "invoice_date": "2026-01-26",
    "due_date": "2026-02-26",
    "total": {"amount": "4125.00", "currency": "EUR"},
    "items": [
      {
        "line_number": 1,
        "source_name": "WidgetA",
        "normalized_item_code": "WidgetA",
        "quantity": 4,
        "unit_price": {"amount": "225.00", "currency": "EUR"},
        "line_total": {"amount": "900.00", "currency": "EUR"}
      }
    ],
    "extraction_confidence": "high"
  },
  "findings": [
    {
      "code": "UNSUPPORTED_CURRENCY",
      "severity": "warning",
      "field_path": "currency",
      "item_line_number": null,
      "message": "EUR invoices require human review."
    }
  ],
  "approval": {
    "route": "review",
    "reason_codes": ["UNSUPPORTED_CURRENCY"],
    "summary": "Inventory and totals are valid; currency requires review.",
    "reflection_count": 1,
    "decided_by": "policy"
  },
  "payment": null,
  "events": [],
  "error": null
}
```

Nullable nested sections are omitted or `null` until their stage completes.

Errors: `404 RUN_NOT_FOUND`, `422 INVALID_RUN_ID`.

## POST `/runs/{run_id}/review`

Request:

```json
{
  "decision": "approve",
  "reason": "Inventory is valid; approve payment in the original EUR amount."
}
```

Rules:

- `decision` is `approve` or `reject`.
- `reason` is trimmed and 3–500 characters.
- Run must be `review_required` with a matching durable interrupt.
- Service persists the human decision before dispatching the JSON-safe resume task.
- Approval resumes toward mock payment; rejection resumes toward rejection.

Response: `202 Accepted` with the current `RunSummary`.

Errors:

| Status | Code | Condition |
| --- | --- | --- |
| 404 | `RUN_NOT_FOUND` | Unknown run |
| 409 | `RUN_NOT_REVIEWABLE` | Run is not `review_required` |
| 409 | `REVIEW_ALREADY_DECIDED` | A valid decision already exists |
| 422 | `INVALID_REVIEW` | Invalid decision or reason |
| 503 | `QUEUE_UNAVAILABLE` | Resume dispatch failed; persisted state remains reviewable |

## POST `/runs/{run_id}/retry`

No request body.

Rules:

- Only `failed` is eligible.
- Source must still be retained and pass an existence/hash check.
- Service increments attempt count, clears public error, appends a retry event,
  sets queued status, and then dispatches.
- Existing decision/payment history and idempotency keys remain intact.

Response: `202 Accepted` with `RunSummary`.

Errors: `404 RUN_NOT_FOUND`, `409 RUN_NOT_RETRYABLE`,
`409 SOURCE_UNAVAILABLE`, `503 QUEUE_UNAVAILABLE`.

## State and Error Mapping

| Internal condition | Public status | Public code |
| --- | --- | --- |
| Provider timeout after bounded retries | failed | `PROVIDER_TIMEOUT` |
| Provider refusal/invalid schema | failed | `PROVIDER_INVALID_OUTPUT` |
| Unsupported/encrypted/image-only PDF | failed | `UNSUPPORTED_PDF` |
| Malformed structured document | failed | `MALFORMED_DOCUMENT` |
| Blocking business validation | rejected | Finding reason codes |
| Payment adapter failure | failed | `PAYMENT_FAILED` |
| Graph recursion limit | failed | `WORKFLOW_LIMIT_EXCEEDED` |

## CLI Contract

The required command remains:

```bash
python main.py --invoice_path=data/invoices/invoice_1001.txt
```

Add optional `--no-wait` and `--timeout-seconds` (default 180, positive integer).
CLI runs always set source origin/provider to `cli`/`grok`. The command prints one
JSON object to stdout for queued/final/review state and structured errors to
stderr.

Exit codes:

| Code | Meaning |
| --- | --- |
| 0 | Successfully reached queued (`--no-wait`), completed, rejected, or review-required |
| 2 | Invalid invoice input |
| 3 | Configuration error, including missing Grok key |
| 4 | Dispatch failure |
| 5 | Processing failed |
| 6 | Wait timeout; run may continue asynchronously |

