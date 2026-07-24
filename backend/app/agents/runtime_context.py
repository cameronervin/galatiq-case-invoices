from dataclasses import dataclass

from backend.app.agents.tools import ToolRegistry
from backend.app.core.config import Settings
from backend.app.infrastructure.llm.factory import ProviderRegistry
from backend.app.repositories.sqlalchemy import (
    InventoryRepository,
    PaymentRepository,
    RunRepository,
)


@dataclass(frozen=True)
class AgentRuntimeContext:
    settings: Settings
    run_repository: RunRepository
    inventory_repository: InventoryRepository
    payment_repository: PaymentRepository
    provider_registry: ProviderRegistry
    tool_registry: ToolRegistry
    deadline_monotonic: float
