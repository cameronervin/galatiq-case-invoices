# Python Rules

Use Python 3.12, FastAPI, Pydantic v2, LangGraph, Celery, SQLite, and uv.

```text
main.py                     CLI entrypoint
backend/app/main.py         FastAPI entrypoint
backend/app/api/v1/         Thin routers
backend/app/services/       Orchestration
backend/app/repositories/   Persistence boundaries
backend/app/agents/         Typed graph state and execution
backend/app/infrastructure/ DB and LLM adapters
backend/app/workers/        Celery app and tasks
backend/app/schemas/        Pydantic DTOs
```

Type public functions, avoid blocking I/O in async code, keep SQLite queries parameterized, and do not return provider payloads or persistence objects across public boundaries.

Verify with `uv run pytest -v` and `uv run ruff check .`.

