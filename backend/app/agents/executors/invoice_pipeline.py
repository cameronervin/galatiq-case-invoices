from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from backend.app.agents.runtime_context import AgentRuntimeContext
from backend.app.agents.states import InvoiceProcessingState


class AgentPipelineExecutor:
    def __init__(self, graph: CompiledStateGraph) -> None:
        self.graph = graph

    def execute(
        self, initial_state: InvoiceProcessingState, context: AgentRuntimeContext
    ) -> InvoiceProcessingState:
        result = self.graph.invoke(
            initial_state,
            {
                "configurable": {"thread_id": initial_state["run_id"]},
                "recursion_limit": 30,
            },
            context=context,
        )
        return InvoiceProcessingState(**result)

    def resume(
        self, run_id: str, context: AgentRuntimeContext
    ) -> InvoiceProcessingState:
        result = self.graph.invoke(
            Command(resume={"run_id": run_id}),
            {
                "configurable": {"thread_id": run_id},
                "recursion_limit": 30,
            },
            context=context,
        )
        return InvoiceProcessingState(**result)
