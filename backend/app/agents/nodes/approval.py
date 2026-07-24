from langgraph.runtime import Runtime

from backend.app.agents.nodes.shared import (
    check_deadline,
    require_invoice,
    require_run,
)
from backend.app.agents.runtime_context import AgentRuntimeContext
from backend.app.agents.states import InvoiceProcessingState
from backend.app.domain.policies import policy_route
from backend.app.schemas.domain import ApprovalRecommendation, RunStage, RunStatus


def approval_agent_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    check_deadline(context)
    invoice = require_invoice(state)
    record = require_run(context, state["run_id"])
    provider = context.provider_registry.get(
        record.provider_name, record.provider_model
    )
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.RECOMMEND,
        event_code="APPROVAL_STARTED",
        message="Approval agent started a recommendation.",
    )
    proposal = provider.propose_approval(
        invoice=invoice, findings=state.get("findings", [])
    )
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.RECOMMEND,
        event_code="APPROVAL_PROPOSED",
        message="Approval agent produced a recommendation.",
    )
    return {"proposal": proposal, "stage": RunStage.RECOMMEND}


def critic_agent_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    check_deadline(context)
    proposal = state.get("proposal")
    if proposal is None:
        raise RuntimeError("Approval proposal is missing")
    invoice = require_invoice(state)
    record = require_run(context, state["run_id"])
    provider = context.provider_registry.get(
        record.provider_name, record.provider_model
    )
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.RECOMMEND,
        event_code="CRITIC_STARTED",
        message="Critic agent started policy review.",
    )
    critique = provider.critique_approval(
        invoice=invoice,
        findings=state.get("findings", []),
        proposal=proposal,
    )
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.RECOMMEND,
        event_code="CRITIC_ACCEPTED" if critique.accepted else "CRITIC_REJECTED",
        message=(
            "Critic accepted the approval proposal."
            if critique.accepted
            else "Critic requested one bounded approval revision."
        ),
    )
    reflection_count = 0
    if not critique.accepted:
        check_deadline(context)
        proposal = provider.propose_approval(
            invoice=invoice, findings=state.get("findings", [])
        )
        reflection_count = 1
        context.run_repository.transition(
            state["run_id"],
            status=RunStatus.RUNNING,
            stage=RunStage.RECOMMEND,
            event_code="APPROVAL_REVISED",
            message="Approval agent revised its proposal after critique.",
        )
    final_route = policy_route(invoice, state.get("findings", []))
    override = proposal.proposed_route != final_route
    reason_codes = list(proposal.reason_codes)
    if override and "POLICY_OVERRIDE" not in reason_codes:
        reason_codes.append("POLICY_OVERRIDE")
        context.run_repository.transition(
            state["run_id"],
            status=RunStatus.RUNNING,
            stage=RunStage.RECOMMEND,
            event_code="POLICY_OVERRIDE",
            message="Deterministic policy overrode the model proposal.",
        )
    recommendation = ApprovalRecommendation(
        proposed_route=proposal.proposed_route,
        final_route=final_route,
        reason_codes=reason_codes,
        summary=proposal.summary,
        reflection_count=reflection_count,
        decided_by="policy" if override else "agent",
    )
    context.run_repository.save_result(
        state["run_id"],
        recommendation=recommendation,
        reflection_count=reflection_count,
    )
    return {
        "proposal": proposal,
        "recommendation": recommendation,
        "reflection_count": reflection_count,
    }


def route_policy(state: InvoiceProcessingState) -> str:
    recommendation = state.get("recommendation")
    if recommendation is None:
        return "reject"
    return recommendation.final_route.value
