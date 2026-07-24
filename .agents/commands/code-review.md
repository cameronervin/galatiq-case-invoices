Review current git changes using `.agents/skills/code-review-expert/SKILL.md`.

Project focus:
- Keep the root CLI and FastAPI routes thin.
- Keep orchestration in services, persistence behind repositories, and graph state typed.
- Treat extracted values, validation decisions, approvals, and payment outcomes as server-owned.
- Keep Celery payloads/results JSON-safe and prevent invoice or secret leakage.
- Keep frontend contracts aligned with Pydantic responses.

Default prompt: Review for correctness, security, workflow regressions, data leaks, race conditions, error handling, performance problems, and missing tests.

