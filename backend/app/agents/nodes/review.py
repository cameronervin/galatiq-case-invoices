from langgraph.runtime import Runtime
from langgraph.types import interrupt

from backend.app.agents.nodes.shared import require_run
from backend.app.agents.runtime_context import AgentRuntimeContext
from backend.app.agents.states import InvoiceProcessingState
from backend.app.schemas.domain import RunStage, RunStatus


def review_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    current = require_run(context, state["run_id"])
    if current.status != RunStatus.REVIEW_REQUIRED:
        context.run_repository.transition(
            state["run_id"],
            status=RunStatus.REVIEW_REQUIRED,
            stage=RunStage.REVIEW,
            event_code="REVIEW_REQUIRED",
            message="Human review is required.",
        )
    interrupt(
        {
            "run_id": state["run_id"],
            "allowed_decisions": ["approve", "reject"],
        }
    )
    detail = context.run_repository.get_detail(state["run_id"])
    if detail is None or detail.review is None:
        raise RuntimeError("Persisted review decision is missing")
    return {"review": detail.review, "stage": RunStage.REVIEW}


def route_review(state: InvoiceProcessingState) -> str:
    review = state.get("review")
    return "pay" if review is not None and review.decision == "approve" else "reject"
