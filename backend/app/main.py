from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.router import api_router
from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import configure_logging
from backend.app.schemas.domain import ErrorBody, ErrorEnvelope
from backend.app.services.agent_run_service import CeleryTaskDispatcher, TaskDispatcher
from backend.app.services.invoice_processing import InvoiceProcessingService

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(app.state.settings.log_level)
    app.state.processor = InvoiceProcessingService(app.state.settings)
    logger.info("api_started", env=app.state.settings.env)
    try:
        yield
    finally:
        app.state.processor.close()
        logger.info("api_stopped", env=app.state.settings.env)


def create_app(
    settings: Settings | None = None,
    *,
    dispatcher: TaskDispatcher | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    app = FastAPI(
        title="Invoice Processing API",
        version="0.2.0",
        description="Local asynchronous workspace for invoice processing.",
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.state.dispatcher = dispatcher or CeleryTaskDispatcher()

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: object, _exc: RequestValidationError
    ) -> JSONResponse:
        envelope = ErrorEnvelope(
            error=ErrorBody(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
            )
        )
        return JSONResponse(
            status_code=422,
            content=envelope.model_dump(mode="json"),
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
