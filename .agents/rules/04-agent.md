# Agent Rules

Use a bounded LangGraph pipeline for the intended workflow:

```text
START -> ingestion -> validation -> approval/reflection -> payment-or-rejection -> END
```

- Keep state typed under `backend/app/agents/states/`.
- Keep topology in `graphs/`, node construction in `builders/`, behavior in `nodes/`, and execution in `executors/`.
- Use runtime/provider boundaries rather than global decisions.
- Return structured flags for missing, malformed, unknown, or suspicious data.
- Require explicit approval before payment; make rejection reasons observable.
- Bound retries and reflection loops.
- Never keep raw model responses, secrets, or full invoice contents in graph state or logs.

