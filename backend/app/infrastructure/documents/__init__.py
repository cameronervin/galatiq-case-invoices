"""Document loading facade with format-specific adapters."""

from backend.app.infrastructure.documents.common import (
    MAX_PDF_PAGES,
    MAX_SOURCE_BYTES,
    MAX_TEXT_CHARACTERS,
)
from backend.app.infrastructure.documents.registry import (
    SUPPORTED_SUFFIXES,
    load_document,
)
from backend.app.ports.documents import DocumentLoadError, LoadedDocument

__all__ = [
    "MAX_PDF_PAGES",
    "MAX_SOURCE_BYTES",
    "MAX_TEXT_CHARACTERS",
    "SUPPORTED_SUFFIXES",
    "DocumentLoadError",
    "LoadedDocument",
    "load_document",
]
