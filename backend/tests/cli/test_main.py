import json
from datetime import UTC, datetime
from io import StringIO
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


class _TerminalBuffer(StringIO):
    def isatty(self) -> bool:
        return True


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
            "--format",
            "json",
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
        [
            "--invoice_path",
            str(PROJECT_ROOT / "data/invoices" / filename),
            "--format",
            "json",
        ],
        settings=settings,
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["status"] == expected_status


def test_cli_rejects_invalid_input_before_processing(tmp_path: Path, capsys) -> None:
    exit_code = cli.run(
        [
            "--invoice_path",
            str(tmp_path / "missing.pdf"),
            "--format",
            "json",
        ]
    )

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
            "--format",
            "json",
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
        [
            "--invoice_path",
            str(PROJECT_ROOT / "data/invoices/invoice_1001.txt"),
            "--format",
            "json",
        ],
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

    exit_code = cli.run(
        ["--invoice_path", str(malformed), "--format", "json"], settings=settings
    )

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
        [
            "--invoice_path",
            str(PROJECT_ROOT / "data/invoices/invoice_1001.txt"),
            "--format",
            "json",
        ],
        settings=Settings(database_path=tmp_path / "app.db"),
    )

    assert exit_code == 6
    assert json.loads(capsys.readouterr().out)["error"]["code"] == ("WORKFLOW_TIMEOUT")


def test_cli_defaults_to_pretty_output_with_upstream_flag(
    tmp_path: Path, capsys
) -> None:
    settings = Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
    )

    exit_code = cli.run(
        [
            "--invoice_path",
            str(PROJECT_ROOT / "data/invoices/invoice_1001.txt"),
            "--no-color",
        ],
        settings=settings,
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Invoice completed" in output
    assert "INV-1001" in output
    assert "5,000.00 USD" in output
    assert "No validation findings" in output
    assert "Simulated payment succeeded" in output
    assert "PAYMENT_SUCCEEDED" not in output
    assert str(PROJECT_ROOT) not in output
    assert not output.lstrip().startswith("{")


def test_cli_accepts_hyphenated_invoice_path_alias(tmp_path: Path, capsys) -> None:
    settings = Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
    )

    exit_code = cli.run(
        [
            "--invoice-path",
            str(PROJECT_ROOT / "data/invoices/invoice_1001.txt"),
            "--format",
            "json",
        ],
        settings=settings,
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "completed"


@pytest.mark.parametrize(
    ("filename", "expected_text"),
    [
        ("invoice_1002.txt", "Invoice rejected"),
        ("invoice_1012.txt", "Review required"),
    ],
)
def test_pretty_output_explains_non_payment_outcomes(
    tmp_path: Path,
    capsys,
    filename: str,
    expected_text: str,
) -> None:
    settings = Settings(
        database_path=tmp_path / f"{filename}.db",
        upload_dir=tmp_path / f"{filename}-uploads",
    )

    exit_code = cli.run(
        [
            "--invoice-path",
            str(PROJECT_ROOT / "data/invoices" / filename),
            "--no-color",
        ],
        settings=settings,
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert expected_text in output
    assert "Findings" in output
    assert "Decision" in output
    assert "Next action" in output


def test_show_events_expands_pretty_timeline(tmp_path: Path, capsys) -> None:
    settings = Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
    )

    exit_code = cli.run(
        [
            "--invoice-path",
            str(PROJECT_ROOT / "data/invoices/invoice_1001.txt"),
            "--show-events",
            "--no-color",
        ],
        settings=settings,
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "RUN_QUEUED" in output
    assert "PAYMENT_SUCCEEDED" in output


def test_pretty_input_error_is_human_readable(tmp_path: Path, capsys) -> None:
    exit_code = cli.run(
        ["--invoice-path", str(tmp_path / "missing.pdf"), "--no-color"]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "Input error" in captured.err
    assert "INVALID_INPUT" in captured.err
    assert str(tmp_path) not in captured.err


def test_pretty_configuration_error_is_human_readable(tmp_path: Path, capsys) -> None:
    settings = Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
        llm_provider="grok",
        llm_model="grok-4.5",
    )

    exit_code = cli.run(
        [
            "--invoice-path",
            str(PROJECT_ROOT / "data/invoices/invoice_1001.txt"),
            "--no-color",
        ],
        settings=settings,
    )

    captured = capsys.readouterr()
    assert exit_code == 3
    assert captured.out == ""
    assert "Configuration error" in captured.err
    assert "PROVIDER_NOT_CONFIGURED" in captured.err


def test_pretty_workflow_failure_is_human_readable(tmp_path: Path, capsys) -> None:
    malformed = tmp_path / "malformed.pdf"
    malformed.write_bytes(b"not a PDF")
    settings = Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
    )

    exit_code = cli.run(
        ["--invoice-path", str(malformed), "--no-color"], settings=settings
    )

    captured = capsys.readouterr()
    assert exit_code == 5
    assert captured.err == ""
    assert "Processing failed" in captured.out
    assert "Workflow error" in captured.out
    assert "UNSUPPORTED_PDF" in captured.out
    assert str(tmp_path) not in captured.out


@pytest.mark.parametrize(
    ("no_color", "use_environment"),
    [(True, False), (False, True)],
)
def test_no_color_modes_disable_terminal_styling(
    monkeypatch, no_color: bool, use_environment: bool
) -> None:
    monkeypatch.setenv("TERM", "xterm-256color")
    if use_environment:
        monkeypatch.setenv("NO_COLOR", "")
    else:
        monkeypatch.delenv("NO_COLOR", raising=False)
    output = _TerminalBuffer()

    console = cli._console(output, no_color=no_color)
    console.print("styled", style="bold red")

    assert console.no_color is True
    assert console.color_system is None
    assert "\x1b" not in output.getvalue()


def test_console_preserves_terminal_styling_by_default(monkeypatch) -> None:
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.delenv("NO_COLOR", raising=False)
    output = _TerminalBuffer()

    console = cli._console(output, no_color=False)
    console.print("styled", style="bold red")

    assert console.color_system is not None
    assert "\x1b" in output.getvalue()
