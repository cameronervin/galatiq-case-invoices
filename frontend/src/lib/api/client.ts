import type {
  ErrorEnvelope,
  HealthResponse,
  RunCreationResponse,
  RunDetail,
  RunListResponse,
  RunSummary
} from "@/types/api";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiClientError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload: unknown = await response.json();
  if (!response.ok) {
    const envelope = payload as Partial<ErrorEnvelope>;
    throw new ApiClientError(
      envelope.error?.message ?? "The request failed.",
      response.status,
      envelope.error?.code ?? "REQUEST_FAILED"
    );
  }
  return payload as T;
}

export async function getHealth(): Promise<HealthResponse> {
  return parseResponse(
    await fetch(`${apiBaseUrl}/api/v1/health`, { cache: "no-store" })
  );
}

export async function createRun(file: File): Promise<RunCreationResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return parseResponse(
    await fetch(`${apiBaseUrl}/api/v1/runs`, {
      method: "POST",
      body: formData
    })
  );
}

export async function listRuns({
  limit = 20
}: {
  limit?: number;
} = {}): Promise<RunListResponse> {
  return parseResponse(
    await fetch(`${apiBaseUrl}/api/v1/runs?limit=${limit}`, {
      cache: "no-store"
    })
  );
}

export async function getRun(
  runId: string,
  signal?: AbortSignal
): Promise<RunDetail> {
  return parseResponse(
    await fetch(`${apiBaseUrl}/api/v1/runs/${runId}`, {
      cache: "no-store",
      signal
    })
  );
}

export async function reviewRun(
  runId: string,
  command: { decision: "approve" | "reject"; reason: string }
): Promise<RunSummary> {
  return parseResponse(
    await fetch(`${apiBaseUrl}/api/v1/runs/${runId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(command)
    })
  );
}
