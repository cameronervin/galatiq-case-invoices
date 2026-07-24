from uuid import UUID

from sqlalchemy import select

from backend.app.infrastructure.db.models import (
    AgentRun,
    Payment,
    RunEventRecord,
    RunResult,
)
from backend.app.infrastructure.db.repositories.base import SessionRepository
from backend.app.infrastructure.db.repositories.mappers import (
    RunRecord,
    to_run_detail,
    to_run_record,
    to_run_summary,
)
from backend.app.infrastructure.db.session import SessionContext
from backend.app.schemas.domain import RunDetail, RunStatus, RunSummary


def find_active_profile(
    sessions: SessionContext,
    content_hash: str,
    provider_name: str,
    provider_model: str,
) -> RunRecord | None:
    statement = (
        select(AgentRun)
        .where(
            AgentRun.content_hash == content_hash,
            AgentRun.provider_name == provider_name,
            AgentRun.provider_model == provider_model,
            AgentRun.status != RunStatus.FAILED.value,
        )
        .order_by(AgentRun.created_at.desc())
        .limit(1)
    )
    with sessions(write=False) as session:
        row = session.scalar(statement)
        return to_run_record(row) if row is not None else None


class RunQueryRepository(SessionRepository):
    def get_internal(self, run_id: UUID | str) -> RunRecord | None:
        with self.sessions(write=False) as session:
            row = session.get(AgentRun, str(run_id))
            return to_run_record(row) if row is not None else None

    def list_summaries(self, limit: int = 20) -> list[RunSummary]:
        statement = (
            select(AgentRun)
            .order_by(AgentRun.created_at.desc(), AgentRun.run_id.desc())
            .limit(limit)
        )
        with self.sessions(write=False) as session:
            return [to_run_summary(row) for row in session.scalars(statement)]

    def get_detail(self, run_id: UUID | str) -> RunDetail | None:
        identifier = str(run_id)
        with self.sessions(write=False) as session:
            run = session.get(AgentRun, identifier)
            if run is None:
                return None
            result = session.get(RunResult, identifier)
            payment = session.get(Payment, identifier)
            events = session.scalars(
                select(RunEventRecord)
                .where(RunEventRecord.run_id == identifier)
                .order_by(RunEventRecord.event_id)
            ).all()
            if result is None:
                raise RuntimeError(f"Run result missing: {run_id}")
            return to_run_detail(run, result, payment, events)
