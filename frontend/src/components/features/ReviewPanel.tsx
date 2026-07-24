"use client";

import { useState } from "react";

interface ReviewPanelProps {
  pending: boolean;
  onReview: (decision: "approve" | "reject", reason: string) => void;
}

export function ReviewPanel({ pending, onReview }: ReviewPanelProps) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");

  function submit(decision: "approve" | "reject") {
    const trimmed = reason.trim();
    if (trimmed.length < 3) {
      setError("Enter at least three characters explaining the decision.");
      return;
    }
    if (
      decision === "approve" &&
      !window.confirm(
        "Approve this invoice and record a simulated payment in its original currency?"
      )
    ) {
      return;
    }
    setError("");
    onReview(decision, trimmed);
  }

  return (
    <section
      className="panel review-panel"
      aria-busy={pending}
      aria-labelledby="review-heading"
    >
      <p className="panel-kicker">Action required</p>
      <h3 id="review-heading">Human review</h3>
      <p>Review the warnings and recommendation before deciding.</p>
      <label htmlFor="review-reason">Review reason</label>
      <textarea
        id="review-reason"
        value={reason}
        minLength={3}
        maxLength={500}
        aria-describedby={error ? "review-error" : undefined}
        aria-invalid={Boolean(error)}
        onChange={(event) => setReason(event.target.value)}
      />
      {error ? (
        <p id="review-error" className="field-error">
          {error}
        </p>
      ) : null}
      <div className="button-row">
        <button
          className="button button-primary"
          disabled={pending}
          onClick={() => submit("approve")}
          type="button"
        >
          Approve and mock pay
        </button>
        <button
          className="button button-danger"
          disabled={pending}
          onClick={() => submit("reject")}
          type="button"
        >
          Reject invoice
        </button>
      </div>
      <p className="sr-only" role="status" aria-live="polite">
        {pending ? "Recording review…" : ""}
      </p>
    </section>
  );
}
