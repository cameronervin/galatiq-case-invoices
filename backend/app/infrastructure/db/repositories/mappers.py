from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from backend.app.infrastructure.db.models import (
    AgentRun,
    Payment,
    RunEventRecord,
    RunResult,
)
from backend.app.schemas.domain import (
    ApprovalRecommendation,
    HumanReview,
    InvoiceData,
    Money,
    PaymentResult,
    RunDetail,
    RunEvent,
    RunStage,
    RunStatus,
    RunSummary,
    ValidationFinding,
    WorkflowError,
)


@dataclass(frozen=True)
class RunRecord:
    run_id: UUID
    content_hash: str
    source_filename: str
    source_path: str
    source_format: str
    source_origin: str
    provider_name: str
    provider_model: str
    status: RunStatus
    stage: RunStage
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


def timestamp(value: datetime | None = None) -> str:
    return (value or datetime.now(UTC)).isoformat().replace("+00:00", "Z")


def json_payload(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in value
        ]
    return value


def to_run_record(row: AgentRun) -> RunRecord:
    return RunRecord(
        run_id=UUID(row.run_id),
        content_hash=row.content_hash,
        source_filename=row.source_filename,
        source_path=row.source_path,
        source_format=row.source_format,
        source_origin=row.source_origin,
        provider_name=row.provider_name,
        provider_model=row.provider_model,
        status=RunStatus(row.status),
        stage=RunStage(row.stage),
        error_code=row.error_code,
        error_message=row.error_message,
        created_at=datetime.fromisoformat(row.created_at.replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(row.updated_at.replace("Z", "+00:00")),
    )


def to_run_summary(row: AgentRun) -> RunSummary:
    return RunSummary(
        run_id=row.run_id,
        source_filename=row.source_filename,
        status=row.status,
        stage=row.stage,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_payment_result(row: Payment) -> PaymentResult:
    return PaymentResult(
        status=row.status,
        amount=Money(
            amount=Decimal(row.amount_cents) / 100,
            currency=row.currency,
        ),
        mock_reference=row.mock_reference,
        error_code=row.error_code,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_run_detail(
    run: AgentRun,
    result: RunResult,
    payment: Payment | None,
    events: list[RunEventRecord],
) -> RunDetail:
    error = None
    if run.error_code:
        error = WorkflowError(
            code=run.error_code,
            message=run.error_message or "Processing failed.",
        )
    return RunDetail(
        **to_run_summary(run).model_dump(),
        invoice=InvoiceData.model_validate(result.invoice) if result.invoice else None,
        findings=[ValidationFinding.model_validate(item) for item in result.findings],
        recommendation=(
            ApprovalRecommendation.model_validate(result.recommendation)
            if result.recommendation
            else None
        ),
        review=HumanReview.model_validate(result.review) if result.review else None,
        payment=to_payment_result(payment) if payment else None,
        events=[
            RunEvent(
                event_id=row.event_id,
                stage=row.stage,
                status=row.status,
                code=row.code,
                message=row.safe_message,
                duration_ms=row.duration_ms,
                created_at=row.created_at,
            )
            for row in events
        ],
        error=error,
    )
