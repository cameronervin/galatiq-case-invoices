from pathlib import Path

import pytest

from backend.app.infrastructure.llm.base import ApprovalCritique
from backend.app.infrastructure.llm.factory import (
    ProviderConfigurationError,
    ProviderRegistry,
)
from backend.app.infrastructure.llm.providers import (
    GrokProvider,
    OfflineProvider,
    ProviderError,
)
from backend.app.schemas.domain import DecisionRoute, FindingSeverity
from backend.app.services.document_loaders import load_document

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


def test_registry_requires_key_only_for_grok() -> None:
    registry = ProviderRegistry(grok_api_key=None, grok_model="grok-4.5")

    assert isinstance(registry.get("offline", "deterministic-v1"), OfflineProvider)
    with pytest.raises(ProviderConfigurationError):
        registry.get("grok", "grok-4.5")


def test_grok_uses_responses_parse_without_storage() -> None:
    class FakeResponses:
        def __init__(self) -> None:
            self.kwargs: dict[str, object] = {}

        def parse(self, **kwargs: object) -> object:
            self.kwargs = kwargs
            return type(
                "Response",
                (),
                {
                    "output_parsed": OfflineProvider().extract_invoice(
                        document_text=(
                            PROJECT_ROOT / "data/invoices/invoice_1001.txt"
                        ).read_text()
                    )
                },
            )()

    fake_responses = FakeResponses()
    fake_client = type("Client", (), {"responses": fake_responses})()
    provider = GrokProvider(
        api_key="test-key",
        model_name="grok-4.5",
        client=fake_client,
    )

    provider.extract_invoice(document_text="invoice")

    assert fake_responses.kwargs["store"] is False
    assert fake_responses.kwargs["model"] == "grok-4.5"
    assert "tools" not in fake_responses.kwargs


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError(),
        type("RateLimit", (Exception,), {"status_code": 429})(),
        type("ServerFailure", (Exception,), {"status_code": 503})(),
    ],
)
def test_grok_retries_one_transient_failure(failure: Exception) -> None:
    expected = OfflineProvider().extract_invoice(
        document_text=(PROJECT_ROOT / "data/invoices/invoice_1001.txt").read_text()
    )

    class FlakyResponses:
        calls = 0

        def parse(self, **_: object) -> object:
            self.calls += 1
            if self.calls == 1:
                raise failure
            return type("Response", (), {"output_parsed": expected})()

    responses = FlakyResponses()
    provider = GrokProvider(
        api_key="test-key",
        model_name="grok-4.5",
        client=type("Client", (), {"responses": responses})(),
    )

    assert provider.extract_invoice(document_text="invoice") == expected
    assert responses.calls == 2


def test_grok_refusal_fails_safely_without_retry() -> None:
    class RefusalResponses:
        calls = 0

        def parse(self, **_: object) -> object:
            self.calls += 1
            return type("Response", (), {"output_parsed": None})()

    refusal = RefusalResponses()
    provider = GrokProvider(
        api_key="test-key",
        model_name="grok-4.5",
        client=type("Client", (), {"responses": refusal})(),
    )

    with pytest.raises(ProviderError, match="invalid structured output") as exc_info:
        provider.extract_invoice(document_text="invoice")

    assert exc_info.value.code == "PROVIDER_INVALID_OUTPUT"
    assert refusal.calls == 1


def test_grok_authentication_failure_is_not_retried() -> None:
    authentication_error = type(
        "AuthenticationFailure", (Exception,), {"status_code": 401}
    )()

    class FailingResponses:
        calls = 0

        def parse(self, **_: object) -> object:
            self.calls += 1
            raise authentication_error

    responses = FailingResponses()
    provider = GrokProvider(
        api_key="bad-key",
        model_name="grok-4.5",
        client=type("Client", (), {"responses": responses})(),
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.extract_invoice(document_text="invoice")

    assert exc_info.value.code == "PROVIDER_FAILURE"
    assert exc_info.value.retryable is False
    assert responses.calls == 1
