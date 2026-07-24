from collections.abc import Callable
from pathlib import Path
from types import MappingProxyType

from backend.app.infrastructure.documents.common import (
    validate_source_size,
)
from backend.app.infrastructure.documents.csv_adapter import load_csv
from backend.app.infrastructure.documents.json_adapter import load_json
from backend.app.infrastructure.documents.pdf_adapter import load_pdf
from backend.app.infrastructure.documents.text_adapter import load_text
from backend.app.infrastructure.documents.xml_adapter import load_xml
from backend.app.ports.documents import DocumentLoadError, LoadedDocument

DocumentLoader = Callable[[Path, str], LoadedDocument]

LOADER_REGISTRY = MappingProxyType(
    {
        ".pdf": load_pdf,
        ".txt": load_text,
        ".json": load_json,
        ".csv": load_csv,
        ".xml": load_xml,
    }
)
SUPPORTED_SUFFIXES = set(LOADER_REGISTRY)


def load_document(path: Path, *, default_currency: str) -> LoadedDocument:
    loader = LOADER_REGISTRY.get(path.suffix.lower())
    if loader is None:
        raise DocumentLoadError("UNSUPPORTED_FILE_TYPE", "Unsupported invoice type.")
    validate_source_size(path)
    return loader(path, default_currency)
