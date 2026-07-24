# Frontend Design Standards

Use the ordered stylesheet modules imported by `frontend/src/app/globals.css`
as the current visual source of truth.

- Build a usable processing workspace rather than a marketing landing page.
- Use existing neutral CSS tokens and local UI primitives before adding dependencies.
- Make upload, queued, processing, review-required, rejected, failed, and completed states distinct and accessible.
- Keep invoice details readable without exposing unnecessary sensitive data.
- Preserve keyboard focus, accessible names, responsive layout, and reduced-motion preferences.
- Add icons or visualization dependencies only when a concrete feature requires them.
