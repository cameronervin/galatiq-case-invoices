from pathlib import Path

from backend.app.schemas.domain import RunStatus
from backend.tests.services.workflow_support import PROJECT_ROOT, service_for


def test_clean_invoice_completes_with_one_mock_payment_and_cleanup(
    tmp_path: Path,
) -> None:
    service = service_for(tmp_path)

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1001.txt",
        origin="cli",
    )

    assert detail.status == RunStatus.COMPLETED
    assert detail.payment is not None and detail.payment.status == "succeeded"
    assert sum(event.code == "PAYMENT_SUCCEEDED" for event in detail.events) == 1
    assert any(event.code == "INVENTORY_TOOL_CALLED" for event in detail.events)
    assert list((tmp_path / "uploads").iterdir()) == []
    event_codes = [event.code for event in detail.events]
    assert event_codes.index("VALIDATION_STARTED") < event_codes.index(
        "INVENTORY_TOOL_CALLED"
    )
    assert event_codes.index("APPROVAL_STARTED") < event_codes.index(
        "APPROVAL_PROPOSED"
    )
    assert event_codes.index("CRITIC_STARTED") < event_codes.index("CRITIC_ACCEPTED")


def test_stock_mismatch_rejects_without_payment(tmp_path: Path) -> None:
    service = service_for(tmp_path)

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1002.txt",
        origin="cli",
    )

    assert detail.status == RunStatus.REJECTED
    assert detail.payment is None
    assert "QUANTITY_EXCEEDS_STOCK" in {finding.code for finding in detail.findings}


def test_ocr_warning_pauses_for_human_review(tmp_path: Path) -> None:
    service = service_for(tmp_path)

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1012.txt",
        origin="cli",
    )

    assert detail.status == RunStatus.REVIEW_REQUIRED
    assert detail.payment is None
    assert "OCR_NORMALIZATION" in {finding.code for finding in detail.findings}
    assert list((tmp_path / "uploads").iterdir()) != []


def test_descriptor_normalization_is_informational_and_does_not_change_route(
    tmp_path: Path,
) -> None:
    service = service_for(tmp_path)

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1010.txt",
        origin="cli",
    )

    finding = next(
        item for item in detail.findings if item.code == "ITEM_ALIAS_NORMALIZATION"
    )
    assert finding.severity.value == "info"
    assert detail.status == RunStatus.COMPLETED
