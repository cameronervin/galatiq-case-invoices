import type { Recommendation } from "@/types/api";

export function RecommendationSection({
  recommendation
}: {
  recommendation: Recommendation;
}) {
  const reasonCodes = [...new Set(recommendation.reason_codes)];

  return (
    <section className="detail-section recommendation" aria-labelledby="recommendation-heading">
      <p className="panel-kicker">Approval + critic</p>
      <h3 id="recommendation-heading">Recommendation</h3>
      <p>{recommendation.summary}</p>
      <div className="recommendation-meta">
        <span>Final route: {recommendation.final_route}</span>
        <span>Decided by: {recommendation.decided_by}</span>
        <span>Critique revisions: {recommendation.reflection_count}</span>
      </div>
      {reasonCodes.length ? (
        <ul className="reason-codes" aria-label="Recommendation reason codes">
          {reasonCodes.map((code) => (
            <li key={code}>{code}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
