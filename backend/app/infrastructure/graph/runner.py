from backend.app.agents.executors import AgentPipelineExecutor
from backend.app.agents.runtime_context import AgentRuntimeContext, RuntimeSettings
from backend.app.agents.states import InvoiceProcessingState
from backend.app.ports.documents import DocumentLoader
from backend.app.ports.providers import ProviderResolver
from backend.app.ports.repositories import PaymentStore, RunRepository
from backend.app.ports.runtime import GraphProvider, InventoryLookup
from backend.app.schemas.domain import RunStage, RunStatus


class AgentWorkflowRunner:
    """LangGraph adapter for the invoice-workflow runner port."""

    def __init__(
        self,
        *,
        settings: RuntimeSettings,
        run_repository: RunRepository,
        payment_repository: PaymentStore,
        provider_registry: ProviderResolver,
        graph_provider: GraphProvider,
        inventory_lookup: InventoryLookup,
        document_loader: DocumentLoader,
    ) -> None:
        self.settings = settings
        self.run_repository = run_repository
        self.payment_repository = payment_repository
        self.provider_registry = provider_registry
        self.graph_provider = graph_provider
        self.inventory_lookup = inventory_lookup
        self.document_loader = document_loader

    def execute(self, run_id: str, stage: RunStage, deadline: float) -> None:
        AgentPipelineExecutor(self.graph_provider.invoice_graph()).execute(
            InvoiceProcessingState(
                run_id=run_id,
                status=RunStatus.RUNNING,
                stage=stage,
                invoice=None,
                findings=[],
                proposal=None,
                recommendation=None,
                review=None,
                payment=None,
                extraction_attempts=0,
                reflection_count=0,
                error=None,
            ),
            self._context(deadline),
        )

    def resume(self, run_id: str, deadline: float) -> None:
        AgentPipelineExecutor(self.graph_provider.invoice_graph()).resume(
            run_id,
            self._context(deadline),
        )

    def _context(self, deadline: float) -> AgentRuntimeContext:
        return AgentRuntimeContext(
            settings=self.settings,
            run_repository=self.run_repository,
            payment_repository=self.payment_repository,
            provider_registry=self.provider_registry,
            inventory_lookup=self.inventory_lookup,
            document_loader=self.document_loader,
            deadline_monotonic=deadline,
        )
