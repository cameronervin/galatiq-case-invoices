from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

from backend.app.core.config import Settings
from backend.app.services.agent_run_service import CeleryTaskDispatcher
from backend.app.services.invoice_processing import InvoiceProcessingService
from backend.app.workers import app as worker_app
from backend.app.workers.tasks import execute_agent_run

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_dispatcher_sends_only_run_id(monkeypatch) -> None:
    run_id = UUID("11111111-1111-4111-8111-111111111111")
    captured: dict[str, object] = {}

    def fake_send_task(name: str, **kwargs: object) -> SimpleNamespace:
        captured.update(name=name, **kwargs)
        return SimpleNamespace(id="task-id")

    monkeypatch.setattr(worker_app.celery_app, "send_task", fake_send_task)

    CeleryTaskDispatcher().enqueue_execute(run_id=run_id)

    assert captured["kwargs"] == {"run_id": str(run_id)}
    assert "invoice_path" not in str(captured)


def test_worker_result_contains_only_identifier_status_and_error(
    tmp_path: Path,
) -> None:
    settings = Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
        llm_provider="offline",
        llm_model="deterministic-v1",
    )
    processor = InvoiceProcessingService(settings)
    record, _ = processor.create_from_path(
        PROJECT_ROOT / "data/invoices/invoice_1001.txt",
        origin="api",
    )
    worker_app.set_worker_processor(processor)

    result = execute_agent_run.run(run_id=str(record.run_id))

    assert result == {
        "run_id": str(record.run_id),
        "status": "completed",
        "error_code": None,
    }


def test_worker_registers_execute_and_resume_tasks() -> None:
    assert {
        "invoice_processing.agent_runs.execute",
        "invoice_processing.agent_runs.resume",
    } <= worker_app.registered_tasks()
