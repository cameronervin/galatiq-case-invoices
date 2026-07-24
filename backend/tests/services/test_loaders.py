from pathlib import Path

from backend.app.schemas.domain import FindingSeverity
from backend.app.services.document_loaders import load_document

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_key_value_csv_defaults_currency_with_informational_finding() -> None:
    loaded = load_document(
        PROJECT_ROOT / "data/invoices/invoice_1006.csv",
        default_currency="USD",
    )

    assert loaded.invoice is not None
    assert loaded.invoice.currency == "USD"
    assert loaded.invoice.total is not None
    assert loaded.invoice.total.amount_as_decimal == 2750
    assert [(finding.code, finding.severity) for finding in loaded.findings] == [
        ("DEFAULT_CURRENCY_APPLIED", FindingSeverity.INFO)
    ]


def test_row_csv_loads_line_items_and_totals() -> None:
    loaded = load_document(
        PROJECT_ROOT / "data/invoices/invoice_1015.csv",
        default_currency="USD",
    )

    assert loaded.invoice is not None
    assert len(loaded.invoice.items) == 3
    assert loaded.invoice.total is not None
    assert loaded.invoice.total.amount_as_decimal == 6500


def test_json_and_xml_load_into_the_same_invoice_contract() -> None:
    json_invoice = load_document(
        PROJECT_ROOT / "data/invoices/invoice_1004.json",
        default_currency="USD",
    ).invoice
    xml_invoice = load_document(
        PROJECT_ROOT / "data/invoices/invoice_1014.xml",
        default_currency="USD",
    ).invoice

    assert json_invoice is not None and json_invoice.invoice_number == "INV-1004"
    assert xml_invoice is not None and xml_invoice.currency == "EUR"
    assert xml_invoice.total is not None
    assert xml_invoice.total.amount_as_decimal == 4125


def test_text_loader_returns_bounded_transient_text() -> None:
    loaded = load_document(
        PROJECT_ROOT / "data/invoices/invoice_1001.txt",
        default_currency="USD",
    )

    assert loaded.invoice is None
    assert loaded.text is not None
    assert "INV-1001" in loaded.text
