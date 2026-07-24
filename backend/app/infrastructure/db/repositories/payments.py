from uuid import UUID

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from backend.app.infrastructure.db.models import Payment
from backend.app.infrastructure.db.repositories.base import SessionRepository
from backend.app.infrastructure.db.repositories.mappers import (
    timestamp,
    to_payment_result,
)
from backend.app.schemas.domain import Money, PaymentResult


class PaymentRepository(SessionRepository):
    def create_or_get(
        self,
        run_id: UUID | str,
        money: Money,
        idempotency_key: str,
    ) -> PaymentResult:
        identifier = str(run_id)
        with self.sessions(write=False) as session:
            existing = session.get(Payment, identifier)
            if existing is not None:
                return to_payment_result(existing)

        now = timestamp()
        payment = Payment(
            run_id=identifier,
            idempotency_key=idempotency_key,
            status="pending",
            amount_cents=int(money.amount * 100),
            currency=money.currency,
            created_at=now,
            updated_at=now,
        )
        try:
            with self.sessions(write=True) as session:
                session.add(payment)
                session.flush()
                result = to_payment_result(payment)
        except IntegrityError:
            with self.sessions(write=False) as session:
                existing = session.get(Payment, identifier)
                if existing is None:
                    raise
                return to_payment_result(existing)
        return result

    def succeed(self, run_id: UUID | str) -> PaymentResult:
        identifier = str(run_id)
        now = timestamp()
        mock_reference = f"MOCK-{identifier[:8].upper()}"
        with self.sessions(write=True) as session:
            session.execute(
                update(Payment)
                .where(Payment.run_id == identifier, Payment.status == "pending")
                .values(
                    status="succeeded",
                    mock_reference=mock_reference,
                    updated_at=now,
                )
            )
            payment = session.get(Payment, identifier)
            if payment is None:
                raise KeyError(f"Unknown payment run: {run_id}")
            session.refresh(payment)
            return to_payment_result(payment)
