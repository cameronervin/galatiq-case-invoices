import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

import {
  api,
  cleanupPageTest,
  detail,
  preparePageTest,
  queuedRun
} from "./pageTestSupport";
import HomePage from "./page";

describe("HomePage error recovery", () => {
  beforeEach(preparePageTest);
  afterEach(cleanupPageTest);

  it("selects the authoritative failed run when creation cannot be queued", async () => {
    const failedRun = detail({
      ...queuedRun,
      status: "failed",
      stage: "finalize",
      error: {
        code: "QUEUE_UNAVAILABLE",
        message: "The run could not be queued."
      }
    });
    jest.mocked(api.createRun).mockRejectedValue(
      new api.ApiClientError(
        "The run could not be queued.",
        503,
        "QUEUE_UNAVAILABLE",
        failedRun.run_id
      )
    );
    jest
      .mocked(api.listRuns)
      .mockResolvedValueOnce({ items: [] })
      .mockResolvedValue({ items: [failedRun] });
    jest.mocked(api.getRun).mockResolvedValue(failedRun);
    const file = new File(["invoice"], "invoice.txt", { type: "text/plain" });
    render(<HomePage />);

    fireEvent.change(screen.getByLabelText("Choose invoice"), {
      target: { files: [file] }
    });
    fireEvent.click(screen.getByRole("button", { name: "Process invoice" }));

    expect(
      await screen.findByRole("heading", { name: "invoice.txt" })
    ).toBeInTheDocument();
    expect(screen.getAllByText("The run could not be queued.")).toHaveLength(2);
    expect(api.getRun).toHaveBeenCalledWith(failedRun.run_id);
  });

  it("does not clear an upload validation error when polling succeeds", async () => {
    jest.useFakeTimers();
    jest.mocked(api.listRuns).mockResolvedValue({ items: [queuedRun] });
    jest.mocked(api.getRun).mockResolvedValue(queuedRun);

    render(<HomePage />);
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "invoice.txt" })).toBeInTheDocument()
    );

    fireEvent.click(screen.getByRole("button", { name: "Process invoice" }));
    expect(
      screen.getByText("Choose an invoice before processing.")
    ).toBeInTheDocument();

    await act(async () => jest.advanceTimersByTimeAsync(2000));

    expect(
      screen.getByText("Choose an invoice before processing.")
    ).toBeInTheDocument();
  });

  it("reconciles a saved review after queue failure and can redispatch it", async () => {
    jest.spyOn(window, "confirm").mockReturnValue(true);
    const awaiting = detail({
      ...queuedRun,
      status: "review_required",
      stage: "review"
    });
    const saved = detail({
      ...awaiting,
      review: {
        decision: "approve",
        reason: "Reviewed the warning.",
        resume_pending: true,
        decided_at: "2026-01-01T00:00:01Z"
      }
    });
    jest.mocked(api.listRuns).mockResolvedValue({ items: [awaiting] });
    jest.mocked(api.getRun).mockResolvedValueOnce(awaiting).mockResolvedValue(saved);
    jest
      .mocked(api.reviewRun)
      .mockRejectedValueOnce(
        new api.ApiClientError(
          "The review was saved but could not be queued.",
          503,
          "QUEUE_UNAVAILABLE",
          awaiting.run_id
        )
      )
      .mockResolvedValueOnce(saved);

    render(<HomePage />);
    fireEvent.change(await screen.findByLabelText("Review reason"), {
      target: { value: "Reviewed the warning." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Approve invoice" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm approval" }));

    expect(
      await screen.findByRole("button", { name: "Retry worker resume" })
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry worker resume" }));

    await waitFor(() =>
      expect(api.reviewRun).toHaveBeenLastCalledWith(awaiting.run_id, {
        decision: "approve",
        reason: "Reviewed the warning."
      })
    );
  });
});
