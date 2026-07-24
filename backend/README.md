# Backend

The backend contains the FastAPI application, LangGraph extension points, Celery
worker, and infrastructure interfaces. The current graph deliberately returns a
`scaffolded` result and does not implement invoice-processing behavior.

Run the API from the repository root:

```bash
uv run uvicorn backend.app.main:app --reload
```

Run tests and linting with `make test-backend` and `make lint-backend`.

