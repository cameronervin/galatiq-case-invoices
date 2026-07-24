---
name: build-plan-writer
description: Create or update a decision-complete implementation or build plan for the invoice-processing repository. Use only when the user explicitly requests planning rather than implementation.
---

# Build Plan Writer

Ground the plan in `README.md`, `backstage/architecture/overview.md`, relevant development docs, and current code/tests. Separate discovered facts from product decisions and ask only when an undiscoverable choice materially changes the result.

Cover the affected CLI, API, service, repository, graph, worker, LLM, SQLite, and frontend boundaries. Call out public contracts, workflow state, failure behavior, security/logging, tests, and documentation. Do not introduce persistent services, paid dependencies, authentication, production deployment, or live payment without approval.

Use concise sections: Summary, Key Changes, Public Interfaces, Test Plan, and Assumptions. Use `references/build-plan-template.md` for larger phased plans.

