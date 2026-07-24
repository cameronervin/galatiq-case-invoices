from decimal import Decimal

from backend.app.schemas.domain import (
    DecisionRoute,
    FindingSeverity,
    InvoiceData,
    ValidationFinding,
)


def policy_route(
    invoice: InvoiceData, findings: list[ValidationFinding]
) -> DecisionRoute:
    """Return the deterministic route that is authoritative for payment safety."""
    if any(finding.severity == FindingSeverity.BLOCKING for finding in findings):
        return DecisionRoute.REJECT
    if any(finding.severity == FindingSeverity.WARNING for finding in findings):
        return DecisionRoute.REVIEW
    if invoice.currency != "USD":
        return DecisionRoute.REVIEW
    if invoice.total is None or invoice.total.amount > Decimal("10000.00"):
        return DecisionRoute.REVIEW
    return DecisionRoute.APPROVE
