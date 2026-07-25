"use client";

import { useEffect, useRef } from "react";

import { ReviewPanel } from "@/components/features/ReviewPanel";
import { FindingsSection } from "@/components/features/run-detail/FindingsSection";
import { InvoiceDetails } from "@/components/features/run-detail/InvoiceDetails";
import { RecommendationSection } from "@/components/features/run-detail/RecommendationSection";
import { ReviewRecord } from "@/components/features/run-detail/ReviewRecord";
import { RunDetailSkeleton } from "@/components/features/run-detail/RunDetailSkeleton";
import { RunOutcome } from "@/components/features/run-detail/RunOutcome";
import { TimelineSection } from "@/components/features/run-detail/TimelineSection";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { RunDetail } from "@/types/api";

interface RunDetailPanelProps {
  detail: RunDetail | null;
  focusVersion: number;
  loading?: boolean;
  reviewPending: boolean;
  selectedRunName?: string | null;
  onReview: (decision: "approve" | "reject", reason: string) => void;
}

export function RunDetailPanel({
  detail,
  focusVersion,
  loading = false,
  reviewPending,
  selectedRunName = null,
  onReview
}: RunDetailPanelProps) {
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (focusVersion > 0) {
      headingRef.current?.focus();
    }
  }, [focusVersion]);

  if (loading && !detail) {
    return <RunDetailSkeleton selectedRunName={selectedRunName} />;
  }

  if (!detail) {
    return (
      <section
        className="detail-panel detail-empty"
        aria-busy="false"
        aria-labelledby="run-detail-heading"
      >
        <p className="panel-kicker">Selected run</p>
        <h2 id="run-detail-heading">Run details</h2>
        <p>
          Select a recent run or process an invoice to inspect its decision trail.
        </p>
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

      <RunOutcome detail={detail} />
      {detail.invoice ? <InvoiceDetails invoice={detail.invoice} /> : null}
      <FindingsSection findings={detail.findings} />
      {detail.recommendation ? (
        <RecommendationSection recommendation={detail.recommendation} />
      ) : null}
      {detail.status === "review_required" && !detail.review ? (
        <ReviewPanel
          key={detail.run_id}
          invoiceNumber={detail.invoice?.invoice_number ?? null}
          invoiceTotal={detail.invoice?.total ?? null}
          pending={reviewPending}
          onReview={onReview}
        />
      ) : null}
      {detail.review ? (
        <ReviewRecord
          review={detail.review}
          pending={reviewPending}
          onReview={onReview}
        />
      ) : null}
      <TimelineSection
        defaultExpanded={
          detail.status === "queued" ||
          detail.status === "running" ||
          detail.status === "failed"
        }
        events={detail.events}
      />
    </article>
  );
}
