---
name: sprint-progress
description: Generate a Markdown progress report from invoice-processing implementation phase files, requirements, code evidence, and validation results without using external AI APIs.
---

# Sprint Progress

Read implementation documents under `backstage/development/` and the requirements in `README.md`. Extract phase, status, goal, acceptance criteria, and validation; verify completion claims against code/tests when practical.

Write `backstage/development/sprint-reports/YYYY-MM-DD/sprint-progress.md` with Summary, By Phase, Verification Notes, and Follow-ups. Mark unsupported completion claims as `Needs verification`. Never include secrets, invoice contents, vendor/payment details, prompts, or provider payloads.

Use `scripts/parse_status.py` for deterministic table parsing when the source format is compatible, and `templates/table_template.md` for report structure.
