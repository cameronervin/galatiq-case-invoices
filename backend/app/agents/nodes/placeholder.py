from backend.app.agents.states import InvoiceProcessingState


async def scaffold_node(state: InvoiceProcessingState) -> dict[str, object]:
    """Mark a run as scaffolded without performing business processing."""
    messages = [*state.get("messages", []), "invoice pipeline is not implemented"]
    return {
        "status": "scaffolded",
        "current_stage": "not_implemented",
        "messages": messages,
    }

