from uuid import UUID

from backend.app.ports.repositories import RunRecordView, RunRepository
from backend.app.schemas.domain import (
    RunCreationResponse,
    RunDetail,
    RunSummary,
)


class RunQueryService:
    """Read invoice-processing runs and shape application responses."""

    def __init__(self, run_repository: RunRepository) -> None:
        self.run_repository = run_repository

    def creation_response(
        self, record: RunRecordView, *, deduplicated: bool
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

    def list_runs(self, limit: int = 20) -> list[RunSummary]:
        return self.run_repository.list_summaries(limit)

    def get_run(self, run_id: UUID | str) -> RunDetail | None:
        return self.run_repository.get_detail(run_id)

    def get_run_summary(self, run_id: UUID | str) -> RunSummary | None:
        record = self.run_repository.get_internal(run_id)
        if record is None:
            return None
        return RunSummary(
            run_id=record.run_id,
            source_filename=record.source_filename,
            status=record.status,
            stage=record.stage,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
