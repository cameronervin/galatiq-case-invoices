import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

import type { RunDetail } from "@/types/api";

import {
  api,
  cleanupPageTest,
  deferred,
  detail,
  preparePageTest
} from "./pageTestSupport";
import HomePage from "./page";

describe("HomePage invoice review", () => {
  beforeEach(preparePageTest);
  afterEach(cleanupPageTest);

  it("keeps review pending state scoped to the run being reviewed", async () => {
    const first = detail({
      run_id: "11111111-1111-4111-8111-111111111111",
      source_filename: "first.txt",
      status: "review_required",
      stage: "review"
    });
    const second = detail({
      run_id: "22222222-2222-4222-8222-222222222222",
      source_filename: "second.txt",
      status: "review_required",
      stage: "review"
    });
    const reviewRequest = deferred<RunDetail>();
    jest.mocked(api.listRuns).mockResolvedValue({ items: [first, second] });
    jest.mocked(api.getRun).mockImplementation(async (runId) =>
      runId === first.run_id ? first : second
    );
    jest.mocked(api.reviewRun).mockReturnValue(reviewRequest.promise);

    render(<HomePage />);
    fireEvent.change(await screen.findByLabelText("Review reason"), {
      target: { value: "Needs a human decision." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Reject invoice" }));
    fireEvent.click(screen.getByRole("button", { name: /second\.txt/i }));

    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "second.txt" })).toBeInTheDocument()
    );
    expect(screen.getByRole("button", { name: "Reject invoice" })).toBeEnabled();

    await act(async () => reviewRequest.resolve(first));
  });
});
