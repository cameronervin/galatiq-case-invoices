import type { RunStage, RunStatus } from "@/types/api";

export type Guard<T> = (candidate: unknown) => candidate is T;

const runStatuses = new Set<RunStatus>([
  "queued",
  "running",
  "review_required",
  "completed",
  "rejected",
  "failed"
]);
const runStages = new Set<RunStage>([
  "ingest",
  "extract",
  "validate",
  "recommend",
  "review",
  "pay",
  "finalize"
]);

export function isRunStatus(value: unknown): value is RunStatus {
  return typeof value === "string" && runStatuses.has(value as RunStatus);
}

export function isRunStage(value: unknown): value is RunStage {
  return typeof value === "string" && runStages.has(value as RunStage);
}

export function hasNullableString(
  value: Record<string, unknown>,
  key: string
): boolean {
  return key in value && (value[key] === null || typeof value[key] === "string");
}

export function hasNullableNumber(
  value: Record<string, unknown>,
  key: string
): boolean {
  return key in value && (value[key] === null || isFiniteNumber(value[key]));
}

export function hasNullable<T>(
  value: Record<string, unknown>,
  key: string,
  validate: Guard<T>
): boolean {
  return key in value && (value[key] === null || validate(value[key]));
}

export function hasArray<T>(
  value: Record<string, unknown>,
  key: string,
  validate: Guard<T>
): boolean {
  return (
    key in value &&
    Array.isArray(value[key]) &&
    value[key].every((candidate) => validate(candidate))
  );
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

export function isTimestamp(value: unknown): value is string {
  return typeof value === "string" && Number.isFinite(Date.parse(value));
}

export function isOneOf<const T extends readonly string[]>(
  value: unknown,
  values: T
): value is T[number] {
  return typeof value === "string" && values.includes(value);
}
