from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from backend.app.agents.builders.nodes_builder import build_scaffold_node
from backend.app.agents.states import InvoiceProcessingState


def build_invoice_graph() -> CompiledStateGraph:
    graph = StateGraph(InvoiceProcessingState)
    graph.add_node("scaffold", build_scaffold_node())
    graph.add_edge(START, "scaffold")
    graph.add_edge("scaffold", END)
    return graph.compile()

