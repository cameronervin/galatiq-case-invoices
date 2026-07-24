from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

from backend.app.agents.graph_provider import GraphProvider
from backend.app.services.agent_run_service import CeleryTaskDispatcher
from backend.app.workers import app as worker_app
from backend.app.workers.app import REQUIRED_TASKS, registered_tasks
from backend.app.workers.tasks import execute_agent_run


def test_required_celery_tasks_are_registered() -> None:
    assert REQUIRED_TASKS <= registered_tasks()


def test_dispatcher_publishes_registered_task_by_name(monkeypatch, tmp_path) -> None:
    invoice = tmp_path / "invoice.txt"
    invoice.write_text("invoice")
    run_id = UUID("11111111-1111-4111-8111-111111111111")
    captured: dict[str, object] = {}

    def fake_send_task(name: str, **kwargs: object) -> SimpleNamespace:
        captured.update(name=name, **kwargs)
        return SimpleNamespace(id=str(run_id))

    monkeypatch.setattr(worker_app.celery_app, "send_task", fake_send_task)

    task_id = CeleryTaskDispatcher().enqueue(
        run_id=run_id,
        invoice_path=invoice,
    )

    assert task_id == str(run_id)
    assert captured == {
        "name": "invoice_processing.agent_runs.execute",
        "kwargs": {"run_id": str(run_id), "invoice_path": str(invoice)},
        "task_id": str(run_id),
    }


def test_worker_resource_lifecycle_is_idempotent() -> None:
    worker_app.init_worker_resources()
    first_provider = worker_app.get_worker_graph_provider()
    worker_app.init_worker_resources()

    assert isinstance(first_provider, GraphProvider)
    assert worker_app.get_worker_graph_provider() is first_provider

    worker_app.teardown_worker_resources()
    worker_app.teardown_worker_resources()

    assert worker_app.get_worker_graph_provider() is None


def test_worker_task_returns_json_safe_placeholder_state(tmp_path) -> None:
    invoice = tmp_path / "invoice.csv"
    invoice.write_text("item,quantity\nWidgetA,1\n")

    result = execute_agent_run.run(
        run_id="run-1",
        invoice_path=str(invoice),
    )

    assert result == {
        "run_id": "run-1",
        "invoice_path": str(invoice),
        "status": "scaffolded",
        "current_stage": "not_implemented",
        "messages": ["invoice pipeline is not implemented"],
        "errors": [],
    }


def test_json_safe_worker_result_does_not_include_path_objects(tmp_path) -> None:
    result = worker_app.run_async(_path_result(tmp_path))

    assert result["path"] == str(tmp_path)


async def _path_result(path: Path) -> dict[str, str]:
    return {"path": str(path)}
