---
name: frontend-design
description: Implement or visually review the invoice-processing Next.js workspace, including upload, run progress, validation findings, approval review, rejection, failure, and completion experiences.
---

# Frontend Design

Read `frontend/src/app/globals.css`, existing layout/UI components, `.agents/style/`, and current API types before editing.

Build a usable processing workspace, not a marketing page. Reuse local primitives and neutral tokens; add dependencies only for a proven feature need. Make workflow states distinct, keep sensitive invoice data minimized, require explicit confirmation for payment-like actions, and preserve keyboard focus, accessible names, responsive layout, and reduced motion.

Run frontend tests, lint, typecheck, and production build. Manually inspect desktop and narrow layouts for substantial UI changes.

