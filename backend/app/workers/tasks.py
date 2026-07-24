from typing import Any

from backend.app.schemas.domain import WorkerResult
from backend.app.workers.app import celery_app, get_worker_processor


@celery_app.task(name="invoice_processing.agent_runs.execute")
def execute_agent_run(*, run_id: str) -> dict[str, Any]:
    detail = get_worker_processor().process_run(run_id)
    return WorkerResult(
        run_id=detail.run_id,
        status=detail.status,
        error_code=detail.error.code if detail.error else None,
    ).model_dump(mode="json")


@celery_app.task(name="invoice_processing.agent_runs.resume")
def resume_agent_run(*, run_id: str) -> dict[str, Any]:
    detail = get_worker_processor().resume_run(run_id)
    return WorkerResult(
        run_id=detail.run_id,
        status=detail.status,
        error_code=detail.error.code if detail.error else None,
    ).model_dump(mode="json")
