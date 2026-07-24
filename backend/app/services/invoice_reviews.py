from datetime import UTC, datetime
from uuid import UUID

from backend.app.ports.repositories import (
    ReviewPersistenceConflict,
    RunRepository,
)
from backend.app.schemas.domain import HumanReview, ReviewRequest, RunStatus


class ReviewConflict(RuntimeError):
    pass


class InvoiceReviewService:
    """Persist human review decisions with conflict protection."""

    def __init__(self, run_repository: RunRepository) -> None:
        self.run_repository = run_repository

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
