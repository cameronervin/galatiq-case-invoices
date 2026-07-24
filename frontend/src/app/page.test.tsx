import { render, screen } from "@testing-library/react";

import HomePage from "./page";

describe("HomePage", () => {
  it("renders the neutral scaffold workspace", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: "Invoice processing workspace" })
    ).toBeInTheDocument();
    expect(screen.getByText("Scaffold ready")).toBeInTheDocument();
    expect(
      screen.getByText(/Business workflow implementation comes next/i)
    ).toBeInTheDocument();
  });
});

