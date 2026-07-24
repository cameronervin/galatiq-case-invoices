"use client";

import { useCallback, useState } from "react";

import { ApiClientError, reviewRun } from "@/lib/api/client";
import type { RunDetail, RunSummary } from "@/types/api";

import { messageFor, type RunFeedback } from "./feedback";

export type ReviewDecision = "approve" | "reject";

interface UseRunReviewOptions {
  detail: RunDetail | null;
  mergeRuns: (runs: RunSummary[]) => void;
  onReconciled: () => void;
  reconcileRun: (runId: string) => Promise<RunDetail | null>;
  refreshRuns: () => Promise<unknown>;
  selectedRunId: string | null;
}

export function useRunReview({
  detail,
  mergeRuns,
  onReconciled,
  reconcileRun,
  refreshRuns,
  selectedRunId
}: UseRunReviewOptions) {
  const [feedbackByRun, setFeedbackByRun] = useState<
    Record<string, RunFeedback>
  >({});
  const [reviewingRunIds, setReviewingRunIds] = useState<ReadonlySet<string>>(
    () => new Set()
  );

  const submitReview = useCallback(
    async (decision: ReviewDecision, reason: string) => {
      if (!detail || detail.run_id !== selectedRunId) {
        return;
      }
      const runId = detail.run_id;
      setReviewingRunIds((current) => withSetValue(current, runId));
      setFeedbackByRun((current) => ({ ...current, [runId]: {} }));
      try {
        const summary = await reviewRun(runId, { decision, reason });
        mergeRuns([summary]);
        const reconciled = await reconcileRun(runId);
        if (reconciled) {
          onReconciled();
        }
        setFeedbackByRun((current) => ({
          ...current,
          [runId]: { notice: "Review recorded. The worker will resume this run." }
        }));
      } catch (error: unknown) {
        if (error instanceof ApiClientError && [409, 503].includes(error.status)) {
          const authoritativeRunId = error.runId ?? runId;
          await Promise.allSettled([
            reconcileRun(authoritativeRunId),
            refreshRuns()
          ]);
        }
        setFeedbackByRun((current) => ({
          ...current,
          [runId]: { error: messageFor(error) }
        }));
      } finally {
        setReviewingRunIds((current) => withoutSetValue(current, runId));
      }
    },
    [detail, mergeRuns, onReconciled, reconcileRun, refreshRuns, selectedRunId]
  );

  return {
    selectedFeedback: selectedRunId
      ? feedbackByRun[selectedRunId]
      : undefined,
    reviewingSelectedRun: selectedRunId
      ? reviewingRunIds.has(selectedRunId)
      : false,
    submitReview
  };
}

function withSetValue(
  current: ReadonlySet<string>,
  value: string
): ReadonlySet<string> {
  const next = new Set(current);
  next.add(value);
  return next;
}

function withoutSetValue(
  current: ReadonlySet<string>,
  value: string
): ReadonlySet<string> {
  const next = new Set(current);
  next.delete(value);
  return next;
}
