import type { HumanReview, Payment, RunEvent } from "@/types/api";

import { isMoney } from "./invoiceArtifacts";
import {
  hasNullableNumber,
  hasNullableString,
  isFiniteNumber,
  isOneOf,
  isRecord,
  isRunStage,
  isRunStatus,
  isTimestamp
} from "./primitives";

export function isHumanReview(value: unknown): value is HumanReview {
  return (
    isRecord(value) &&
    isOneOf(value.decision, ["approve", "reject"] as const) &&
    typeof value.reason === "string" &&
    typeof value.resume_pending === "boolean" &&
    isTimestamp(value.decided_at)
  );
}

export function isPayment(value: unknown): value is Payment {
  return (
    isRecord(value) &&
    isOneOf(value.status, ["pending", "succeeded", "failed"] as const) &&
    isMoney(value.amount) &&
    hasNullableString(value, "mock_reference") &&
    hasNullableString(value, "error_code") &&
    isTimestamp(value.created_at) &&
    isTimestamp(value.updated_at)
  );
}

export function isRunEvent(value: unknown): value is RunEvent {
  return (
    isRecord(value) &&
    isFiniteNumber(value.event_id) &&
    isRunStage(value.stage) &&
    isRunStatus(value.status) &&
    typeof value.code === "string" &&
    typeof value.message === "string" &&
    isTimestamp(value.created_at) &&
    hasNullableNumber(value, "duration_ms")
  );
}

export function isWorkflowError(
  value: unknown
): value is { code: string; message: string } {
  return (
    isRecord(value) &&
    typeof value.code === "string" &&
    typeof value.message === "string"
  );
}
