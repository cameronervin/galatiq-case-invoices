from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class HumanReview(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str = Field(min_length=3, max_length=500)
    resume_pending: bool = True
    decided_at: datetime


class ReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("reason")
    @classmethod
    def trim_reason(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 3:
            raise ValueError("Review reason must contain at least three characters")
        return stripped
