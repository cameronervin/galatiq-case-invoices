from pathlib import Path

from backend.app.infrastructure.documents.common import (
    read_text,
    suspicious_language_findings,
)
from backend.app.ports.documents import LoadedDocument


def load_text(path: Path, _default_currency: str) -> LoadedDocument:
    text = read_text(path)
    return LoadedDocument(
        format="txt",
        text=text,
        findings=suspicious_language_findings(text),
    )
