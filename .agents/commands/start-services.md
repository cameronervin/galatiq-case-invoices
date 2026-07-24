Start the local invoice-processing services from the repository root.

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
make broker-up
make dev-worker
make dev-backend
make dev-frontend
```

Run long-lived commands in separate terminals. Verify the API at `http://127.0.0.1:8000/api/v1/health`, API docs at `http://127.0.0.1:8000/docs`, and frontend at `http://localhost:3000`. Do not commit real environment files.
