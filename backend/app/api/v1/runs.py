from uuid import UUID

from fastapi import APIRouter, File, Query, Request, Response, UploadFile
from fastapi.responses import JSONResponse

from backend.app.infrastructure.llm.factory import ProviderConfigurationError
from backend.app.schemas.domain import (
    ErrorBody,
    ErrorEnvelope,
    ReviewRequest,
    RunCreationResponse,
    RunDetail,
    RunListResponse,
    RunSummary,
)
from backend.app.services.agent_run_service import AgentRunDispatchError, TaskDispatcher
from backend.app.services.invoice_processing import (
    InvalidInvoiceInput,
    InvoiceProcessingService,
    ReviewConflict,
)

router = APIRouter(prefix="/runs")


def _processor(request: Request) -> InvoiceProcessingService:
    return request.app.state.processor


def _dispatcher(request: Request) -> TaskDispatcher:
    return request.app.state.dispatcher


def _error(
    status_code: int,
    code: str,
    message: str,
    run_id: UUID | None = None,
) -> JSONResponse:
    envelope = ErrorEnvelope(error=ErrorBody(code=code, message=message, run_id=run_id))
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(mode="json"),
    )


@router.post(
    "",
    response_model=RunCreationResponse,
    status_code=202,
    responses={
        200: {"model": RunCreationResponse, "description": "Deduplicated run"},
        400: {"model": ErrorEnvelope},
        413: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
        503: {"model": ErrorEnvelope},
    },
)
async def create_run(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
) -> RunCreationResponse | JSONResponse:
    processor = _processor(request)
    content = await file.read(processor.settings.max_upload_bytes + 1)
    try:
        record, deduplicated = processor.create_from_bytes(
            filename=file.filename or "invoice",
            content=content,
            origin="api",
        )
    except InvalidInvoiceInput as exc:
        code = "FILE_TOO_LARGE" if "10 MB" in str(exc) else "INVALID_UPLOAD"
        return _error(413 if code == "FILE_TOO_LARGE" else 400, code, str(exc))
    except ProviderConfigurationError:
        return _error(
            503,
            "PROVIDER_NOT_CONFIGURED",
            "The requested model provider is not configured.",
        )
    creation = processor.creation_response(record, deduplicated=deduplicated)
    if deduplicated:
        response.status_code = 200
        return creation
    try:
        _dispatcher(request).enqueue_execute(run_id=record.run_id)
    except AgentRunDispatchError:
        processor.mark_queue_failure(record.run_id)
        return _error(
            503,
            "QUEUE_UNAVAILABLE",
            "The run could not be queued.",
            record.run_id,
        )
    return creation


@router.get(
    "", response_model=RunListResponse, responses={422: {"model": ErrorEnvelope}}
)
async def list_runs(
    request: Request, limit: int = Query(default=20, ge=1, le=50)
) -> RunListResponse:
    return RunListResponse(
        items=_processor(request).run_repository.list_summaries(limit)
    )


@router.get(
    "/{run_id}",
    response_model=RunDetail,
    responses={404: {"model": ErrorEnvelope}, 422: {"model": ErrorEnvelope}},
)
async def get_run(request: Request, run_id: UUID) -> RunDetail | JSONResponse:
    detail = _processor(request).run_repository.get_detail(run_id)
    if detail is None:
        return _error(404, "RUN_NOT_FOUND", "The requested run was not found.")
    return detail


@router.post(
    "/{run_id}/review",
    response_model=RunSummary,
    status_code=202,
    responses={
        404: {"model": ErrorEnvelope},
        409: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
        503: {"model": ErrorEnvelope},
    },
)
async def review_run(
    request: Request, run_id: UUID, command: ReviewRequest
) -> RunSummary | JSONResponse:
    processor = _processor(request)
    try:
        processor.persist_review(run_id, command)
    except KeyError:
        return _error(404, "RUN_NOT_FOUND", "The requested run was not found.")
    except ReviewConflict as exc:
        return _error(409, "REVIEW_ALREADY_DECIDED", str(exc), run_id)
    try:
        _dispatcher(request).enqueue_resume(run_id=run_id)
    except AgentRunDispatchError:
        return _error(
            503,
            "QUEUE_UNAVAILABLE",
            "The review was saved but could not be queued.",
            run_id,
        )
    record = processor.run_repository.get_internal(run_id)
    assert record is not None
    return RunSummary(
        run_id=record.run_id,
        source_filename=record.source_filename,
        status=record.status,
        stage=record.stage,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
