# Frontend Rules

Use Next.js App Router, React 19, strict TypeScript, Tailwind v4, Jest, Testing Library, and pnpm.

- Use Server Components by default and client components only when necessary.
- Keep routes as default exports and reusable components as named exports.
- Use typed props and API contracts; avoid `any` and speculative state libraries.
- Preserve accessible loading, error, empty, queued, processing, review, rejected, and completed states.
- Keep trusted workflow decisions on the server.

Verify with frontend test, lint, typecheck, and production build commands from the Makefile.

