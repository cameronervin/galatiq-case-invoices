# Documentation Coverage Checklist

## Core documents

- [ ] `README.md` requirements and run commands match implemented behavior.
- [ ] `AGENTS.md` architecture and verification commands match the repository.
- [ ] `backstage/architecture/overview.md` matches CLI, API, graph, Celery, SQLite, and frontend boundaries.
- [ ] `backstage/guides/setup.md` works from a fresh checkout.
- [ ] Environment examples contain placeholders only and match settings.
- [ ] Bug and technical-debt logs distinguish current defects from planned work.

## Code-to-document alignment

- [ ] Every implemented API route and Pydantic response is documented.
- [ ] Root CLI arguments, output, and exit behavior are accurate.
- [ ] LangGraph topology/state documentation matches code.
- [ ] Celery task names, broker setup, and worker commands are current.
- [ ] SQLite schemas and seed behavior are documented when implemented.
- [ ] LLM, extraction, validation, approval, and payment behavior is never described as complete before code/tests prove it.
- [ ] Frontend documentation matches implemented screens and API integration.

## Cross-references

- [ ] Markdown links and referenced paths resolve.
- [ ] Commands use root-relative working directories correctly.
- [ ] Dependency/version claims match lockfiles.
- [ ] External links point to current primary documentation.

## Common checks

| Issue | Detection | Fix |
| --- | --- | --- |
| Undocumented endpoint | Compare `@router` usage with docs | Add contract and error behavior |
| Stale setup | Follow setup from a clean environment | Correct commands and prerequisites |
| Planned behavior marked complete | Compare docs with tests/code | Label as planned or implement it |
| Wrong structure | Compare documented tree with `rg --files` | Update the documentation |
| Broken link | Resolve each relative target | Fix or remove the reference |

