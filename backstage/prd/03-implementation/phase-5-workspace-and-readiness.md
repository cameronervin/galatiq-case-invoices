# Phase 5 — Workspace and Demo Readiness

## Objective

Deliver the accessible operational workspace, close the automated acceptance
matrix, enforce coverage, and reconcile all project documentation for handoff.

## Dependencies

- Complete Phase 4 API, worker, and CLI contracts.

## Task Plan

| Status | Goal | User Stories | Validation | PRD Docs |
| --- | --- | --- | --- | --- |
| ☐ | **[feature] Align frontend API contracts and client** — Add strict TypeScript types and client functions for create/list/detail/review/retry, typed safe errors, multipart upload, and abortable polling requests. | US-02, US-03, US-05, US-11, US-14 | Types mirror Pydantic examples/enums → mocked client tests cover success/error/status codes → multipart contains only file → abort stops pending poll → no `any`, provider/internal/path fields, or speculative client decisions. | `api-specification.md`, `workspace-ux.md` |
| ☐ | **[feature] Build upload and recent-run workspace** — Replace static scaffold with accessible uploader, local validation, recent runs, selection, empty/uploading/queued/processing states, and two-second non-overlapping polling. | US-02, US-03, US-16 | Accessible upload creates/selects run → exact duplicate message is visible → active run polls and stops in inactive state → transient poll error preserves last result → newest-first selection works → narrow/keyboard/reduced-motion behavior is tested. | `workspace-ux.md`, `api-specification.md` |
| ☐ | **[feature] Build run detail, timeline, and findings** — Render normalized invoice summary, ordered safe events, current stage, and warning/blocking findings without exposing unnecessary sensitive/internal data. | US-03, US-08, US-09, US-14, US-16 | Each workflow state has text label and heading → line items/money render exactly → findings group by severity with codes/plain text → timeline order persists after retry → no raw prompt/path/provider payload is renderable from types. | `workspace-ux.md`, `security-and-observability.md` |
| ☐ | **[feature] Build review and outcome interactions** — Add required review reason, approve-and-mock-pay confirmation, rejection, completed payment, failed retry, pending-action protection, focus management, and live announcements. | US-05, US-11–US-13, US-16 | Empty/short reason blocks → approval confirmation precedes API call → reject/approve call once while pending → `409` refreshes authoritative state → completed/rejected/failed outcomes expose correct actions → keyboard/focus/live-region tests pass. | `workspace-ux.md`, `api-specification.md`, `security-and-observability.md` |
| ☐ | **[eval] Complete fixture and contract evaluation suite** — Run every supplied fixture through appropriate loader/workflow/API paths plus threshold, duplicate, prompt-injection, failure, replay, and review synthetic cases; enforce backend app coverage. | US-01–US-16 | PRD fixture matrix passes → public API/TS contracts remain aligned → backend `backend/app` coverage is at least 90% → frontend state/accessibility tests pass → no supplied fixture changes → all security/idempotency cases pass. | `prd/README.md`, all technical specs |
| ☐ | **[docs] Reconcile product and developer documentation** — Update README, backend/frontend READMEs, architecture, setup, tech-debt/bug tracking, `.env.example`, and `.agents` guidance only to describe implemented behavior and commands. | US-01, US-14–US-16 | Docs no longer claim scaffolded result → exact CLI/API/UI/worker setup works → environment examples contain no secrets → PRD links resolve → deferred non-goals remain explicit → doc drift scan finds no stale behavior claims. | `prd/README.md`, `_implementation-plan.md`, all technical specs |
| ☐ | **[eval] Perform final visual and runtime verification** — Inspect desktop/narrow workspace states, run full verification, and execute documented asynchronous worker smoke when Docker is available. | US-01–US-16 | 1440/768/375 layouts are usable → empty/active/review/rejected/failed/completed states inspected → `make verify` passes → clean CLI and UI demos complete → worker smoke passes or Docker unavailability is documented. | `workspace-ux.md`, `prd/README.md` |

## Definition of Done

- [ ] All Phase 5 tasks are `☑` or deviations explicitly re-scope them.
- [ ] Every US-01 through US-16 criterion is mapped to passing evidence.
- [ ] Workspace is accessible, responsive, and visually verified in all states.
- [ ] Fixture and synthetic acceptance matrix passes.
- [ ] Backend application coverage is at least 90%.
- [ ] No raw sensitive/internal data appears in logs, API/CLI output, or UI.
- [ ] All product/developer docs match implementation.
- [ ] `make verify` passes.
- [ ] Docker/Valkey asynchronous worker smoke passes when Docker is available.

