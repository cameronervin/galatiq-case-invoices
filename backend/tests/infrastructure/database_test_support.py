from pathlib import Path

from backend.app.infrastructure.db.repositories.runs import RunRepository
from backend.app.ports.repositories import RunRecordView


def create_run(
    repository: RunRepository,
    tmp_path: Path,
    *,
    content_hash: str,
    filename: str = "invoice.txt",
    origin: str = "cli",
    provider_name: str = "offline",
    provider_model: str = "deterministic-v1",
) -> tuple[RunRecordView, bool]:
    return repository.create_run(
        content_hash=content_hash,
        source_filename=filename,
        source_path=str(tmp_path / filename),
        source_format="txt",
        source_origin=origin,
        provider_name=provider_name,
        provider_model=provider_model,
    )
