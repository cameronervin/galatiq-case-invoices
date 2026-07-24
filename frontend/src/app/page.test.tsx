import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import * as api from "@/lib/api/client";
import type { RunDetail } from "@/types/api";

import HomePage from "./page";

jest.mock("@/lib/api/client");

const queuedRun: RunDetail = {
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

describe("HomePage", () => {
  beforeEach(() => {
    jest.mocked(api.listRuns).mockResolvedValue({ items: [] });
    jest.mocked(api.getRun).mockResolvedValue(queuedRun);
    jest.mocked(api.createRun).mockResolvedValue({
      ...queuedRun,
      deduplicated: false
    });
  });

  it("renders the operational upload and recent-run workspace", async () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: "Invoice processing workspace" })
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Choose invoice")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recent runs" })).toBeInTheDocument();
    expect(screen.queryByText(/retry/i)).not.toBeInTheDocument();
    await waitFor(() => expect(api.listRuns).toHaveBeenCalledWith({ limit: 20 }));
  });

  it("uploads a supported invoice and selects the queued run", async () => {
    render(<HomePage />);
    const file = new File(["invoice"], "invoice.txt", { type: "text/plain" });

    fireEvent.change(screen.getByLabelText("Choose invoice"), {
      target: { files: [file] }
    });
    fireEvent.click(screen.getByRole("button", { name: "Process invoice" }));

    await waitFor(() => expect(api.createRun).toHaveBeenCalledWith(file));
    expect(await screen.findByText("invoice.txt")).toBeInTheDocument();
    expect(screen.getByText("Queued")).toBeInTheDocument();
  });
});
