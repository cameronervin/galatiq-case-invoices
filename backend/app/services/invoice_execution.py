from __future__ import annotations

import time
from pathlib import Path
from uuid import UUID

from backend.app.ports.documents import DocumentLoadError
from backend.app.ports.providers import (
    ProviderConfigurationError,
    ProviderError,
)
from backend.app.ports.repositories import (
    RunRepository,
    RunTransitionConflict,
)
from backend.app.ports.runtime import InvoiceWorkflowRunner, WorkflowSettings
from backend.app.schemas.domain import RunDetail, RunStage, RunStatus
from backend.app.services.invoice_reviews import ReviewConflict


class InvoiceExecutionService:
    """Execute and resume the durable invoice-processing workflow."""

    def __init__(
        self,
        *,
        settings: WorkflowSettings,
        run_repository: RunRepository,
        workflow_runner: InvoiceWorkflowRunner,
    ) -> None:
        self.settings = settings
        self.run_repository = run_repository
        self.workflow_runner = workflow_runner

    @property
    def graph_provider(self):
        return self.workflow_runner.graph_provider

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
            return self._required_detail(record.run_id)
        if not self.run_repository.claim_execution(record.run_id):
            return self._required_detail(record.run_id)
        try:
            self.workflow_runner.execute(
                str(record.run_id),
                record.stage,
                self._deadline(timeout_seconds),
            )
        except Exception as exc:
            self._fail(record.run_id, exc)
        return self._finalize(record.run_id)

    def resume_run(
        self, run_id: UUID | str, *, timeout_seconds: int | None = None
    ) -> RunDetail:
        review = self.run_repository.clear_resume_pending(run_id)
        if review is None:
            raise ReviewConflict("No persisted review is available to resume.")
        try:
            self.workflow_runner.resume(
                str(run_id),
                self._deadline(timeout_seconds),
            )
        except Exception as exc:
            self._fail(run_id, exc)
        return self._finalize(run_id, unknown_is_key_error=True)

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
        if record is not None:
            Path(record.source_path).unlink(missing_ok=True)

    def _deadline(self, timeout_seconds: int | None) -> float:
        return time.monotonic() + (
            timeout_seconds or self.settings.workflow_timeout_seconds
        )

    def _finalize(
        self, run_id: UUID | str, *, unknown_is_key_error: bool = False
    ) -> RunDetail:
        detail = self.run_repository.get_detail(run_id)
        if detail is None:
            if unknown_is_key_error:
                raise KeyError(f"Unknown run: {run_id}")
            raise RuntimeError("Run detail disappeared")
        if detail.status in {
            RunStatus.COMPLETED,
            RunStatus.REJECTED,
            RunStatus.FAILED,
        }:
            self.cleanup_source(run_id)
        return self.run_repository.get_detail(run_id) or detail

    def _required_detail(self, run_id: UUID | str) -> RunDetail:
        detail = self.run_repository.get_detail(run_id)
        if detail is None:
            raise RuntimeError("Run detail disappeared")
        return detail

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
        try:
            self.run_repository.transition(
                run_id,
                status=RunStatus.FAILED,
                stage=RunStage.FINALIZE,
                event_code="RUN_FAILED",
                message=message,
                error_code=code,
            )
        except RunTransitionConflict:
            pass
