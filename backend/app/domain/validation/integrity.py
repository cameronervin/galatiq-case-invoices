from decimal import Decimal

from backend.app.schemas.invoice import InvoiceData
from backend.app.schemas.workflow import FindingSeverity, ValidationFinding

from .findings import blocking_finding


def integrity_findings(invoice: InvoiceData) -> list[ValidationFinding]:
    """Validate required invoice fields and monetary reconciliation."""
    findings: list[ValidationFinding] = []
    if not invoice.vendor_name:
        findings.append(
            blocking_finding("MISSING_VENDOR", "vendor_name", "Vendor is required.")
        )
    if invoice.due_date is None:
        findings.append(
            blocking_finding("MISSING_DUE_DATE", "due_date", "Due date is required.")
        )
    elif invoice.invoice_date and invoice.due_date < invoice.invoice_date:
        findings.append(
            blocking_finding(
                "INVALID_DUE_DATE", "due_date", "Due date precedes invoice date."
            )
        )
    if invoice.currency is None:
        findings.append(
            blocking_finding("MISSING_CURRENCY", "currency", "Currency is required.")
        )
    if not invoice.items:
        findings.append(
            blocking_finding("MISSING_ITEMS", "items", "At least one item is required.")
        )
    for item in invoice.items:
        if item.quantity is None or item.quantity <= 0:
            findings.append(
                blocking_finding(
                    "INVALID_QUANTITY",
                    f"items.{item.line_number - 1}.quantity",
                    "Item quantity must be a positive integer.",
                    line=item.line_number,
                )
            )
        if item.unit_price is None or item.unit_price.amount <= 0:
            findings.append(
                blocking_finding(
                    "INVALID_UNIT_PRICE",
                    f"items.{item.line_number - 1}.unit_price",
                    "Item price must be positive.",
                    line=item.line_number,
                )
            )
    findings.extend(_total_findings(invoice))
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


def _total_findings(invoice: InvoiceData) -> list[ValidationFinding]:
    if invoice.total is None or invoice.total.amount <= 0:
        return [
            blocking_finding(
                "INVALID_TOTAL", "total", "Invoice total must be positive."
            )
        ]
    line_sum = sum(
        (item.line_total.amount for item in invoice.items if item.line_total),
        Decimal("0"),
    )
    subtotal = invoice.subtotal.amount if invoice.subtotal else line_sum
    tax = invoice.tax.amount if invoice.tax else Decimal("0")
    shipping = invoice.shipping.amount if invoice.shipping else Decimal("0")
    findings: list[ValidationFinding] = []
    if invoice.subtotal and abs(line_sum - subtotal) > Decimal("0.01"):
        findings.append(
            blocking_finding(
                "TOTAL_MISMATCH", "subtotal", "Line totals do not reconcile."
            )
        )
    if abs(subtotal + tax + shipping - invoice.total.amount) > Decimal("0.01"):
        findings.append(
            blocking_finding(
                "TOTAL_MISMATCH", "total", "Invoice total does not reconcile."
            )
        )
    return findings
