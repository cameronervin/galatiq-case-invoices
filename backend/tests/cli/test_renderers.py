from datetime import UTC, datetime
from io import StringIO
from uuid import uuid4

from rich.console import Console

from backend.app.cli.renderers import PrettyCliRenderer
from backend.app.schemas.domain import (
    ApprovalRecommendation,
    DecisionRoute,
    FindingSeverity,
    InvoiceData,
    Money,
    RunDetail,
    RunEvent,
    RunStage,
    RunStatus,
    ValidationFinding,
)


def _detail() -> RunDetail:
    now = datetime.now(UTC)
    return RunDetail(
        run_id=uuid4(),
        source_filename="invoice.xml",
        status=RunStatus.REJECTED,
        stage=RunStage.FINALIZE,
        created_at=now,
        updated_at=now,
        invoice=InvoiceData(
            vendor_name="[red]Literal vendor[/red]\x1b[31m",
            currency="EUR",
            total=Money(amount="10.00", currency="EUR"),
        ),
        findings=[
            ValidationFinding(
                code="INFO_CODE",
                severity=FindingSeverity.INFO,
                message="Informational detail.",
            ),
            ValidationFinding(
                code="BLOCKING_CODE",
                severity=FindingSeverity.BLOCKING,
                field_path="items[0]",
                message="Blocking detail.",
            ),
        ],
        recommendation=ApprovalRecommendation(
            proposed_route=DecisionRoute.REJECT,
            final_route=DecisionRoute.REJECT,
            reason_codes=["BLOCKING_CODE"],
            summary="Blocking validation finding requires rejection.",
            decided_by="policy",
        ),
        events=[
            RunEvent(
                event_id=1,
                stage=RunStage.INGEST,
                status=RunStatus.RUNNING,
                code="INGEST_STARTED",
                message="Invoice ingestion started.",
                created_at=now,
            ),
            RunEvent(
                event_id=2,
                stage=RunStage.FINALIZE,
                status=RunStatus.REJECTED,
                code="RUN_REJECTED",
                message="Invoice was rejected without payment.",
                created_at=now,
            ),
        ],
    )


def test_renderer_groups_findings_preserves_literals_and_missing_values() -> None:
    output = StringIO()
    console = Console(
        file=output,
        width=100,
        force_terminal=True,
        color_system=None,
        no_color=True,
        highlight=False,
    )

    PrettyCliRenderer(console).render_result(_detail())

    rendered = output.getvalue()
    assert "[red]Literal vendor[/red]" in rendered
    assert "10.00 EUR" in rendered
    assert "—" in rendered
    assert rendered.index("BLOCKING_CODE") < rendered.index("INFO_CODE")
    assert "RUN_REJECTED" not in rendered
    assert "\x1b[" not in rendered
    assert "\x1b" not in rendered


def test_renderer_wraps_at_narrow_terminal_width() -> None:
    output = StringIO()
    console = Console(
        file=output,
        width=40,
        force_terminal=False,
        no_color=True,
        highlight=False,
    )

    PrettyCliRenderer(console).render_result(_detail(), show_events=True)

    rendered = output.getvalue()
    assert "RUN_REJECTED" in rendered
    assert max(len(line) for line in rendered.splitlines()) <= 40
