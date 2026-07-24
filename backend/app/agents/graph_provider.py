from functools import lru_cache

from langgraph.graph.state import CompiledStateGraph

from backend.app.agents.graphs import create_invoice_graph


class GraphProvider:
    def __init__(self) -> None:
        self._invoice_graph: CompiledStateGraph | None = None

    def invoice_graph(self) -> CompiledStateGraph:
        if self._invoice_graph is None:
            self._invoice_graph = create_invoice_graph()
        return self._invoice_graph


@lru_cache
def get_graph_provider() -> GraphProvider:
    return GraphProvider()


def clear_graph_provider_cache() -> None:
    get_graph_provider.cache_clear()

