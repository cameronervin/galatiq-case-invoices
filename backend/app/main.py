from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.agents.graph_provider import (
    clear_graph_provider_cache,
    get_graph_provider,
)
from backend.app.api.v1.router import api_router
from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    configure_logging(settings.log_level)
    graph_provider = get_graph_provider()
    graph_provider.invoice_graph()
    app.state.graph_provider = graph_provider
    logger.info("api_started", env=settings.env)
    try:
        yield
    finally:
        clear_graph_provider_cache()
        logger.info("api_stopped", env=settings.env)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    app = FastAPI(
        title="Invoice Processing API",
        version="0.1.0",
        description="Scaffold for asynchronous multi-agent invoice processing.",
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
