const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const requestTimeoutMs = 15_000;

export type Validator<T> = (value: unknown) => value is T;

export class ApiClientError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly runId: string | null = null
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

export async function request<T>(
  path: string,
  init: RequestInit,
  validate: Validator<T>
): Promise<T> {
  const controller = new AbortController();
  const callerSignal = init.signal;
  let timedOut = false;
  const abortFromCaller = () => controller.abort(callerSignal?.reason);
  if (callerSignal?.aborted) {
    abortFromCaller();
  } else {
    callerSignal?.addEventListener("abort", abortFromCaller, { once: true });
  }
  const timeout = globalThis.setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, requestTimeoutMs);

  try {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      signal: controller.signal
    });
    return await parseResponse(response, validate);
  } catch (error: unknown) {
    if (timedOut) {
      throw new ApiClientError(
        "The request timed out. Check the local services and try again.",
        408,
        "REQUEST_TIMEOUT"
      );
    }
    throw error;
  } finally {
    globalThis.clearTimeout(timeout);
    callerSignal?.removeEventListener("abort", abortFromCaller);
  }
}

async function parseResponse<T>(
  response: Response,
  validate: Validator<T>
): Promise<T> {
  const payload = await readJson(response);
  if (!response.ok) {
    const envelope = parseErrorEnvelope(payload);
    throw new ApiClientError(
      envelope?.message ?? "The request failed.",
      response.status,
      envelope?.code ?? "REQUEST_FAILED",
      envelope?.runId ?? null
    );
  }
  if (!validate(payload)) {
    throw new ApiClientError(
      "The server returned an invalid response.",
      response.status,
      "INVALID_RESPONSE"
    );
  }
  return payload;
}

async function readJson(response: Response): Promise<unknown> {
  try {
    const body = await response.text();
    return body ? (JSON.parse(body) as unknown) : null;
  } catch {
    return null;
  }
}

function parseErrorEnvelope(
  value: unknown
): { code: string; message: string; runId: string | null } | null {
  if (!isRecord(value) || !isRecord(value.error)) {
    return null;
  }
  const { code, message, run_id: runId } = value.error;
  if (
    typeof code !== "string" ||
    typeof message !== "string" ||
    (runId !== undefined && runId !== null && typeof runId !== "string")
  ) {
    return null;
  }
  return { code, message, runId: runId ?? null };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
