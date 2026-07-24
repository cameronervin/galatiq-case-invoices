import type { RunSummary } from "@/types/api";

import { mergeRunSummaries, withoutKey } from "./runSummaries";

function run(
  runId: string,
  createdAt: string,
  updatedAt = createdAt
): RunSummary {
  return {
    run_id: runId,
    source_filename: `${runId}.txt`,
    status: "queued",
    stage: "ingest",
    created_at: createdAt,
    updated_at: updatedAt
  };
}

describe("mergeRunSummaries", () => {
  it("keeps the freshest representation and sorts newest runs first", () => {
    const stale = run("same", "2026-01-02T00:00:00Z");
    const fresh = {
      ...stale,
      status: "completed" as const,
      updated_at: "2026-01-03T00:00:00Z"
    };
    const older = run("older", "2026-01-01T00:00:00Z");

    expect(mergeRunSummaries([stale], [older, fresh])).toEqual([
      fresh,
      older
    ]);
    expect(mergeRunSummaries([fresh], [stale])).toEqual([fresh]);
  });

  it("limits the catalog to the twenty newest runs", () => {
    const runs = Array.from({ length: 25 }, (_, index) =>
      run(
        index.toString().padStart(2, "0"),
        `2026-01-${(index + 1).toString().padStart(2, "0")}T00:00:00Z`
      )
    );

    const merged = mergeRunSummaries([], runs);

    expect(merged).toHaveLength(20);
    expect(merged[0]?.run_id).toBe("24");
    expect(merged.at(-1)?.run_id).toBe("05");
  });
});

describe("withoutKey", () => {
  it("preserves identity when no state changes", () => {
    const current = { first: "message" };

    expect(withoutKey(current, "missing")).toBe(current);
    expect(withoutKey(current, "first")).toEqual({});
  });
});
