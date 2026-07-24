import { formatMoney } from "@/components/features/run-detail/formatters";
import type { RunDetail } from "@/types/api";

export function RunOutcome({ detail }: { detail: RunDetail }) {
  const status = detail.status;
  switch (status) {
    case "completed":
      return detail.payment ? (
        <section className="outcome outcome-success" aria-label="Payment outcome">
          <div>
            <p className="panel-kicker">Mock payment complete</p>
            <strong>{formatMoney(detail.payment.amount)}</strong>
          </div>
          <p>Reference {detail.payment.mock_reference ?? "recorded"}</p>
        </section>
      ) : (
        <p className="outcome outcome-running">Processing completed.</p>
      );
    case "rejected":
      return <p className="outcome outcome-rejected">Rejected safely; no payment was created.</p>;
    case "failed":
      return (
        <p className="outcome outcome-failed">
          {detail.error?.message ?? "Processing failed safely. Submit the source as a new run."}
        </p>
      );
    case "review_required":
      return <p className="outcome outcome-review">Payment is paused until a reviewer decides.</p>;
    case "queued":
    case "running":
      return <p className="outcome outcome-running">Processing stage: {detail.stage}</p>;
    default:
      return assertNever(status);
  }
}

function assertNever(status: never): never {
  throw new Error(`Unhandled run status: ${status satisfies never}`);
}
