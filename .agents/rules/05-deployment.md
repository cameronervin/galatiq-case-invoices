# Local Runtime Rules

This prototype runs locally and requires no cloud deployment. The only Compose service is Valkey for Celery.

```bash
make broker-up
make broker-logs
make broker-down
make dev-backend
make dev-worker
make dev-frontend
```

Commit environment examples only. Keep CORS explicit. Ask before adding persistent services, authentication, paid APIs, or production deployment infrastructure.

