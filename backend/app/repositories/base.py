from typing import Protocol
from uuid import UUID


class AgentRunRepository(Protocol):
    """Persistence boundary for future agent-run state."""

    async def save_status(self, run_id: UUID, status: str) -> None: ...

    async def get_status(self, run_id: UUID) -> str | None: ...

