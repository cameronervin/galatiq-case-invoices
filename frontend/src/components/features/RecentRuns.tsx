import { StatusBadge } from "@/components/ui/StatusBadge";
import type { RunSummary } from "@/types/api";

interface RecentRunsProps {
  loading: boolean;
  runs: RunSummary[];
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
}

export function RecentRuns({
  loading,
  runs,
  selectedRunId,
  onSelect
}: RecentRunsProps) {
  return (
    <aside className="recent-runs" aria-labelledby="recent-runs-heading">
      <div className="section-heading">
        <div>
          <p className="panel-kicker">Queue</p>
          <h2 id="recent-runs-heading">Recent runs</h2>
        </div>
        <span className="record-count">Newest 20</span>
      </div>
      {loading ? <p className="empty-state">Loading runs…</p> : null}
      {!loading && runs.length === 0 ? (
        <p className="empty-state">No runs yet. Choose an invoice to begin.</p>
      ) : null}
      <ol className="run-list">
        {runs.map((run) => (
          <li key={run.run_id}>
            <button
              className="run-list-item"
              data-selected={run.run_id === selectedRunId}
              aria-current={run.run_id === selectedRunId ? "true" : undefined}
              onClick={() => onSelect(run.run_id)}
              type="button"
            >
              <span className="run-list-name">{run.source_filename}</span>
              <StatusBadge status={run.status} />
              <span className="run-list-meta">
                {stageLabel(run.stage)} · {formatDate(run.updated_at)}
              </span>
            </button>
          </li>
        ))}
      </ol>
    </aside>
  );
}

function stageLabel(stage: RunSummary["stage"]): string {
  return stage.charAt(0).toUpperCase() + stage.slice(1);
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}
