import { isRunDetail, isRunListResponse } from "./runs";

describe("run envelope decoders", () => {
  it("rejects malformed values at every composed collection boundary", () => {
    expect(isRunListResponse({ items: [null] })).toBe(false);
    expect(isRunDetail({ ...minimalRunDetail(), findings: [null] })).toBe(false);
    expect(isRunDetail({ ...minimalRunDetail(), events: [null] })).toBe(false);
  });

  it("requires the complete detail envelope", () => {
    const { payment: _payment, ...missingPayment } = minimalRunDetail();

    expect(isRunDetail(missingPayment)).toBe(false);
  });

  it("accepts the complete minimal detail envelope", () => {
    expect(isRunDetail(minimalRunDetail())).toBe(true);
  });
});

function minimalRunDetail() {
  return {
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
}
