import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

import main as cli
from backend.app.core.config import Settings
from backend.app.schemas.domain import (
    RunDetail,
    RunStage,
    RunStatus,
    WorkflowError,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_cli_processes_invoice_without_broker(tmp_path: Path, capsys) -> None:
    settings = Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
        llm_provider="offline",
        llm_model="deterministic-v1",
    )

    exit_code = cli.run(
        [
            "--invoice_path",
            str(PROJECT_ROOT / "data/invoices/invoice_1001.txt"),
        ],
        settings=settings,
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "completed"
    assert payload["payment"]["status"] == "succeeded"
    assert "invoice_path" not in captured.out
    assert str(PROJECT_ROOT) not in captured.out


@pytest.mark.parametrize(
    ("filename", "expected_status"),
    [
        ("invoice_1002.txt", "rejected"),
        ("invoice_1012.txt", "review_required"),
    ],
)
def test_cli_returns_business_outcomes_as_success(
    tmp_path: Path,
    capsys,
    filename: str,
    expected_status: str,
) -> None:
    settings = Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
    )

    exit_code = cli.run(
        ["--invoice_path", str(PROJECT_ROOT / "data/invoices" / filename)],
        settings=settings,
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["status"] == expected_status


def test_cli_rejects_invalid_input_before_processing(tmp_path: Path, capsys) -> None:
    exit_code = cli.run(["--invoice_path", str(tmp_path / "missing.pdf")])

    payload = json.loads(capsys.readouterr().err)
    assert exit_code == 2
    assert payload["error"]["code"] == "INVALID_INPUT"


def test_cli_rejects_non_positive_timeout(capsys) -> None:
    exit_code = cli.run(
        [
            "--invoice_path",
            str(PROJECT_ROOT / "data/invoices/invoice_1001.txt"),
            "--timeout-seconds",
            "0",
        ]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().err)["error"]["code"] == "INVALID_INPUT"


def test_cli_reports_provider_configuration_error(tmp_path: Path, capsys) -> None:
    settings = Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
        llm_provider="grok",
        llm_model="grok-4.5",
    )

    exit_code = cli.run(
        ["--invoice_path", str(PROJECT_ROOT / "data/invoices/invoice_1001.txt")],
        settings=settings,
    )

    assert exit_code == 3
    assert json.loads(capsys.readouterr().err)["error"]["code"] == (
        "PROVIDER_NOT_CONFIGURED"
    )


def test_cli_reports_safe_workflow_failure(tmp_path: Path, capsys) -> None:
    malformed = tmp_path / "malformed.pdf"
    malformed.write_bytes(b"not a PDF")
    settings = Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
    )

    exit_code = cli.run(["--invoice_path", str(malformed)], settings=settings)

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 5
    assert payload["status"] == "failed"
    assert payload["error"]["code"] == "UNSUPPORTED_PDF"
    assert list((tmp_path / "uploads").iterdir()) == []


def test_cli_maps_workflow_timeout_to_exit_six(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    now = datetime.now(UTC)

    class TimeoutProcessor:
        def __init__(self, _settings: Settings) -> None:
            pass

        def process_path(self, *_args: object, **_kwargs: object) -> RunDetail:
            return RunDetail(
                run_id=uuid4(),
                source_filename="invoice.txt",
                status=RunStatus.FAILED,
                stage=RunStage.FINALIZE,
                created_at=now,
                updated_at=now,
                error=WorkflowError(
                    code="WORKFLOW_TIMEOUT",
                    message="Workflow exceeded its time limit.",
                ),
            )

        def close(self) -> None:
            pass

    monkeypatch.setattr(cli, "build_invoice_processor", TimeoutProcessor)

    exit_code = cli.run(
        ["--invoice_path", str(PROJECT_ROOT / "data/invoices/invoice_1001.txt")],
        settings=Settings(database_path=tmp_path / "app.db"),
    )

    assert exit_code == 6
    assert json.loads(capsys.readouterr().out)["error"]["code"] == ("WORKFLOW_TIMEOUT")
