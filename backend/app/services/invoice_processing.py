from __future__ import annotations

import hashlib
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from backend.app.agents.executors import AgentPipelineExecutor
from backend.app.agents.graph_provider import GraphProvider
from backend.app.agents.runtime_context import AgentRuntimeContext
from backend.app.agents.states import InvoiceProcessingState
from backend.app.agents.tools import ToolRegistry
from backend.app.core.config import Settings
from backend.app.infrastructure.db.migrations import initialize_database
from backend.app.infrastructure.db.session import Database
from backend.app.infrastructure.llm.factory import (
    ProviderConfigurationError,
    ProviderRegistry,
)
from backend.app.infrastructure.llm.providers import ProviderError
from backend.app.repositories.sqlalchemy import (
    InventoryRepository,
    PaymentRepository,
    ReviewPersistenceConflict,
    RunRecord,
    RunRepository,
)
from backend.app.schemas.domain import (
    HumanReview,
    ReviewRequest,
    RunCreationResponse,
    RunDetail,
    RunStage,
    RunStatus,
)
from backend.app.services.document_loaders import (
    MAX_SOURCE_BYTES,
    SUPPORTED_SUFFIXES,
    DocumentLoadError,
)


class InvalidInvoiceInput(ValueError):
    pass


class ReviewConflict(RuntimeError):
    pass


class InvoiceProcessingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.database = Database(settings.database_path)
        initialize_database(self.database)
        self.run_repository = RunRepository(self.database.session)
        self.inventory_repository = InventoryRepository(self.database.session)
        self.payment_repository = PaymentRepository(self.database.session)
        self.provider_registry = ProviderRegistry(
            grok_api_key=settings.xai_api_key,
            grok_model=settings.grok_model,
        )
        self.tool_registry = ToolRegistry()
        self.tool_registry.register(
            "inventory.lookup", self.inventory_repository.resolve_item
        )
        self.graph_provider = GraphProvider(settings.database_path)
        self._closed = False

    def process_path(
        self,
        path: Path,
        *,
        origin: str,
        timeout_seconds: int | None = None,
    ) -> RunDetail:
        record, deduplicated = self.create_from_path(path, origin=origin)
        if deduplicated:
            detail = self.run_repository.get_detail(record.run_id)
            if detail is None:
                raise RuntimeError("Deduplicated run disappeared")
            return detail
        return self.process_run(record.run_id, timeout_seconds=timeout_seconds)

    def create_from_path(self, path: Path, *, origin: str) -> tuple[RunRecord, bool]:
        resolved = self._validate_source(path)
        content = resolved.read_bytes()
        return self.create_from_bytes(
            filename=resolved.name,
            content=content,
            origin=origin,
        )

    def create_from_bytes(
        self, *, filename: str, content: bytes, origin: str
    ) -> tuple[RunRecord, bool]:
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            raise InvalidInvoiceInput("Unsupported invoice type.")
        if not content:
            raise InvalidInvoiceInput("Invoice file is empty.")
        if len(content) > self.settings.max_upload_bytes:
            raise InvalidInvoiceInput("Invoice exceeds the 10 MB limit.")
        provider_name, provider_model = self._provider_profile()
        self.provider_registry.get(provider_name, provider_model)
        self.settings.upload_dir.mkdir(parents=True, exist_ok=True)
        staged = self.settings.upload_dir / f"{uuid4().hex}{suffix}"
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
        if deduplicated:
            staged.unlink(missing_ok=True)
        return record, deduplicated

    def creation_response(
        self, record: RunRecord, *, deduplicated: bool
    ) -> RunCreationResponse:
        return RunCreationResponse(
            run_id=record.run_id,
            source_filename=record.source_filename,
            status=record.status,
            stage=record.stage,
            created_at=record.created_at,
            updated_at=record.updated_at,
            deduplicated=deduplicated,
        )

    def process_run(
        self, run_id: UUID | str, *, timeout_seconds: int | None = None
    ) -> RunDetail:
        record = self.run_repository.get_internal(run_id)
        if record is None:
            raise KeyError(f"Unknown run: {run_id}")
        if record.status in {
            RunStatus.COMPLETED,
            RunStatus.REJECTED,
            RunStatus.FAILED,
            RunStatus.REVIEW_REQUIRED,
        }:
            detail = self.run_repository.get_detail(run_id)
            if detail is None:
                raise RuntimeError("Run detail disappeared")
            return detail
        deadline = time.monotonic() + (
            timeout_seconds or self.settings.workflow_timeout_seconds
        )
        context = self._context(deadline)
        executor = AgentPipelineExecutor(self.graph_provider.invoice_graph())
        initial = InvoiceProcessingState(
            run_id=str(record.run_id),
            status=record.status,
            stage=record.stage,
            invoice=None,
            findings=[],
            proposal=None,
            recommendation=None,
            review=None,
            payment=None,
            extraction_attempts=0,
            reflection_count=0,
            error=None,
        )
        try:
            executor.execute(initial, context)
        except Exception as exc:
            self._fail(record.run_id, exc)
        detail = self.run_repository.get_detail(record.run_id)
        if detail is None:
            raise RuntimeError("Run detail disappeared")
        if detail.status in {RunStatus.COMPLETED, RunStatus.REJECTED, RunStatus.FAILED}:
            self.cleanup_source(record.run_id)
        return self.run_repository.get_detail(record.run_id) or detail

    def resume_run(
        self, run_id: UUID | str, *, timeout_seconds: int | None = None
    ) -> RunDetail:
        review = self.run_repository.clear_resume_pending(run_id)
        if review is None:
            raise ReviewConflict("No persisted review is available to resume.")
        context = self._context(
            time.monotonic()
            + (timeout_seconds or self.settings.workflow_timeout_seconds)
        )
        try:
            AgentPipelineExecutor(self.graph_provider.invoice_graph()).resume(
                str(run_id), context
            )
        except Exception as exc:
            self._fail(run_id, exc)
        detail = self.run_repository.get_detail(run_id)
        if detail is None:
            raise KeyError(f"Unknown run: {run_id}")
        if detail.status in {RunStatus.COMPLETED, RunStatus.REJECTED, RunStatus.FAILED}:
            self.cleanup_source(run_id)
        return self.run_repository.get_detail(run_id) or detail

    def persist_review(self, run_id: UUID | str, request: ReviewRequest) -> bool:
        record = self.run_repository.get_internal(run_id)
        if record is None:
            raise KeyError(f"Unknown run: {run_id}")
        if record.status != RunStatus.REVIEW_REQUIRED:
            raise ReviewConflict("Run is not awaiting review.")
        review = HumanReview(
            decision=request.decision,
            reason=request.reason,
            resume_pending=True,
            decided_at=datetime.now(UTC),
        )
        try:
            stored, identical_pending = self.run_repository.persist_review(
                run_id, review
            )
        except ReviewPersistenceConflict as exc:
            raise ReviewConflict(str(exc)) from exc
        if stored != review and not identical_pending:
            raise ReviewConflict("A different review decision already exists.")
        return identical_pending

    def mark_queue_failure(self, run_id: UUID | str) -> None:
        self.run_repository.transition(
            run_id,
            status=RunStatus.FAILED,
            stage=RunStage.FINALIZE,
            event_code="RUN_FAILED",
            message="Run could not be queued.",
            error_code="QUEUE_UNAVAILABLE",
        )
        self.cleanup_source(run_id)

    def cleanup_source(self, run_id: UUID | str) -> None:
        record = self.run_repository.get_internal(run_id)
        if record is None:
            return
        Path(record.source_path).unlink(missing_ok=True)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.graph_provider.close()
        self.database.close()

    def _provider_profile(self) -> tuple[str, str]:
        if self.settings.llm_provider == "grok":
            model = (
                self.settings.grok_model
                if self.settings.llm_model == "deterministic-v1"
                else self.settings.llm_model
            )
            return "grok", model
        return self.settings.llm_provider, self.settings.llm_model

    def _context(self, deadline: float) -> AgentRuntimeContext:
        return AgentRuntimeContext(
            settings=self.settings,
            run_repository=self.run_repository,
            inventory_repository=self.inventory_repository,
            payment_repository=self.payment_repository,
            provider_registry=self.provider_registry,
            tool_registry=self.tool_registry,
            deadline_monotonic=deadline,
        )

    def _fail(self, run_id: UUID | str, exc: Exception) -> None:
        record = self.run_repository.get_internal(run_id)
        if record is None or record.status in {
            RunStatus.COMPLETED,
            RunStatus.REJECTED,
            RunStatus.FAILED,
        }:
            return
        if isinstance(exc, TimeoutError):
            code, message = "WORKFLOW_TIMEOUT", "Workflow exceeded its time limit."
        elif isinstance(exc, DocumentLoadError):
            code, message = exc.code, exc.safe_message
        elif isinstance(exc, ProviderError):
            code, message = exc.code, exc.safe_message
        elif isinstance(exc, ProviderConfigurationError):
            code, message = "PROVIDER_NOT_CONFIGURED", str(exc)
        else:
            code, message = "WORKFLOW_FAILED", "Invoice processing failed safely."
        self.run_repository.transition(
            run_id,
            status=RunStatus.FAILED,
            stage=RunStage.FINALIZE,
            event_code="RUN_FAILED",
            message=message,
            error_code=code,
        )

    def _validate_source(self, path: Path) -> Path:
        resolved = path.expanduser().resolve()
        if not resolved.is_file():
            raise InvalidInvoiceInput("Invoice file does not exist.")
        if resolved.suffix.lower() not in SUPPORTED_SUFFIXES:
            raise InvalidInvoiceInput("Unsupported invoice type.")
        size = resolved.stat().st_size
        if size <= 0:
            raise InvalidInvoiceInput("Invoice file is empty.")
        if size > min(MAX_SOURCE_BYTES, self.settings.max_upload_bytes):
            raise InvalidInvoiceInput("Invoice exceeds the 10 MB limit.")
        return resolved
