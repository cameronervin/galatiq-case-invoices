from typing import TypedDict

from backend.app.ports.providers import ApprovalProposal
from backend.app.schemas.domain import (
    ApprovalRecommendation,
    HumanReview,
    InvoiceData,
    PaymentResult,
    RunStage,
    RunStatus,
    ValidationFinding,
    WorkflowError,
)


class InvoiceProcessingState(TypedDict, total=False):
    run_id: str
    status: RunStatus
    stage: RunStage
    invoice: InvoiceData | None
    findings: list[ValidationFinding]
    proposal: ApprovalProposal | None
    recommendation: ApprovalRecommendation | None
    review: HumanReview | None
    payment: PaymentResult | None
    extraction_attempts: int
    reflection_count: int
    error: WorkflowError | None
