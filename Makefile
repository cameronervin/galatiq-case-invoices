COMPOSE = docker compose -f deploy/compose/local.yml

.PHONY: broker-up broker-down broker-logs dev-backend dev-frontend dev-worker generate-api-types test-backend lint-backend test-frontend lint-frontend typecheck-frontend build-frontend verify

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

test-backend:
	uv run pytest -v

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

verify: generate-api-types test-backend lint-backend test-frontend lint-frontend typecheck-frontend build-frontend
