import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import {
  api,
  cleanupPageTest,
  preparePageTest
} from "./pageTestSupport";
import HomePage from "./page";

describe("HomePage invoice upload", () => {
  beforeEach(preparePageTest);
  afterEach(cleanupPageTest);

  it("uploads a supported invoice and selects the queued run", async () => {
    render(<HomePage />);
    const file = new File(["invoice"], "invoice.txt", { type: "text/plain" });

    fireEvent.change(screen.getByLabelText("Choose invoice"), {
      target: { files: [file] }
    });
    fireEvent.click(screen.getByRole("button", { name: "Process invoice" }));

    await waitFor(() => expect(api.createRun).toHaveBeenCalledWith(file));
    expect(
      await screen.findByRole("heading", { name: "invoice.txt" })
    ).toBeInTheDocument();
    expect(screen.getAllByText("Queued")).not.toHaveLength(0);
  });
});
