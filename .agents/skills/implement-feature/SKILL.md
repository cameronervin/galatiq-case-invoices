---
name: implement-feature
description: Implement invoice-processing CLI, API, LangGraph, Celery, SQLite, LLM-boundary, or Next.js features with focused tests, documentation updates, and repository-standard verification.
---

# Implement Feature

1. Inspect git state, `README.md`, architecture docs, affected code, and tests.
2. Identify affected entrypoint, schema, service, repository, graph, infrastructure, worker, and frontend boundaries.
3. Use TDD for non-trivial behavior and prove the failure before implementation.
4. Keep the root CLI and FastAPI routes thin, state typed, orchestration in services, persistence behind repositories, and Celery messages JSON-safe.
5. Preserve explicit missing-data flags, bounded reflection, approval-before-payment, redacted logging, and deterministic local behavior.
6. Update API, architecture, setup, security, and workflow documentation when behavior changes.
7. Run targeted checks followed by `make verify` when appropriate.

Ask before adding persistent services, authentication, paid dependencies, production deployment, or live payment. Use `references/feature-template.md` and `references/tdd-checklist.md` when useful.

