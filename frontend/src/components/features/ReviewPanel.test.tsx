import { fireEvent, render, screen } from "@testing-library/react";

import { ReviewPanel } from "./ReviewPanel";

describe("ReviewPanel", () => {
  const invoice = {
    invoiceNumber: "INV-1012",
    invoiceTotal: { amount: "1250.00", currency: "USD" }
  };

  it("requires a reason and an inline confirmation before approval", () => {
    const onReview = jest.fn();
    render(<ReviewPanel pending={false} onReview={onReview} {...invoice} />);

    fireEvent.click(screen.getByRole("button", { name: "Approve invoice" }));
    expect(onReview).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Review reason"), {
      target: { value: "Reviewed the warning." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Approve invoice" }));

    expect(
      screen.getByText(/INV-1012.*1250\.00 USD/i)
    ).toBeInTheDocument();
    expect(onReview).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Confirm approval" }));
    expect(onReview).toHaveBeenCalledWith("approve", "Reviewed the warning.");
  });

  it("states when approval confirmation details are unavailable and can be cancelled", () => {
    render(
      <ReviewPanel
        invoiceNumber={null}
        invoiceTotal={null}
        pending={false}
        onReview={jest.fn()}
      />
    );

    fireEvent.change(screen.getByLabelText("Review reason"), {
      target: { value: "Reviewed available evidence." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Approve invoice" }));

    expect(screen.getByText(/invoice number unavailable/i)).toBeInTheDocument();
    expect(screen.getByText(/amount unavailable/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("button", { name: "Confirm approval" })).not.toBeInTheDocument();
  });

  it("announces a pending review action", () => {
    const { rerender } = render(
      <ReviewPanel pending={false} onReview={jest.fn()} {...invoice} />
    );

    rerender(<ReviewPanel pending onReview={jest.fn()} {...invoice} />);

    expect(screen.getByRole("region", { name: "Human review" })).toHaveAttribute(
      "aria-busy",
      "true"
    );
    expect(screen.getByRole("status")).toHaveTextContent("Recording review");
  });
});
