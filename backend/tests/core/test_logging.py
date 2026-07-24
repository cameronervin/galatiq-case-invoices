from backend.app.core.logging import redact_log_message


def test_redacts_sensitive_fragments_and_url_queries() -> None:
    message = (
        "request https://example.test/pay?token=secret api_key=abc password=hunter2"
    )

    redacted = redact_log_message(message)

    assert "secret" not in redacted
    assert "abc" not in redacted
    assert "hunter2" not in redacted
    assert "[redacted]" in redacted
