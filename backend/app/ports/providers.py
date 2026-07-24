from typing import Protocol

from pydantic import BaseModel, Field

from backend.app.schemas.domain import (
    DecisionRoute,
    InvoiceData,
    ValidationFinding,
)


class ProviderConfigurationError(RuntimeError):
    pass


class ProviderError(RuntimeError):
    def __init__(
        self, code: str, message: str, *, retryable: bool = False
    ) -> None:
        super().__init__(message)
        self.code = code
        self.safe_message = message
        self.retryable = retryable


class ProviderExtraction(BaseModel):
    invoice: InvoiceData
    findings: list[ValidationFinding] = Field(default_factory=list)


class ApprovalProposal(BaseModel):
    proposed_route: DecisionRoute
    reason_codes: list[str] = Field(default_factory=list)
    summary: str


class ApprovalCritique(BaseModel):
    accepted: bool
    feedback: list[str] = Field(default_factory=list)


class LLMProvider(Protocol):
    provider_name: str
    model_name: str

    def extract_invoice(self, *, document_text: str) -> ProviderExtraction: ...

    def repair_invoice(
        self, *, document_text: str, current: ProviderExtraction, feedback: list[str]
    ) -> ProviderExtraction: ...

    def propose_approval(
        self, *, invoice: InvoiceData, findings: list[ValidationFinding]
    ) -> ApprovalProposal: ...

    def critique_approval(
        self,
        *,
        invoice: InvoiceData,
        findings: list[ValidationFinding],
        proposal: ApprovalProposal,
    ) -> ApprovalCritique: ...


class ProviderResolver(Protocol):
    def get(self, provider_name: str, model_name: str) -> LLMProvider: ...
