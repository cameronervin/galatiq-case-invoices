from __future__ import annotations

import re

from backend.app.domain.policies import policy_route
from backend.app.infrastructure.llm.parsing import (
    invoice_number,
    labeled_date,
    labeled_money,
    payment_terms,
    text_items,
    total_money,
    vendor,
)
from backend.app.ports.providers import (
    ApprovalCritique,
    ApprovalProposal,
    ProviderExtraction,
)
from backend.app.schemas.domain import (
    DecisionRoute,
    FindingSeverity,
    InvoiceData,
    ValidationFinding,
)


class OfflineProvider:
    provider_name = "offline"
    model_name = "deterministic-v1"

    def extract_invoice(self, *, document_text: str) -> ProviderExtraction:
        original = document_text
        normalized = original.replace("2O26", "2026").replace(".O0", ".00")
        currency = "EUR" if "EUR" in normalized or "€" in normalized else "USD"
        findings: list[ValidationFinding] = []
        if normalized != original:
            findings.append(
                ValidationFinding(
                    code="OCR_NORMALIZATION",
                    severity=FindingSeverity.WARNING,
                    message=(
                        "OCR-like characters were normalized with visible evidence."
                    ),
                )
            )
        invoice_date = labeled_date(normalized, ("Date", "Dt", "DATE"))
        due_date = labeled_date(normalized, ("Due Date", "Due Dt", "Due", "DUE"))
        if re.search(
            r"(?im)^\s*(?:Due Date|Due Dt|Due|DUE)\s*:\s*yesterday\s*$", normalized
        ):
            findings.append(
                ValidationFinding(
                    code="INVALID_DUE_DATE",
                    severity=FindingSeverity.BLOCKING,
                    field_path="due_date",
                    message="Due date must be an absolute date.",
                )
            )
        invoice = InvoiceData(
            invoice_number=invoice_number(normalized),
            vendor_name=vendor(normalized),
            invoice_date=invoice_date,
            due_date=due_date,
            currency=currency,
            items=text_items(normalized, currency),
            subtotal=labeled_money(normalized, "Subtotal", currency),
            tax=labeled_money(normalized, "(?:Sales )?Tax(?: \\([^)]*\\))?", currency),
            shipping=labeled_money(normalized, "Shipping", currency),
            total=total_money(normalized, currency),
            payment_terms=payment_terms(normalized),
            extraction_confidence="medium" if findings else "high",
        )
        return ProviderExtraction(invoice=invoice, findings=findings)

    def repair_invoice(
        self, *, document_text: str, current: ProviderExtraction, feedback: list[str]
    ) -> ProviderExtraction:
        del current, feedback
        return self.extract_invoice(document_text=document_text)

    def propose_approval(
        self, *, invoice: InvoiceData, findings: list[ValidationFinding]
    ) -> ApprovalProposal:
        route = policy_route(invoice, findings)
        codes = [finding.code for finding in findings]
        summary = {
            DecisionRoute.APPROVE: "Invoice is eligible for automatic mock payment.",
            DecisionRoute.REVIEW: "Invoice requires human review before mock payment.",
            DecisionRoute.REJECT: "Invoice contains blocking validation findings.",
        }[route]
        return ApprovalProposal(
            proposed_route=route,
            reason_codes=codes,
            summary=summary,
        )

    def critique_approval(
        self,
        *,
        invoice: InvoiceData,
        findings: list[ValidationFinding],
        proposal: ApprovalProposal,
    ) -> ApprovalCritique:
        expected = policy_route(invoice, findings)
        if proposal.proposed_route == expected:
            return ApprovalCritique(accepted=True, feedback=[])
        return ApprovalCritique(
            accepted=False,
            feedback=[f"Policy requires route {expected.value}."],
        )
