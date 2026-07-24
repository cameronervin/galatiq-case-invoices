from typing import Protocol
from uuid import UUID


class AgentRunDispatchError(RuntimeError):
    pass


class TaskDispatcher(Protocol):
    def enqueue_execute(self, *, run_id: UUID) -> str: ...

    def enqueue_resume(self, *, run_id: UUID) -> str: ...
