import json
from pathlib import Path

from backend.app.infrastructure.documents.common import (
    money,
    optional_int,
    optional_string,
    parse_optional_date,
    read_text,
    structured_currency,
    suspicious_language_findings,
)
from backend.app.ports.documents import DocumentLoadError, LoadedDocument
from backend.app.schemas.domain import InvoiceData, InvoiceItem, Money


def load_json(path: Path, _default_currency: str) -> LoadedDocument:
    text = read_text(path)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DocumentLoadError(
            "MALFORMED_DOCUMENT", "Invoice JSON is malformed."
        ) from exc
    if not isinstance(payload, dict):
        raise DocumentLoadError("MALFORMED_DOCUMENT", "Invoice JSON must be an object.")
    currency, findings = structured_currency(payload.get("currency"))
    findings.extend(suspicious_language_findings(text))
    vendor = payload.get("vendor")
    vendor_name = vendor.get("name") if isinstance(vendor, dict) else vendor
    items = []
    for number, item in enumerate(payload.get("line_items") or [], start=1):
        if not isinstance(item, dict):
            raise DocumentLoadError("MALFORMED_DOCUMENT", "Invoice item is malformed.")
        quantity = optional_int(item.get("quantity"))
        unit_price = money(item.get("unit_price"), currency)
        line_total = money(item.get("amount"), currency)
        if line_total is None and unit_price is not None and quantity is not None:
            line_total = Money(amount=unit_price.amount * quantity, currency=currency)
        items.append(
            InvoiceItem(
                line_number=number,
                source_name=optional_string(item.get("item")),
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )
    invoice = InvoiceData(
        invoice_number=optional_string(payload.get("invoice_number")),
        revision=optional_string(payload.get("revision")),
        vendor_name=optional_string(vendor_name),
        invoice_date=parse_optional_date(payload.get("date")),
        due_date=parse_optional_date(payload.get("due_date")),
        currency=currency,
        items=items,
        subtotal=money(payload.get("subtotal"), currency),
        tax=money(payload.get("tax_amount"), currency),
        shipping=money(payload.get("shipping"), currency),
        total=money(payload.get("total"), currency),
        payment_terms=optional_string(payload.get("payment_terms")),
    )
    return LoadedDocument(format="json", invoice=invoice, findings=findings)
