from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from backend.app.schemas.domain import InvoiceData, ValidationFinding


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


class DocumentLoader(Protocol):
    def __call__(
        self, path: Path, *, default_currency: str
    ) -> LoadedDocument: ...
