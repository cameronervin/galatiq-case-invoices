import type {
  RunCreationResponse,
  RunDetail,
  RunListResponse,
  RunSummary
} from "@/types/api";

import {
  isRunCreationResponse,
  isRunDetail,
  isRunListResponse,
  isRunSummary
} from "./runDecoders";
import { ApiClientError, request } from "./transport";

export { ApiClientError } from "./transport";

export async function createRun(file: File): Promise<RunCreationResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request(
    "/api/v1/runs",
    { method: "POST", body: formData },
    isRunCreationResponse
  );
}

export async function listRuns({
  limit = 20
}: {
  limit?: number;
} = {}): Promise<RunListResponse> {
  return request(
    `/api/v1/runs?limit=${limit}`,
    { cache: "no-store" },
    isRunListResponse
  );
}

export async function getRun(
  runId: string,
  signal?: AbortSignal
): Promise<RunDetail> {
  return request(
    `/api/v1/runs/${encodeURIComponent(runId)}`,
    { cache: "no-store", signal },
    isRunDetail
  );
}

export async function reviewRun(
  runId: string,
  command: { decision: "approve" | "reject"; reason: string }
): Promise<RunSummary> {
  return request(
    `/api/v1/runs/${encodeURIComponent(runId)}/review`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(command)
    },
    isRunSummary
  );
}
