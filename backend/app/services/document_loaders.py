from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz
from defusedxml import ElementTree

from backend.app.schemas.domain import (
    FindingSeverity,
    InvoiceData,
    InvoiceItem,
    Money,
    ValidationFinding,
)

MAX_SOURCE_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 20
MAX_TEXT_CHARACTERS = 100_000
SUPPORTED_SUFFIXES = {".pdf", ".txt", ".json", ".csv", ".xml"}


class DocumentLoadError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.safe_message = message


@dataclass(frozen=True)
class LoadedDocument:
    format: str
    invoice: InvoiceData | None = None
    text: str | None = None
    findings: list[ValidationFinding] = field(default_factory=list)


def load_document(path: Path, *, default_currency: str) -> LoadedDocument:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise DocumentLoadError("UNSUPPORTED_FILE_TYPE", "Unsupported invoice type.")
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

    if suffix == ".json":
        return _load_json(path, default_currency)
    if suffix == ".csv":
        return _load_csv(path, default_currency)
    if suffix == ".xml":
        return _load_xml(path, default_currency)
    if suffix == ".pdf":
        return LoadedDocument(format="pdf", text=_load_pdf_text(path))
    return LoadedDocument(format="txt", text=_load_text(path))


def _load_json(path: Path, default_currency: str) -> LoadedDocument:
    try:
        payload = json.loads(_load_text(path))
    except json.JSONDecodeError as exc:
        raise DocumentLoadError(
            "MALFORMED_DOCUMENT", "Invoice JSON is malformed."
        ) from exc
    if not isinstance(payload, dict):
        raise DocumentLoadError("MALFORMED_DOCUMENT", "Invoice JSON must be an object.")
    currency, findings = _currency(payload.get("currency"), default_currency)
    vendor = payload.get("vendor")
    vendor_name = vendor.get("name") if isinstance(vendor, dict) else vendor
    items = []
    for number, item in enumerate(payload.get("line_items") or [], start=1):
        if not isinstance(item, dict):
            raise DocumentLoadError("MALFORMED_DOCUMENT", "Invoice item is malformed.")
        quantity = _optional_int(item.get("quantity"))
        unit_price = _money(item.get("unit_price"), currency)
        line_total = _money(item.get("amount"), currency)
        if line_total is None and unit_price is not None and quantity is not None:
            line_total = Money(amount=unit_price.amount * quantity, currency=currency)
        items.append(
            InvoiceItem(
                line_number=number,
                source_name=_optional_string(item.get("item")),
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )
    invoice = InvoiceData(
        invoice_number=_optional_string(payload.get("invoice_number")),
        revision=_optional_string(payload.get("revision")),
        vendor_name=_optional_string(vendor_name),
        invoice_date=_parse_optional_date(payload.get("date")),
        due_date=_parse_optional_date(payload.get("due_date")),
        currency=currency,
        items=items,
        subtotal=_money(payload.get("subtotal"), currency),
        tax=_money(payload.get("tax_amount"), currency),
        shipping=_money(payload.get("shipping"), currency),
        total=_money(payload.get("total"), currency),
        payment_terms=_optional_string(payload.get("payment_terms")),
    )
    return LoadedDocument(format="json", invoice=invoice, findings=findings)


def _load_csv(path: Path, default_currency: str) -> LoadedDocument:
    text = _load_text(path)
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise DocumentLoadError("MALFORMED_DOCUMENT", "Invoice CSV is empty.")
    if [cell.strip().lower() for cell in rows[0][:2]] == ["field", "value"]:
        return _load_key_value_csv(rows[1:], default_currency)
    return _load_row_csv(rows, default_currency)


def _load_key_value_csv(rows: list[list[str]], default_currency: str) -> LoadedDocument:
    scalar: dict[str, str] = {}
    item_data: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for row in rows:
        if len(row) < 2:
            continue
        key, value = row[0].strip().lower(), row[1].strip()
        if key == "item":
            if current:
                item_data.append(current)
            current = {"item": value}
        elif current is not None and key in {"quantity", "unit_price"}:
            current[key] = value
        else:
            scalar[key] = value
    if current:
        item_data.append(current)
    currency, findings = _currency(scalar.get("currency"), default_currency)
    items = [
        _candidate_item(number, item, currency)
        for number, item in enumerate(item_data, start=1)
    ]
    invoice = InvoiceData(
        invoice_number=scalar.get("invoice_number"),
        vendor_name=scalar.get("vendor"),
        invoice_date=_parse_optional_date(scalar.get("date")),
        due_date=_parse_optional_date(scalar.get("due_date")),
        currency=currency,
        items=items,
        subtotal=_money(scalar.get("subtotal"), currency),
        tax=_money(scalar.get("tax"), currency),
        shipping=_money(scalar.get("shipping"), currency),
        total=_money(scalar.get("total"), currency),
        payment_terms=scalar.get("payment_terms"),
    )
    return LoadedDocument(format="csv", invoice=invoice, findings=findings)


def _load_row_csv(rows: list[list[str]], default_currency: str) -> LoadedDocument:
    if len(rows) < 2:
        raise DocumentLoadError("MALFORMED_DOCUMENT", "Invoice CSV has no data rows.")
    headers = [header.strip().lower().replace(" ", "_") for header in rows[0]]
    records: list[dict[str, str]] = []
    totals: dict[str, str] = {}
    for row in rows[1:]:
        padded = row + [""] * (len(headers) - len(row))
        record = dict(zip(headers, padded, strict=False))
        if not record.get("invoice_number", "").strip():
            label = record.get("unit_price", "").strip().rstrip(":").lower()
            value = record.get("line_total", "").strip()
            if label.startswith("subtotal"):
                totals["subtotal"] = value
            elif label.startswith("tax"):
                totals["tax"] = value
            elif label.startswith("total"):
                totals["total"] = value
            continue
        records.append(record)
    if not records:
        raise DocumentLoadError("MALFORMED_DOCUMENT", "Invoice CSV has no line items.")
    currency, findings = _currency(None, default_currency)
    first = records[0]
    items = [
        InvoiceItem(
            line_number=number,
            source_name=record.get("item", "").strip() or None,
            quantity=_optional_int(record.get("qty")),
            unit_price=_money(record.get("unit_price"), currency),
            line_total=_money(record.get("line_total"), currency),
        )
        for number, record in enumerate(records, start=1)
    ]
    invoice = InvoiceData(
        invoice_number=first.get("invoice_number", "").strip() or None,
        vendor_name=first.get("vendor", "").strip() or None,
        invoice_date=_parse_optional_date(first.get("date")),
        due_date=_parse_optional_date(first.get("due_date")),
        currency=currency,
        items=items,
        subtotal=_money(totals.get("subtotal"), currency),
        tax=_money(totals.get("tax"), currency),
        total=_money(totals.get("total"), currency),
    )
    return LoadedDocument(format="csv", invoice=invoice, findings=findings)


def _load_xml(path: Path, default_currency: str) -> LoadedDocument:
    try:
        root = ElementTree.fromstring(_load_text(path))
    except Exception as exc:
        raise DocumentLoadError(
            "MALFORMED_DOCUMENT", "Invoice XML is malformed."
        ) from exc
    currency, findings = _currency(root.findtext("./header/currency"), default_currency)
    items = []
    for number, element in enumerate(root.findall("./line_items/item"), start=1):
        quantity = _optional_int(element.findtext("quantity"))
        unit_price = _money(element.findtext("unit_price"), currency)
        items.append(
            InvoiceItem(
                line_number=number,
                source_name=_optional_string(element.findtext("name")),
                quantity=quantity,
                unit_price=unit_price,
                line_total=(
                    Money(amount=unit_price.amount * quantity, currency=currency)
                    if unit_price is not None and quantity is not None
                    else None
                ),
            )
        )
    invoice = InvoiceData(
        invoice_number=_optional_string(root.findtext("./header/invoice_number")),
        vendor_name=_optional_string(root.findtext("./header/vendor")),
        invoice_date=_parse_optional_date(root.findtext("./header/date")),
        due_date=_parse_optional_date(root.findtext("./header/due_date")),
        currency=currency,
        items=items,
        subtotal=_money(root.findtext("./totals/subtotal"), currency),
        tax=_money(root.findtext("./totals/tax_amount"), currency),
        total=_money(root.findtext("./totals/total"), currency),
        payment_terms=_optional_string(root.findtext("payment_terms")),
    )
    return LoadedDocument(format="xml", invoice=invoice, findings=findings)


def _load_text(path: Path) -> str:
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


def _load_pdf_text(path: Path) -> str:
    try:
        with fitz.open(path) as document:
            if document.needs_pass:
                raise DocumentLoadError(
                    "UNSUPPORTED_PDF", "Encrypted PDFs are unsupported."
                )
            if document.page_count > MAX_PDF_PAGES:
                raise DocumentLoadError(
                    "UNSUPPORTED_PDF", "PDF exceeds the page limit."
                )
            text = "\n".join(page.get_text("text") for page in document)
    except DocumentLoadError:
        raise
    except Exception as exc:
        raise DocumentLoadError("UNSUPPORTED_PDF", "PDF could not be read.") from exc
    if not text.strip():
        raise DocumentLoadError(
            "UNSUPPORTED_PDF", "Image-only or empty PDFs are unsupported."
        )
    if len(text) > MAX_TEXT_CHARACTERS:
        raise DocumentLoadError("FILE_TOO_LARGE", "Extracted PDF text is too large.")
    return text


def _candidate_item(number: int, payload: dict[str, str], currency: str) -> InvoiceItem:
    quantity = _optional_int(payload.get("quantity"))
    unit_price = _money(payload.get("unit_price"), currency)
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


def _currency(value: Any, default: str) -> tuple[str, list[ValidationFinding]]:
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


def _money(value: Any, currency: str) -> Money | None:
    if value is None or str(value).strip() == "":
        return None
    cleaned = str(value).replace("$", "").replace("€", "").replace(",", "").strip()
    return Money(amount=cleaned, currency=currency)


def _optional_int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(str(value).strip())
    except ValueError as exc:
        raise DocumentLoadError(
            "MALFORMED_DOCUMENT", "Invoice quantity is not integral."
        ) from exc


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def _parse_optional_date(value: Any) -> str | None:
    if value is None or not str(value).strip():
        return None
    text = str(value).strip()
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%b %d %Y", "%B %d, %Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    return None
