import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

import type { RunDetail } from "@/types/api";

import {
  api,
  cleanupPageTest,
  deferred,
  preparePageTest,
  queuedRun
} from "./pageTestSupport";
import HomePage from "./page";

describe("HomePage workspace and run list", () => {
  beforeEach(preparePageTest);
  afterEach(cleanupPageTest);

  it("renders the operational upload and recent-run workspace", async () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: "Invoice processing" })
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Choose invoice")).toBeInTheDocument();
    const recentRunsHeading = screen.getByRole("heading", { name: "Recent runs" });
    const detailHeading = screen.getByRole("heading", { name: "Run details" });
    expect(
      recentRunsHeading.compareDocumentPosition(detailHeading) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
    expect(screen.queryByText(/retry/i)).not.toBeInTheDocument();
    await waitFor(() => expect(api.listRuns).toHaveBeenCalledWith({ limit: 20 }));
  });

  it("does not let an older list response remove a newly created run", async () => {
    const initialList = deferred<{ items: RunDetail[] }>();
    const refreshedList = deferred<{ items: RunDetail[] }>();
    jest
      .mocked(api.listRuns)
      .mockReturnValueOnce(initialList.promise)
      .mockReturnValueOnce(refreshedList.promise);
    const file = new File(["invoice"], "invoice.txt", { type: "text/plain" });

    render(<HomePage />);
    fireEvent.change(screen.getByLabelText("Choose invoice"), {
      target: { files: [file] }
    });
    fireEvent.click(screen.getByRole("button", { name: "Process invoice" }));

    await waitFor(() => expect(api.listRuns).toHaveBeenCalledTimes(2));
    await act(async () => refreshedList.resolve({ items: [queuedRun] }));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /invoice\.txt/i })).toBeInTheDocument()
    );

    await act(async () => initialList.resolve({ items: [] }));

    expect(screen.getByRole("button", { name: /invoice\.txt/i })).toBeInTheDocument();
  });
});
