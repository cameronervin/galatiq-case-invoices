from __future__ import annotations

from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    literal,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from backend.app.schemas.domain import RunStage, RunStatus


class Base(DeclarativeBase):
    """Declarative base for application-owned persistence models."""

    pass


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"

    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    applied_at: Mapped[str] = mapped_column(Text, nullable=False)


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    item_code: Mapped[str] = mapped_column(Text, primary_key=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    aliases: Mapped[list[str]] = mapped_column(
        "aliases_json",
        JSON(none_as_null=True),
        nullable=False,
    )


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


class RunResult(Base):
    __tablename__ = "run_results"

    run_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("agent_runs.run_id", ondelete="CASCADE"),
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


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("idempotency_key"),)

    run_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("agent_runs.run_id", ondelete="CASCADE"),
        primary_key=True,
    )
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False)
    mock_reference: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)


class RunEventRecord(Base):
    __tablename__ = "run_events"

    event_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    run_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("agent_runs.run_id", ondelete="CASCADE"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    safe_message: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


InventoryItem.__table__.append_constraint(
    CheckConstraint(InventoryItem.__table__.c.stock >= 0, name="ck_inventory_stock")
)
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
Payment.__table__.append_constraint(
    CheckConstraint(
        Payment.__table__.c.status.in_(("pending", "succeeded", "failed")),
        name="ck_payments_status",
    )
)
Payment.__table__.append_constraint(
    CheckConstraint(Payment.__table__.c.amount_cents > 0, name="ck_payments_amount")
)
RunEventRecord.__table__.append_constraint(
    CheckConstraint(
        (RunEventRecord.__table__.c.duration_ms.is_(None))
        | (RunEventRecord.__table__.c.duration_ms >= 0),
        name="ck_run_events_duration",
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
Index(
    "idx_run_events_run",
    RunEventRecord.__table__.c.run_id,
    RunEventRecord.__table__.c.event_id,
)
