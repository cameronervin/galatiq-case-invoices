from pathlib import Path

import pytest

from backend.app.agents.nodes.workflow import policy_route
from backend.app.core.config import Settings
from backend.app.infrastructure.llm.base import (
    ApprovalCritique,
    ApprovalProposal,
    ProviderExtraction,
)
from backend.app.infrastructure.llm.providers import OfflineProvider
from backend.app.schemas.domain import InvoiceData, Money, ReviewRequest, RunStatus
from backend.app.services.invoice_processing import InvoiceProcessingService

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def settings_for(tmp_path: Path) -> Settings:
    return Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
        llm_provider="offline",
        llm_model="deterministic-v1",
    )


def test_service_cleanup_closes_graph_then_database_once(
    tmp_path: Path, monkeypatch
) -> None:
    service = InvoiceProcessingService(settings_for(tmp_path))
    calls: list[str] = []
    monkeypatch.setattr(service.graph_provider, "close", lambda: calls.append("graph"))
    monkeypatch.setattr(service.database, "close", lambda: calls.append("database"))

    service.close()
    service.close()

    assert calls == ["graph", "database"]


def test_clean_invoice_completes_with_one_mock_payment_and_cleanup(
    tmp_path: Path,
) -> None:
    service = InvoiceProcessingService(settings_for(tmp_path))

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1001.txt",
        origin="cli",
    )

    assert detail.status == RunStatus.COMPLETED
    assert detail.payment is not None and detail.payment.status == "succeeded"
    assert sum(event.code == "PAYMENT_SUCCEEDED" for event in detail.events) == 1
    assert any(event.code == "INVENTORY_TOOL_CALLED" for event in detail.events)
    assert service.tool_registry.names() == ("inventory.lookup",)
    assert list((tmp_path / "uploads").iterdir()) == []


def test_stock_mismatch_rejects_without_payment(tmp_path: Path) -> None:
    service = InvoiceProcessingService(settings_for(tmp_path))

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1002.txt",
        origin="cli",
    )

    assert detail.status == RunStatus.REJECTED
    assert detail.payment is None
    assert "QUANTITY_EXCEEDS_STOCK" in {finding.code for finding in detail.findings}


def test_ocr_warning_pauses_for_human_review(tmp_path: Path) -> None:
    service = InvoiceProcessingService(settings_for(tmp_path))

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1012.txt",
        origin="cli",
    )

    assert detail.status == RunStatus.REVIEW_REQUIRED
    assert detail.payment is None
    assert "OCR_NORMALIZATION" in {finding.code for finding in detail.findings}
    assert list((tmp_path / "uploads").iterdir()) != []


def test_duplicate_processing_returns_existing_terminal_run(tmp_path: Path) -> None:
    service = InvoiceProcessingService(settings_for(tmp_path))
    path = PROJECT_ROOT / "data/invoices/invoice_1001.txt"

    first = service.process_path(path, origin="cli")
    second = service.process_path(path, origin="cli")

    assert second.run_id == first.run_id
    assert sum(event.code == "PAYMENT_SUCCEEDED" for event in second.events) == 1


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("invoice_1001.txt", RunStatus.COMPLETED),
        ("invoice_1004.json", RunStatus.COMPLETED),
        ("invoice_1004_revised.json", RunStatus.COMPLETED),
        ("invoice_1006.csv", RunStatus.COMPLETED),
        ("invoice_1010.txt", RunStatus.COMPLETED),
        ("invoice_1011.pdf", RunStatus.COMPLETED),
        ("invoice_1015.csv", RunStatus.COMPLETED),
        ("invoice_1012.pdf", RunStatus.REVIEW_REQUIRED),
        ("invoice_1014.xml", RunStatus.REVIEW_REQUIRED),
        ("invoice_1002.txt", RunStatus.REJECTED),
        ("invoice_1003.txt", RunStatus.REJECTED),
        ("invoice_1005.json", RunStatus.REJECTED),
        ("invoice_1007.csv", RunStatus.REJECTED),
        ("invoice_1008.txt", RunStatus.REJECTED),
        ("invoice_1009.json", RunStatus.REJECTED),
        ("invoice_1013.json", RunStatus.REJECTED),
        ("invoice_1016.json", RunStatus.REJECTED),
    ],
)
def test_fixture_acceptance_matrix(
    tmp_path: Path, filename: str, expected: RunStatus
) -> None:
    service = InvoiceProcessingService(settings_for(tmp_path))

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices" / filename,
        origin="cli",
    )

    assert detail.status == expected, [
        (finding.code, finding.message) for finding in detail.findings
    ]


@pytest.mark.parametrize(
    ("decision", "expected"),
    [("approve", RunStatus.COMPLETED), ("reject", RunStatus.REJECTED)],
)
def test_human_review_resumes_the_durable_graph(
    tmp_path: Path, decision: str, expected: RunStatus
) -> None:
    service = InvoiceProcessingService(settings_for(tmp_path))
    pending = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1012.txt",
        origin="cli",
    )
    service.persist_review(
        pending.run_id,
        ReviewRequest(decision=decision, reason="Reviewed the documented warning."),
    )

    result = service.resume_run(pending.run_id)

    assert result.status == expected
    assert (result.payment is not None) is (decision == "approve")


def test_policy_threshold_is_strictly_above_ten_thousand() -> None:
    base = InvoiceData(
        vendor_name="Vendor",
        due_date="2026-02-01",
        currency="USD",
        total=Money(amount="10000.00", currency="USD"),
    )

    assert policy_route(base, []).value == "approve"
    assert (
        policy_route(
            base.model_copy(update={"total": Money(amount="10000.01", currency="USD")}),
            [],
        ).value
        == "review"
    )


def test_descriptor_normalization_is_informational_and_does_not_change_route(
    tmp_path: Path,
) -> None:
    service = InvoiceProcessingService(settings_for(tmp_path))

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1010.txt",
        origin="cli",
    )

    finding = next(
        item for item in detail.findings if item.code == "ITEM_ALIAS_NORMALIZATION"
    )
    assert finding.severity.value == "info"
    assert detail.status == RunStatus.COMPLETED


def test_approval_revision_is_bounded_and_observable(tmp_path: Path) -> None:
    class RevisingProvider(OfflineProvider):
        proposal_calls = 0

        def propose_approval(self, **kwargs: object) -> ApprovalProposal:
            self.proposal_calls += 1
            return super().propose_approval(**kwargs)

        def critique_approval(self, **_: object) -> ApprovalCritique:
            return ApprovalCritique(accepted=False, feedback=["Revise once."])

    service = InvoiceProcessingService(settings_for(tmp_path))
    provider = RevisingProvider()
    service.provider_registry._offline = provider

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1001.txt",
        origin="cli",
    )

    assert detail.recommendation is not None
    assert detail.recommendation.reflection_count == 1
    assert provider.proposal_calls == 2
    assert sum(event.code == "APPROVAL_REVISED" for event in detail.events) == 1


def test_extraction_repair_is_bounded_and_observable(tmp_path: Path) -> None:
    class RepairingProvider(OfflineProvider):
        repair_calls = 0

        def extract_invoice(self, *, document_text: str) -> ProviderExtraction:
            extracted = super().extract_invoice(document_text=document_text)
            return extracted.model_copy(
                update={
                    "invoice": extracted.invoice.model_copy(
                        update={"vendor_name": None}
                    )
                }
            )

        def repair_invoice(
            self,
            *,
            document_text: str,
            current: ProviderExtraction,
            feedback: list[str],
        ) -> ProviderExtraction:
            del current, feedback
            self.repair_calls += 1
            return super().extract_invoice(document_text=document_text)

    service = InvoiceProcessingService(settings_for(tmp_path))
    provider = RepairingProvider()
    service.provider_registry._offline = provider

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1001.txt",
        origin="cli",
    )

    assert detail.status == RunStatus.COMPLETED
    assert provider.repair_calls == 1
    assert sum(event.code == "EXTRACTION_REPAIRED" for event in detail.events) == 1


def test_deterministic_policy_overrides_unsafe_provider_route(tmp_path: Path) -> None:
    class UnsafeProvider(OfflineProvider):
        def propose_approval(self, **_: object) -> ApprovalProposal:
            return ApprovalProposal(
                proposed_route="approve",
                reason_codes=[],
                summary="Unsafe model proposal.",
            )

    service = InvoiceProcessingService(settings_for(tmp_path))
    service.provider_registry._offline = UnsafeProvider()

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1002.txt",
        origin="cli",
    )

    assert detail.status == RunStatus.REJECTED
    assert detail.recommendation is not None
    assert detail.recommendation.decided_by == "policy"
    assert "POLICY_OVERRIDE" in detail.recommendation.reason_codes
    assert sum(event.code == "POLICY_OVERRIDE" for event in detail.events) == 1
