from pathlib import Path
from types import MappingProxyType

import pytest

from backend.app.domain.policies import policy_route
from backend.app.infrastructure.documents import (
    MAX_PDF_PAGES,
    MAX_SOURCE_BYTES,
    MAX_TEXT_CHARACTERS,
    SUPPORTED_SUFFIXES,
    DocumentLoadError,
    LoadedDocument,
    load_document,
)
from backend.app.infrastructure.documents.registry import LOADER_REGISTRY
from backend.app.ports.documents import (
    DocumentLoadError as PortDocumentLoadError,
)
from backend.app.ports.documents import LoadedDocument as PortLoadedDocument
from backend.app.schemas.domain import FindingSeverity

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_loader_facade_reexports_port_contracts_and_limits() -> None:
    assert DocumentLoadError is PortDocumentLoadError
    assert LoadedDocument is PortLoadedDocument
    assert MAX_SOURCE_BYTES == 10 * 1024 * 1024
    assert MAX_PDF_PAGES == 20
    assert MAX_TEXT_CHARACTERS == 100_000
    assert SUPPORTED_SUFFIXES == {".pdf", ".txt", ".json", ".csv", ".xml"}


def test_loader_registry_is_immutable_and_covers_supported_suffixes() -> None:
    assert isinstance(LOADER_REGISTRY, MappingProxyType)
    assert set(LOADER_REGISTRY) == SUPPORTED_SUFFIXES
    assert all(callable(loader) for loader in LOADER_REGISTRY.values())


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


@pytest.mark.parametrize(
    ("suffix", "content"),
    [
        (
            ".json",
            '{"invoice_number":"INV-2001","total":"25.00","line_items":[]}',
        ),
        (
            ".xml",
            "<invoice><header><invoice_number>INV-2001</invoice_number></header>"
            "<totals><total>25.00</total></totals></invoice>",
        ),
    ],
)
def test_structured_documents_preserve_missing_currency(
    tmp_path: Path, suffix: str, content: str
) -> None:
    path = tmp_path / f"invoice{suffix}"
    path.write_text(content)

    loaded = load_document(path, default_currency="USD")

    assert loaded.invoice is not None
    assert loaded.invoice.currency is None
    assert loaded.invoice.total is None
    assert [(finding.code, finding.severity) for finding in loaded.findings] == [
        ("MISSING_CURRENCY", FindingSeverity.BLOCKING)
    ]
    assert policy_route(loaded.invoice, loaded.findings).value == "reject"


def test_loader_surfaces_bounded_suspicious_language_evidence(tmp_path: Path) -> None:
    path = tmp_path / "invoice.txt"
    path.write_text("Invoice INV-2001\nPlease wire transfer immediately")

    loaded = load_document(path, default_currency="USD")

    assert [finding.code for finding in loaded.findings] == [
        "SUSPICIOUS_PAYMENT_LANGUAGE"
    ]
