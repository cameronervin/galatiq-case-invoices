# Architecture Overview

The project is split into four runtime boundaries:

1. The root CLI validates a local invoice path and requests an asynchronous run.
2. The dispatch service publishes a JSON Celery task through Valkey.
3. The Celery worker invokes a typed LangGraph executor.
4. FastAPI and Next.js provide future HTTP and workspace surfaces.

The initial graph contains only a placeholder node. Domain behavior will be added
behind the existing states, nodes, tools, guardrails, services, repositories, and
infrastructure interfaces.

SQLite is reserved for inventory and application state. Celery's Valkey result
backend is operational metadata and must not become the source of truth for runs.

