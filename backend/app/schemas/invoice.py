from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)

    amount: Decimal
    currency: str

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: object) -> Decimal:
        try:
            decimal = Decimal(str(value).replace(",", ""))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("Amount must be a decimal value") from exc
        if decimal.as_tuple().exponent < -2:
            raise ValueError("Amount may contain at most two fractional digits")
        return decimal.quantize(Decimal("0.01"))

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("Currency must be a three-letter ISO code")
        return normalized

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return f"{value:.2f}"

    @property
    def amount_as_decimal(self) -> Decimal:
        return self.amount


class InvoiceItem(BaseModel):
    line_number: int = Field(ge=1)
    source_name: str | None = None
    normalized_item_code: str | None = None
    quantity: int | None = None
    unit_price: Money | None = None
    line_total: Money | None = None


class InvoiceData(BaseModel):
    invoice_number: str | None = None
    revision: str | None = None
    vendor_name: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    currency: str | None = None
    items: list[InvoiceItem] = Field(default_factory=list)
    subtotal: Money | None = None
    tax: Money | None = None
    shipping: Money | None = None
    total: Money | None = None
    payment_terms: str | None = None
    extraction_confidence: Literal["high", "medium", "low"] = "high"

    @field_validator("currency")
    @classmethod
    def normalize_optional_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("Currency must be a three-letter ISO code")
        return normalized
