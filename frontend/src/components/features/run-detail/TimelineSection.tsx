import { formatTimestamp } from "@/components/features/run-detail/formatters";
import type { RunEvent } from "@/types/api";

export function TimelineSection({
  defaultExpanded,
  events
}: {
  defaultExpanded: boolean;
  events: RunEvent[];
}) {
  return (
    <section className="detail-section history-section" aria-labelledby="timeline-heading">
      <details className="disclosure history-disclosure" open={defaultExpanded}>
        <summary>
          <span id="timeline-heading">Workflow history</span>
          <span className="record-count">{events.length} events</span>
        </summary>
        {events.length ? (
          <ol className="timeline">
            {events.map((event) => (
              <li key={event.event_id}>
                <span className="timeline-marker" aria-hidden="true" />
                <div>
                  <div className="timeline-title">
                    <strong>{event.message}</strong>
                    <time dateTime={event.created_at}>{formatTimestamp(event.created_at)}</time>
                  </div>
                  <p>
                    {event.stage} · {event.code}
                    {event.duration_ms !== null ? ` · ${event.duration_ms} ms` : ""}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <p className="empty-state inset">The first workflow event will appear here.</p>
        )}
      </details>
    </section>
  );
}
