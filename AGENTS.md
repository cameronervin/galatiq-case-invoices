# Invoice Processing Coding Instructions

This repository is a local-first multi-agent invoice-processing prototype with a
FastAPI and LangGraph backend, a Celery worker, and a Next.js workspace.

## Architecture

- Keep HTTP routes and the root CLI thin.
- Put orchestration in services and persistence behind repositories.
- Keep LangGraph state explicit and typed.
- Treat tools, prompts, guardrails, and model providers as replaceable boundaries.
- Keep Celery payloads and results JSON-safe.
- Use SQLite for application data and Valkey only for queue operations.

## Working Rules

- Preserve the supplied invoice fixtures.
- Do not commit secrets, generated databases, or real vendor information.
- Add tests before implementing non-trivial workflow behavior.
- Do not silently replace missing invoice data with assumptions.
- Keep extraction, validation, approval, and payment decisions observable.
- Use the context7 mcp for the most up to date documentation.

## Agent Kit

Reusable project commands, rules, skills, and UI guidance live under `.agents/`.
Treat those files as repository-specific instructions and keep them aligned with
the implemented architecture and developer commands.

## Verification

Run `make verify` before handing off a change. If Docker is available, also run
the asynchronous worker smoke test documented in `backstage/guides/setup.md`.
