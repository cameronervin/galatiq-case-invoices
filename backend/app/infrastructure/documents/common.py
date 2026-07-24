from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.app.ports.documents import DocumentLoadError
from backend.app.schemas.domain import (
    FindingSeverity,
    InvoiceItem,
    Money,
    ValidationFinding,
)

MAX_SOURCE_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 20
MAX_TEXT_CHARACTERS = 100_000


def validate_source_size(path: Path) -> None:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise DocumentLoadError(
            "SOURCE_UNAVAILABLE", "Invoice source is unavailable."
        ) from exc
    if size <= 0:
        raise DocumentLoadError("EMPTY_FILE", "Invoice file is empty.")
    if size > MAX_SOURCE_BYTES:
        raise DocumentLoadError("FILE_TOO_LARGE", "Invoice exceeds the 10 MB limit.")


def read_text(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise DocumentLoadError(
            "SOURCE_UNAVAILABLE", "Invoice source is unavailable."
        ) from exc
    if b"\x00" in data:
        raise DocumentLoadError(
            "MALFORMED_DOCUMENT", "Invoice text contains invalid bytes."
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentLoadError(
            "MALFORMED_DOCUMENT", "Invoice text is not UTF-8."
        ) from exc
    if len(text) > MAX_TEXT_CHARACTERS:
        raise DocumentLoadError("FILE_TOO_LARGE", "Invoice text is too large.")
    return text


def candidate_item(number: int, payload: dict[str, str], currency: str) -> InvoiceItem:
    quantity = optional_int(payload.get("quantity"))
    unit_price = money(payload.get("unit_price"), currency)
    return InvoiceItem(
        line_number=number,
        source_name=payload.get("item"),
        quantity=quantity,
        unit_price=unit_price,
        line_total=(
            Money(amount=unit_price.amount * quantity, currency=currency)
            if unit_price is not None and quantity is not None
            else None
        ),
    )


def default_currency(value: Any, default: str) -> tuple[str, list[ValidationFinding]]:
    if value and str(value).strip():
        return str(value).strip().upper(), []
    return default.upper(), [
        ValidationFinding(
            code="DEFAULT_CURRENCY_APPLIED",
            severity=FindingSeverity.INFO,
            field_path="currency",
            message=f"Currency was absent; configured {default.upper()} was applied.",
        )
    ]


def structured_currency(
    value: Any,
) -> tuple[str | None, list[ValidationFinding]]:
    if value and str(value).strip():
        return str(value).strip().upper(), []
    return None, [
        ValidationFinding(
            code="MISSING_CURRENCY",
            severity=FindingSeverity.BLOCKING,
            field_path="currency",
            message="Currency is required and was not inferred.",
        )
    ]


def money(value: Any, currency: str | None) -> Money | None:
    if currency is None or value is None or str(value).strip() == "":
        return None
    cleaned = str(value).replace("$", "").replace("€", "").replace(",", "").strip()
    return Money(amount=cleaned, currency=currency)


def suspicious_language_findings(text: str) -> list[ValidationFinding]:
    if not re.search(r"(?i)urgent|wire transfer|pay immediately", text):
        return []
    return [
        ValidationFinding(
            code="SUSPICIOUS_PAYMENT_LANGUAGE",
            severity=FindingSeverity.BLOCKING,
            message="Suspicious urgency or wire-payment language was detected.",
        )
    ]


def optional_int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(str(value).strip())
    except ValueError as exc:
        raise DocumentLoadError(
            "MALFORMED_DOCUMENT", "Invoice quantity is not integral."
        ) from exc


def optional_string(value: Any) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def parse_optional_date(value: Any) -> str | None:
    if value is None or not str(value).strip():
        return None
    text = str(value).strip()
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%b %d %Y", "%B %d, %Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    return None
