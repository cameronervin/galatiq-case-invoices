# Testing Rules

Backend tests use pytest under `backend/tests/`; frontend tests use Jest and Testing Library.

- Use async tests for async services and graph execution.
- Mock LLM/payment boundaries and keep invoice fixtures deterministic.
- Cover supported formats, malformed input, stock mismatches, unknown items, approval thresholds, reflection bounds, payment gating, queue failures, and JSON serialization as behavior is implemented.
- Test frontend behavior through accessible roles and visible state.
- Never include real invoices, vendors, secrets, or raw provider payloads.

Run `make verify` before handoff.

