from pathlib import Path

import pytest

from backend.app.infrastructure.llm.live import GrokProvider
from backend.app.infrastructure.llm.offline import OfflineProvider
from backend.app.ports.providers import ProviderError

PROJECT_ROOT = Path(__file__).resolve().parents[3]


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


def test_grok_keeps_repair_payload_out_of_trusted_instructions() -> None:
    extraction = OfflineProvider().extract_invoice(
        document_text=(PROJECT_ROOT / "data/invoices/invoice_1001.txt").read_text()
    )

    class FakeResponses:
        kwargs: dict[str, object] = {}

        def parse(self, **kwargs: object) -> object:
            self.kwargs = kwargs
            return type("Response", (), {"output_parsed": extraction})()

    responses = FakeResponses()
    provider = GrokProvider(
        api_key="test-key",
        model_name="grok-4.5",
        client=type("Client", (), {"responses": responses})(),
    )

    provider.repair_invoice(
        document_text="UNTRUSTED DOCUMENT",
        current=extraction,
        feedback=["UNTRUSTED FEEDBACK"],
    )

    assert "UNTRUSTED" not in str(responses.kwargs["instructions"])
    assert "UNTRUSTED DOCUMENT" in str(responses.kwargs["input"])
    assert "UNTRUSTED FEEDBACK" in str(responses.kwargs["input"])


def test_grok_closes_client_idempotently() -> None:
    class FakeClient:
        responses = object()

        def __init__(self) -> None:
            self.close_calls = 0

        def close(self) -> None:
            self.close_calls += 1

    client = FakeClient()
    provider = GrokProvider(api_key="test-key", model_name="grok-4.5", client=client)

    provider.close()
    provider.close()

    assert client.close_calls == 1


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
