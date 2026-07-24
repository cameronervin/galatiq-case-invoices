from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

import pytest

from backend.app.bootstrap.invoice_runtime import (
    InvoiceProcessingRuntime,
    compose_invoice_processor,
)
from backend.app.schemas.domain import ReviewRequest, RunStatus
from backend.app.services.invoice_processing import InvalidInvoiceInput
from backend.tests.services.workflow_support import (
    PROJECT_ROOT,
    service_for,
    settings_for,
)


def test_invalid_invoice_input_contains_no_http_status() -> None:
    error = InvalidInvoiceInput("FILE_TOO_LARGE", "Invoice is too large.")

    assert error.code == "FILE_TOO_LARGE"
    assert not hasattr(error, "status_code")


def test_service_cleanup_closes_graph_provider_and_database_once(
    tmp_path: Path, monkeypatch
) -> None:
    runtime = InvoiceProcessingRuntime.create(settings_for(tmp_path))
    service = compose_invoice_processor(runtime)
    calls: list[str] = []
    monkeypatch.setattr(service.graph_provider, "close", lambda: calls.append("graph"))
    monkeypatch.setattr(
        service.provider_registry,
        "close",
        lambda: calls.append("provider"),
    )
    monkeypatch.setattr(runtime.database, "close", lambda: calls.append("database"))

    service.close()
    service.close()

    assert calls == ["graph", "provider", "database"]


def test_staged_upload_is_removed_when_run_persistence_fails(
    tmp_path: Path, monkeypatch
) -> None:
    service = service_for(tmp_path)

    def fail_create(**_: object) -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(service.run_repository, "create_run", fail_create)

    with pytest.raises(RuntimeError, match="database unavailable"):
        service.create_from_bytes(
            filename="invoice.txt",
            content=b"invoice",
            origin="api",
        )

    assert list((tmp_path / "uploads").iterdir()) == []


@pytest.mark.parametrize("failing_boundary", ["context", "graph"])
def test_setup_failure_marks_run_failed_and_cleans_source(
    tmp_path: Path, monkeypatch, failing_boundary: str
) -> None:
    service = service_for(tmp_path)
    record, _ = service.create_from_path(
        PROJECT_ROOT / "data/invoices/invoice_1001.txt",
        origin="api",
    )

    def fail(*_: object, **__: object) -> None:
        raise RuntimeError(f"{failing_boundary} unavailable")

    if failing_boundary == "context":
        monkeypatch.setattr(service.execution.workflow_runner, "_context", fail)
    else:
        monkeypatch.setattr(service.graph_provider, "invoice_graph", fail)

    detail = service.process_run(record.run_id)

    assert detail.status == RunStatus.FAILED
    assert detail.error is not None
    assert detail.error.code == "WORKFLOW_FAILED"
    assert list((tmp_path / "uploads").iterdir()) == []


def test_resume_setup_failure_marks_run_failed_and_cleans_source(
    tmp_path: Path, monkeypatch
) -> None:
    service = service_for(tmp_path)
    pending = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1012.txt",
        origin="api",
    )
    service.persist_review(
        pending.run_id,
        ReviewRequest(decision="approve", reason="Reviewed the warning."),
    )

    def fail_graph() -> None:
        raise RuntimeError("graph unavailable")

    monkeypatch.setattr(service.graph_provider, "invoice_graph", fail_graph)

    detail = service.resume_run(pending.run_id)

    assert detail.status == RunStatus.FAILED
    assert detail.error is not None
    assert detail.error.code == "WORKFLOW_FAILED"
    assert list((tmp_path / "uploads").iterdir()) == []


def test_duplicate_worker_deliveries_execute_graph_once(
    tmp_path: Path, monkeypatch
) -> None:
    service = service_for(tmp_path)
    record, _ = service.create_from_path(
        PROJECT_ROOT / "data/invoices/invoice_1001.txt",
        origin="api",
    )
    calls = 0
    lock = Lock()

    def record_execution(*_: object, **__: object) -> None:
        nonlocal calls
        with lock:
            calls += 1

    monkeypatch.setattr(
        "backend.app.infrastructure.graph.runner.AgentPipelineExecutor.execute",
        record_execution,
    )
    monkeypatch.setattr(service.graph_provider, "invoice_graph", lambda: object())

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(lambda _: service.process_run(record.run_id), range(2)))

    assert calls == 1


def test_duplicate_processing_returns_existing_terminal_run(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    path = PROJECT_ROOT / "data/invoices/invoice_1001.txt"

    first = service.process_path(path, origin="cli")
    second = service.process_path(path, origin="cli")

    assert second.run_id == first.run_id
    assert sum(event.code == "PAYMENT_SUCCEEDED" for event in second.events) == 1
