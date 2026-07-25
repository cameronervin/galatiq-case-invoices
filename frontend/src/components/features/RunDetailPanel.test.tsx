import { render, screen } from "@testing-library/react";

import type { RunDetail } from "@/types/api";

import { RunDetailPanel } from "./RunDetailPanel";

it("shows safe recommendation reason codes", () => {
  const detail: RunDetail = {
    run_id: "11111111-1111-4111-8111-111111111111",
    source_filename: "rejected.txt",
    status: "rejected",
    stage: "finalize",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:01Z",
    invoice: null,
    findings: [],
    recommendation: {
      proposed_route: "reject",
      final_route: "reject",
      reason_codes: ["BLOCKING_FINDING", "POLICY_OVERRIDE"],
      summary: "Rejected safely.",
      reflection_count: 1,
      decided_by: "policy"
    },
    review: null,
    payment: null,
    events: [],
    error: null
  };

  render(
    <RunDetailPanel
      detail={detail}
      focusVersion={0}
      reviewPending={false}
      onReview={jest.fn()}
    />
  );

  expect(screen.getByText("BLOCKING_FINDING")).toBeInTheDocument();
  expect(screen.getByText("POLICY_OVERRIDE")).toBeInTheDocument();
  expect(screen.getByText("Decision metadata").closest("details")).not.toHaveAttribute(
    "open"
  );
});

it("shows each recommendation reason code once", () => {
  const detail: RunDetail = {
    run_id: "11111111-1111-4111-8111-111111111111",
    source_filename: "normalized.txt",
    status: "completed",
    stage: "finalize",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:01Z",
    invoice: null,
    findings: [],
    recommendation: {
      proposed_route: "approve",
      final_route: "approve",
      reason_codes: ["ITEM_ALIAS_NORMALIZATION", "ITEM_ALIAS_NORMALIZATION"],
      summary: "Approved safely.",
      reflection_count: 0,
      decided_by: "agent"
    },
    review: null,
    payment: null,
    events: [],
    error: null
  };

  render(
    <RunDetailPanel
      detail={detail}
      focusVersion={0}
      reviewPending={false}
      onReview={jest.fn()}
    />
  );

  expect(screen.getAllByText("ITEM_ALIAS_NORMALIZATION")).toHaveLength(1);
});

it.each([
  ["queued", true],
  ["running", true],
  ["failed", true],
  ["review_required", false],
  ["completed", false],
  ["rejected", false]
] as const)("sets workflow history disclosure for %s runs", (status, expanded) => {
  const detail: RunDetail = {
    run_id: "11111111-1111-4111-8111-111111111111",
    source_filename: "invoice.txt",
    status,
    stage: status === "queued" ? "ingest" : "finalize",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:01Z",
    invoice: null,
    findings: [],
    recommendation: null,
    review: null,
    payment: null,
    events: [],
    error: status === "failed" ? { code: "FAILED", message: "Run failed." } : null
  };

  render(
    <RunDetailPanel
      detail={detail}
      focusVersion={0}
      reviewPending={false}
      onReview={jest.fn()}
    />
  );

  const history = screen.getByText(/Workflow history/).closest("details");
  expect(history).not.toBeNull();
  if (expanded) {
    expect(history).toHaveAttribute("open");
  } else {
    expect(history).not.toHaveAttribute("open");
  }
});
