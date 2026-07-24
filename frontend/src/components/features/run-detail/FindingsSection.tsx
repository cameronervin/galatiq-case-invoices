import type { Finding } from "@/types/api";

export function FindingsSection({ findings }: { findings: Finding[] }) {
  return (
    <section className="detail-section" aria-labelledby="findings-heading">
      <div className="section-heading compact">
        <div>
          <p className="panel-kicker">Validation</p>
          <h3 id="findings-heading">Findings</h3>
        </div>
        <span className="record-count">{findings.length}</span>
      </div>
      {findings.length ? (
        <ul className="findings-list">
          {findings.map((finding, index) => (
            <FindingRow key={`${finding.code}-${index}`} finding={finding} />
          ))}
        </ul>
      ) : (
        <p className="empty-state inset">No findings were recorded.</p>
      )}
    </section>
  );
}

function FindingRow({ finding }: { finding: Finding }) {
  return (
    <li className={`finding finding-${finding.severity}`}>
      <span className="finding-severity">{finding.severity}</span>
      <div>
        <strong>{finding.message}</strong>
        <p>
          {finding.code}
          {finding.field_path ? ` · ${finding.field_path}` : ""}
          {finding.item_line_number !== null ? ` · line ${finding.item_line_number}` : ""}
        </p>
      </div>
    </li>
  );
}
