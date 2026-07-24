from sqlalchemy import CheckConstraint, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.infrastructure.db.models.base import Base
from backend.app.schemas.workflow import RunStage, RunStatus


class AgentRun(Base):
    __tablename__ = "agent_runs"

    run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    source_filename: Mapped[str] = mapped_column(Text, nullable=False)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    source_format: Mapped[str] = mapped_column(Text, nullable=False)
    source_origin: Mapped[str] = mapped_column(Text, nullable=False)
    provider_name: Mapped[str] = mapped_column(Text, nullable=False)
    provider_model: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    error_code: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    completed_at: Mapped[str | None] = mapped_column(Text)


AgentRun.__table__.append_constraint(
    CheckConstraint(
        AgentRun.__table__.c.source_format.in_(("pdf", "txt", "json", "csv", "xml")),
        name="ck_agent_runs_source_format",
    )
)
AgentRun.__table__.append_constraint(
    CheckConstraint(
        AgentRun.__table__.c.source_origin.in_(("cli", "api")),
        name="ck_agent_runs_source_origin",
    )
)
AgentRun.__table__.append_constraint(
    CheckConstraint(
        AgentRun.__table__.c.status.in_(tuple(status.value for status in RunStatus)),
        name="ck_agent_runs_status",
    )
)
AgentRun.__table__.append_constraint(
    CheckConstraint(
        AgentRun.__table__.c.stage.in_(tuple(stage.value for stage in RunStage)),
        name="ck_agent_runs_stage",
    )
)
Index(
    "idx_agent_runs_active_profile",
    AgentRun.__table__.c.content_hash,
    AgentRun.__table__.c.provider_name,
    AgentRun.__table__.c.provider_model,
    unique=True,
    sqlite_where=AgentRun.__table__.c.status != RunStatus.FAILED.value,
)
Index(
    "idx_agent_runs_newest",
    AgentRun.__table__.c.created_at.desc(),
    AgentRun.__table__.c.run_id.desc(),
)
