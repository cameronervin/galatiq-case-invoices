from pathlib import Path

from langgraph.runtime import Runtime

from backend.app.agents.nodes.shared import check_deadline, require_run
from backend.app.agents.runtime_context import AgentRuntimeContext
from backend.app.agents.states import InvoiceProcessingState
from backend.app.domain.validation import extraction_feedback, ordered_unique
from backend.app.ports.providers import ProviderExtraction
from backend.app.schemas.domain import RunStage, RunStatus


def ingest_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    check_deadline(runtime.context)
    runtime.context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.INGEST,
        event_code="INGEST_STARTED",
        message="Invoice ingestion started.",
    )
    return {"status": RunStatus.RUNNING, "stage": RunStage.INGEST}


def extraction_agent_node(
    state: InvoiceProcessingState, runtime: Runtime[AgentRuntimeContext]
) -> dict[str, object]:
    context = runtime.context
    check_deadline(context)
    record = require_run(context, state["run_id"])
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.EXTRACT,
        event_code="EXTRACTION_STARTED",
        message="Extraction agent started.",
    )
    loaded = context.document_loader(
        Path(record.source_path), default_currency=context.settings.default_currency
    )
    attempts = 0
    if loaded.invoice is not None:
        extraction = ProviderExtraction(
            invoice=loaded.invoice,
            findings=loaded.findings,
        )
    else:
        provider = context.provider_registry.get(
            record.provider_name, record.provider_model
        )
        extraction = provider.extract_invoice(document_text=loaded.text or "")
        attempts = 1
        feedback = extraction_feedback(extraction.invoice)
        if feedback:
            check_deadline(context)
            extraction = provider.repair_invoice(
                document_text=loaded.text or "",
                current=extraction,
                feedback=feedback,
            )
            attempts = 2
            context.run_repository.transition(
                state["run_id"],
                status=RunStatus.RUNNING,
                stage=RunStage.EXTRACT,
                event_code="EXTRACTION_REPAIRED",
                message="Extraction agent performed one bounded repair.",
            )
        extraction = extraction.model_copy(
            update={
                "findings": ordered_unique([*loaded.findings, *extraction.findings])
            }
        )
    context.run_repository.save_result(
        state["run_id"],
        invoice=extraction.invoice,
        findings=extraction.findings,
        extraction_attempts=attempts,
    )
    context.run_repository.transition(
        state["run_id"],
        status=RunStatus.RUNNING,
        stage=RunStage.EXTRACT,
        event_code="EXTRACTION_COMPLETED",
        message="Extraction agent produced a typed invoice.",
    )
    return {
        "invoice": extraction.invoice,
        "findings": extraction.findings,
        "extraction_attempts": attempts,
        "stage": RunStage.EXTRACT,
    }
