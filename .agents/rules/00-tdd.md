# TDD Workflow

Use TDD for non-trivial services, repositories, API contracts, invoice parsing/validation, LangGraph transitions, Celery behavior, approval/payment safeguards, and frontend business interactions.

Cycle: `RED -> GREEN -> REFACTOR`.

```bash
uv run pytest -v
uv run ruff check .
pnpm --dir frontend test --runInBand
pnpm --dir frontend lint
pnpm --dir frontend typecheck
```

Confirm failures are meaningful, keep fixtures deterministic, and update docs after behavior changes.

