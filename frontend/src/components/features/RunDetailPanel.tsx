"use client";

import { useEffect, useRef } from "react";

import { ReviewPanel } from "@/components/features/ReviewPanel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Finding, Money, RunDetail } from "@/types/api";

interface RunDetailPanelProps {
  detail: RunDetail | null;
  focusVersion: number;
  reviewPending: boolean;
  onReview: (decision: "approve" | "reject", reason: string) => void;
}

export function RunDetailPanel({
  detail,
  focusVersion,
  reviewPending,
  onReview
}: RunDetailPanelProps) {
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (focusVersion > 0) {
      headingRef.current?.focus();
    }
  }, [focusVersion]);

  if (!detail) {
    return (
      <section className="detail-panel detail-empty" aria-labelledby="run-detail-heading">
        <p className="panel-kicker">Audit view</p>
        <h2 id="run-detail-heading">Run details</h2>
        <p>Select a recent run or process an invoice to inspect its decision trail.</p>
      </section>
    );
  }

  return (
    <article className="detail-panel" aria-labelledby="run-detail-heading">
      <header className="detail-header">
        <div>
          <p className="panel-kicker">Run details</p>
          <h2 ref={headingRef} id="run-detail-heading" tabIndex={-1}>
            {detail.source_filename}
          </h2>
          <p className="run-id">Run {detail.run_id}</p>
        </div>
        <StatusBadge status={detail.status} />
      </header>

      <Outcome detail={detail} />

      {detail.invoice ? (
        <section className="detail-section" aria-labelledby="invoice-heading">
          <div className="section-heading compact">
            <div>
              <p className="panel-kicker">Extracted record</p>
              <h3 id="invoice-heading">
                Invoice {detail.invoice.invoice_number ?? "number unavailable"}
              </h3>
            </div>
            <span className="confidence">{detail.invoice.extraction_confidence} confidence</span>
          </div>
          <dl className="invoice-facts">
            <Fact label="Vendor" value={detail.invoice.vendor_name} />
            <Fact label="Invoice date" value={detail.invoice.invoice_date} />
            <Fact label="Due date" value={detail.invoice.due_date} />
            <Fact label="Terms" value={detail.invoice.payment_terms} />
            <Fact label="Total" value={formatMoney(detail.invoice.total)} />
            <Fact label="Currency" value={detail.invoice.currency} />
          </dl>
          {detail.invoice.items.length ? (
            <div className="table-wrap">
              <table>
                <caption className="sr-only">Extracted invoice line items</caption>
                <thead>
                  <tr>
                    <th scope="col">Item</th>
                    <th scope="col">Qty</th>
                    <th scope="col">Unit price</th>
                    <th scope="col">Line total</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.invoice.items.map((item) => (
                    <tr key={item.line_number}>
                      <td>
                        <strong>{item.normalized_item_code ?? "Unmatched"}</strong>
                        <span>{item.source_name ?? `Line ${item.line_number}`}</span>
                      </td>
                      <td>{item.quantity ?? "—"}</td>
                      <td>{formatMoney(item.unit_price)}</td>
                      <td>{formatMoney(item.line_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      ) : null}

      <section className="detail-section" aria-labelledby="findings-heading">
        <div className="section-heading compact">
          <div>
            <p className="panel-kicker">Validation</p>
            <h3 id="findings-heading">Findings</h3>
          </div>
          <span className="record-count">{detail.findings.length}</span>
        </div>
        {detail.findings.length ? (
          <ul className="findings-list">
            {detail.findings.map((finding, index) => (
              <FindingRow key={`${finding.code}-${index}`} finding={finding} />
            ))}
          </ul>
        ) : (
          <p className="empty-state inset">No findings were recorded.</p>
        )}
      </section>

      {detail.recommendation ? (
        <section className="detail-section recommendation" aria-labelledby="recommendation-heading">
          <p className="panel-kicker">Approval + critic</p>
          <h3 id="recommendation-heading">Recommendation</h3>
          <p>{detail.recommendation.summary}</p>
          <div className="recommendation-meta">
            <span>Final route: {detail.recommendation.final_route}</span>
            <span>Decided by: {detail.recommendation.decided_by}</span>
            <span>Critique revisions: {detail.recommendation.reflection_count}</span>
          </div>
        </section>
      ) : null}

      {detail.status === "review_required" && !detail.review ? (
        <ReviewPanel pending={reviewPending} onReview={onReview} />
      ) : null}
      {detail.review ? (
        <section className="detail-section" aria-labelledby="review-record-heading">
          <p className="panel-kicker">Human decision</p>
          <h3 id="review-record-heading">
            {detail.review.decision === "approve" ? "Approved" : "Rejected"} by reviewer
          </h3>
          <p>{detail.review.reason}</p>
          {detail.review.resume_pending ? (
            <p className="pending-note">Recorded · waiting for worker resume</p>
          ) : null}
        </section>
      ) : null}

      <section className="detail-section" aria-labelledby="timeline-heading">
        <div className="section-heading compact">
          <div>
            <p className="panel-kicker">Observable workflow</p>
            <h3 id="timeline-heading">Timeline</h3>
          </div>
          <span className="record-count">{detail.events.length}</span>
        </div>
        {detail.events.length ? (
          <ol className="timeline">
            {detail.events.map((event) => (
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
      </section>
    </article>
  );
}

function Outcome({ detail }: { detail: RunDetail }) {
  if (detail.status === "completed" && detail.payment) {
    return (
      <section className="outcome outcome-success" aria-label="Payment outcome">
        <div>
          <p className="panel-kicker">Mock payment complete</p>
          <strong>{formatMoney(detail.payment.amount)}</strong>
        </div>
        <p>Reference {detail.payment.mock_reference ?? "recorded"}</p>
      </section>
    );
  }
  if (detail.status === "rejected") {
    return <p className="outcome outcome-rejected">Rejected safely; no payment was created.</p>;
  }
  if (detail.status === "failed") {
    return (
      <p className="outcome outcome-failed">
        {detail.error?.message ?? "Processing failed safely. Submit the source as a new run."}
      </p>
    );
  }
  if (detail.status === "review_required") {
    return <p className="outcome outcome-review">Payment is paused until a reviewer decides.</p>;
  }
  return <p className="outcome outcome-running">Processing stage: {detail.stage}</p>;
}

function Fact({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value ?? "—"}</dd>
    </div>
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

function formatMoney(money: Money | null): string {
  if (!money) {
    return "—";
  }
  return `${money.amount} ${money.currency}`;
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit"
  }).format(new Date(value));
}
