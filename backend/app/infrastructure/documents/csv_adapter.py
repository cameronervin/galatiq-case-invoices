import csv
import io
from pathlib import Path

from backend.app.infrastructure.documents.common import (
    candidate_item,
    default_currency,
    money,
    optional_int,
    parse_optional_date,
    read_text,
    suspicious_language_findings,
)
from backend.app.ports.documents import DocumentLoadError, LoadedDocument
from backend.app.schemas.domain import InvoiceData, InvoiceItem


def load_csv(path: Path, configured_currency: str) -> LoadedDocument:
    text = read_text(path)
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise DocumentLoadError("MALFORMED_DOCUMENT", "Invoice CSV is empty.")
    if [cell.strip().lower() for cell in rows[0][:2]] == ["field", "value"]:
        loaded = _load_key_value_csv(rows[1:], configured_currency)
    else:
        loaded = _load_row_csv(rows, configured_currency)
    return LoadedDocument(
        format=loaded.format,
        invoice=loaded.invoice,
        text=loaded.text,
        findings=[*loaded.findings, *suspicious_language_findings(text)],
    )


def _load_key_value_csv(
    rows: list[list[str]], configured_currency: str
) -> LoadedDocument:
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
    currency, findings = default_currency(scalar.get("currency"), configured_currency)
    items = [
        candidate_item(number, item, currency)
        for number, item in enumerate(item_data, start=1)
    ]
    invoice = InvoiceData(
        invoice_number=scalar.get("invoice_number"),
        vendor_name=scalar.get("vendor"),
        invoice_date=parse_optional_date(scalar.get("date")),
        due_date=parse_optional_date(scalar.get("due_date")),
        currency=currency,
        items=items,
        subtotal=money(scalar.get("subtotal"), currency),
        tax=money(scalar.get("tax"), currency),
        shipping=money(scalar.get("shipping"), currency),
        total=money(scalar.get("total"), currency),
        payment_terms=scalar.get("payment_terms"),
    )
    return LoadedDocument(format="csv", invoice=invoice, findings=findings)


def _load_row_csv(rows: list[list[str]], configured_currency: str) -> LoadedDocument:
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
    currency, findings = default_currency(None, configured_currency)
    first = records[0]
    items = [
        InvoiceItem(
            line_number=number,
            source_name=record.get("item", "").strip() or None,
            quantity=optional_int(record.get("qty")),
            unit_price=money(record.get("unit_price"), currency),
            line_total=money(record.get("line_total"), currency),
        )
        for number, record in enumerate(records, start=1)
    ]
    invoice = InvoiceData(
        invoice_number=first.get("invoice_number", "").strip() or None,
        vendor_name=first.get("vendor", "").strip() or None,
        invoice_date=parse_optional_date(first.get("date")),
        due_date=parse_optional_date(first.get("due_date")),
        currency=currency,
        items=items,
        subtotal=money(totals.get("subtotal"), currency),
        tax=money(totals.get("tax"), currency),
        total=money(totals.get("total"), currency),
    )
    return LoadedDocument(format="csv", invoice=invoice, findings=findings)
