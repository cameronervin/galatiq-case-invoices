from typing import Protocol
from uuid import UUID

from backend.app.ports.queue import AgentRunDispatchError


class CeleryTaskResult(Protocol):
    id: str


class CeleryTaskClient(Protocol):
    def send_task(
        self,
        name: str,
        *,
        kwargs: dict[str, str],
        task_id: str,
    ) -> CeleryTaskResult: ...


class CeleryTaskDispatcher:
    def __init__(self, client: CeleryTaskClient) -> None:
        self.client = client

    def enqueue_execute(self, *, run_id: UUID) -> str:
        return self._send("invoice_processing.agent_runs.execute", run_id)

    def enqueue_resume(self, *, run_id: UUID) -> str:
        return self._send("invoice_processing.agent_runs.resume", run_id)

    def _send(self, task_name: str, run_id: UUID) -> str:
        try:
            result = self.client.send_task(
                task_name,
                kwargs={"run_id": str(run_id)},
                task_id=f"{task_name}:{run_id}",
            )
        except Exception as exc:
            raise AgentRunDispatchError(
                "Unable to queue invoice-processing run."
            ) from exc
        return result.id
