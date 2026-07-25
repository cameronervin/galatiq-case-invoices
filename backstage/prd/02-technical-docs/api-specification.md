# API Specification

## Conventions

Base path is `/api/v1`; JSON uses `snake_case`. UUIDs and UTC timestamps are
strings. Money is `{ "amount": "5000.00", "currency": "USD" }`. Clients cannot
set provider, status, stage, findings, policy, review state, or payment state.

## Endpoints

| Method | Path | Success | Purpose |
| --- | --- | --- | --- |
| GET | `/health` | `200` | Service health |
| POST | `/runs` | `202` or `200` | Upload/queue or return same-profile duplicate |
| GET | `/runs?limit=20` | `200` | Newest runs, limit 1-50 |
| GET | `/runs/{run_id}` | `200` | Complete public run state |
| POST | `/runs/{run_id}/review` | `202` | Persist and dispatch review resume |

There is no retry endpoint, offset pagination, total count, or status filter.

## Public Models

`RunSummary` contains `run_id`, `source_filename`, `status`, `stage`, `created_at`,
and `updated_at`. `RunCreationResponse` adds `deduplicated`. `RunDetail` contains
the summary fields plus nullable `invoice`, `recommendation`, `review`, `payment`,
and `error`, and arrays of `findings` and `events`.

An error response is:

```json
{"error":{"code":"RUN_NOT_FOUND","message":"The requested run was not found.","run_id":null}}
```

## POST `/runs`

Accept one multipart `file`: non-empty, at most 10 MB, and one of PDF, TXT, JSON,
CSV, or XML after suffix/content validation. The server stages to a generated
path, hashes content, and assigns the configured provider/model.

- New run: `202`, `deduplicated=false`, then queue only its run ID.
- Existing non-failed same content/provider/model: `200`,
  `deduplicated=true`, without queueing.
- Queue failure: mark the run failed, delete its source, and return
  `503 QUEUE_UNAVAILABLE` with the run ID.

Input errors use `EMPTY_FILE`, `FILE_TOO_LARGE`, `UNSUPPORTED_FILE_TYPE`, or
`INVALID_UPLOAD`. Missing provider configuration uses
`PROVIDER_NOT_CONFIGURED`.

## GET `/runs`

`limit` defaults to 20 and must be 1-50. Return
`{"items": [RunSummary, ...]}` ordered by creation time and run ID descending.

## GET `/runs/{run_id}`

Return `RunDetail`. Use `404 RUN_NOT_FOUND` for an unknown UUID and FastAPI's
validation response for malformed UUID input. Source paths and internal/provider
payloads are absent from the model.

## POST `/runs/{run_id}/review`

Request:

```json
{"decision":"approve","reason":"Inventory is valid; approve simulated payment."}
```

The run must be `review_required`; reason is trimmed and 3-500 characters. The
service atomically stores the first decision with `resume_pending=true`, then
queues a run-ID-only resume task.

- First decision: `202`.
- Repeated identical decision while resume is pending: redispatch and return
  `202` without changing stored review.
- Different or completed decision: `409 REVIEW_ALREADY_DECIDED`.
- Queue failure: keep `resume_pending=true` and return `503 QUEUE_UNAVAILABLE`;
  repeating the identical request retries dispatch.

The worker clears `resume_pending` when resume begins.

## Celery Contract

Execute and resume tasks accept `{ "run_id": "uuid" }`. Results contain only
`run_id`, status, and optional safe error code. Valkey is never queried for run
detail and never stores invoices, findings, review text, or payment details.

## CLI Contract

```bash
python main.py --invoice_path=data/invoices/invoice_1001.txt
```

The CLI executes synchronously and accepts optional `--timeout-seconds` (default
300, positive). Rich-formatted output is the default; `--format json` prints one
compact `RunDetail` JSON object. `--show-events` expands the pretty timeline,
while `--no-color` and `NO_COLOR` disable styles. Both `--invoice_path` and
`--invoice-path` are accepted. Exit codes are `0` for
completed/rejected/review-required, `2` invalid input, `3` configuration, `5`
workflow failure, and `6` timeout.
