from __future__ import annotations

from dataclasses import dataclass

from backend.app.bootstrap.invoice_runtime import build_invoice_processor
from backend.app.core.config import Settings
from backend.app.ports.queue import TaskDispatcher
from backend.app.services.invoice_processing import InvoiceProcessingService
from backend.app.services.run_application import RunApplicationService


@dataclass
class ApplicationRuntime:
    """Composition root for the API's application services."""

    processor: InvoiceProcessingService
    runs: RunApplicationService

    @classmethod
    def create(
        cls,
        settings: Settings,
        dispatcher: TaskDispatcher,
    ) -> ApplicationRuntime:
        processor = build_invoice_processor(settings)
        return cls(
            processor=processor,
            runs=RunApplicationService(processor, dispatcher),
        )

    def close(self) -> None:
        self.processor.close()
