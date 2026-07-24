# Application Patterns

```text
CLI or FastAPI route -> service -> port -> infrastructure adapter
                              |
                              -> agent executor -> domain policy
```

- Keep entrypoints thin and contracts typed.
- Keep concrete construction and lifecycle ownership in `bootstrap`.
- Put use-case orchestration in services and persistence behind repositories.
- Put business rules in `domain`, interfaces in `ports`, and I/O in `infrastructure`.
- Put workflow steps in LangGraph nodes with bounded state.
- Normalize external/model output before business logic consumes it.
- Return explicit flags/errors instead of inventing missing invoice values.
- Avoid abstractions until repeated complexity justifies them.
