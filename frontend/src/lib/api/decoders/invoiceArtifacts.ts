import type {
  Finding,
  InvoiceData,
  InvoiceItem,
  Money,
  Recommendation
} from "@/types/api";

import {
  hasArray,
  hasNullable,
  hasNullableNumber,
  hasNullableString,
  isFiniteNumber,
  isOneOf,
  isRecord
} from "./primitives";

export function isInvoiceData(value: unknown): value is InvoiceData {
  return (
    isRecord(value) &&
    hasNullableString(value, "vendor_name") &&
    hasNullableString(value, "invoice_number") &&
    hasNullableString(value, "revision") &&
    hasNullableString(value, "invoice_date") &&
    hasNullableString(value, "due_date") &&
    hasNullableString(value, "payment_terms") &&
    hasNullableString(value, "currency") &&
    isOneOf(value.extraction_confidence, ["high", "medium", "low"] as const) &&
    hasArray(value, "items", isInvoiceItem) &&
    hasNullable(value, "subtotal", isMoney) &&
    hasNullable(value, "tax", isMoney) &&
    hasNullable(value, "shipping", isMoney) &&
    hasNullable(value, "total", isMoney)
  );
}

export function isInvoiceItem(value: unknown): value is InvoiceItem {
  return (
    isRecord(value) &&
    isFiniteNumber(value.line_number) &&
    hasNullableString(value, "source_name") &&
    hasNullableString(value, "normalized_item_code") &&
    hasNullableNumber(value, "quantity") &&
    hasNullable(value, "unit_price", isMoney) &&
    hasNullable(value, "line_total", isMoney)
  );
}

export function isMoney(value: unknown): value is Money {
  return (
    isRecord(value) &&
    typeof value.amount === "string" &&
    typeof value.currency === "string"
  );
}

export function isFinding(value: unknown): value is Finding {
  return (
    isRecord(value) &&
    typeof value.code === "string" &&
    isOneOf(value.severity, ["info", "warning", "blocking"] as const) &&
    typeof value.message === "string" &&
    hasNullableString(value, "field_path") &&
    hasNullableNumber(value, "item_line_number") &&
    "expected" in value &&
    "actual" in value
  );
}

export function isRecommendation(value: unknown): value is Recommendation {
  return (
    isRecord(value) &&
    isOneOf(value.proposed_route, ["approve", "review", "reject"] as const) &&
    isOneOf(value.final_route, ["approve", "review", "reject"] as const) &&
    Array.isArray(value.reason_codes) &&
    value.reason_codes.every((code) => typeof code === "string") &&
    typeof value.summary === "string" &&
    isFiniteNumber(value.reflection_count) &&
    isOneOf(value.decided_by, ["agent", "policy"] as const)
  );
}
