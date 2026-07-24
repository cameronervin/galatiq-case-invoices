# Backend

The backend owns the typed invoice contracts, SQLAlchemy models/repositories,
document loaders, offline and Grok provider adapters, the LangGraph workflow,
FastAPI routes, and run-ID-only Celery tasks.

From the repository root:

```bash
uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
uv run uvicorn backend.app.main:app --reload
uv run celery -A backend.app.workers.app:celery_app worker --loglevel=info --concurrency=1
```

The CLI is synchronous and requires no broker. The API path requires Valkey and a
worker for execution. Run backend tests and lint with `make test-backend` and
`make lint-backend`.

Persistence uses context-managed SQLAlchemy sessions injected into repositories;
see [data and persistence](../backstage/docs/03-data-and-persistence.md).
