from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from backend.app.schemas.invoice import Money


class PaymentResult(BaseModel):
    status: Literal["pending", "succeeded", "failed"]
    amount: Money
    mock_reference: str | None = None
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime
