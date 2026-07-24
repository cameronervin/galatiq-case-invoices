# Interfaces and Operations

## CLI

```bash
uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
```

`--timeout-seconds` defaults to 300. The CLI prints one safe `RunDetail`. Exit
codes are `0` for completed/rejected/review-required, `2` for invalid input, `3`
for provider configuration, `5` for workflow failure, and `6` for timeout.

Optional live mode:

```bash
APP_LLM_PROVIDER=grok APP_LLM_MODEL=grok-4.5 XAI_API_KEY=your_key \
  uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
```

## HTTP API

All routes use `/api/v1`:

| Method | Path | Contract |
| --- | --- | --- |
| `GET` | `/health` | Process health |
| `POST` | `/runs` | `202` new queued run; `200` same-profile duplicate |
| `GET` | `/runs?limit=20` | Newest runs; limit 1-50 |
| `GET` | `/runs/{run_id}` | Public run detail |
| `POST` | `/runs/{run_id}/review` | Store and queue approve/reject resume |

There is no retry endpoint, offset pagination, total count, or status filter.
Errors use a stable code, safe message, and optional run ID. Public contracts do
not expose paths, prompts, keys, provider payloads, documents, or hidden reasoning.
Upload validation distinguishes `EMPTY_FILE`, `UNSUPPORTED_FILE_TYPE`, and
`FILE_TOO_LARGE`; the last uses the configured effective byte limit.

## Celery contract

The worker has execute and resume tasks. Each receives only a `run_id` keyword
argument, loads authoritative state through the service, and returns only
`{run_id, status, error_code}`. Celery is delivery infrastructure; it does not
run the broker-free CLI and it does not store complete business state in Valkey.

## Frontend and OpenAPI

The Next.js workspace supports upload, newest-20 navigation, selected-run polling,
invoice and finding inspection, timeline, human review, and terminal outcomes.
Polling ignores stale selection responses and retries transient read failures. A
review saved during a queue outage exposes an identical worker-resume redispatch;
failed workflow runs still have no retry control. Payment copy always says the
payment is simulated.

Transport, runtime response decoding, workspace orchestration, and run-detail
presentation are separate modules. Runtime decoders reject malformed nested API
responses before they reach components, and list/review state is keyed so stale
requests cannot regress a newer run or disable an unrelated selection.

`frontend/openapi.json` is a checked-in generated contract snapshot, not a runtime
dependency. `make generate-api-types` intentionally refreshes the snapshot and
`src/types/generated-api.ts`; `make check-generated` compares both with temporary
fresh outputs and fails on drift without rewriting the worktree.

Validate the UI with:

```bash
make check-generated
make test-frontend
make lint-frontend
make typecheck-frontend
make build-frontend
```

## Local startup

Prerequisites are Python 3.12+, `uv`, Node.js 20+, and `pnpm`. Docker is needed
only for the Valkey-backed worker/workspace path.

Install and configure:

```bash
uv sync
pnpm install
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

For the optional workspace, run each command in its own terminal:

```bash
make broker-up
make dev-worker
make dev-backend
make dev-frontend
```

Open `http://localhost:3000`; FastAPI is at `http://127.0.0.1:8000` and its
interactive OpenAPI page is `/docs`.

## Execute-and-review worker smoke test

Use one clean `APP_DATABASE_PATH` and `APP_UPLOAD_DIR` shared by the backend and
worker processes, then start Valkey, the worker, and the backend as above.

1. Upload `invoice_1001.txt`, poll its detail URL to `completed`, and confirm one
   `PAYMENT_SUCCEEDED` event and one mock payment.
2. Upload `invoice_1012.txt`, poll to `review_required`, then submit
   `{"decision":"approve","reason":"Reviewed the documented OCR warning."}` to
   `/api/v1/runs/{run_id}/review`.
3. Poll the review run to `completed`; confirm the persisted review, one mock
   payment, and one `PAYMENT_SUCCEEDED` event.
4. Stop the backend and worker, then run `make broker-down`.

This exercises real Valkey delivery while proving that business state is read
back from SQLite rather than task results.

## Configuration

The main settings are `APP_DATABASE_PATH`, `APP_UPLOAD_DIR`,
`APP_MAX_UPLOAD_BYTES`, `APP_DEFAULT_CURRENCY`,
`APP_WORKFLOW_TIMEOUT_SECONDS`, broker/result URLs, provider/model, and
`XAI_API_KEY` for Grok. Frontend API origin uses `NEXT_PUBLIC_API_BASE_URL`.
Defaults are listed in [.env.example](../../.env.example).

## Demo scenarios and scope

- Clean: `invoice_1001.txt` completes with one mock payment.
- Review/resume: `invoice_1012.txt` pauses on an OCR warning.
- Reject: `invoice_1002.txt` explains an inventory mismatch.
- Optional UI: upload the same scenarios and inspect the live audit timeline.

- **Implemented:** the CLI, five API routes, two run-ID tasks, generated frontend
  contract, workspace, and validation commands above.
- **Take-home default:** CLI is primary; the broker-backed workspace is optional
  polish and uses local processes.
- **Production follow-up:** authentication/authorization, deployment manifests,
  managed secrets, rate limits, and operational dashboards.
