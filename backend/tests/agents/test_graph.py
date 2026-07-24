import pytest

from backend.app.agents.executors import AgentPipelineExecutor
from backend.app.agents.graph_provider import GraphProvider


def test_graph_provider_reuses_compiled_graph() -> None:
    provider = GraphProvider()

    assert provider.invoice_graph() is provider.invoice_graph()


@pytest.mark.asyncio
async def test_executor_returns_explicit_placeholder_state() -> None:
    state = await AgentPipelineExecutor().execute(
        {
            "run_id": "run-1",
            "invoice_path": "/tmp/invoice.txt",
            "status": "running",
            "current_stage": "scaffold",
            "messages": [],
            "errors": [],
        }
    )

    assert state["run_id"] == "run-1"
    assert state["status"] == "scaffolded"
    assert state["current_stage"] == "not_implemented"
    assert state["messages"] == ["invoice pipeline is not implemented"]

