from __future__ import annotations

import re
import time
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import cast

from langgraph.runtime import Runtime
from langgraph.types import interrupt

from backend.app.agents.runtime_context import AgentRuntimeContext
from backend.app.agents.states import InvoiceProcessingState
from backend.app.infrastructure.llm.base import ProviderExtraction
from backend.app.schemas.domain import (
    ApprovalRecommendation,
    DecisionRoute,
    FindingSeverity,
    InvoiceData,
    InvoiceItem,
    RunStage,
    RunStatus,
    ValidationFinding,
)
from backend.app.services.document_loaders import load_document


def ingest_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    _check_deadline(runtime.context)
    runtime.context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.INGEST,
        event_code="INGEST_STARTED",
        message="Invoice ingestion started.",
    )
    return {"status": RunStatus.RUNNING, "stage": RunStage.INGEST}


def extraction_agent_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    _check_deadline(context)
    record = _run(context, state["run_id"])
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.EXTRACT,
        event_code="EXTRACTION_STARTED",
        message="Extraction agent started.",
    )
    loaded = load_document(
        Path(record.source_path), default_currency=context.settings.default_currency
    )
    attempts = 0
    if loaded.invoice is not None:
        extraction = ProviderExtraction(
            invoice=loaded.invoice,
            findings=loaded.findings,
        )
    else:
        provider = context.provider_registry.get(
            record.provider_name, record.provider_model
        )
        extraction = provider.extract_invoice(document_text=loaded.text or "")
        attempts = 1
        feedback = _extraction_feedback(extraction.invoice)
        if feedback:
            _check_deadline(context)
            extraction = provider.repair_invoice(
                document_text=loaded.text or "",
                current=extraction,
                feedback=feedback,
            )
            attempts = 2
            context.run_repository.transition(
                state["run_id"],
                status=RunStatus.RUNNING,
                stage=RunStage.EXTRACT,
                event_code="EXTRACTION_REPAIRED",
                message="Extraction agent performed one bounded repair.",
            )
    context.run_repository.save_result(
        state["run_id"],
        invoice=extraction.invoice,
        findings=extraction.findings,
        extraction_attempts=attempts,
    )
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.EXTRACT,
        event_code="EXTRACTION_COMPLETED",
        message="Extraction agent produced a typed invoice.",
    )
    return {
        "invoice": extraction.invoice,
        "findings": extraction.findings,
        "extraction_attempts": attempts,
        "stage": RunStage.EXTRACT,
    }


def validation_agent_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    _check_deadline(context)
    invoice = state.get("invoice")
    if invoice is None:
        raise RuntimeError("Extraction did not produce an invoice")
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.VALIDATE,
        event_code="INVENTORY_TOOL_CALLED",
        message="Validation agent invoked the read-only inventory tool.",
    )
    findings = list(state.get("findings", []))
    findings.extend(_integrity_findings(invoice, context, state["run_id"]))
    normalized_items, inventory_findings = _inventory_findings(invoice, context)
    findings.extend(inventory_findings)
    findings = _ordered_unique(findings)
    normalized_invoice = invoice.model_copy(update={"items": normalized_items})
    context.run_repository.save_result(
        state["run_id"], invoice=normalized_invoice, findings=findings
    )
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.VALIDATE,
        event_code="VALIDATION_COMPLETED",
        message="Deterministic validation completed.",
    )
    return {
        "invoice": normalized_invoice,
        "findings": findings,
        "stage": RunStage.VALIDATE,
    }


def approval_agent_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    _check_deadline(context)
    invoice = _invoice(state)
    record = _run(context, state["run_id"])
    provider = context.provider_registry.get(
        record.provider_name, record.provider_model
    )
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.RECOMMEND,
        event_code="APPROVAL_PROPOSED",
        message="Approval agent produced a recommendation.",
    )
    proposal = provider.propose_approval(
        invoice=invoice, findings=state.get("findings", [])
    )
    return {"proposal": proposal, "stage": RunStage.RECOMMEND}


def critic_agent_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    _check_deadline(context)
    proposal = state.get("proposal")
    if proposal is None:
        raise RuntimeError("Approval proposal is missing")
    invoice = _invoice(state)
    record = _run(context, state["run_id"])
    provider = context.provider_registry.get(
        record.provider_name, record.provider_model
    )
    critique = provider.critique_approval(
        invoice=invoice,
        findings=state.get("findings", []),
        proposal=proposal,
    )
    reflection_count = 0
    if not critique.accepted:
        _check_deadline(context)
        proposal = provider.propose_approval(
            invoice=invoice, findings=state.get("findings", [])
        )
        reflection_count = 1
        context.run_repository.transition(
            state["run_id"],
            status=RunStatus.RUNNING,
            stage=RunStage.RECOMMEND,
            event_code="APPROVAL_REVISED",
            message="Approval agent revised its proposal after critique.",
        )
    final_route = policy_route(invoice, state.get("findings", []))
    override = proposal.proposed_route != final_route
    reason_codes = list(proposal.reason_codes)
    if override and "POLICY_OVERRIDE" not in reason_codes:
        reason_codes.append("POLICY_OVERRIDE")
        context.run_repository.transition(
            state["run_id"],
            status=RunStatus.RUNNING,
            stage=RunStage.RECOMMEND,
            event_code="POLICY_OVERRIDE",
            message="Deterministic policy overrode the model proposal.",
        )
    recommendation = ApprovalRecommendation(
        proposed_route=proposal.proposed_route,
        final_route=final_route,
        reason_codes=reason_codes,
        summary=proposal.summary,
        reflection_count=reflection_count,
        decided_by="policy" if override else "agent",
    )
    context.run_repository.save_result(
        state["run_id"],
        recommendation=recommendation,
        reflection_count=reflection_count,
    )
    return {
        "proposal": proposal,
        "recommendation": recommendation,
        "reflection_count": reflection_count,
    }


def review_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    current = _run(context, state["run_id"])
    if current.status != RunStatus.REVIEW_REQUIRED:
        context.run_repository.transition(
            state["run_id"],
            status=RunStatus.REVIEW_REQUIRED,
            stage=RunStage.REVIEW,
            event_code="REVIEW_REQUIRED",
            message="Human review is required.",
        )
    interrupt(
        {
            "run_id": state["run_id"],
            "allowed_decisions": ["approve", "reject"],
        }
    )
    detail = context.run_repository.get_detail(state["run_id"])
    if detail is None or detail.review is None:
        raise RuntimeError("Persisted review decision is missing")
    return {"review": detail.review, "stage": RunStage.REVIEW}


def payment_agent_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    invoice = _invoice(state)
    recommendation = state.get("recommendation")
    review = state.get("review")
    approved = (
        recommendation is not None
        and recommendation.final_route == DecisionRoute.APPROVE
    ) or (review is not None and review.decision == "approve")
    if not approved or invoice.total is None:
        raise RuntimeError("Payment requires persisted approval and positive total")
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.PAY,
        event_code="PAYMENT_STARTED",
        message="Simulated payment started.",
    )
    payment = context.payment_repository.create_or_get(
        state["run_id"], invoice.total, f"payment:{state['run_id']}"
    )
    if payment.status == "pending":
        payment = context.payment_repository.succeed(state["run_id"])
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.COMPLETED,
        stage=RunStage.FINALIZE,
        event_code="PAYMENT_SUCCEEDED",
        message="Simulated payment completed.",
    )
    return {
        "payment": payment,
        "status": RunStatus.COMPLETED,
        "stage": RunStage.FINALIZE,
    }


def reject_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    runtime.context.run_repository.transition(
        state["run_id"],
        status=RunStatus.REJECTED,
        stage=RunStage.FINALIZE,
        event_code="RUN_REJECTED",
        message="Invoice was rejected without payment.",
    )
    return {"status": RunStatus.REJECTED, "stage": RunStage.FINALIZE}


def route_policy(state: InvoiceProcessingState) -> str:
    recommendation = state.get("recommendation")
    if recommendation is None:
        return "reject"
    return recommendation.final_route.value


def route_review(state: InvoiceProcessingState) -> str:
    review = state.get("review")
    return "pay" if review is not None and review.decision == "approve" else "reject"


def policy_route(
    invoice: InvoiceData, findings: list[ValidationFinding]
) -> DecisionRoute:
    if any(finding.severity == FindingSeverity.BLOCKING for finding in findings):
        return DecisionRoute.REJECT
    if any(finding.severity == FindingSeverity.WARNING for finding in findings):
        return DecisionRoute.REVIEW
    if invoice.currency != "USD":
        return DecisionRoute.REVIEW
    if invoice.total is None or invoice.total.amount > Decimal("10000.00"):
        return DecisionRoute.REVIEW
    return DecisionRoute.APPROVE


def _integrity_findings(
    invoice: InvoiceData, context: AgentRuntimeContext, run_id: str
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if not invoice.vendor_name:
        findings.append(
            _finding("MISSING_VENDOR", "vendor_name", "Vendor is required.")
        )
    if invoice.due_date is None:
        findings.append(
            _finding("MISSING_DUE_DATE", "due_date", "Due date is required.")
        )
    elif invoice.invoice_date and invoice.due_date < invoice.invoice_date:
        findings.append(
            _finding("INVALID_DUE_DATE", "due_date", "Due date precedes invoice date.")
        )
    if not invoice.items:
        findings.append(
            _finding("MISSING_ITEMS", "items", "At least one item is required.")
        )
    for item in invoice.items:
        if item.quantity is None or item.quantity <= 0:
            findings.append(
                _finding(
                    "INVALID_QUANTITY",
                    f"items.{item.line_number - 1}.quantity",
                    "Item quantity must be a positive integer.",
                    line=item.line_number,
                )
            )
        if item.unit_price is None or item.unit_price.amount <= 0:
            findings.append(
                _finding(
                    "INVALID_UNIT_PRICE",
                    f"items.{item.line_number - 1}.unit_price",
                    "Item price must be positive.",
                    line=item.line_number,
                )
            )
    if invoice.total is None or invoice.total.amount <= 0:
        findings.append(
            _finding("INVALID_TOTAL", "total", "Invoice total must be positive.")
        )
    else:
        line_sum = sum(
            (item.line_total.amount for item in invoice.items if item.line_total),
            Decimal("0"),
        )
        subtotal = invoice.subtotal.amount if invoice.subtotal else line_sum
        tax = invoice.tax.amount if invoice.tax else Decimal("0")
        shipping = invoice.shipping.amount if invoice.shipping else Decimal("0")
        if invoice.subtotal and abs(line_sum - subtotal) > Decimal("0.01"):
            findings.append(
                _finding("TOTAL_MISMATCH", "subtotal", "Line totals do not reconcile.")
            )
        if abs(subtotal + tax + shipping - invoice.total.amount) > Decimal("0.01"):
            findings.append(
                _finding("TOTAL_MISMATCH", "total", "Invoice total does not reconcile.")
            )
    record = _run(context, run_id)
    try:
        source = Path(record.source_path).read_text(errors="ignore")
    except OSError:
        source = ""
    if re.search(r"(?i)urgent|wire transfer|pay immediately", source):
        findings.append(
            _finding(
                "SUSPICIOUS_PAYMENT_LANGUAGE",
                None,
                "Suspicious urgency or wire-payment language was detected.",
            )
        )
    if invoice.currency and invoice.currency != "USD":
        findings.append(
            ValidationFinding(
                code="UNSUPPORTED_CURRENCY",
                severity=FindingSeverity.WARNING,
                field_path="currency",
                message=f"{invoice.currency} invoices require human review.",
            )
        )
    if invoice.total and invoice.total.amount > Decimal("10000.00"):
        findings.append(
            ValidationFinding(
                code="HIGH_VALUE_INVOICE",
                severity=FindingSeverity.WARNING,
                field_path="total",
                message=(
                    "Invoices above $10,000 require human review when otherwise valid."
                ),
            )
        )
    return findings


def _inventory_findings(
    invoice: InvoiceData, context: AgentRuntimeContext
) -> tuple[list[InvoiceItem], list[ValidationFinding]]:
    findings: list[ValidationFinding] = []
    normalized: list[InvoiceItem] = []
    totals: dict[str, int] = {}
    stocks: dict[str, int] = {}
    lines: dict[str, list[int]] = {}
    lookup = cast(
        Callable[[str], tuple[str, int, bool] | None],
        context.tool_registry.get("inventory.lookup"),
    )
    for item in invoice.items:
        if not item.source_name:
            normalized.append(item)
            continue
        resolved = lookup(item.source_name)
        if resolved is None:
            findings.append(
                _finding(
                    "UNKNOWN_ITEM",
                    f"items.{item.line_number - 1}.source_name",
                    "Item is not present in inventory.",
                    line=item.line_number,
                )
            )
            normalized.append(item)
            continue
        code, stock, used_alias = resolved
        normalized.append(item.model_copy(update={"normalized_item_code": code}))
        if used_alias:
            findings.append(
                ValidationFinding(
                    code="ITEM_ALIAS_NORMALIZATION",
                    severity=FindingSeverity.INFO,
                    field_path=f"items.{item.line_number - 1}.source_name",
                    item_line_number=item.line_number,
                    message="An exact configured item alias was normalized.",
                )
            )
        if item.quantity is not None and item.quantity > 0:
            totals[code] = totals.get(code, 0) + item.quantity
            stocks[code] = stock
            lines.setdefault(code, []).append(item.line_number)
    for code, quantity in totals.items():
        stock = stocks[code]
        if stock == 0:
            findings.append(
                ValidationFinding(
                    code="OUT_OF_STOCK",
                    severity=FindingSeverity.BLOCKING,
                    field_path="items",
                    item_line_number=lines[code][0],
                    message="Inventory stock is zero.",
                    expected={"maximum_quantity": stock},
                    actual={"quantity": quantity},
                )
            )
        elif quantity > stock:
            findings.append(
                ValidationFinding(
                    code="QUANTITY_EXCEEDS_STOCK",
                    severity=FindingSeverity.BLOCKING,
                    field_path="items",
                    item_line_number=lines[code][0],
                    message="Aggregated quantity exceeds inventory stock.",
                    expected={"maximum_quantity": stock},
                    actual={"quantity": quantity},
                )
            )
    return normalized, findings


def _finding(
    code: str, field_path: str | None, message: str, *, line: int | None = None
) -> ValidationFinding:
    return ValidationFinding(
        code=code,
        severity=FindingSeverity.BLOCKING,
        field_path=field_path,
        item_line_number=line,
        message=message,
    )


def _ordered_unique(findings: list[ValidationFinding]) -> list[ValidationFinding]:
    ordered = sorted(
        findings,
        key=lambda finding: (
            {
                FindingSeverity.BLOCKING: 0,
                FindingSeverity.WARNING: 1,
                FindingSeverity.INFO: 2,
            }[finding.severity],
            finding.code,
            finding.item_line_number or 0,
        ),
    )
    seen: set[tuple[str, str | None, int | None]] = set()
    result: list[ValidationFinding] = []
    for finding in ordered:
        key = (finding.code, finding.field_path, finding.item_line_number)
        if key not in seen:
            seen.add(key)
            result.append(finding)
    return result


def _extraction_feedback(invoice: InvoiceData) -> list[str]:
    feedback = []
    if not invoice.vendor_name:
        feedback.append("vendor_name is missing")
    if not invoice.items:
        feedback.append("items are missing")
    if invoice.total is None:
        feedback.append("total is missing")
    return feedback


def _invoice(state: InvoiceProcessingState) -> InvoiceData:
    invoice = state.get("invoice")
    if invoice is None:
        raise RuntimeError("Invoice state is missing")
    return invoice


def _run(context: AgentRuntimeContext, run_id: str):
    record = context.run_repository.get_internal(run_id)
    if record is None:
        raise KeyError(f"Unknown run: {run_id}")
    return record


def _check_deadline(context: AgentRuntimeContext) -> None:
    if time.monotonic() >= context.deadline_monotonic:
        raise TimeoutError("Workflow deadline exceeded")
