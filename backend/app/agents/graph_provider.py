import sqlite3
from pathlib import Path

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.state import CompiledStateGraph

from backend.app.agents.graphs import create_invoice_graph

CHECKPOINT_TYPE_ALLOWLIST = [
    ("backend.app.infrastructure.llm.base", "ApprovalProposal"),
    ("backend.app.schemas.domain", "ApprovalRecommendation"),
    ("backend.app.schemas.domain", "DecisionRoute"),
    ("backend.app.schemas.domain", "FindingSeverity"),
    ("backend.app.schemas.domain", "InvoiceData"),
    ("backend.app.schemas.domain", "InvoiceItem"),
    ("backend.app.schemas.domain", "Money"),
    ("backend.app.schemas.domain", "RunStage"),
    ("backend.app.schemas.domain", "RunStatus"),
    ("backend.app.schemas.domain", "ValidationFinding"),
]


class GraphProvider:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._connection: sqlite3.Connection | None = None
        self._invoice_graph: CompiledStateGraph | None = None

    def invoice_graph(self) -> CompiledStateGraph:
        if self._invoice_graph is None:
            self._connection = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=5.0,
                isolation_level="IMMEDIATE",
            )
            self._connection.setconfig(sqlite3.SQLITE_DBCONFIG_ENABLE_FKEY, True)
            saver = SqliteSaver(
                self._connection,
                serde=JsonPlusSerializer(
                    allowed_msgpack_modules=CHECKPOINT_TYPE_ALLOWLIST
                ),
            )
            saver.setup()
            self._invoice_graph = create_invoice_graph(checkpointer=saver)
        return self._invoice_graph

    def close(self) -> None:
        self._invoice_graph = None
        if self._connection is not None:
            self._connection.close()
            self._connection = None


def get_graph_provider(database_path: Path) -> GraphProvider:
    return GraphProvider(database_path)


def clear_graph_provider_cache() -> None:
    """Compatibility hook; graph providers are now explicitly owned resources."""
