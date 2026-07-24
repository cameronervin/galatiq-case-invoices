from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from backend.app.schemas.domain import (
    InvoiceData as ExportedInvoiceData,
)
from backend.app.schemas.domain import (
    RunStatus as ExportedRunStatus,
)
from backend.app.schemas.invoice import InvoiceData, InvoiceItem, Money
from backend.app.schemas.payment import PaymentResult
from backend.app.schemas.review import ReviewRequest
from backend.app.schemas.runs import RunDetail
from backend.app.schemas.workflow import (
    FindingSeverity,
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


def test_domain_module_remains_a_compatibility_export_surface() -> None:
    assert ExportedInvoiceData is InvoiceData
    assert ExportedRunStatus is RunStatus


def test_review_request_normalizes_reason_in_focused_module() -> None:
    request = ReviewRequest(decision="approve", reason="  Matches receipt.  ")

    assert request.reason == "Matches receipt."


def test_run_detail_round_trips_nested_payment_across_schema_modules() -> None:
    timestamp = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
    detail = RunDetail(
        run_id=UUID("00000000-0000-0000-0000-000000000001"),
        source_filename="invoice.json",
        status=RunStatus.COMPLETED,
        stage=RunStage.FINALIZE,
        created_at=timestamp,
        updated_at=timestamp,
        payment=PaymentResult(
            status="succeeded",
            amount=Money(amount="20.00", currency="USD"),
            mock_reference="MOCK-1",
            created_at=timestamp,
            updated_at=timestamp,
        ),
    )

    assert RunDetail.model_validate_json(detail.model_dump_json()) == detail
