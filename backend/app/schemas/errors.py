from uuid import UUID

from pydantic import BaseModel


class WorkflowError(BaseModel):
    code: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    run_id: UUID | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody
