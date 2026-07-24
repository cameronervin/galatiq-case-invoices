from uuid import UUID

from fastapi import APIRouter, File, Query, Request, Response, UploadFile
from fastapi.responses import JSONResponse

from backend.app.ports.providers import ProviderConfigurationError
from backend.app.schemas.domain import (
    ErrorBody,
    ErrorEnvelope,
    ReviewRequest,
    RunCreationResponse,
    RunDetail,
    RunListResponse,
    RunSummary,
)
from backend.app.services.invoice_processing import (
    InvalidInvoiceInput,
    ReviewConflict,
)
from backend.app.services.run_application import (
    RunApplicationDispatchError,
    RunApplicationService,
)

router = APIRouter(prefix="/runs")


def _application(request: Request) -> RunApplicationService:
    return request.app.state.runtime.runs


_INPUT_STATUS_CODES = {
    "FILE_TOO_LARGE": 413,
}


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
def create_run(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
) -> RunCreationResponse | JSONResponse:
    application = _application(request)
    content = file.file.read(application.max_source_bytes + 1)
    try:
        creation = application.create_run(
            filename=file.filename or "invoice",
            content=content,
            origin="api",
        )
    except InvalidInvoiceInput as exc:
        return _error(_INPUT_STATUS_CODES.get(exc.code, 400), exc.code, str(exc))
    except ProviderConfigurationError:
        return _error(
            503,
            "PROVIDER_NOT_CONFIGURED",
            "The requested model provider is not configured.",
        )
    except RunApplicationDispatchError as exc:
        return _error(
            503,
            "QUEUE_UNAVAILABLE",
            "The run could not be queued.",
            exc.run_id,
        )
    if creation.deduplicated:
        response.status_code = 200
    return creation


@router.get(
    "", response_model=RunListResponse, responses={422: {"model": ErrorEnvelope}}
)
def list_runs(
    request: Request, limit: int = Query(default=20, ge=1, le=50)
) -> RunListResponse:
    return RunListResponse(items=_application(request).list_runs(limit))


@router.get(
    "/{run_id}",
    response_model=RunDetail,
    responses={404: {"model": ErrorEnvelope}, 422: {"model": ErrorEnvelope}},
)
def get_run(request: Request, run_id: UUID) -> RunDetail | JSONResponse:
    detail = _application(request).get_run(run_id)
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
def review_run(
    request: Request, run_id: UUID, command: ReviewRequest
) -> RunSummary | JSONResponse:
    try:
        return _application(request).review_run(run_id, command)
    except KeyError:
        return _error(404, "RUN_NOT_FOUND", "The requested run was not found.")
    except ReviewConflict as exc:
        return _error(409, "REVIEW_ALREADY_DECIDED", str(exc), run_id)
    except RunApplicationDispatchError:
        return _error(
            503,
            "QUEUE_UNAVAILABLE",
            "The review was saved but could not be queued.",
            run_id,
        )
