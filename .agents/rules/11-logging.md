# Logging Rules

Use `structlog` for application logs and plain JSON output only at the CLI boundary.

- Log service boundaries and important state transitions with sanitized run ID, stage, status, duration, and file type.
- Never log invoice contents, full paths when avoidable, vendor/payment details, prompts, model inputs, tokens, keys, secrets, or raw provider payloads.
- Use structured fields instead of string interpolation.
- Keep hot-loop logging intentional.

```python
logger.info("agent_run_started", run_id=run_id, stage="ingestion")
logger.warning("invoice_validation_failed", run_id=run_id, reason_code=reason)
```

