from backend.app.agents.executors import AgentPipelineExecutor
from backend.app.agents.states import InvoiceProcessingState


class AgentExecutionService:
    def __init__(self, executor: AgentPipelineExecutor | None = None) -> None:
        self.executor = executor or AgentPipelineExecutor()

    async def execute(
        self, *, run_id: str, invoice_path: str
    ) -> InvoiceProcessingState:
        initial_state = InvoiceProcessingState(
            run_id=run_id,
            invoice_path=invoice_path,
            status="running",
            current_stage="scaffold",
            messages=[],
            errors=[],
        )
        return await self.executor.execute(initial_state)
