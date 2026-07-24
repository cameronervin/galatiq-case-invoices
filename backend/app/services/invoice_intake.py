from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from backend.app.ports.providers import ProviderResolver
from backend.app.ports.repositories import RunRecordView, RunRepository
from backend.app.ports.runtime import InvoiceIntakeSettings


class InvalidInvoiceInput(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class InvoiceIntakeService:
    """Validate and stage an invoice before a run is dispatched."""

    def __init__(
        self,
        *,
        settings: InvoiceIntakeSettings,
        run_repository: RunRepository,
        provider_registry: ProviderResolver,
        supported_suffixes: frozenset[str],
        max_source_bytes: int,
    ) -> None:
        self.settings = settings
        self.run_repository = run_repository
        self.provider_registry = provider_registry
        self.supported_suffixes = supported_suffixes
        self.infrastructure_max_source_bytes = max_source_bytes

    @property
    def max_source_bytes(self) -> int:
        return min(
            self.infrastructure_max_source_bytes,
            self.settings.max_upload_bytes,
        )

    def create_from_path(
        self, path: Path, *, origin: str
    ) -> tuple[RunRecordView, bool]:
        resolved = self._validate_source(path)
        return self.create_from_bytes(
            filename=resolved.name,
            content=resolved.read_bytes(),
            origin=origin,
        )

    def create_from_bytes(
        self, *, filename: str, content: bytes, origin: str
    ) -> tuple[RunRecordView, bool]:
        suffix = Path(filename).suffix.lower()
        if suffix not in self.supported_suffixes:
            raise InvalidInvoiceInput(
                "UNSUPPORTED_FILE_TYPE", "Unsupported invoice type."
            )
        if not content:
            raise InvalidInvoiceInput("EMPTY_FILE", "Invoice file is empty.")
        if len(content) > self.max_source_bytes:
            raise self._file_too_large()

        provider_name, provider_model = self._provider_profile()
        self.provider_registry.get(provider_name, provider_model)
        self.settings.upload_dir.mkdir(parents=True, exist_ok=True)
        staged = self.settings.upload_dir / f"{uuid4().hex}{suffix}"
        try:
            staged.write_bytes(content)
            record, deduplicated = self.run_repository.create_run(
                content_hash=hashlib.sha256(content).hexdigest(),
                source_filename=Path(filename).name,
                source_path=str(staged),
                source_format=suffix.removeprefix("."),
                source_origin=origin,
                provider_name=provider_name,
                provider_model=provider_model,
            )
        except Exception:
            staged.unlink(missing_ok=True)
            raise
        if deduplicated:
            staged.unlink(missing_ok=True)
        return record, deduplicated

    def _provider_profile(self) -> tuple[str, str]:
        if self.settings.llm_provider == "grok":
            model = (
                self.settings.grok_model
                if self.settings.llm_model == "deterministic-v1"
                else self.settings.llm_model
            )
            return "grok", model
        return self.settings.llm_provider, self.settings.llm_model

    def _validate_source(self, path: Path) -> Path:
        resolved = path.expanduser().resolve()
        if not resolved.is_file():
            raise InvalidInvoiceInput(
                "INVALID_UPLOAD", "Invoice file does not exist."
            )
        if resolved.suffix.lower() not in self.supported_suffixes:
            raise InvalidInvoiceInput(
                "UNSUPPORTED_FILE_TYPE", "Unsupported invoice type."
            )
        size = resolved.stat().st_size
        if size <= 0:
            raise InvalidInvoiceInput("EMPTY_FILE", "Invoice file is empty.")
        if size > self.max_source_bytes:
            raise self._file_too_large()
        return resolved

    def _file_too_large(self) -> InvalidInvoiceInput:
        limit = self.max_source_bytes
        if limit % (1024 * 1024) == 0:
            label = f"{limit // (1024 * 1024)} MB"
        elif limit % 1024 == 0:
            label = f"{limit // 1024} KB"
        else:
            label = f"{limit} {'byte' if limit == 1 else 'bytes'}"
        return InvalidInvoiceInput(
            "FILE_TOO_LARGE",
            f"Invoice exceeds the {label} limit.",
        )
