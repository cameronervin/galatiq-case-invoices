from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class QueuedAgentRun(BaseModel):
    run_id: UUID
    task_id: str
    invoice_path: Path
    status: Literal["queued"] = "queued"

