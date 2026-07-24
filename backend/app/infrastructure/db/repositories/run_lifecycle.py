from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from backend.app.infrastructure.db.models import AgentRun, RunEventRecord, RunResult
from backend.app.infrastructure.db.repositories.base import SessionRepository
from backend.app.infrastructure.db.repositories.mappers import (
    RunRecord,
    timestamp,
    to_run_record,
)
from backend.app.infrastructure.db.repositories.run_queries import find_active_profile
from backend.app.ports.repositories import RunTransitionConflict
from backend.app.schemas.domain import RunStage, RunStatus

_ALLOWED_PREVIOUS_STATUSES: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.RUNNING: frozenset(
        {RunStatus.QUEUED, RunStatus.RUNNING, RunStatus.REVIEW_REQUIRED}
    ),
    RunStatus.REVIEW_REQUIRED: frozenset({RunStatus.RUNNING}),
    RunStatus.COMPLETED: frozenset({RunStatus.RUNNING}),
    RunStatus.REJECTED: frozenset({RunStatus.RUNNING, RunStatus.REVIEW_REQUIRED}),
    RunStatus.FAILED: frozenset(
        {RunStatus.QUEUED, RunStatus.RUNNING, RunStatus.REVIEW_REQUIRED}
    ),
}


class RunLifecycleRepository(SessionRepository):
    def create_run(
        self,
        *,
        content_hash: str,
        source_filename: str,
        source_path: str,
        source_format: str,
        source_origin: str,
        provider_name: str,
        provider_model: str,
    ) -> tuple[RunRecord, bool]:
        existing = find_active_profile(
            self.sessions, content_hash, provider_name, provider_model
        )
        if existing is not None:
            return existing, True

        now = timestamp()
        run = AgentRun(
            run_id=str(uuid4()),
            content_hash=content_hash,
            source_filename=source_filename,
            source_path=source_path,
            source_format=source_format,
            source_origin=source_origin,
            provider_name=provider_name,
            provider_model=provider_model,
            status=RunStatus.QUEUED.value,
            stage=RunStage.INGEST.value,
            created_at=now,
            updated_at=now,
        )
        try:
            with self.sessions(write=True) as session:
                session.add(run)
                session.add(RunResult(run_id=run.run_id, findings=[], updated_at=now))
                session.add(
                    RunEventRecord(
                        run_id=run.run_id,
                        stage=RunStage.INGEST.value,
                        status=RunStatus.QUEUED.value,
                        code="RUN_QUEUED",
                        safe_message="Run queued.",
                        created_at=now,
                    )
                )
                session.flush()
                record = to_run_record(run)
        except IntegrityError:
            existing = find_active_profile(
                self.sessions, content_hash, provider_name, provider_model
            )
            if existing is None:
                raise
            return existing, True
        return record, False

    def claim_execution(self, run_id: UUID | str) -> bool:
        """Atomically claim a queued run for one execution worker."""
        identifier = str(run_id)
        with self.sessions(write=True) as session:
            changed = session.execute(
                update(AgentRun)
                .where(
                    AgentRun.run_id == identifier,
                    AgentRun.status == RunStatus.QUEUED.value,
                )
                .values(
                    status=RunStatus.RUNNING.value,
                    stage=RunStage.INGEST.value,
                    updated_at=timestamp(),
                )
            ).rowcount
            if changed == 1:
                return True
            if session.get(AgentRun, identifier) is None:
                raise KeyError(f"Unknown run: {run_id}")
            return False

    def transition(
        self,
        run_id: UUID | str,
        *,
        status: RunStatus,
        stage: RunStage,
        event_code: str,
        message: str,
        error_code: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        now = timestamp()
        terminal = status in {RunStatus.COMPLETED, RunStatus.REJECTED, RunStatus.FAILED}
        allowed_previous = _ALLOWED_PREVIOUS_STATUSES.get(status, frozenset())
        with self.sessions(write=True) as session:
            identifier = str(run_id)
            values: dict[str, Any] = {
                "status": status.value,
                "stage": stage.value,
                "error_code": error_code,
                "error_message": message if error_code else None,
                "updated_at": now,
            }
            if terminal:
                values["completed_at"] = now
            changed = session.execute(
                update(AgentRun)
                .where(
                    AgentRun.run_id == identifier,
                    AgentRun.status.in_(
                        tuple(previous.value for previous in allowed_previous)
                    ),
                )
                .values(**values)
            ).rowcount
            if changed != 1:
                run = session.get(AgentRun, identifier)
                if run is None:
                    raise KeyError(f"Unknown run: {run_id}")
                raise RunTransitionConflict(
                    f"Run {run_id} cannot transition from "
                    f"{run.status} to {status.value}."
                )
            session.add(
                RunEventRecord(
                    run_id=identifier,
                    stage=stage.value,
                    status=status.value,
                    code=event_code,
                    safe_message=message,
                    duration_ms=duration_ms,
                    created_at=now,
                )
            )
