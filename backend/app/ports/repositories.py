from datetime import datetime
from typing import Protocol
from uuid import UUID

from backend.app.schemas.domain import (
    ApprovalRecommendation,
    HumanReview,
    InvoiceData,
    Money,
    PaymentResult,
    RunDetail,
    RunStage,
    RunStatus,
    RunSummary,
    ValidationFinding,
)


class RunRecordView(Protocol):
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


class RunTransitionConflict(RuntimeError):
    pass


class RunRepository(Protocol):
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
    ) -> tuple[RunRecordView, bool]: ...

    def get_detail(self, run_id: UUID | str) -> RunDetail | None: ...

    def get_internal(self, run_id: UUID | str) -> RunRecordView | None: ...

    def claim_execution(self, run_id: UUID | str) -> bool: ...

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
    ) -> None: ...

    def save_result(
        self,
        run_id: UUID | str,
        *,
        invoice: InvoiceData | None = None,
        findings: list[ValidationFinding] | None = None,
        recommendation: ApprovalRecommendation | None = None,
        extraction_attempts: int | None = None,
        reflection_count: int | None = None,
    ) -> None: ...

    def persist_review(
        self, run_id: UUID | str, review: HumanReview
    ) -> tuple[HumanReview, bool]: ...

    def clear_resume_pending(self, run_id: UUID | str) -> HumanReview | None: ...

    def list_summaries(self, limit: int = 20) -> list[RunSummary]: ...


AgentRunRepository = RunRepository


class InventoryLookupRepository(Protocol):
    def resolve_item(self, source_name: str) -> tuple[str, int, bool] | None: ...


class PaymentStore(Protocol):
    def create_or_get(
        self, run_id: UUID | str, money: Money, idempotency_key: str
    ) -> PaymentResult: ...

    def succeed(self, run_id: UUID | str) -> PaymentResult: ...
