from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.infrastructure.db.models.agent_runs import AgentRun
from backend.app.infrastructure.db.models.base import Base


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("idempotency_key"),)

    run_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey(AgentRun.__table__.c.run_id, ondelete="CASCADE"),
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


Payment.__table__.append_constraint(
    CheckConstraint(
        Payment.__table__.c.status.in_(("pending", "succeeded", "failed")),
        name="ck_payments_status",
    )
)
Payment.__table__.append_constraint(
    CheckConstraint(Payment.__table__.c.amount_cents > 0, name="ck_payments_amount")
)
