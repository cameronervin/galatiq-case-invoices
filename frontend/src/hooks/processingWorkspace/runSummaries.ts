import type { RunSummary } from "@/types/api";

const maximumVisibleRuns = 20;

export function mergeRunSummaries(
  current: RunSummary[],
  incoming: RunSummary[]
): RunSummary[] {
  const byId = new Map(current.map((run) => [run.run_id, run]));
  for (const run of incoming) {
    const existing = byId.get(run.run_id);
    if (!existing || run.updated_at.localeCompare(existing.updated_at) > 0) {
      byId.set(run.run_id, run);
    }
  }
  return [...byId.values()]
    .sort(
      (left, right) =>
        right.created_at.localeCompare(left.created_at) ||
        right.run_id.localeCompare(left.run_id)
    )
    .slice(0, maximumVisibleRuns);
}

export function withoutKey<T>(
  current: Record<string, T>,
  key: string
): Record<string, T> {
  if (!(key in current)) {
    return current;
  }
  const next = { ...current };
  delete next[key];
  return next;
}
