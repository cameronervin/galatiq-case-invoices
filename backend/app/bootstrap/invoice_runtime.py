from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.core.config import Settings
from backend.app.infrastructure.db.migrations import initialize_database
from backend.app.infrastructure.db.repositories.inventory import InventoryRepository
from backend.app.infrastructure.db.repositories.payments import PaymentRepository
from backend.app.infrastructure.db.repositories.runs import RunRepository
from backend.app.infrastructure.db.session import Database
from backend.app.infrastructure.documents import (
    MAX_SOURCE_BYTES,
    SUPPORTED_SUFFIXES,
    load_document,
)
from backend.app.infrastructure.graph.provider import GraphProvider
from backend.app.infrastructure.graph.runner import AgentWorkflowRunner
from backend.app.infrastructure.llm.factory import ProviderRegistry
from backend.app.ports.documents import DocumentLoader
from backend.app.ports.runtime import InventoryLookup
from backend.app.services.invoice_execution import InvoiceExecutionService
from backend.app.services.invoice_intake import InvoiceIntakeService
from backend.app.services.invoice_processing import InvoiceProcessingService
from backend.app.services.invoice_reviews import InvoiceReviewService
from backend.app.services.run_queries import RunQueryService


@dataclass
class InvoiceProcessingRuntime:
    """Owns the replaceable infrastructure used by invoice processing."""

    settings: Settings
    database: Database
    run_repository: RunRepository
    payment_repository: PaymentRepository
    provider_registry: ProviderRegistry
    graph_provider: GraphProvider
    inventory_lookup: InventoryLookup
    document_loader: DocumentLoader
    supported_suffixes: frozenset[str]
    max_source_bytes: int
    _closed: bool = field(default=False, init=False, repr=False)

    @classmethod
    def create(cls, settings: Settings) -> InvoiceProcessingRuntime:
        database = Database(settings.database_path)
        initialize_database(database)
        run_repository = RunRepository(database.session)
        inventory_repository = InventoryRepository(database.session)
        payment_repository = PaymentRepository(database.session)
        provider_registry = ProviderRegistry(
            grok_api_key=settings.xai_api_key,
            grok_model=settings.grok_model,
        )
        return cls(
            settings=settings,
            database=database,
            run_repository=run_repository,
            payment_repository=payment_repository,
            provider_registry=provider_registry,
            graph_provider=GraphProvider(settings.database_path),
            inventory_lookup=inventory_repository.resolve_item,
            document_loader=load_document,
            supported_suffixes=frozenset(SUPPORTED_SUFFIXES),
            max_source_bytes=MAX_SOURCE_BYTES,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        # The graph checkpoint connection must release before the application engine.
        self.graph_provider.close()
        self.provider_registry.close()
        self.database.close()


def compose_invoice_processor(
    runtime: InvoiceProcessingRuntime,
) -> InvoiceProcessingService:
    return InvoiceProcessingService(
        intake=InvoiceIntakeService(
            settings=runtime.settings,
            run_repository=runtime.run_repository,
            provider_registry=runtime.provider_registry,
            supported_suffixes=runtime.supported_suffixes,
            max_source_bytes=runtime.max_source_bytes,
        ),
        execution=InvoiceExecutionService(
            settings=runtime.settings,
            run_repository=runtime.run_repository,
            workflow_runner=AgentWorkflowRunner(
                settings=runtime.settings,
                run_repository=runtime.run_repository,
                payment_repository=runtime.payment_repository,
                provider_registry=runtime.provider_registry,
                graph_provider=runtime.graph_provider,
                inventory_lookup=runtime.inventory_lookup,
                document_loader=runtime.document_loader,
            ),
        ),
        reviews=InvoiceReviewService(runtime.run_repository),
        queries=RunQueryService(runtime.run_repository),
        close_resources=runtime.close,
    )


def build_invoice_processor(settings: Settings) -> InvoiceProcessingService:
    return compose_invoice_processor(InvoiceProcessingRuntime.create(settings))
