from decimal import Decimal

import pytest
from pydantic import ValidationError

from backend.app.schemas.domain import (
    FindingSeverity,
    InvoiceData,
    InvoiceItem,
    Money,
    RunStage,
    RunStatus,
    ValidationFinding,
)


def test_money_serializes_as_exact_two_decimal_string() -> None:
    money = Money(amount=Decimal("5000.00"), currency="usd")

    assert money.model_dump(mode="json") == {
        "amount": "5000.00",
        "currency": "USD",
    }


def test_money_rejects_more_than_two_fractional_digits() -> None:
    with pytest.raises(ValidationError):
        Money(amount="1.001", currency="USD")


def test_public_workflow_enums_are_small_and_non_overlapping() -> None:
    assert {status.value for status in RunStatus} == {
        "queued",
        "running",
        "review_required",
        "completed",
        "rejected",
        "failed",
    }
    assert {stage.value for stage in RunStage} == {
        "ingest",
        "extract",
        "validate",
        "recommend",
        "review",
        "pay",
        "finalize",
    }


def test_invoice_and_finding_round_trip_through_json() -> None:
    invoice = InvoiceData(
        invoice_number="INV-1",
        vendor_name="Vendor",
        invoice_date="2026-01-01",
        due_date="2026-02-01",
        currency="USD",
        items=[
            InvoiceItem(
                line_number=1,
                source_name="WidgetA",
                normalized_item_code="WidgetA",
                quantity=2,
                unit_price=Money(amount="10.00", currency="USD"),
                line_total=Money(amount="20.00", currency="USD"),
            )
        ],
        total=Money(amount="20.00", currency="USD"),
    )
    finding = ValidationFinding(
        code="ITEM_ALIAS_NORMALIZATION",
        severity=FindingSeverity.INFO,
        field_path="items.0.source_name",
        message="An exact configured alias was normalized.",
    )

    assert InvoiceData.model_validate_json(invoice.model_dump_json()) == invoice
    assert ValidationFinding.model_validate_json(finding.model_dump_json()) == finding
