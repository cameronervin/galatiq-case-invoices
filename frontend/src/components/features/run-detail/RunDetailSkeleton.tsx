interface RunDetailSkeletonProps {
  selectedRunName: string | null;
}

const factPlaceholders = Array.from({ length: 6 });
const tableRows = Array.from({ length: 3 });
const findingRows = Array.from({ length: 2 });

export function RunDetailSkeleton({ selectedRunName }: RunDetailSkeletonProps) {
  const loadingLabel = `Loading ${selectedRunName ?? "selected run"}…`;

  return (
    <article
      className="detail-panel detail-skeleton"
      aria-busy="true"
      aria-labelledby="run-detail-loading-status"
    >
      <p
        className="sr-only"
        id="run-detail-loading-status"
        role="status"
        aria-live="polite"
      >
        {loadingLabel}
      </p>

      <div aria-hidden="true">
        <header className="detail-header">
          <div className="skeleton-stack">
            <SkeletonLine className="skeleton-kicker" />
            <SkeletonLine className="skeleton-title" />
            <SkeletonLine className="skeleton-meta" />
          </div>
          <span className="skeleton-block skeleton-badge" />
        </header>

        <div className="outcome skeleton-outcome">
          <SkeletonLine />
        </div>

        <section className="detail-section">
          <SkeletonSectionHeading />
          <div className="invoice-facts">
            {factPlaceholders.map((_, index) => (
              <div key={index}>
                <SkeletonLine className="skeleton-fact-label" />
                <SkeletonLine className="skeleton-fact-value" />
              </div>
            ))}
          </div>
          <div className="table-wrap skeleton-table">
            {tableRows.map((_, index) => (
              <div className="skeleton-table-row" key={index}>
                <SkeletonLine />
                <SkeletonLine />
                <SkeletonLine />
                <SkeletonLine />
              </div>
            ))}
          </div>
        </section>

        <section className="detail-section">
          <SkeletonSectionHeading />
          <div className="findings-list">
            {findingRows.map((_, index) => (
              <div className="finding skeleton-finding" key={index}>
                <SkeletonLine className="skeleton-fact-label" />
                <div className="skeleton-stack">
                  <SkeletonLine />
                  <SkeletonLine className="skeleton-meta" />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="detail-section recommendation">
          <SkeletonLine className="skeleton-kicker" />
          <SkeletonLine className="skeleton-section-title" />
          <SkeletonLine className="skeleton-summary" />
          <div className="skeleton-disclosure">
            <SkeletonLine />
          </div>
        </section>

        <section className="detail-section history-section">
          <div className="skeleton-history">
            <SkeletonLine />
            <SkeletonLine className="skeleton-meta" />
          </div>
        </section>
      </div>
    </article>
  );
}

function SkeletonSectionHeading() {
  return (
    <div className="section-heading compact">
      <div className="skeleton-stack">
        <SkeletonLine className="skeleton-kicker" />
        <SkeletonLine className="skeleton-section-title" />
      </div>
      <span className="skeleton-block skeleton-count" />
    </div>
  );
}

function SkeletonLine({ className = "" }: { className?: string }) {
  return <span className={`skeleton-block skeleton-line ${className}`.trim()} />;
}
