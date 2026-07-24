from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from backend.app.agents.nodes import (
    approval_agent_node,
    critic_agent_node,
    extraction_agent_node,
    ingest_node,
    payment_agent_node,
    reject_node,
    review_node,
    route_policy,
    route_review,
    validation_agent_node,
)
from backend.app.agents.runtime_context import AgentRuntimeContext
from backend.app.agents.states import InvoiceProcessingState


def build_invoice_graph(
    *, checkpointer: BaseCheckpointSaver[str] | None = None
) -> CompiledStateGraph:
    graph = StateGraph(
        state_schema=InvoiceProcessingState,
        context_schema=AgentRuntimeContext,
    )
    graph.add_node("ingest", ingest_node)
    graph.add_node("extraction_agent", extraction_agent_node)
    graph.add_node("validation_agent", validation_agent_node)
    graph.add_node("approval_agent", approval_agent_node)
    graph.add_node("critic_agent", critic_agent_node)
    graph.add_node("review", review_node)
    graph.add_node("payment_agent", payment_agent_node)
    graph.add_node("reject", reject_node)
    graph.add_edge(START, "ingest")
    graph.add_edge("ingest", "extraction_agent")
    graph.add_edge("extraction_agent", "validation_agent")
    graph.add_edge("validation_agent", "approval_agent")
    graph.add_edge("approval_agent", "critic_agent")
    graph.add_conditional_edges(
        "critic_agent",
        route_policy,
        {"approve": "payment_agent", "review": "review", "reject": "reject"},
    )
    graph.add_conditional_edges(
        "review", route_review, {"pay": "payment_agent", "reject": "reject"}
    )
    graph.add_edge("payment_agent", END)
    graph.add_edge("reject", END)
    return graph.compile(checkpointer=checkpointer)
