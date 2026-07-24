COMPOSE = docker compose -f deploy/compose/local.yml

.PHONY: broker-up broker-down broker-logs dev-backend dev-frontend dev-worker generate-api-types check-generated test-backend lint-backend test-frontend lint-frontend typecheck-frontend build-frontend verify

broker-up:
	$(COMPOSE) up -d valkey

broker-down:
	$(COMPOSE) down

broker-logs:
	$(COMPOSE) logs -f valkey

dev-backend:
	uv run uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend:
	pnpm --dir frontend dev

dev-worker:
	uv run celery -A backend.app.workers.app:celery_app worker --loglevel=info --concurrency=1

generate-api-types:
	uv run python -m scripts.export_openapi
	pnpm --dir frontend exec openapi-typescript openapi.json -o src/types/generated-api.ts

check-generated:
	@generated_dir="$$(mktemp -d)"; \
	trap 'rm -rf "$$generated_dir"' EXIT; \
	uv run python -m scripts.export_openapi --output "$$generated_dir/openapi.json"; \
	pnpm --dir frontend exec openapi-typescript "$$generated_dir/openapi.json" -o "$$generated_dir/generated-api.ts"; \
	cmp frontend/openapi.json "$$generated_dir/openapi.json"; \
	cmp frontend/src/types/generated-api.ts "$$generated_dir/generated-api.ts"

test-backend:
	uv run pytest -v --cov=backend/app --cov=main --cov-branch

lint-backend:
	uv run ruff check .

test-frontend:
	pnpm --dir frontend test --runInBand

lint-frontend:
	pnpm --dir frontend lint

typecheck-frontend:
	pnpm --dir frontend typecheck

build-frontend:
	pnpm --dir frontend build

verify: check-generated test-backend lint-backend test-frontend lint-frontend typecheck-frontend build-frontend
