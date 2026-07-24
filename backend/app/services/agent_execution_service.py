from uuid import UUID

from backend.app.core.config import Settings
from backend.app.schemas.domain import RunDetail
from backend.app.services.invoice_processing import InvoiceProcessingService


class AgentExecutionService:
    def __init__(self, settings: Settings) -> None:
        self.processor = InvoiceProcessingService(settings)

    def execute(self, *, run_id: UUID | str) -> RunDetail:
        return self.processor.process_run(run_id)

    def resume(self, *, run_id: UUID | str) -> RunDetail:
        return self.processor.resume_run(run_id)
