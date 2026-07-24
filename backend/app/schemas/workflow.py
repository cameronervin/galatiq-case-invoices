from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class RunStage(StrEnum):
    INGEST = "ingest"
    EXTRACT = "extract"
    VALIDATE = "validate"
    RECOMMEND = "recommend"
    REVIEW = "review"
    PAY = "pay"
    FINALIZE = "finalize"


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


class DecisionRoute(StrEnum):
    APPROVE = "approve"
    REVIEW = "review"
    REJECT = "reject"


class ValidationFinding(BaseModel):
    code: str
    severity: FindingSeverity
    field_path: str | None = None
    item_line_number: int | None = None
    message: str
    expected: Any | None = None
    actual: Any | None = None


class ApprovalRecommendation(BaseModel):
    proposed_route: DecisionRoute
    final_route: DecisionRoute
    reason_codes: list[str] = Field(default_factory=list)
    summary: str
    reflection_count: int = Field(default=0, ge=0, le=1)
    decided_by: Literal["agent", "policy"] = "agent"
