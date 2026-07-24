from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from backend.app.agents.builders import build_invoice_graph


def create_invoice_graph(
    *, checkpointer: BaseCheckpointSaver[str] | None = None
) -> CompiledStateGraph:
    return build_invoice_graph(checkpointer=checkpointer)
