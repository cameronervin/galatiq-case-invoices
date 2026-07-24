import asyncio
from collections.abc import Coroutine
from importlib import import_module
from typing import Any

import structlog
from celery import Celery
from celery.signals import (
    worker_process_init,
    worker_process_shutdown,
    worker_ready,
    worker_shutdown,
)

from backend.app.agents.graph_provider import (
    GraphProvider,
    clear_graph_provider_cache,
    get_graph_provider,
)
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger(__name__)

celery_app = Celery(
    "invoice_processing",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.app.workers.tasks"],
)
celery_app.conf.update(
    accept_content=["json"],
    result_expires=settings.celery_result_expires_seconds,
    result_serializer="json",
    task_serializer="json",
    timezone="UTC",
)

REQUIRED_TASKS = {"invoice_processing.agent_runs.execute"}
_worker_graph_provider: GraphProvider | None = None


def run_async(coroutine: Coroutine[Any, Any, dict[str, Any]]) -> dict[str, Any]:
    return asyncio.run(coroutine)


@worker_process_init.connect
@worker_ready.connect
def init_worker_resources(**_: object) -> None:
    global _worker_graph_provider
    if _worker_graph_provider is not None:
        logger.debug("worker_resources_already_initialized")
        return
    _worker_graph_provider = get_graph_provider()
    _worker_graph_provider.invoice_graph()
    logger.info("worker_resources_initialized")


@worker_process_shutdown.connect
@worker_shutdown.connect
def teardown_worker_resources(**_: object) -> None:
    global _worker_graph_provider
    was_initialized = _worker_graph_provider is not None
    _worker_graph_provider = None
    clear_graph_provider_cache()
    logger.info("worker_resources_released", was_initialized=was_initialized)


def get_worker_graph_provider() -> GraphProvider | None:
    return _worker_graph_provider


def registered_tasks() -> set[str]:
    return {
        task_name
        for task_name in celery_app.tasks
        if task_name.startswith("invoice_processing.")
    }


def assert_required_tasks_registered() -> None:
    missing = REQUIRED_TASKS - registered_tasks()
    if missing:
        raise RuntimeError(
            "Celery worker task registry is missing tasks: "
            + ", ".join(sorted(missing))
        )


import_module("backend.app.workers.tasks")
assert_required_tasks_registered()

