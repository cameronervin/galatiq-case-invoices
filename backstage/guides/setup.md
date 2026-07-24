# Local Setup

## Install

```bash
uv sync
pnpm install
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

## Development services

Run these in separate terminals:

```bash
make broker-up
make dev-worker
make dev-backend
make dev-frontend
```

## Submit an invoice

```bash
uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
```

The CLI prints a queued run and task identifier. The worker logs a JSON-safe
`scaffolded` result because invoice business behavior is intentionally absent.

After activating `.venv`, the exact case command also works:

```bash
python main.py --invoice_path=data/invoices/invoice_1001.txt
```

## Verify

```bash
make verify
```

Stop the local broker with `make broker-down`.

