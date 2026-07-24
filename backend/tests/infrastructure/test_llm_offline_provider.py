from pathlib import Path

from backend.app.infrastructure.documents import load_document
from backend.app.infrastructure.llm.offline import OfflineProvider
from backend.app.ports.providers import ApprovalCritique
from backend.app.schemas.domain import DecisionRoute, FindingSeverity

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_offline_provider_extracts_clean_text_invoice() -> None:
    loaded = load_document(
        PROJECT_ROOT / "data/invoices/invoice_1001.txt",
        default_currency="USD",
    )

    result = OfflineProvider().extract_invoice(document_text=loaded.text or "")

    assert result.invoice.invoice_number == "INV-1001"
    assert result.invoice.vendor_name == "Widgets Inc."
    assert [item.quantity for item in result.invoice.items] == [10, 5]
    assert result.invoice.total is not None
    assert result.invoice.total.amount_as_decimal == 5000


def test_offline_provider_surfaces_ocr_normalization_warning() -> None:
    loaded = load_document(
        PROJECT_ROOT / "data/invoices/invoice_1012.txt",
        default_currency="USD",
    )

    result = OfflineProvider().extract_invoice(document_text=loaded.text or "")

    assert result.invoice.invoice_number == "INV-1012"
    assert any(
        finding.code == "OCR_NORMALIZATION"
        and finding.severity == FindingSeverity.WARNING
        for finding in result.findings
    )


def test_offline_approval_and_critique_are_typed() -> None:
    extraction = OfflineProvider().extract_invoice(
        document_text=(PROJECT_ROOT / "data/invoices/invoice_1001.txt").read_text()
    )

    proposal = OfflineProvider().propose_approval(
        invoice=extraction.invoice,
        findings=[],
    )
    critique = OfflineProvider().critique_approval(
        invoice=extraction.invoice,
        findings=[],
        proposal=proposal,
    )

    assert proposal.proposed_route == DecisionRoute.APPROVE
    assert critique == ApprovalCritique(accepted=True, feedback=[])
