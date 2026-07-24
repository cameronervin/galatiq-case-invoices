from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Integer, Text, func, literal
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.infrastructure.db.models.agent_runs import AgentRun
from backend.app.infrastructure.db.models.base import Base


class RunResult(Base):
    __tablename__ = "run_results"

    run_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey(AgentRun.__table__.c.run_id, ondelete="CASCADE"),
        primary_key=True,
    )
    invoice: Mapped[dict[str, Any] | None] = mapped_column(
        "invoice_json",
        JSON(none_as_null=True),
    )
    findings: Mapped[list[dict[str, Any]]] = mapped_column(
        "findings_json",
        JSON(none_as_null=True),
        nullable=False,
        default=list,
        server_default=func.json_array(),
    )
    recommendation: Mapped[dict[str, Any] | None] = mapped_column(
        "recommendation_json",
        JSON(none_as_null=True),
    )
    review: Mapped[dict[str, Any] | None] = mapped_column(
        "review_json",
        JSON(none_as_null=True),
    )
    extraction_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=literal(0),
    )
    reflection_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=literal(0),
    )
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)


RunResult.__table__.append_constraint(
    CheckConstraint(
        RunResult.__table__.c.extraction_attempts.between(0, 2),
        name="ck_run_results_extraction_attempts",
    )
)
RunResult.__table__.append_constraint(
    CheckConstraint(
        RunResult.__table__.c.reflection_count.between(0, 1),
        name="ck_run_results_reflection_count",
    )
)
