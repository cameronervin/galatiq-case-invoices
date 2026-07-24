import json
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

import main as cli
from backend.app.schemas.run import QueuedAgentRun
from backend.app.services.agent_run_service import AgentRunDispatchError

RUN_ID = UUID("11111111-1111-4111-8111-111111111111")


class SuccessfulDispatchService:
    def enqueue(self, invoice_path: Path) -> QueuedAgentRun:
        return QueuedAgentRun(
            run_id=RUN_ID,
            task_id=str(RUN_ID),
            invoice_path=invoice_path,
        )


class FailedDispatchService:
    def enqueue(self, invoice_path: Path) -> QueuedAgentRun:
        raise AgentRunDispatchError("broker unavailable")


def test_cli_queues_valid_invoice(tmp_path, capsys) -> None:
    invoice = tmp_path / "invoice.json"
    invoice.write_text("{}")

    exit_code = cli.run(
        ["--invoice_path", str(invoice)],
        dispatch_service=SuccessfulDispatchService(),
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["run_id"] == str(RUN_ID)
    assert payload["task_id"] == str(RUN_ID)
    assert payload["invoice_path"] == str(invoice.resolve())
    assert payload["status"] == "queued"


def test_cli_rejects_missing_invoice(tmp_path, capsys) -> None:
    exit_code = cli.run(["--invoice_path", str(tmp_path / "missing.pdf")])

    payload = json.loads(capsys.readouterr().err)
    assert exit_code == cli.EXIT_INVALID_INPUT
    assert payload["error"] == "invalid_input"


def test_cli_rejects_unsupported_invoice(tmp_path, capsys) -> None:
    invoice = tmp_path / "invoice.docx"
    invoice.write_text("not supported")

    exit_code = cli.run(["--invoice_path", str(invoice)])

    payload = json.loads(capsys.readouterr().err)
    assert exit_code == cli.EXIT_INVALID_INPUT
    assert "Unsupported invoice type" in payload["message"]


def test_cli_reports_configuration_error(tmp_path, capsys, monkeypatch) -> None:
    invoice = tmp_path / "invoice.txt"
    invoice.write_text("invoice")
    error = ValidationError.from_exception_data("Settings", [])
    monkeypatch.setattr(cli, "get_settings", lambda: (_ for _ in ()).throw(error))

    exit_code = cli.run(["--invoice_path", str(invoice)])

    payload = json.loads(capsys.readouterr().err)
    assert exit_code == cli.EXIT_CONFIGURATION_ERROR
    assert payload["error"] == "configuration_error"


def test_cli_reports_broker_failure(tmp_path, capsys) -> None:
    invoice = tmp_path / "invoice.xml"
    invoice.write_text("<invoice />")

    exit_code = cli.run(
        ["--invoice_path", str(invoice)],
        dispatch_service=FailedDispatchService(),
    )

    payload = json.loads(capsys.readouterr().err)
    assert exit_code == cli.EXIT_DISPATCH_ERROR
    assert payload == {
        "error": "dispatch_error",
        "message": "broker unavailable",
    }


def test_cli_requires_invoice_path() -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.run([])

    assert exc_info.value.code == 2

