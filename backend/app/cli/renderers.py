from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Final
from unicodedata import category

from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from backend.app.schemas.domain import (
    ErrorEnvelope,
    FindingSeverity,
    Money,
    RunDetail,
    RunEvent,
    RunStatus,
    ValidationFinding,
)

MISSING: Final = "—"
SEVERITY_ORDER: Final = {
    FindingSeverity.BLOCKING: 0,
    FindingSeverity.WARNING: 1,
    FindingSeverity.INFO: 2,
}
STATUS_PRESENTATION: Final = {
    RunStatus.COMPLETED: ("✓", "Invoice completed", "green"),
    RunStatus.REJECTED: ("✗", "Invoice rejected", "red"),
    RunStatus.REVIEW_REQUIRED: ("!", "Review required", "yellow"),
    RunStatus.FAILED: ("✗", "Processing failed", "bold red"),
    RunStatus.QUEUED: ("•", "Invoice queued", "cyan"),
    RunStatus.RUNNING: ("•", "Invoice processing", "cyan"),
}


class PrettyCliRenderer:
    """Render public workflow artifacts without exposing internal state."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def render_result(self, detail: RunDetail, *, show_events: bool = False) -> None:
        sections: list[RenderableType] = [self._outcome(detail), self._run(detail)]
        if detail.invoice is not None:
            sections.append(self._invoice(detail))
        sections.append(self._findings(detail.findings))
        if detail.recommendation is not None:
            sections.append(self._decision(detail))
        if detail.review is not None:
            sections.append(self._review(detail))
        if detail.payment is not None:
            sections.append(self._payment(detail))
        if detail.error is not None:
            sections.append(
                self._error_panel(
                    code=detail.error.code,
                    message=detail.error.message,
                    title="Workflow error",
                )
            )
        if detail.events:
            sections.append(self._timeline(detail.events, expanded=show_events))
        sections.append(self._next_action(detail.status))
        self.console.print(Group(*sections))

    def render_error(self, envelope: ErrorEnvelope) -> None:
        error = envelope.error
        title = {
            "INVALID_INPUT": "Input error",
            "PROVIDER_NOT_CONFIGURED": "Configuration error",
        }.get(error.code, "Error")
        self.console.print(
            self._error_panel(code=error.code, message=error.message, title=title)
        )

    def _outcome(self, detail: RunDetail) -> Panel:
        symbol, label, style = STATUS_PRESENTATION[detail.status]
        text = Text()
        text.append(f"{symbol} ", style=style)
        text.append(label, style=f"bold {style}")
        return Panel(text, border_style=style, padding=(0, 1))

    def _run(self, detail: RunDetail) -> Panel:
        elapsed_ms = max(
            0, round((detail.updated_at - detail.created_at).total_seconds() * 1000)
        )
        rows = (
            ("Source", detail.source_filename),
            ("Run ID", str(detail.run_id)),
            ("Final stage", detail.stage.value),
            ("Elapsed", _format_duration(elapsed_ms)),
        )
        return Panel(_key_value_grid(rows), title="Run", border_style="blue")

    def _invoice(self, detail: RunDetail) -> Panel:
        invoice = detail.invoice
        assert invoice is not None
        rows = (
            ("Invoice", invoice.invoice_number),
            ("Revision", invoice.revision),
            ("Vendor", invoice.vendor_name),
            ("Invoice date", invoice.invoice_date),
            ("Due date", invoice.due_date),
            ("Total", _format_money(invoice.total)),
            ("Items", str(len(invoice.items))),
            ("Terms", invoice.payment_terms),
            ("Confidence", invoice.extraction_confidence),
        )
        return Panel(_key_value_grid(rows), title="Invoice", border_style="blue")

    def _findings(self, findings: list[ValidationFinding]) -> Panel:
        if not findings:
            return Panel(
                Text("✓ No validation findings", style="green"),
                title="Findings",
                border_style="green",
            )
        ordered = sorted(findings, key=_finding_key)
        if self.console.width < 70:
            rows = Table.grid(expand=True, padding=(0, 0))
            rows.add_column(overflow="fold")
            for finding in ordered:
                style = {
                    FindingSeverity.BLOCKING: "red",
                    FindingSeverity.WARNING: "yellow",
                    FindingSeverity.INFO: "cyan",
                }[finding.severity]
                entry = Text()
                entry.append(
                    f"{finding.severity.value} · {_display(finding.code)}", style=style
                )
                entry.append(f"\nField: {_display(finding.field_path)}")
                entry.append(f"\n{_display(finding.message)}")
                rows.add_row(entry)
            return Panel(rows, title="Findings", border_style="yellow")
        table = Table(expand=True, box=None, pad_edge=False)
        table.add_column("Severity", no_wrap=True)
        table.add_column("Code", overflow="fold")
        table.add_column("Field", overflow="fold")
        table.add_column("Message", ratio=2, overflow="fold")
        for finding in ordered:
            style = {
                FindingSeverity.BLOCKING: "red",
                FindingSeverity.WARNING: "yellow",
                FindingSeverity.INFO: "cyan",
            }[finding.severity]
            table.add_row(
                Text(finding.severity.value, style=style),
                _text(finding.code),
                _text(finding.field_path),
                _text(finding.message),
            )
        return Panel(table, title="Findings", border_style="yellow")

    def _decision(self, detail: RunDetail) -> Panel:
        recommendation = detail.recommendation
        assert recommendation is not None
        rows = (
            ("Proposed route", recommendation.proposed_route.value),
            ("Final route", recommendation.final_route.value),
            ("Decided by", recommendation.decided_by),
            ("Critique revisions", str(recommendation.reflection_count)),
            ("Reason codes", ", ".join(recommendation.reason_codes) or MISSING),
            ("Summary", recommendation.summary),
        )
        return Panel(_key_value_grid(rows), title="Decision", border_style="magenta")

    def _review(self, detail: RunDetail) -> Panel:
        review = detail.review
        assert review is not None
        rows = (
            ("Decision", review.decision),
            ("Reason", review.reason),
            ("Resume pending", "yes" if review.resume_pending else "no"),
            ("Decided at", _format_timestamp(review.decided_at)),
        )
        return Panel(_key_value_grid(rows), title="Human review", border_style="yellow")

    def _payment(self, detail: RunDetail) -> Panel:
        payment = detail.payment
        assert payment is not None
        status = {
            "succeeded": "✓ Simulated payment succeeded",
            "pending": "• Simulated payment pending",
            "failed": "✗ Simulated payment failed",
        }[payment.status]
        rows = (
            ("Status", status),
            ("Amount", _format_money(payment.amount)),
            ("Reference", payment.mock_reference),
            ("Error code", payment.error_code),
        )
        style = "green" if payment.status == "succeeded" else "yellow"
        return Panel(_key_value_grid(rows), title="Payment", border_style=style)

    def _timeline(self, events: list[RunEvent], *, expanded: bool) -> Panel:
        selected = events if expanded else list(_last_event_by_stage(events))
        if self.console.width < 70:
            return self._narrow_timeline(selected, expanded=expanded)
        table = Table(expand=True, box=None, pad_edge=False)
        if expanded:
            table.add_column("Time", no_wrap=True)
            table.add_column("Stage", no_wrap=True)
            table.add_column("Code", overflow="fold")
            table.add_column("Message", ratio=2, overflow="fold")
            table.add_column("Duration", no_wrap=True)
            for event in selected:
                table.add_row(
                    Text(_format_timestamp(event.created_at, time_only=True)),
                    Text(event.stage.value),
                    _text(event.code),
                    _text(event.message),
                    Text(_format_duration(event.duration_ms)),
                )
        else:
            table.add_column("Stage", no_wrap=True)
            table.add_column("Status", no_wrap=True)
            table.add_column("Last event", ratio=2, overflow="fold")
            for event in selected:
                table.add_row(
                    Text(event.stage.value),
                    Text(event.status.value),
                    _text(event.message),
                )
        title = "Timeline · all events" if expanded else "Timeline · stage summary"
        return Panel(table, title=title, border_style="cyan")

    def _narrow_timeline(self, events: list[RunEvent], *, expanded: bool) -> Panel:
        table = Table.grid(expand=True, padding=(0, 0))
        table.add_column(overflow="fold")
        for event in events:
            entry = Text()
            if expanded:
                entry.append(
                    f"{_format_timestamp(event.created_at, time_only=True)} · "
                    f"{event.stage.value} · {_display(event.code)}"
                )
                entry.append(f"\n{_display(event.message)}")
                if event.duration_ms is not None:
                    entry.append(f" · {_format_duration(event.duration_ms)}")
            else:
                entry.append(f"{event.stage.value} · {event.status.value}")
                entry.append(f"\n{_display(event.message)}")
            table.add_row(entry)
        title = "Timeline · all events" if expanded else "Timeline · stage summary"
        return Panel(table, title=title, border_style="cyan")

    def _next_action(self, status: RunStatus) -> Panel:
        message = {
            RunStatus.COMPLETED: (
                "No action required. Payment was simulated; no funds moved."
            ),
            RunStatus.REJECTED: (
                "Correct the blocking invoice data and resubmit the source document."
            ),
            RunStatus.REVIEW_REQUIRED: (
                "Use the API or web workspace to approve or reject this run."
            ),
            RunStatus.FAILED: "Resolve the reported error and resubmit the invoice.",
            RunStatus.QUEUED: "Inspect this run through the API or web workspace.",
            RunStatus.RUNNING: "Inspect this run through the API or web workspace.",
        }[status]
        return Panel(Text(message), title="Next action", border_style="blue")

    def _error_panel(self, *, code: str, message: str, title: str) -> Panel:
        rows = (
            ("Code", code),
            ("Message", message),
            ("Next action", "Correct the issue and run the command again."),
        )
        return Panel(_key_value_grid(rows), title=title, border_style="red")


def _key_value_grid(rows: Iterable[tuple[str, object]]) -> Table:
    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(style="bold", no_wrap=True)
    table.add_column(ratio=1, overflow="fold")
    for key, value in rows:
        table.add_row(Text(key), Text(_display(value)))
    return table


def _display(value: object | None) -> str:
    if value is None or value == "":
        return MISSING
    return "".join(
        " " if category(character) in {"Cc", "Cf", "Cs"} else character
        for character in str(value)
    )


def _text(value: object | None) -> Text:
    return Text(_display(value))


def _format_money(money: Money | None) -> str:
    if money is None:
        return MISSING
    return f"{money.amount:,.2f} {money.currency}"


def _format_duration(duration_ms: int | None) -> str:
    if duration_ms is None:
        return MISSING
    if duration_ms < 1000:
        return f"{duration_ms} ms"
    return f"{duration_ms / 1000:.2f} s"


def _format_timestamp(value: datetime, *, time_only: bool = False) -> str:
    if time_only:
        return value.strftime("%H:%M:%S")
    return value.isoformat().replace("+00:00", "Z")


def _finding_key(finding: ValidationFinding) -> tuple[int, str, str, int]:
    return (
        SEVERITY_ORDER[finding.severity],
        finding.code,
        finding.field_path or "",
        finding.item_line_number or 0,
    )


def _last_event_by_stage(events: list[RunEvent]) -> Iterable[RunEvent]:
    last_by_stage: dict[str, RunEvent] = {}
    stage_order: list[str] = []
    for event in events:
        stage = event.stage.value
        if stage not in last_by_stage:
            stage_order.append(stage)
        last_by_stage[stage] = event
    return (last_by_stage[stage] for stage in stage_order)
