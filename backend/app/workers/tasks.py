from typing import Any

from pydantic import BaseModel

from backend.app.agents.executors import AgentPipelineExecutor
from backend.app.services.agent_execution_service import AgentExecutionService
from backend.app.workers.app import (
    celery_app,
    get_worker_graph_provider,
    run_async,
)


@celery_app.task(name="invoice_processing.agent_runs.execute")
def execute_agent_run(*, run_id: str, invoice_path: str) -> dict[str, Any]:
    """Execute one invoice graph run and return JSON-safe state."""
    return run_async(_execute_agent_run(run_id=run_id, invoice_path=invoice_path))


async def _execute_agent_run(*, run_id: str, invoice_path: str) -> dict[str, Any]:
    graph_provider = get_worker_graph_provider()
    executor = AgentPipelineExecutor(graph_provider=graph_provider)
    state = await AgentExecutionService(executor=executor).execute(
        run_id=run_id,
        invoice_path=invoice_path,
    )
    return _json_safe(state)


def _json_safe(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
