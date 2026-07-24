from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.infrastructure.db.models.agent_runs import AgentRun
from backend.app.infrastructure.db.models.base import Base


class RunEventRecord(Base):
    __tablename__ = "run_events"

    event_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    run_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey(AgentRun.__table__.c.run_id, ondelete="CASCADE"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    safe_message: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


RunEventRecord.__table__.append_constraint(
    CheckConstraint(
        (RunEventRecord.__table__.c.duration_ms.is_(None))
        | (RunEventRecord.__table__.c.duration_ms >= 0),
        name="ck_run_events_duration",
    )
)

Index(
    "idx_run_events_run",
    RunEventRecord.__table__.c.run_id,
    RunEventRecord.__table__.c.event_id,
)
