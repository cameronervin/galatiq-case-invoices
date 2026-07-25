import type { RunStatus } from "@/types/api";

const labels: Record<RunStatus, string> = {
  queued: "Queued",
  running: "In progress",
  review_required: "Review required",
  completed: "Completed",
  rejected: "Rejected",
  failed: "Failed"
};

export function StatusBadge({ status }: { status: RunStatus }) {
  return <span className={`status-badge status-${status}`}>{labels[status]}</span>;
}
