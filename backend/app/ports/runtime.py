from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from langgraph.graph.state import CompiledStateGraph

from backend.app.schemas.domain import RunStage

InventoryLookup = Callable[[str], tuple[str, int, bool] | None]


class GraphProvider(Protocol):
    def invoice_graph(self) -> CompiledStateGraph: ...

    def close(self) -> None: ...


class InvoiceIntakeSettings(Protocol):
    upload_dir: Path
    max_upload_bytes: int
    llm_provider: str
    llm_model: str
    grok_model: str


class WorkflowSettings(Protocol):
    workflow_timeout_seconds: int


class InvoiceWorkflowRunner(Protocol):
    graph_provider: GraphProvider

    def execute(self, run_id: str, stage: RunStage, deadline: float) -> None: ...

    def resume(self, run_id: str, deadline: float) -> None: ...
