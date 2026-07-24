from backend.app.agents.graph_provider import GraphProvider, get_graph_provider
from backend.app.agents.states import InvoiceProcessingState


class AgentPipelineExecutor:
    def __init__(self, graph_provider: GraphProvider | None = None) -> None:
        self.graph_provider = graph_provider or get_graph_provider()

    async def execute(
        self, initial_state: InvoiceProcessingState
    ) -> InvoiceProcessingState:
        result = await self.graph_provider.invoice_graph().ainvoke(initial_state)
        return InvoiceProcessingState(**result)

