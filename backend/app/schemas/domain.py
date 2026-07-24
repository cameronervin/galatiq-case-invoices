from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


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


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)

    amount: Decimal
    currency: str

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: object) -> Decimal:
        try:
            decimal = Decimal(str(value).replace(",", ""))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("Amount must be a decimal value") from exc
        if decimal.as_tuple().exponent < -2:
            raise ValueError("Amount may contain at most two fractional digits")
        return decimal.quantize(Decimal("0.01"))

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("Currency must be a three-letter ISO code")
        return normalized

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return f"{value:.2f}"

    @property
    def amount_as_decimal(self) -> Decimal:
        return self.amount


class InvoiceItem(BaseModel):
    line_number: int = Field(ge=1)
    source_name: str | None = None
    normalized_item_code: str | None = None
    quantity: int | None = None
    unit_price: Money | None = None
    line_total: Money | None = None


class InvoiceData(BaseModel):
    invoice_number: str | None = None
    revision: str | None = None
    vendor_name: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    currency: str | None = None
    items: list[InvoiceItem] = Field(default_factory=list)
    subtotal: Money | None = None
    tax: Money | None = None
    shipping: Money | None = None
    total: Money | None = None
    payment_terms: str | None = None
    extraction_confidence: Literal["high", "medium", "low"] = "high"

    @field_validator("currency")
    @classmethod
    def normalize_optional_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("Currency must be a three-letter ISO code")
        return normalized


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


class HumanReview(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str = Field(min_length=3, max_length=500)
    resume_pending: bool = True
    decided_at: datetime


class PaymentResult(BaseModel):
    status: Literal["pending", "succeeded", "failed"]
    amount: Money
    mock_reference: str | None = None
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime


class WorkflowError(BaseModel):
    code: str
    message: str


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


class ReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("reason")
    @classmethod
    def trim_reason(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 3:
            raise ValueError("Review reason must contain at least three characters")
        return stripped


class ErrorBody(BaseModel):
    code: str
    message: str
    run_id: UUID | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class WorkerResult(BaseModel):
    run_id: UUID
    status: RunStatus
    error_code: str | None = None
