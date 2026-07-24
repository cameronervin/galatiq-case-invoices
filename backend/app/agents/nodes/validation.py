from langgraph.runtime import Runtime

from backend.app.agents.runtime_context import AgentRuntimeContext
from backend.app.agents.states import InvoiceProcessingState
from backend.app.domain.validation import (
    integrity_findings,
    inventory_findings,
    ordered_unique,
)
from backend.app.schemas.domain import RunStage, RunStatus

from .shared import check_deadline


def validation_agent_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    check_deadline(context)
    invoice = state.get("invoice")
    if invoice is None:
        raise RuntimeError("Extraction did not produce an invoice")
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.VALIDATE,
        event_code="VALIDATION_STARTED",
        message="Deterministic validation started.",
    )
    findings = list(state.get("findings", []))
    findings.extend(integrity_findings(invoice))
    normalized_items, inventory_results = inventory_findings(
        invoice, context.inventory_lookup
    )
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.VALIDATE,
        event_code="INVENTORY_TOOL_CALLED",
        message="Validation agent completed read-only inventory lookup.",
    )
    findings.extend(inventory_results)
    findings = ordered_unique(findings)
    normalized_invoice = invoice.model_copy(update={"items": normalized_items})
    context.run_repository.save_result(
        state["run_id"], invoice=normalized_invoice, findings=findings
    )
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.VALIDATE,
        event_code="VALIDATION_COMPLETED",
        message="Deterministic validation completed.",
    )
    return {
        "invoice": normalized_invoice,
        "findings": findings,
        "stage": RunStage.VALIDATE,
    }
