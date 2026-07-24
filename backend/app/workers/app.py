from importlib import import_module

import structlog
from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.services.invoice_processing import InvoiceProcessingService

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
    worker_concurrency=1,
)

REQUIRED_TASKS = {
    "invoice_processing.agent_runs.execute",
    "invoice_processing.agent_runs.resume",
}
_worker_processor: InvoiceProcessingService | None = None


@worker_process_init.connect
def init_worker_resources(**_: object) -> None:
    global _worker_processor
    if _worker_processor is None:
        _worker_processor = InvoiceProcessingService(get_settings())
        logger.info("worker_resources_initialized")


@worker_process_shutdown.connect
def teardown_worker_resources(**_: object) -> None:
    global _worker_processor
    if _worker_processor is not None:
        _worker_processor.close()
        _worker_processor = None
    logger.info("worker_resources_released")


def set_worker_processor(processor: InvoiceProcessingService | None) -> None:
    global _worker_processor
    if _worker_processor is not None and _worker_processor is not processor:
        _worker_processor.close()
    _worker_processor = processor


def get_worker_processor() -> InvoiceProcessingService:
    if _worker_processor is None:
        init_worker_resources()
    assert _worker_processor is not None
    return _worker_processor


def registered_tasks() -> set[str]:
    return {
        task_name
        for task_name in celery_app.tasks
        if task_name.startswith("invoice_processing.")
    }


import_module("backend.app.workers.tasks")
