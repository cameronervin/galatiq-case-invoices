from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.schemas.domain import ReviewRequest
from backend.app.services.agent_run_service import AgentRunDispatchError

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class RecordingDispatcher:
    def __init__(self) -> None:
        self.execute_ids: list[UUID] = []
        self.resume_ids: list[UUID] = []
        self.fail = False

    def enqueue_execute(self, *, run_id: UUID) -> str:
        if self.fail:
            raise AgentRunDispatchError("queue unavailable")
        self.execute_ids.append(run_id)
        return str(run_id)

    def enqueue_resume(self, *, run_id: UUID) -> str:
        if self.fail:
            raise AgentRunDispatchError("queue unavailable")
        self.resume_ids.append(run_id)
        return str(run_id)


def settings_for(tmp_path: Path) -> Settings:
    return Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
        llm_provider="offline",
        llm_model="deterministic-v1",
    )


def test_create_list_and_detail_run_contract(tmp_path: Path) -> None:
    dispatcher = RecordingDispatcher()
    app = create_app(settings_for(tmp_path), dispatcher=dispatcher)
    content = (PROJECT_ROOT / "data/invoices/invoice_1001.txt").read_bytes()

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


def test_list_limit_is_bounded(tmp_path: Path) -> None:
    app = create_app(settings_for(tmp_path), dispatcher=RecordingDispatcher())

    with TestClient(app) as client:
        below = client.get("/api/v1/runs?limit=0")
        above = client.get("/api/v1/runs?limit=51")

    assert below.status_code == 422
    assert below.json()["error"]["code"] == "VALIDATION_ERROR"
    assert above.status_code == 422
    assert above.json()["error"]["code"] == "VALIDATION_ERROR"


def test_requested_grok_without_key_returns_safe_configuration_error(
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path).model_copy(
        update={"llm_provider": "grok", "llm_model": "grok-4.5", "xai_api_key": None}
    )
    app = create_app(settings, dispatcher=RecordingDispatcher())

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/runs",
            files={
                "file": (
                    "invoice.txt",
                    (PROJECT_ROOT / "data/invoices/invoice_1001.txt").read_bytes(),
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


def test_queue_failure_returns_safe_error_and_marks_run_failed(tmp_path: Path) -> None:
    dispatcher = RecordingDispatcher()
    dispatcher.fail = True
    app = create_app(settings_for(tmp_path), dispatcher=dispatcher)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/runs",
            files={
                "file": (
                    "invoice.txt",
                    (PROJECT_ROOT / "data/invoices/invoice_1001.txt").read_bytes(),
                    "text/plain",
                )
            },
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "QUEUE_UNAVAILABLE"
    assert response.json()["error"]["run_id"] is not None


def test_review_queue_failure_can_redispatch_identical_decision(tmp_path: Path) -> None:
    dispatcher = RecordingDispatcher()
    app = create_app(settings_for(tmp_path), dispatcher=dispatcher)

    with TestClient(app) as client:
        processor = app.state.processor
        pending = processor.process_path(
            PROJECT_ROOT / "data/invoices/invoice_1012.txt",
            origin="cli",
        )
        dispatcher.fail = True
        failed = client.post(
            f"/api/v1/runs/{pending.run_id}/review",
            json={"decision": "approve", "reason": "Reviewed the warning."},
        )
        dispatcher.fail = False
        retried = client.post(
            f"/api/v1/runs/{pending.run_id}/review",
            json={"decision": "approve", "reason": "Reviewed the warning."},
        )
        conflict = client.post(
            f"/api/v1/runs/{pending.run_id}/review",
            json={"decision": "reject", "reason": "Changed my decision."},
        )

    assert failed.status_code == 503
    assert retried.status_code == 202
    assert dispatcher.resume_ids == [pending.run_id]
    assert conflict.status_code == 409


def test_completed_review_cannot_be_resubmitted(tmp_path: Path) -> None:
    app = create_app(settings_for(tmp_path), dispatcher=RecordingDispatcher())

    with TestClient(app) as client:
        processor = app.state.processor
        pending = processor.process_path(
            PROJECT_ROOT / "data/invoices/invoice_1012.txt",
            origin="cli",
        )
        command = {
            "decision": "approve",
            "reason": "Reviewed the documented warning.",
        }
        processor.persist_review(pending.run_id, ReviewRequest.model_validate(command))
        processor.resume_run(pending.run_id)

        response = client.post(f"/api/v1/runs/{pending.run_id}/review", json=command)

    assert response.status_code == 409
