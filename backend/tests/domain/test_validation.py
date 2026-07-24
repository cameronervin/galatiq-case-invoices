from datetime import date
from decimal import Decimal

from backend.app.domain.validation import (
    extraction_feedback,
    integrity_findings,
    inventory_findings,
    ordered_unique,
)
from backend.app.domain.validation.extraction import (
    extraction_feedback as extraction_feedback_implementation,
)
from backend.app.domain.validation.findings import (
    ordered_unique as ordered_unique_implementation,
)
from backend.app.domain.validation.integrity import (
    integrity_findings as integrity_findings_implementation,
)
from backend.app.domain.validation.inventory import (
    inventory_findings as inventory_findings_implementation,
)
from backend.app.schemas.invoice import InvoiceData, InvoiceItem, Money
from backend.app.schemas.workflow import FindingSeverity, ValidationFinding


def test_validation_package_exports_rule_family_functions() -> None:
    assert extraction_feedback is extraction_feedback_implementation
    assert integrity_findings is integrity_findings_implementation
    assert inventory_findings is inventory_findings_implementation
    assert ordered_unique is ordered_unique_implementation


def test_integrity_validation_reconciles_line_totals() -> None:
    invoice = InvoiceData(
        vendor_name="Vendor",
        invoice_date=date(2026, 1, 1),
        due_date=date(2026, 1, 1),
        currency="USD",
        items=[
            InvoiceItem(
                line_number=1,
                quantity=2,
                unit_price=Money(amount=Decimal("5.00"), currency="USD"),
                line_total=Money(amount=Decimal("10.00"), currency="USD"),
            )
        ],
        subtotal=Money(amount=Decimal("11.00"), currency="USD"),
        total=Money(amount=Decimal("11.00"), currency="USD"),
    )

    assert [finding.field_path for finding in integrity_findings(invoice)] == [
        "subtotal"
    ]


def test_ordered_unique_prioritizes_severity_and_deduplicates_identity() -> None:
    warning = ValidationFinding(
        code="REVIEW",
        severity=FindingSeverity.WARNING,
        field_path="total",
        message="First message wins after stable ordering.",
    )
    duplicate = warning.model_copy(update={"message": "Duplicate message."})
    blocking = ValidationFinding(
        code="MISSING",
        severity=FindingSeverity.BLOCKING,
        field_path="vendor_name",
        message="Vendor is missing.",
    )

    assert ordered_unique([warning, duplicate, blocking]) == [blocking, warning]


def test_extraction_feedback_reports_only_repairable_core_fields() -> None:
    assert extraction_feedback(InvoiceData()) == [
        "vendor_name is missing",
        "items are missing",
        "total is missing",
    ]


def test_inventory_validation_resolves_repeated_source_once() -> None:
    calls: list[str] = []

    def lookup(source_name: str) -> tuple[str, int, bool] | None:
        calls.append(source_name)
        return "WidgetA", 20, True

    invoice = InvoiceData(
        items=[
            InvoiceItem(line_number=1, source_name="Widget A", quantity=2),
            InvoiceItem(line_number=2, source_name="Widget A", quantity=3),
        ]
    )

    normalized, findings = inventory_findings(invoice, lookup)

    assert calls == ["Widget A"]
    assert [item.normalized_item_code for item in normalized] == [
        "WidgetA",
        "WidgetA",
    ]
    assert [finding.code for finding in findings] == [
        "ITEM_ALIAS_NORMALIZATION",
        "ITEM_ALIAS_NORMALIZATION",
    ]
