from typing import TYPE_CHECKING
from uuid import UUID

from backend.app.ports.queue import AgentRunDispatchError, TaskDispatcher
from backend.app.schemas.domain import (
    ReviewRequest,
    RunCreationResponse,
    RunDetail,
    RunSummary,
)

if TYPE_CHECKING:
    from backend.app.services.invoice_processing import InvoiceProcessingService


class RunApplicationDispatchError(RuntimeError):
    def __init__(self, run_id: UUID) -> None:
        super().__init__("Unable to dispatch invoice-processing run.")
        self.run_id = run_id


class RunApplicationService:
    """Application boundary for HTTP run queries, commands, and dispatch."""

    def __init__(
        self,
        processor: "InvoiceProcessingService",
        dispatcher: TaskDispatcher,
    ) -> None:
        self.processor = processor
        self.dispatcher = dispatcher

    @property
    def max_source_bytes(self) -> int:
        return self.processor.max_source_bytes

    def create_run(
        self, *, filename: str, content: bytes, origin: str
    ) -> RunCreationResponse:
        record, deduplicated = self.processor.create_from_bytes(
            filename=filename,
            content=content,
            origin=origin,
        )
        response = self.processor.creation_response(
            record,
            deduplicated=deduplicated,
        )
        if deduplicated:
            return response
        try:
            self.dispatcher.enqueue_execute(run_id=record.run_id)
        except AgentRunDispatchError as exc:
            self.processor.mark_queue_failure(record.run_id)
            raise RunApplicationDispatchError(record.run_id) from exc
        return response

    def list_runs(self, limit: int = 20) -> list[RunSummary]:
        return self.processor.list_runs(limit)

    def get_run(self, run_id: UUID) -> RunDetail | None:
        return self.processor.get_run(run_id)

    def review_run(self, run_id: UUID, command: ReviewRequest) -> RunSummary:
        self.processor.persist_review(run_id, command)
        try:
            self.dispatcher.enqueue_resume(run_id=run_id)
        except AgentRunDispatchError as exc:
            raise RunApplicationDispatchError(run_id) from exc
        summary = self.processor.get_run_summary(run_id)
        if summary is None:
            raise KeyError(f"Unknown run: {run_id}")
        return summary
