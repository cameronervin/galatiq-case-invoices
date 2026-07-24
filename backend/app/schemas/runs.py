from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.schemas.errors import WorkflowError
from backend.app.schemas.invoice import InvoiceData
from backend.app.schemas.payment import PaymentResult
from backend.app.schemas.review import HumanReview
from backend.app.schemas.workflow import (
    ApprovalRecommendation,
    RunStage,
    RunStatus,
    ValidationFinding,
)


class RunEvent(BaseModel):
    event_id: int
    stage: RunStage
    status: RunStatus
    code: str
    message: str
    duration_ms: int | None = None
    created_at: datetime


class RunSummary(BaseModel):
    run_id: UUID
    source_filename: str
    status: RunStatus
    stage: RunStage
    created_at: datetime
    updated_at: datetime


class RunCreationResponse(RunSummary):
    deduplicated: bool


class RunDetail(RunSummary):
    invoice: InvoiceData | None = None
    findings: list[ValidationFinding] = Field(default_factory=list)
    recommendation: ApprovalRecommendation | None = None
    review: HumanReview | None = None
    payment: PaymentResult | None = None
    events: list[RunEvent] = Field(default_factory=list)
    error: WorkflowError | None = None


class RunListResponse(BaseModel):
    items: list[RunSummary]


class WorkerResult(BaseModel):
    run_id: UUID
    status: RunStatus
    error_code: str | None = None
