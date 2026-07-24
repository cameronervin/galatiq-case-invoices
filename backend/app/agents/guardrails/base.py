from typing import Protocol

from backend.app.agents.states import InvoiceProcessingState


class Guardrail(Protocol):
    async def evaluate(self, state: InvoiceProcessingState) -> list[str]: ...

