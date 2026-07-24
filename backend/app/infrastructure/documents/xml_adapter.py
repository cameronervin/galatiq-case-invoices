from pathlib import Path

from defusedxml import ElementTree

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


def load_xml(path: Path, _default_currency: str) -> LoadedDocument:
    text = read_text(path)
    try:
        root = ElementTree.fromstring(text)
    except Exception as exc:
        raise DocumentLoadError(
            "MALFORMED_DOCUMENT", "Invoice XML is malformed."
        ) from exc
    currency, findings = structured_currency(root.findtext("./header/currency"))
    findings.extend(suspicious_language_findings(text))
    items = []
    for number, element in enumerate(root.findall("./line_items/item"), start=1):
        quantity = optional_int(element.findtext("quantity"))
        unit_price = money(element.findtext("unit_price"), currency)
        items.append(
            InvoiceItem(
                line_number=number,
                source_name=optional_string(element.findtext("name")),
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
        invoice_number=optional_string(root.findtext("./header/invoice_number")),
        vendor_name=optional_string(root.findtext("./header/vendor")),
        invoice_date=parse_optional_date(root.findtext("./header/date")),
        due_date=parse_optional_date(root.findtext("./header/due_date")),
        currency=currency,
        items=items,
        subtotal=money(root.findtext("./totals/subtotal"), currency),
        tax=money(root.findtext("./totals/tax_amount"), currency),
        total=money(root.findtext("./totals/total"), currency),
        payment_terms=optional_string(root.findtext("payment_terms")),
    )
    return LoadedDocument(format="xml", invoice=invoice, findings=findings)
