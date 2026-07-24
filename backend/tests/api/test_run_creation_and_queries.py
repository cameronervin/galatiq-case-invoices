import inspect

from fastapi.testclient import TestClient

from backend.app.api.v1 import runs as run_routes
from backend.app.api.v1.runs import create_run, get_run, list_runs, review_run
from backend.app.main import create_app


def test_create_list_and_detail_run_contract(
    api_settings,
    dispatcher,
    invoice_dir,
) -> None:
    app = create_app(api_settings, dispatcher=dispatcher)
    content = (invoice_dir / "invoice_1001.txt").read_bytes()

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/runs",
            files={"file": ("invoice.txt", content, "text/plain")},
        )
        duplicate = client.post(
            "/api/v1/runs",
            files={"file": ("renamed.txt", content, "text/plain")},
        )
        listed = client.get("/api/v1/runs?limit=20")
        detail = client.get(f"/api/v1/runs/{created.json()['run_id']}")

    assert created.status_code == 202
    assert created.json()["deduplicated"] is False
    assert duplicate.status_code == 200
    assert duplicate.json()["run_id"] == created.json()["run_id"]
    assert duplicate.json()["deduplicated"] is True
    assert len(dispatcher.execute_ids) == 1
    assert listed.json()["items"][0]["run_id"] == created.json()["run_id"]
    assert detail.json()["status"] == "queued"
    assert "source_path" not in detail.text


def test_blocking_run_routes_are_synchronous() -> None:
    assert not inspect.iscoroutinefunction(create_run)
    assert not inspect.iscoroutinefunction(list_runs)
    assert not inspect.iscoroutinefunction(get_run)
    assert not inspect.iscoroutinefunction(review_run)


def test_run_routes_only_use_the_application_boundary() -> None:
    source = inspect.getsource(run_routes)

    assert ".run_repository" not in source
    assert ".enqueue_execute" not in source
    assert ".enqueue_resume" not in source


def test_upload_errors_have_stable_codes_and_configured_limit(
    api_settings,
    dispatcher,
) -> None:
    app = create_app(
        api_settings.model_copy(update={"max_upload_bytes": 3}),
        dispatcher=dispatcher,
    )

    with TestClient(app) as client:
        empty = client.post(
            "/api/v1/runs",
            files={"file": ("invoice.txt", b"", "text/plain")},
        )
        unsupported = client.post(
            "/api/v1/runs",
            files={"file": ("invoice.exe", b"x", "application/octet-stream")},
        )
        oversized = client.post(
            "/api/v1/runs",
            files={"file": ("invoice.txt", b"four", "text/plain")},
        )

    assert empty.status_code == 400
    assert empty.json()["error"]["code"] == "EMPTY_FILE"
    assert unsupported.status_code == 400
    assert unsupported.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert oversized.status_code == 413
    assert oversized.json()["error"] == {
        "code": "FILE_TOO_LARGE",
        "message": "Invoice exceeds the 3 bytes limit.",
        "run_id": None,
    }


def test_list_limit_is_bounded(api_settings, dispatcher) -> None:
    app = create_app(api_settings, dispatcher=dispatcher)

    with TestClient(app) as client:
        below = client.get("/api/v1/runs?limit=0")
        above = client.get("/api/v1/runs?limit=51")

    assert below.status_code == 422
    assert below.json()["error"]["code"] == "VALIDATION_ERROR"
    assert above.status_code == 422
    assert above.json()["error"]["code"] == "VALIDATION_ERROR"


def test_requested_grok_without_key_returns_safe_configuration_error(
    api_settings,
    dispatcher,
    invoice_dir,
) -> None:
    settings = api_settings.model_copy(
        update={"llm_provider": "grok", "llm_model": "grok-4.5", "xai_api_key": None}
    )
    app = create_app(settings, dispatcher=dispatcher)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/runs",
            files={
                "file": (
                    "invoice.txt",
                    (invoice_dir / "invoice_1001.txt").read_bytes(),
                    "text/plain",
                )
            },
        )

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "PROVIDER_NOT_CONFIGURED",
        "message": "The requested model provider is not configured.",
        "run_id": None,
    }
