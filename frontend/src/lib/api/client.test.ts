import { getRun, listRuns } from "./client";

describe("API client", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    jest.useRealTimers();
    global.fetch = originalFetch;
  });

  it("preserves the authoritative run ID from an error envelope", async () => {
    global.fetch = jest.fn().mockResolvedValue(
      response(
        503,
        JSON.stringify({
          error: {
            code: "QUEUE_UNAVAILABLE",
            message: "The run could not be queued.",
            run_id: "11111111-1111-4111-8111-111111111111"
          }
        })
      )
    );

    await expect(listRuns()).rejects.toMatchObject({
      code: "QUEUE_UNAVAILABLE",
      runId: "11111111-1111-4111-8111-111111111111",
      status: 503
    });
  });

  it("normalizes a non-JSON response", async () => {
    global.fetch = jest.fn().mockResolvedValue(response(502, "upstream unavailable"));

    await expect(listRuns()).rejects.toMatchObject({
      code: "REQUEST_FAILED",
      status: 502
    });
  });

  it("rejects malformed successful payloads", async () => {
    global.fetch = jest.fn().mockResolvedValue(response(200, JSON.stringify({ items: "invalid" })));

    await expect(listRuns()).rejects.toMatchObject({
      code: "INVALID_RESPONSE",
      status: 200
    });
  });

  it("rejects unknown run statuses instead of trusting string values", async () => {
    global.fetch = jest.fn().mockResolvedValue(
      response(
        200,
        JSON.stringify({
          items: [
            {
              run_id: "11111111-1111-4111-8111-111111111111",
              source_filename: "invoice.txt",
              status: "unexpected",
              stage: "ingest",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z"
            }
          ]
        })
      )
    );

    await expect(listRuns()).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
  });

  it("rejects malformed nested run detail data", async () => {
    global.fetch = jest.fn().mockResolvedValue(
      response(
        200,
        JSON.stringify({
          run_id: "11111111-1111-4111-8111-111111111111",
          source_filename: "invoice.txt",
          status: "running",
          stage: "extract",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          invoice: { items: "not-an-array" },
          findings: [null],
          recommendation: null,
          review: null,
          payment: null,
          events: [],
          error: null
        })
      )
    );

    await expect(
      getRun("11111111-1111-4111-8111-111111111111")
    ).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
  });

  it("accepts a complete minimal run detail payload", async () => {
    const payload = {
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
    global.fetch = jest.fn().mockResolvedValue(response(200, JSON.stringify(payload)));

    await expect(
      getRun("11111111-1111-4111-8111-111111111111")
    ).resolves.toEqual(payload);
  });

  it("times out a request with a bounded client error", async () => {
    jest.useFakeTimers();
    global.fetch = jest.fn((_input, init) =>
      new Promise((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(init.signal?.reason));
      })
    ) as typeof fetch;

    const request = listRuns();
    const expectation = expect(request).rejects.toMatchObject({
      code: "REQUEST_TIMEOUT"
    });
    await jest.advanceTimersByTimeAsync(15_000);

    await expectation;
  });

  it("honors caller cancellation without reporting a timeout", async () => {
    global.fetch = jest.fn((_input, init) =>
      new Promise((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
      })
    ) as typeof fetch;
    const controller = new AbortController();
    const request = getRun("11111111-1111-4111-8111-111111111111", controller.signal);

    controller.abort();

    await expect(request).rejects.toMatchObject({ name: "AbortError" });
  });
});

function response(status: number, body: string): Response {
  return {
    json: async () => JSON.parse(body) as unknown,
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 502 ? "Bad Gateway" : "Service Unavailable",
    text: async () => body
  } as Response;
}
