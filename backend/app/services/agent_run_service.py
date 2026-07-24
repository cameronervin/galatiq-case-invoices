from typing import Protocol
from uuid import UUID


class AgentRunDispatchError(RuntimeError):
    pass


class TaskDispatcher(Protocol):
    def enqueue_execute(self, *, run_id: UUID) -> str: ...

    def enqueue_resume(self, *, run_id: UUID) -> str: ...


class CeleryTaskDispatcher:
    def enqueue_execute(self, *, run_id: UUID) -> str:
        return self._send("invoice_processing.agent_runs.execute", run_id)

    def enqueue_resume(self, *, run_id: UUID) -> str:
        return self._send("invoice_processing.agent_runs.resume", run_id)

    @staticmethod
    def _send(task_name: str, run_id: UUID) -> str:
        try:
            from backend.app.workers.app import celery_app

            result = celery_app.send_task(
                task_name,
                kwargs={"run_id": str(run_id)},
                task_id=f"{task_name}:{run_id}",
            )
        except Exception as exc:
            raise AgentRunDispatchError(
                "Unable to queue invoice-processing run."
            ) from exc
        return result.id


AgentRunDispatchService = CeleryTaskDispatcher
