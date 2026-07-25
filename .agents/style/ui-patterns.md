# Invoice Processing UI Patterns

- Build local primitives under `frontend/src/components/ui/`.
- Use panels for upload, run status, validation findings, approval review, and final outcomes.
- Prefer flat sections and dividers over nested cards, shadows, and decorative effects.
- Keep workflow stages easy to scan and distinguish queued, running, review-required, rejected, failed, and completed states.
- Show validation and rejection reasons in plain language.
- Keep the outcome and actionable evidence visible; disclose decision metadata and terminal workflow history on demand.
- Require an inline second-step confirmation for payment-like actions and show the invoice identifier and amount when available.
- Use accessible labels, keyboard navigation, calm sentence-case copy, and responsive layouts.
- Do not display raw model responses, secrets, unnecessary file paths, or sensitive invoice details.
