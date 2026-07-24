import time

from backend.app.agents.runtime_context import AgentRuntimeContext
from backend.app.agents.states import InvoiceProcessingState
from backend.app.ports.repositories import RunRecordView
from backend.app.schemas.domain import InvoiceData


def require_invoice(state: InvoiceProcessingState) -> InvoiceData:
    invoice = state.get("invoice")
    if invoice is None:
        raise RuntimeError("Invoice state is missing")
    return invoice


def require_run(context: AgentRuntimeContext, run_id: str) -> RunRecordView:
    record = context.run_repository.get_internal(run_id)
    if record is None:
        raise KeyError(f"Unknown run: {run_id}")
    return record


def check_deadline(context: AgentRuntimeContext) -> None:
    if time.monotonic() >= context.deadline_monotonic:
        raise TimeoutError("Workflow deadline exceeded")
