from typing import Protocol
from uuid import UUID

from backend.app.schemas.domain import Money, PaymentResult, RunDetail


class AgentRunRepository(Protocol):
    def get_detail(self, run_id: UUID | str) -> RunDetail | None: ...


class InventoryLookupRepository(Protocol):
    def resolve_item(self, source_name: str) -> tuple[str, int, bool] | None: ...


class PaymentStore(Protocol):
    def create_or_get(
        self, run_id: UUID | str, money: Money, idempotency_key: str
    ) -> PaymentResult: ...
