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

describe("HomePage run selection", () => {
  beforeEach(preparePageTest);
  afterEach(cleanupPageTest);

  it("ignores stale detail responses after selecting another run", async () => {
    const first = detail({
      run_id: "11111111-1111-4111-8111-111111111111",
      source_filename: "first.txt",
      status: "review_required",
      stage: "review"
    });
    const second = detail({
      run_id: "22222222-2222-4222-8222-222222222222",
      source_filename: "second.txt"
    });
    const firstRequest = deferred<RunDetail>();
    const secondRequest = deferred<RunDetail>();
    jest.mocked(api.listRuns).mockResolvedValue({ items: [first, second] });
    jest.mocked(api.getRun).mockImplementation((runId) =>
      runId === first.run_id ? firstRequest.promise : secondRequest.promise
    );

    render(<HomePage />);
    await waitFor(() =>
      expect(api.getRun).toHaveBeenCalledWith(first.run_id, expect.anything())
    );
    fireEvent.click(screen.getByRole("button", { name: /second\.txt/i }));
    await waitFor(() =>
      expect(api.getRun).toHaveBeenCalledWith(second.run_id, expect.anything())
    );

    await act(async () => firstRequest.resolve(first));
    expect(
      screen.queryByRole("heading", { name: "first.txt" })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Approve and mock pay" })
    ).not.toBeInTheDocument();

    await act(async () => secondRequest.resolve(second));
    expect(screen.getByRole("heading", { name: "second.txt" })).toBeInTheDocument();
  });

  it("shows which selected run is loading", async () => {
    const first = detail({
      run_id: "11111111-1111-4111-8111-111111111111",
      source_filename: "first.txt"
    });
    const second = detail({
      run_id: "22222222-2222-4222-8222-222222222222",
      source_filename: "second.txt"
    });
    const secondRequest = deferred<RunDetail>();
    jest.mocked(api.listRuns).mockResolvedValue({ items: [first, second] });
    jest.mocked(api.getRun).mockImplementation((runId) =>
      runId === first.run_id ? Promise.resolve(first) : secondRequest.promise
    );

    render(<HomePage />);
    await screen.findByRole("heading", { name: "first.txt" });
    fireEvent.click(screen.getByRole("button", { name: /second\.txt/i }));

    expect(screen.getByText("Loading second.txt…")).toBeInTheDocument();

    await act(async () => secondRequest.resolve(second));
  });
});
