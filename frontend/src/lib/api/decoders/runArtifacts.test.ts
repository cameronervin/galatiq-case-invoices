import { isHumanReview, isPayment, isRunEvent } from "./runArtifacts";

describe("run artifact decoders", () => {
  it("rejects invalid review timestamps", () => {
    expect(
      isHumanReview({
        decision: "approve",
        reason: "Verified",
        resume_pending: false,
        decided_at: "not-a-date"
      })
    ).toBe(false);
  });

  it("validates nested payment money", () => {
    expect(
      isPayment({
        status: "succeeded",
        amount: { amount: "10.00", currency: 123 },
        mock_reference: "mock-1",
        error_code: null,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z"
      })
    ).toBe(false);
  });

  it("rejects unknown event stages and non-finite durations", () => {
    const event = {
      event_id: 1,
      stage: "validate",
      status: "running",
      code: "VALIDATION_STARTED",
      message: "Validating invoice.",
      created_at: "2026-01-01T00:00:00Z",
      duration_ms: 10
    };

    expect(isRunEvent({ ...event, stage: "unknown" })).toBe(false);
    expect(isRunEvent({ ...event, duration_ms: Number.POSITIVE_INFINITY })).toBe(false);
  });
});
