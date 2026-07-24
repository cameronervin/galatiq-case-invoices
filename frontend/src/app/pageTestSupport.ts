import * as api from "@/lib/api/client";
import type { RunDetail } from "@/types/api";

jest.mock("@/lib/api/client", () => ({
  ...jest.requireActual("@/lib/api/client"),
  createRun: jest.fn(),
  getRun: jest.fn(),
  listRuns: jest.fn(),
  reviewRun: jest.fn()
}));

export { api };

export const queuedRun: RunDetail = {
  run_id: "11111111-1111-4111-8111-111111111111",
  source_filename: "invoice.txt",
  status: "queued",
  stage: "ingest",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  invoice: null,
  findings: [],
  recommendation: null,
  review: null,
  payment: null,
  events: [],
  error: null
};

export function detail(
  overrides: Partial<RunDetail> & Pick<RunDetail, "run_id" | "source_filename">
): RunDetail {
  return { ...queuedRun, ...overrides };
}

export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, reject, resolve };
}

export function preparePageTest() {
  jest.useRealTimers();
  jest.resetAllMocks();
  jest.mocked(api.listRuns).mockResolvedValue({ items: [] });
  jest.mocked(api.getRun).mockResolvedValue(queuedRun);
  jest.mocked(api.createRun).mockResolvedValue({
    ...queuedRun,
    deduplicated: false
  });
}

export function cleanupPageTest() {
  jest.useRealTimers();
  jest.restoreAllMocks();
}
