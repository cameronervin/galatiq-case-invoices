---
name: garbage-cleanup
description: Identify dead code, stale scaffolding, duplicate logic, unused dependencies, and architectural drift in the invoice-processing backend, worker, frontend, tests, and documentation.
---

# Garbage Cleanup

Inspect git status, Ruff/ESLint findings, TODO markers, imports, manifests, routes, agent modules, and documentation claims. Prioritize safe removal of unused symbols and stale placeholders while preserving public CLI/API contracts, fixture coverage, workflow safeguards, and extension boundaries that have a documented near-term purpose.

Do not remove public endpoints, Pydantic fields, invoice fixtures, validation/approval/payment safeguards, or queue failure handling without a plan. Separate safe removals from architectural work and list verification for each group.

Use `references/cleanup-checklist.md` and `references/code-smell-patterns.md` when a broad audit is requested.

