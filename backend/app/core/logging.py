import logging
import re
from urllib.parse import urlsplit, urlunsplit

import structlog

URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+")
SENSITIVE_FRAGMENT_PATTERN = re.compile(
    r"(?i)\b(key|api_key|token|secret|password|email)=([^&\s\"'<>]+)"
)


class RedactingLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_log_message(record.getMessage())
        record.args = ()
        return True


def redact_log_message(message: object) -> str:
    redacted = URL_PATTERN.sub(_redact_url_match, str(message))
    return SENSITIVE_FRAGMENT_PATTERN.sub(r"\1=[redacted]", redacted)


def _redact_url_match(match: re.Match[str]) -> str:
    raw_url = match.group(0)
    parsed = urlsplit(raw_url)
    if not parsed.query:
        return raw_url
    return urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, "[redacted]", parsed.fragment)
    )


def _redact_value(value: object) -> object:
    if isinstance(value, str):
        return redact_log_message(value)
    if isinstance(value, dict):
        return {key: _redact_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)
    return value


def _redact_structlog_event(
    _logger: object,
    _method_name: str,
    event_dict: dict[str, object],
) -> dict[str, object]:
    return {key: _redact_value(value) for key, value in event_dict.items()}


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level.upper(), format="%(message)s")
    root = logging.getLogger()
    root.setLevel(level.upper())
    for target in [root, *root.handlers]:
        if not any(isinstance(item, RedactingLogFilter) for item in target.filters):
            target.addFilter(RedactingLogFilter())
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_structlog_event,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )
