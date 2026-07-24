from langgraph.runtime import Runtime

from backend.app.agents.nodes.shared import require_invoice
from backend.app.agents.runtime_context import AgentRuntimeContext
from backend.app.agents.states import InvoiceProcessingState
from backend.app.schemas.domain import DecisionRoute, RunStage, RunStatus


def payment_agent_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    invoice = require_invoice(state)
    recommendation = state.get("recommendation")
    review = state.get("review")
    approved = (
        recommendation is not None
        and recommendation.final_route == DecisionRoute.APPROVE
    ) or (review is not None and review.decision == "approve")
    if not approved or invoice.total is None:
        raise RuntimeError("Payment requires persisted approval and positive total")
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.PAY,
        event_code="PAYMENT_STARTED",
        message="Simulated payment started.",
    )
    payment = context.payment_repository.create_or_get(
        state["run_id"], invoice.total, f"payment:{state['run_id']}"
    )
    if payment.status == "pending":
        payment = context.payment_repository.succeed(state["run_id"])
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.COMPLETED,
        stage=RunStage.FINALIZE,
        event_code="PAYMENT_SUCCEEDED",
        message="Simulated payment completed.",
    )
    return {
        "payment": payment,
        "status": RunStatus.COMPLETED,
        "stage": RunStage.FINALIZE,
    }


def reject_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    runtime.context.run_repository.transition(
        state["run_id"],
        status=RunStatus.REJECTED,
        stage=RunStage.FINALIZE,
        event_code="RUN_REJECTED",
        message="Invoice was rejected without payment.",
    )
    return {"status": RunStatus.REJECTED, "stage": RunStage.FINALIZE}
