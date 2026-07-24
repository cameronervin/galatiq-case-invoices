from dataclasses import dataclass
from typing import Protocol

from backend.app.ports.documents import DocumentLoader
from backend.app.ports.providers import ProviderResolver
from backend.app.ports.repositories import (
    AgentRunRepository,
    PaymentStore,
)
from backend.app.ports.runtime import InventoryLookup


class RuntimeSettings(Protocol):
    default_currency: str


@dataclass(frozen=True)
class AgentRuntimeContext:
    settings: RuntimeSettings
    run_repository: AgentRunRepository
    payment_repository: PaymentStore
    provider_registry: ProviderResolver
    inventory_lookup: InventoryLookup
    document_loader: DocumentLoader
    deadline_monotonic: float
