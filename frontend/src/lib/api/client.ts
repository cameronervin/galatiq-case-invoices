import type { HealthResponse } from "@/types/api";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiClientError extends Error {
  constructor(
    message: string,
    readonly status: number
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/health`, {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new ApiClientError("Health request failed", response.status);
  }
  return (await response.json()) as HealthResponse;
}

