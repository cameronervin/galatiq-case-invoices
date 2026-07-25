"use client";

import { useEffect, useRef, useState } from "react";

import { formatMoney } from "@/components/features/run-detail/formatters";
import type { Money } from "@/types/api";

interface ReviewPanelProps {
  invoiceNumber: string | null;
  invoiceTotal: Money | null;
  pending: boolean;
  onReview: (decision: "approve" | "reject", reason: string) => void;
}

export function ReviewPanel({
  invoiceNumber,
  invoiceTotal,
  pending,
  onReview
}: ReviewPanelProps) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [confirmingApproval, setConfirmingApproval] = useState(false);
  const confirmButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (confirmingApproval) {
      confirmButtonRef.current?.focus();
    }
  }, [confirmingApproval]);

  function validatedReason(): string | null {
    const trimmed = reason.trim();
    if (trimmed.length < 3) {
      setError("Enter at least three characters explaining the decision.");
      return null;
    }
    setError("");
    return trimmed;
  }

  function requestApproval() {
    if (validatedReason()) {
      setConfirmingApproval(true);
    }
  }

  function submitRejection() {
    const trimmed = validatedReason();
    if (trimmed) {
      onReview("reject", trimmed);
    }
  }

  return (
    <section
      className="panel review-panel"
      aria-busy={pending}
      aria-labelledby="review-heading"
    >
      <p className="panel-kicker">Action required</p>
      <h3 id="review-heading">Human review</h3>
      <p>Review the findings and recommendation before deciding.</p>
      <label htmlFor="review-reason">Review reason</label>
      <textarea
        id="review-reason"
        value={reason}
        minLength={3}
        maxLength={500}
        aria-describedby={error ? "review-error" : undefined}
        aria-invalid={Boolean(error)}
        onChange={(event) => {
          setReason(event.target.value);
          setConfirmingApproval(false);
        }}
      />
      {error ? (
        <p id="review-error" className="field-error">
          {error}
        </p>
      ) : null}
      {confirmingApproval ? (
        <div className="approval-confirmation" role="group" aria-labelledby="approval-copy">
          <p id="approval-copy">
            Approve {invoiceNumber ? `invoice ${invoiceNumber}` : "this invoice — invoice number unavailable"}
            {invoiceTotal
              ? ` and create a simulated payment of ${formatMoney(invoiceTotal)}?`
              : " and create a simulated payment — amount unavailable?"}
          </p>
          <div className="button-row">
            <button
              ref={confirmButtonRef}
              className="button button-primary"
              disabled={pending}
              onClick={() => onReview("approve", reason.trim())}
              type="button"
            >
              Confirm approval
            </button>
            <button
              className="button button-quiet"
              disabled={pending}
              onClick={() => setConfirmingApproval(false)}
              type="button"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="button-row">
          <button
            className="button button-primary"
            disabled={pending}
            onClick={requestApproval}
            type="button"
          >
            Approve invoice
          </button>
          <button
            className="button button-danger"
            disabled={pending}
            onClick={submitRejection}
            type="button"
          >
            Reject invoice
          </button>
        </div>
      )}
      <p className="sr-only" role="status" aria-live="polite">
        {pending ? "Recording review…" : ""}
      </p>
    </section>
  );
}
