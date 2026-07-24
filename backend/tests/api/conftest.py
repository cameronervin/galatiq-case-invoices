from pathlib import Path
from uuid import UUID

import pytest

from backend.app.core.config import Settings
from backend.app.ports.queue import AgentRunDispatchError

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class RecordingDispatcher:
    def __init__(self) -> None:
        self.execute_ids: list[UUID] = []
        self.resume_ids: list[UUID] = []
        self.fail = False

    def enqueue_execute(self, *, run_id: UUID) -> str:
        if self.fail:
            raise AgentRunDispatchError("queue unavailable")
        self.execute_ids.append(run_id)
        return str(run_id)

    def enqueue_resume(self, *, run_id: UUID) -> str:
        if self.fail:
            raise AgentRunDispatchError("queue unavailable")
        self.resume_ids.append(run_id)
        return str(run_id)


@pytest.fixture
def api_settings(tmp_path: Path) -> Settings:
    return Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
        llm_provider="offline",
        llm_model="deterministic-v1",
    )


@pytest.fixture
def dispatcher() -> RecordingDispatcher:
    return RecordingDispatcher()


@pytest.fixture
def invoice_dir() -> Path:
    return PROJECT_ROOT / "data/invoices"
