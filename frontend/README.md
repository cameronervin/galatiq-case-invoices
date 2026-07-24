# Frontend

The Next.js workspace supports invoice upload, the newest 20 runs, live polling,
extracted invoice detail, findings, recommendation and timeline inspection,
human review, and completed/rejected/failed outcomes. Payment language is always
explicitly marked as mock; there is no failed-run retry control.

From the repository root:

```bash
pnpm install
make dev-frontend
```

The API defaults to `http://127.0.0.1:8000`; override it with
`NEXT_PUBLIC_API_BASE_URL`. `make generate-api-types` regenerates the checked-in
TypeScript contract from FastAPI's OpenAPI schema. Validate the workspace with `make test-frontend`,
`make lint-frontend`, `make typecheck-frontend`, and `make build-frontend`.
