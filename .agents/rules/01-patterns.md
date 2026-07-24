# Application Patterns

```text
CLI or FastAPI route -> service -> repository -> SQLite
                              |
                              -> agent executor -> provider/tool adapters
```

- Keep entrypoints thin and contracts typed.
- Put use-case orchestration in services and persistence behind repositories.
- Put workflow steps in LangGraph nodes with bounded state.
- Normalize external/model output before business logic consumes it.
- Return explicit flags/errors instead of inventing missing invoice values.
- Avoid abstractions until repeated complexity justifies them.

