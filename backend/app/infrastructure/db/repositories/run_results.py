from typing import Any
from uuid import UUID

from sqlalchemy import update

from backend.app.infrastructure.db.models import AgentRun, RunResult
from backend.app.infrastructure.db.repositories.base import SessionRepository
from backend.app.infrastructure.db.repositories.mappers import json_payload, timestamp
from backend.app.ports.repositories import ReviewPersistenceConflict
from backend.app.schemas.domain import (
    ApprovalRecommendation,
    HumanReview,
    InvoiceData,
    RunStatus,
    ValidationFinding,
)


class RunResultRepository(SessionRepository):
    def save_result(
        self,
        run_id: UUID | str,
        *,
        invoice: InvoiceData | None = None,
        findings: list[ValidationFinding] | None = None,
        recommendation: ApprovalRecommendation | None = None,
        extraction_attempts: int | None = None,
        reflection_count: int | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                invoice,
                findings,
                recommendation,
                extraction_attempts,
                reflection_count,
            )
        ):
            return
        with self.sessions(write=True) as session:
            result = session.get(RunResult, str(run_id))
            if result is None:
                raise KeyError(f"Unknown run: {run_id}")
            if invoice is not None:
                result.invoice = json_payload(invoice)
            if findings is not None:
                result.findings = json_payload(findings)
            if recommendation is not None:
                result.recommendation = json_payload(recommendation)
            if extraction_attempts is not None:
                result.extraction_attempts = extraction_attempts
            if reflection_count is not None:
                result.reflection_count = reflection_count
            result.updated_at = timestamp()

    def persist_review(
        self,
        run_id: UUID | str,
        review: HumanReview,
    ) -> tuple[HumanReview, bool]:
        identifier = str(run_id)
        with self.sessions(write=True) as session:
            run = session.get(AgentRun, identifier)
            result = session.get(RunResult, identifier)
            if run is None or result is None:
                raise KeyError(f"Unknown run: {run_id}")
            if run.status != RunStatus.REVIEW_REQUIRED.value:
                raise ReviewPersistenceConflict("Run is not awaiting review.")
            if result.review is not None:
                return _review_result(result.review, review)

            payload = json_payload(review)
            changed = session.execute(
                update(RunResult)
                .where(RunResult.run_id == identifier, RunResult.review.is_(None))
                .values(review=payload, updated_at=timestamp())
            ).rowcount
            if changed == 1:
                return review, False
            session.refresh(result)
            if result.review is None:
                raise ReviewPersistenceConflict("Review could not be persisted.")
            return _review_result(result.review, review)

    def clear_resume_pending(self, run_id: UUID | str) -> HumanReview | None:
        identifier = str(run_id)
        with self.sessions(write=True) as session:
            result = session.get(RunResult, identifier)
            if result is None:
                raise KeyError(f"Unknown run: {run_id}")
            if result.review is None:
                return None
            review = HumanReview.model_validate(result.review)
            if not review.resume_pending:
                return None
            updated_review = review.model_copy(update={"resume_pending": False})
            original = result.review
            changed = session.execute(
                update(RunResult)
                .where(RunResult.run_id == identifier, RunResult.review == original)
                .values(review=json_payload(updated_review), updated_at=timestamp())
            ).rowcount
            return updated_review if changed == 1 else None


def _review_result(
    stored_payload: dict[str, Any],
    requested: HumanReview,
) -> tuple[HumanReview, bool]:
    existing = HumanReview.model_validate(stored_payload)
    identical_pending = (
        existing.decision == requested.decision
        and existing.reason == requested.reason
        and existing.resume_pending
    )
    return existing, identical_pending
