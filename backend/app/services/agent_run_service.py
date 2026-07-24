from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from backend.app.core.config import Settings
from backend.app.schemas.run import QueuedAgentRun


class AgentRunDispatchError(RuntimeError):
    pass


class TaskDispatcher(Protocol):
    def enqueue(self, *, run_id: UUID, invoice_path: Path) -> str: ...


class CeleryTaskDispatcher:
    def enqueue(self, *, run_id: UUID, invoice_path: Path) -> str:
        try:
            from backend.app.workers.app import celery_app

            result = celery_app.send_task(
                "invoice_processing.agent_runs.execute",
                kwargs={"run_id": str(run_id), "invoice_path": str(invoice_path)},
                task_id=str(run_id),
            )
        except Exception as exc:
            raise AgentRunDispatchError(
                f"Unable to queue invoice-processing run: {exc}"
            ) from exc
        return result.id


class AgentRunDispatchService:
    def __init__(
        self,
        *,
        settings: Settings,
        dispatcher: TaskDispatcher | None = None,
    ) -> None:
        self.settings = settings
        self.dispatcher = dispatcher or CeleryTaskDispatcher()

    def enqueue(self, invoice_path: Path) -> QueuedAgentRun:
        run_id = uuid4()
        task_id = self.dispatcher.enqueue(run_id=run_id, invoice_path=invoice_path)
        return QueuedAgentRun(
            run_id=run_id,
            task_id=task_id,
            invoice_path=invoice_path,
        )
