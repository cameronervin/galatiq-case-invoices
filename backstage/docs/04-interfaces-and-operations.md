# Interfaces and Operations

## Prerequisites and install

- Broker-free CLI: Python 3.12+ and `uv`.
- Optional workspace: Node.js 20.9+, `pnpm`, and Docker in addition to the CLI
  prerequisites.

Install from the repository root:

```bash
uv sync
pnpm install
```

SQLite tables and inventory seed data are created automatically. The offline
defaults work without environment files. To make local configuration explicit:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

## CLI

```bash
uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
```

Both `--invoice_path` and `--invoice-path` are accepted. Pretty output is the
default; `--format json` emits one compact `RunDetail`, `--show-events` expands
the pretty timeline, and `--no-color` or `NO_COLOR` disables styling.
`--timeout-seconds` defaults to 300.

```bash
uv run python main.py --invoice-path=data/invoices/invoice_1001.txt --format json
```

Exit codes are `0` for completed, rejected, or review-required; `2` for invalid
input; `3` for provider configuration; `5` for workflow failure; and `6` for
timeout. JSON mode keeps its single result on stdout and input/configuration
errors on stderr.

Optional Grok mode:

```bash
APP_LLM_PROVIDER=grok APP_LLM_MODEL=grok-4.5 XAI_API_KEY=your_key \
  uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
```

## Workspace startup

Run each command in its own terminal, in this order:

```bash
make broker-up
make dev-worker
make dev-backend
make dev-frontend
```

| Surface | Address or command |
| --- | --- |
| Frontend | `http://localhost:3000` |
| FastAPI | `http://127.0.0.1:8000` |
| OpenAPI UI | `http://127.0.0.1:8000/docs` |
| Stop Valkey | `make broker-down` |

Backend and worker must use the same `APP_DATABASE_PATH` and `APP_UPLOAD_DIR`.
The documented root-level commands share the same defaults.

## HTTP API and worker

All routes use `/api/v1`:

| Method | Path | Behavior |
| --- | --- | --- |
| `GET` | `/health` | Process health |
| `POST` | `/runs` | `202` new queued run; `200` same-profile duplicate |
| `GET` | `/runs?limit=20` | Newest runs; limit 1–50 |
| `GET` | `/runs/{run_id}` | Public run detail |
| `POST` | `/runs/{run_id}/review` | Persist and queue approve/reject resume |

Errors expose a stable code, safe message, and optional run ID. Public contracts
exclude paths, documents, prompts, credentials, provider payloads, and hidden
reasoning. There is no failed-run retry endpoint, offset pagination, total count,
or status filter.

Celery registers `invoice_processing.agent_runs.execute` and
`invoice_processing.agent_runs.resume`. Each task receives only a `run_id` and
returns `{run_id, status, error_code}`. SQLite—not Valkey task results—holds the
authoritative run.

## Frontend and OpenAPI

The Next.js workspace supports upload, newest-20 triage, selected-run polling,
invoice and finding inspection, progressively disclosed decision metadata and
workflow history, human review, and terminal outcomes. Approval uses an inline
second-step confirmation that identifies the invoice and simulated payment amount
when available. Payment language always states that payment is simulated.

Polling ignores stale selection responses and retries transient read failures. A
review saved during a queue outage offers an identical resume redispatch; failed
workflow runs have no retry control.

`frontend/openapi.json` and `src/types/generated-api.ts` are checked-in generated
contracts. `make generate-api-types` refreshes them; `make check-generated`
detects drift without rewriting the worktree.

## Execute-and-review worker smoke test

With Valkey, worker, and backend running against one clean database/upload pair:

1. Upload `data/invoices/invoice_1001.txt`, poll the returned detail URL to
   `completed`, and confirm one `PAYMENT_SUCCEEDED` event and one mock payment.
2. Upload `data/invoices/invoice_1012.txt` and poll to `review_required`.
3. Submit `{"decision":"approve","reason":"Reviewed the documented OCR warning."}`
   to `/api/v1/runs/{run_id}/review`.
4. Poll to `completed`; confirm the persisted review, one mock payment, and one
   `PAYMENT_SUCCEEDED` event.
5. Stop backend and worker, then run `make broker-down`.

This proves real queue delivery while business state is read from SQLite.

## Configuration and verification

The main settings are `APP_DATABASE_PATH`, `APP_UPLOAD_DIR`,
`APP_MAX_UPLOAD_BYTES`, `APP_DEFAULT_CURRENCY`,
`APP_WORKFLOW_TIMEOUT_SECONDS`, broker/result URLs, provider/model, and
`XAI_API_KEY` for Grok. The frontend uses `NEXT_PUBLIC_API_BASE_URL`. Defaults and
safe placeholders are in [.env.example](../../.env.example) and
[frontend/.env.example](../../frontend/.env.example).

```bash
make verify
```

This checks generated contracts, backend tests and branch coverage, Python lint,
frontend tests and lint, TypeScript types, and a production build.

## Scope boundary

- **Implemented:** broker-free CLI, five API routes, two run-ID tasks, generated
  frontend contract, review workspace, and repository verification.
- **Take-home default:** the CLI is primary; the broker-backed workspace is
  optional local polish.
- **Production follow-up:** authentication and authorization, deployments,
  managed secrets, rate limits, queue monitoring, and operational dashboards.
