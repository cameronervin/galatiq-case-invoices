import { act, render, screen, waitFor } from "@testing-library/react";

import {
  api,
  cleanupPageTest,
  detail,
  preparePageTest,
  queuedRun
} from "./pageTestSupport";
import HomePage from "./page";

describe("HomePage run polling", () => {
  beforeEach(preparePageTest);
  afterEach(cleanupPageTest);

  it("recovers polling after a transient request failure", async () => {
    jest.useFakeTimers();
    const completed = detail({
      ...queuedRun,
      status: "completed",
      stage: "finalize",
      payment: {
        status: "succeeded",
        amount: { amount: "100.00", currency: "USD" },
        mock_reference: "MOCK-1",
        error_code: null,
        created_at: "2026-01-01T00:00:01Z",
        updated_at: "2026-01-01T00:00:01Z"
      }
    });
    jest.mocked(api.listRuns).mockResolvedValue({ items: [queuedRun] });
    jest
      .mocked(api.getRun)
      .mockResolvedValueOnce(queuedRun)
      .mockRejectedValueOnce(new Error("temporary outage"))
      .mockResolvedValueOnce(completed);

    render(<HomePage />);
    await waitFor(() => expect(screen.getAllByText("Queued")).not.toHaveLength(0));
    await act(async () => jest.advanceTimersByTimeAsync(2000));
    await act(async () => jest.advanceTimersByTimeAsync(2000));

    expect(await screen.findByText(/MOCK-1/)).toBeInTheDocument();
  });

  it("continues polling while a persisted review is waiting for resume", async () => {
    jest.useFakeTimers();
    const pendingReview = detail({
      ...queuedRun,
      status: "review_required",
      stage: "review",
      review: {
        decision: "approve",
        reason: "Reviewed the warning.",
        resume_pending: true,
        decided_at: "2026-01-01T00:00:01Z"
      }
    });
    const completed = detail({
      ...pendingReview,
      status: "completed",
      stage: "finalize",
      review: { ...pendingReview.review!, resume_pending: false },
      payment: {
        status: "succeeded",
        amount: { amount: "100.00", currency: "USD" },
        mock_reference: "MOCK-2",
        error_code: null,
        created_at: "2026-01-01T00:00:02Z",
        updated_at: "2026-01-01T00:00:02Z"
      }
    });
    jest.mocked(api.listRuns).mockResolvedValue({ items: [pendingReview] });
    jest
      .mocked(api.getRun)
      .mockResolvedValueOnce(pendingReview)
      .mockResolvedValueOnce(completed);

    render(<HomePage />);
    await waitFor(() =>
      expect(screen.getByText(/waiting for worker resume/i)).toBeInTheDocument()
    );
    await act(async () => jest.advanceTimersByTimeAsync(2000));

    expect(await screen.findByText(/MOCK-2/)).toBeInTheDocument();
  });
});
