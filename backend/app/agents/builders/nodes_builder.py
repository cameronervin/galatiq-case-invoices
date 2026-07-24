from collections.abc import Awaitable, Callable

from backend.app.agents.nodes import scaffold_node
from backend.app.agents.states import InvoiceProcessingState

AgentNode = Callable[[InvoiceProcessingState], Awaitable[dict[str, object]]]


def build_scaffold_node() -> AgentNode:
    return scaffold_node

