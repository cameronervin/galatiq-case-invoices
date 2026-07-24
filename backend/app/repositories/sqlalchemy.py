from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from backend.app.infrastructure.db.session import SessionContext
from backend.app.models import (
    AgentRun,
    InventoryItem,
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


def utc_now() -> datetime:
    return datetime.now(UTC)


def _timestamp(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat().replace("+00:00", "Z")


def _payload(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in value
        ]
    return value


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


class ReviewPersistenceConflict(RuntimeError):
    pass


class InventoryRepository:
    def __init__(self, sessions: SessionContext) -> None:
        self.sessions = sessions

    def resolve_item(self, source_name: str) -> tuple[str, int, bool] | None:
        normalized = " ".join(source_name.strip().lower().split())
        with self.sessions(write=False) as session:
            items = session.scalars(select(InventoryItem)).all()
            for item in items:
                if normalized in item.aliases:
                    canonical = normalized == item.item_code.lower()
                    return item.item_code, item.stock, not canonical
        return None


class RunRepository:
    def __init__(self, sessions: SessionContext) -> None:
        self.sessions = sessions

    def create_run(
        self,
        *,
        content_hash: str,
        source_filename: str,
        source_path: str,
        source_format: str,
        source_origin: str,
        provider_name: str,
        provider_model: str,
    ) -> tuple[RunRecord, bool]:
        existing = self._active_profile(content_hash, provider_name, provider_model)
        if existing is not None:
            return existing, True

        now = _timestamp()
        run = AgentRun(
            run_id=str(uuid4()),
            content_hash=content_hash,
            source_filename=source_filename,
            source_path=source_path,
            source_format=source_format,
            source_origin=source_origin,
            provider_name=provider_name,
            provider_model=provider_model,
            status=RunStatus.QUEUED.value,
            stage=RunStage.INGEST.value,
            created_at=now,
            updated_at=now,
        )
        try:
            with self.sessions(write=True) as session:
                session.add(run)
                session.add(RunResult(run_id=run.run_id, findings=[], updated_at=now))
                session.add(
                    RunEventRecord(
                        run_id=run.run_id,
                        stage=RunStage.INGEST.value,
                        status=RunStatus.QUEUED.value,
                        code="RUN_QUEUED",
                        safe_message="Run queued.",
                        created_at=now,
                    )
                )
                session.flush()
                record = self._record(run)
        except IntegrityError:
            existing = self._active_profile(
                content_hash,
                provider_name,
                provider_model,
            )
            if existing is None:
                raise
            return existing, True
        return record, False

    def get_internal(self, run_id: UUID | str) -> RunRecord | None:
        with self.sessions(write=False) as session:
            row = session.get(AgentRun, str(run_id))
            return self._record(row) if row is not None else None

    def transition(
        self,
        run_id: UUID | str,
        *,
        status: RunStatus,
        stage: RunStage,
        event_code: str,
        message: str,
        error_code: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        now = _timestamp()
        terminal = status in {RunStatus.COMPLETED, RunStatus.REJECTED, RunStatus.FAILED}
        with self.sessions(write=True) as session:
            run = session.get(AgentRun, str(run_id))
            if run is None:
                raise KeyError(f"Unknown run: {run_id}")
            run.status = status.value
            run.stage = stage.value
            run.error_code = error_code
            run.error_message = message if error_code else None
            run.updated_at = now
            if terminal:
                run.completed_at = now
            session.add(
                RunEventRecord(
                    run_id=str(run_id),
                    stage=stage.value,
                    status=status.value,
                    code=event_code,
                    safe_message=message,
                    duration_ms=duration_ms,
                    created_at=now,
                )
            )

    def save_result(
        self,
        run_id: UUID | str,
        *,
        invoice: InvoiceData | None = None,
        findings: list[ValidationFinding] | None = None,
        recommendation: ApprovalRecommendation | None = None,
        extraction_attempts: int | None = None,
        reflection_count: int | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                invoice,
                findings,
                recommendation,
                extraction_attempts,
                reflection_count,
            )
        ):
            return
        with self.sessions(write=True) as session:
            result = session.get(RunResult, str(run_id))
            if result is None:
                raise KeyError(f"Unknown run: {run_id}")
            if invoice is not None:
                result.invoice = _payload(invoice)
            if findings is not None:
                result.findings = _payload(findings)
            if recommendation is not None:
                result.recommendation = _payload(recommendation)
            if extraction_attempts is not None:
                result.extraction_attempts = extraction_attempts
            if reflection_count is not None:
                result.reflection_count = reflection_count
            result.updated_at = _timestamp()

    def persist_review(
        self,
        run_id: UUID | str,
        review: HumanReview,
    ) -> tuple[HumanReview, bool]:
        identifier = str(run_id)
        with self.sessions(write=True) as session:
            run = session.get(AgentRun, identifier)
            result = session.get(RunResult, identifier)
            if run is None or result is None:
                raise KeyError(f"Unknown run: {run_id}")
            if run.status != RunStatus.REVIEW_REQUIRED.value:
                raise ReviewPersistenceConflict("Run is not awaiting review.")
            if result.review is not None:
                return self._review_result(result.review, review)

            payload = _payload(review)
            changed = session.execute(
                update(RunResult)
                .where(RunResult.run_id == identifier, RunResult.review.is_(None))
                .values(review=payload, updated_at=_timestamp())
            ).rowcount
            if changed == 1:
                return review, False
            session.refresh(result)
            if result.review is None:
                raise ReviewPersistenceConflict("Review could not be persisted.")
            return self._review_result(result.review, review)

    def clear_resume_pending(self, run_id: UUID | str) -> HumanReview | None:
        identifier = str(run_id)
        with self.sessions(write=True) as session:
            result = session.get(RunResult, identifier)
            if result is None:
                raise KeyError(f"Unknown run: {run_id}")
            if result.review is None:
                return None
            review = HumanReview.model_validate(result.review)
            if not review.resume_pending:
                return None
            updated_review = review.model_copy(update={"resume_pending": False})
            original = result.review
            changed = session.execute(
                update(RunResult)
                .where(RunResult.run_id == identifier, RunResult.review == original)
                .values(review=_payload(updated_review), updated_at=_timestamp())
            ).rowcount
            return updated_review if changed == 1 else None

    def list_summaries(self, limit: int = 20) -> list[RunSummary]:
        statement = (
            select(AgentRun)
            .order_by(AgentRun.created_at.desc(), AgentRun.run_id.desc())
            .limit(limit)
        )
        with self.sessions(write=False) as session:
            return [self._summary(row) for row in session.scalars(statement)]

    def get_detail(self, run_id: UUID | str) -> RunDetail | None:
        identifier = str(run_id)
        with self.sessions(write=False) as session:
            run = session.get(AgentRun, identifier)
            if run is None:
                return None
            result = session.get(RunResult, identifier)
            payment = session.get(Payment, identifier)
            events = session.scalars(
                select(RunEventRecord)
                .where(RunEventRecord.run_id == identifier)
                .order_by(RunEventRecord.event_id)
            ).all()
            if result is None:
                raise RuntimeError(f"Run result missing: {run_id}")
            return self._detail(run, result, payment, events)

    def _active_profile(
        self,
        content_hash: str,
        provider_name: str,
        provider_model: str,
    ) -> RunRecord | None:
        statement = (
            select(AgentRun)
            .where(
                AgentRun.content_hash == content_hash,
                AgentRun.provider_name == provider_name,
                AgentRun.provider_model == provider_model,
                AgentRun.status != RunStatus.FAILED.value,
            )
            .order_by(AgentRun.created_at.desc())
            .limit(1)
        )
        with self.sessions(write=False) as session:
            row = session.scalar(statement)
            return self._record(row) if row is not None else None

    @staticmethod
    def _review_result(
        stored_payload: dict[str, Any],
        requested: HumanReview,
    ) -> tuple[HumanReview, bool]:
        existing = HumanReview.model_validate(stored_payload)
        identical_pending = (
            existing.decision == requested.decision
            and existing.reason == requested.reason
            and existing.resume_pending
        )
        return existing, identical_pending

    @staticmethod
    def _record(row: AgentRun) -> RunRecord:
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

    @staticmethod
    def _summary(row: AgentRun) -> RunSummary:
        return RunSummary(
            run_id=row.run_id,
            source_filename=row.source_filename,
            status=row.status,
            stage=row.stage,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @classmethod
    def _detail(
        cls,
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
            **cls._summary(run).model_dump(),
            invoice=InvoiceData.model_validate(result.invoice)
            if result.invoice
            else None,
            findings=[
                ValidationFinding.model_validate(item) for item in result.findings
            ],
            recommendation=(
                ApprovalRecommendation.model_validate(result.recommendation)
                if result.recommendation
                else None
            ),
            review=(
                HumanReview.model_validate(result.review) if result.review else None
            ),
            payment=PaymentRepository._payment(payment) if payment else None,
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


class PaymentRepository:
    def __init__(self, sessions: SessionContext) -> None:
        self.sessions = sessions

    def create_or_get(
        self,
        run_id: UUID | str,
        money: Money,
        idempotency_key: str,
    ) -> PaymentResult:
        identifier = str(run_id)
        with self.sessions(write=False) as session:
            existing = session.get(Payment, identifier)
            if existing is not None:
                return self._payment(existing)

        now = _timestamp()
        payment = Payment(
            run_id=identifier,
            idempotency_key=idempotency_key,
            status="pending",
            amount_cents=int(money.amount * 100),
            currency=money.currency,
            created_at=now,
            updated_at=now,
        )
        try:
            with self.sessions(write=True) as session:
                session.add(payment)
                session.flush()
                result = self._payment(payment)
        except IntegrityError:
            with self.sessions(write=False) as session:
                existing = session.get(Payment, identifier)
                if existing is None:
                    raise
                return self._payment(existing)
        return result

    def succeed(self, run_id: UUID | str) -> PaymentResult:
        identifier = str(run_id)
        now = _timestamp()
        mock_reference = f"MOCK-{identifier[:8].upper()}"
        with self.sessions(write=True) as session:
            session.execute(
                update(Payment)
                .where(Payment.run_id == identifier, Payment.status == "pending")
                .values(
                    status="succeeded",
                    mock_reference=mock_reference,
                    updated_at=now,
                )
            )
            payment = session.get(Payment, identifier)
            if payment is None:
                raise KeyError(f"Unknown payment run: {run_id}")
            session.refresh(payment)
            return self._payment(payment)

    @staticmethod
    def _payment(row: Payment) -> PaymentResult:
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
