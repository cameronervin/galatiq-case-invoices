---
name: bug-squasher
description: Diagnose and fix unclear bugs, intermittent failures, and regressions in the invoice-processing CLI, API, agents, Celery worker, SQLite adapters, or frontend using hypothesis-driven evidence and focused verification.
---

# Bug Squasher

1. Inspect status, diffs, relevant code/tests, `README.md`, and `backstage/architecture/overview.md`.
2. List and rank 3-7 plausible causes before editing.
3. Use focused repros, tests, and sanitized logs to eliminate hypotheses.
4. Patch the proven root cause with the smallest safe change.
5. Run targeted checks, then broaden to `make verify` when warranted.
6. Report root cause, changes, verification, documentation impact, and remaining risk.

Preserve typed API/graph contracts, deterministic fixtures, approval-before-payment safeguards, and JSON-safe worker messages. Never log invoice contents, payment/vendor details, prompts, provider payloads, tokens, or keys.

Read `references/hypothesis-template.md`, `references/instrumentation-patterns.md`, or `references/root-cause-checklist.md` only when the debugging shape calls for them.

