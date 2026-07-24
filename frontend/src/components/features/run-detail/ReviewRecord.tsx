import type { HumanReview } from "@/types/api";

interface ReviewRecordProps {
  review: HumanReview;
  pending: boolean;
  onReview: (decision: "approve" | "reject", reason: string) => void;
}

export function ReviewRecord({ review, pending, onReview }: ReviewRecordProps) {
  return (
    <section className="detail-section" aria-labelledby="review-record-heading">
      <p className="panel-kicker">Human decision</p>
      <h3 id="review-record-heading">
        {review.decision === "approve" ? "Approved" : "Rejected"} by reviewer
      </h3>
      <p>{review.reason}</p>
      {review.resume_pending ? (
        <>
          <p className="pending-note">Recorded · waiting for worker resume</p>
          <button
            className="button button-secondary"
            disabled={pending}
            onClick={() => onReview(review.decision, review.reason)}
            type="button"
          >
            {pending ? "Retrying worker resume…" : "Retry worker resume"}
          </button>
          <p className="sr-only" role="status" aria-live="polite">
            {pending ? "Retrying worker resume…" : ""}
          </p>
        </>
      ) : null}
    </section>
  );
}
