from pathlib import Path

import fitz

from backend.app.infrastructure.documents.common import (
    MAX_PDF_PAGES,
    MAX_TEXT_CHARACTERS,
    suspicious_language_findings,
)
from backend.app.ports.documents import DocumentLoadError, LoadedDocument


def load_pdf(path: Path, _default_currency: str) -> LoadedDocument:
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
    return LoadedDocument(
        format="pdf",
        text=text,
        findings=suspicious_language_findings(text),
    )
