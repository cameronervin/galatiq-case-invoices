from pathlib import Path

import pytest

from backend.app.domain.policies import policy_route
from backend.app.infrastructure.llm.offline import OfflineProvider
from backend.app.ports.providers import (
    ApprovalCritique,
    ApprovalProposal,
    ProviderExtraction,
)
from backend.app.schemas.domain import InvoiceData, Money, ReviewRequest, RunStatus
from backend.tests.services.workflow_support import PROJECT_ROOT, service_for


@pytest.mark.parametrize(
    ("decision", "expected"),
    [("approve", RunStatus.COMPLETED), ("reject", RunStatus.REJECTED)],
)
def test_human_review_resumes_the_durable_graph(
    tmp_path: Path, decision: str, expected: RunStatus
) -> None:
    service = service_for(tmp_path)
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


def test_approval_revision_is_bounded_and_observable(tmp_path: Path) -> None:
    class RevisingProvider(OfflineProvider):
        proposal_calls = 0

        def propose_approval(self, **kwargs: object) -> ApprovalProposal:
            self.proposal_calls += 1
            return super().propose_approval(**kwargs)

        def critique_approval(self, **_: object) -> ApprovalCritique:
            return ApprovalCritique(accepted=False, feedback=["Revise once."])

    service = service_for(tmp_path)
    provider = RevisingProvider()
    service.provider_registry.register_factory(
        "offline", lambda _model: provider, replace=True
    )

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1001.txt",
        origin="cli",
    )

    assert detail.recommendation is not None
    assert detail.recommendation.reflection_count == 1
    assert provider.proposal_calls == 2
    assert sum(event.code == "APPROVAL_REVISED" for event in detail.events) == 1
    assert sum(event.code == "CRITIC_REJECTED" for event in detail.events) == 1


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

    service = service_for(tmp_path)
    provider = RepairingProvider()
    service.provider_registry.register_factory(
        "offline", lambda _model: provider, replace=True
    )

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

    service = service_for(tmp_path)
    provider = UnsafeProvider()
    service.provider_registry.register_factory(
        "offline", lambda _model: provider, replace=True
    )

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices/invoice_1002.txt",
        origin="cli",
    )

    assert detail.status == RunStatus.REJECTED
    assert detail.recommendation is not None
    assert detail.recommendation.decided_by == "policy"
    assert "POLICY_OVERRIDE" in detail.recommendation.reason_codes
    assert sum(event.code == "POLICY_OVERRIDE" for event in detail.events) == 1
