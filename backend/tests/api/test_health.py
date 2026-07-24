from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app


def test_health_endpoint() -> None:
    with TestClient(create_app(Settings(env="test"))) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "invoice-processing-api",
    }


def test_cors_preflight_uses_configured_frontend_origin() -> None:
    app = create_app(Settings(frontend_origin="http://localhost:3100"))

    with TestClient(app) as client:
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3100",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3100"
