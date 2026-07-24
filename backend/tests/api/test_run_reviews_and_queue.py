from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.schemas.domain import ReviewRequest


def test_queue_failure_returns_safe_error_and_marks_run_failed(
    tmp_path: Path,
    api_settings,
    dispatcher,
    invoice_dir,
) -> None:
    dispatcher.fail = True
    app = create_app(api_settings, dispatcher=dispatcher)

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
        run = client.get(f"/api/v1/runs/{response.json()['error']['run_id']}")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "QUEUE_UNAVAILABLE"
    assert response.json()["error"]["run_id"] is not None
    assert run.json()["status"] == "failed"
    assert run.json()["error"]["code"] == "QUEUE_UNAVAILABLE"
    assert list((tmp_path / "uploads").iterdir()) == []


def test_review_queue_failure_can_redispatch_identical_decision(
    api_settings,
    dispatcher,
    invoice_dir,
) -> None:
    app = create_app(api_settings, dispatcher=dispatcher)

    with TestClient(app) as client:
        processor = app.state.processor
        pending = processor.process_path(
            invoice_dir / "invoice_1012.txt",
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


def test_completed_review_cannot_be_resubmitted(
    api_settings,
    dispatcher,
    invoice_dir,
) -> None:
    app = create_app(api_settings, dispatcher=dispatcher)

    with TestClient(app) as client:
        processor = app.state.processor
        pending = processor.process_path(
            invoice_dir / "invoice_1012.txt",
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
