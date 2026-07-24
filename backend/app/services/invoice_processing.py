from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from backend.app.ports.providers import ProviderResolver
from backend.app.ports.repositories import RunRecordView, RunRepository
from backend.app.ports.runtime import GraphProvider
from backend.app.schemas.domain import (
    ReviewRequest,
    RunCreationResponse,
    RunDetail,
    RunSummary,
)
from backend.app.services.invoice_execution import InvoiceExecutionService
from backend.app.services.invoice_intake import (
    InvalidInvoiceInput,
    InvoiceIntakeService,
)
from backend.app.services.invoice_reviews import InvoiceReviewService, ReviewConflict
from backend.app.services.run_queries import RunQueryService

__all__ = [
    "InvalidInvoiceInput",
    "InvoiceProcessingService",
    "ReviewConflict",
]


class InvoiceProcessingService:
    """Stable facade composed from focused invoice-processing use cases."""

    def __init__(
        self,
        *,
        intake: InvoiceIntakeService,
        execution: InvoiceExecutionService,
        reviews: InvoiceReviewService,
        queries: RunQueryService,
        close_resources: Callable[[], None],
    ) -> None:
        self.intake = intake
        self.execution = execution
        self.reviews = reviews
        self.queries = queries
        self.close_resources = close_resources

    @property
    def max_source_bytes(self) -> int:
        return self.intake.max_source_bytes

    @property
    def run_repository(self) -> RunRepository:
        return self.intake.run_repository

    @property
    def provider_registry(self) -> ProviderResolver:
        return self.intake.provider_registry

    @property
    def graph_provider(self) -> GraphProvider:
        return self.execution.graph_provider

    def process_path(
        self,
        path: Path,
        *,
        origin: str,
        timeout_seconds: int | None = None,
    ) -> RunDetail:
        record, deduplicated = self.create_from_path(path, origin=origin)
        if deduplicated:
            detail = self.get_run(record.run_id)
            if detail is None:
                raise RuntimeError("Deduplicated run disappeared")
            return detail
        return self.process_run(record.run_id, timeout_seconds=timeout_seconds)

    def create_from_path(
        self, path: Path, *, origin: str
    ) -> tuple[RunRecordView, bool]:
        return self.intake.create_from_path(path, origin=origin)

    def create_from_bytes(
        self, *, filename: str, content: bytes, origin: str
    ) -> tuple[RunRecordView, bool]:
        return self.intake.create_from_bytes(
            filename=filename,
            content=content,
            origin=origin,
        )

    def creation_response(
        self, record: RunRecordView, *, deduplicated: bool
    ) -> RunCreationResponse:
        return self.queries.creation_response(record, deduplicated=deduplicated)

    def list_runs(self, limit: int = 20) -> list[RunSummary]:
        return self.queries.list_runs(limit)

    def get_run(self, run_id: UUID | str) -> RunDetail | None:
        return self.queries.get_run(run_id)

    def get_run_summary(self, run_id: UUID | str) -> RunSummary | None:
        return self.queries.get_run_summary(run_id)

    def process_run(
        self, run_id: UUID | str, *, timeout_seconds: int | None = None
    ) -> RunDetail:
        return self.execution.process_run(run_id, timeout_seconds=timeout_seconds)

    def resume_run(
        self, run_id: UUID | str, *, timeout_seconds: int | None = None
    ) -> RunDetail:
        return self.execution.resume_run(run_id, timeout_seconds=timeout_seconds)

    def persist_review(self, run_id: UUID | str, request: ReviewRequest) -> bool:
        return self.reviews.persist_review(run_id, request)

    def mark_queue_failure(self, run_id: UUID | str) -> None:
        self.execution.mark_queue_failure(run_id)

    def cleanup_source(self, run_id: UUID | str) -> None:
        self.execution.cleanup_source(run_id)

    def close(self) -> None:
        self.close_resources()
