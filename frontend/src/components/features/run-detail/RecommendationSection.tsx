import type { Recommendation } from "@/types/api";

export function RecommendationSection({
  recommendation
}: {
  recommendation: Recommendation;
}) {
  const reasonCodes = [...new Set(recommendation.reason_codes)];

  return (
    <section className="detail-section recommendation" aria-labelledby="recommendation-heading">
      <p className="panel-kicker">Decision</p>
      <h3 id="recommendation-heading">Recommendation</h3>
      <p>{recommendation.summary}</p>
      <details className="disclosure">
        <summary>Decision metadata</summary>
        <dl className="recommendation-meta">
          <div>
            <dt>Final route</dt>
            <dd>{recommendation.final_route}</dd>
          </div>
          <div>
            <dt>Decided by</dt>
            <dd>{recommendation.decided_by}</dd>
          </div>
          <div>
            <dt>Revisions</dt>
            <dd>{recommendation.reflection_count}</dd>
          </div>
        </dl>
        {reasonCodes.length ? (
          <ul className="reason-codes" aria-label="Recommendation reason codes">
            {reasonCodes.map((code) => (
              <li key={code}>{code}</li>
            ))}
          </ul>
        ) : null}
      </details>
    </section>
  );
}
