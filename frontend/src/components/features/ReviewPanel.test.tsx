import { fireEvent, render, screen } from "@testing-library/react";

import { ReviewPanel } from "./ReviewPanel";

describe("ReviewPanel", () => {
  it("requires a reason and confirmation before approval", () => {
    const onReview = jest.fn();
    jest.spyOn(window, "confirm").mockReturnValue(true);
    render(<ReviewPanel pending={false} onReview={onReview} />);

    fireEvent.click(screen.getByRole("button", { name: "Approve and mock pay" }));
    expect(onReview).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Review reason"), {
      target: { value: "Reviewed the warning." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Approve and mock pay" }));

    expect(window.confirm).toHaveBeenCalled();
    expect(onReview).toHaveBeenCalledWith("approve", "Reviewed the warning.");
  });

  it("announces a pending review action", () => {
    const { rerender } = render(<ReviewPanel pending={false} onReview={jest.fn()} />);

    rerender(<ReviewPanel pending onReview={jest.fn()} />);

    expect(screen.getByRole("region", { name: "Human review" })).toHaveAttribute(
      "aria-busy",
      "true"
    );
    expect(screen.getByRole("status")).toHaveTextContent("Recording review");
  });
});
