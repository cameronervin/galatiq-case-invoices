import type {
  RunCreationResponse,
  RunDetail,
  RunListResponse,
  RunSummary
} from "@/types/api";

import { isFinding, isInvoiceData, isRecommendation } from "./invoiceArtifacts";
import {
  hasArray,
  hasNullable,
  isRecord,
  isRunStage,
  isRunStatus,
  isTimestamp
} from "./primitives";
import {
  isHumanReview,
  isPayment,
  isRunEvent,
  isWorkflowError
} from "./runArtifacts";

export function isRunSummary(value: unknown): value is RunSummary {
  return (
    isRecord(value) &&
    typeof value.run_id === "string" &&
    typeof value.source_filename === "string" &&
    isRunStatus(value.status) &&
    isRunStage(value.stage) &&
    isTimestamp(value.created_at) &&
    isTimestamp(value.updated_at)
  );
}

export function isRunCreationResponse(
  value: unknown
): value is RunCreationResponse {
  return (
    isRunSummary(value) &&
    typeof (value as Record<string, unknown>).deduplicated === "boolean"
  );
}

export function isRunListResponse(value: unknown): value is RunListResponse {
  return isRecord(value) && hasArray(value, "items", isRunSummary);
}

export function isRunDetail(value: unknown): value is RunDetail {
  return (
    isRunSummary(value) &&
    hasNullable(value, "invoice", isInvoiceData) &&
    hasArray(value, "findings", isFinding) &&
    hasNullable(value, "recommendation", isRecommendation) &&
    hasNullable(value, "review", isHumanReview) &&
    hasNullable(value, "payment", isPayment) &&
    hasArray(value, "events", isRunEvent) &&
    hasNullable(value, "error", isWorkflowError)
  );
}
