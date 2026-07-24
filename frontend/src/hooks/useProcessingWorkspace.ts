"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useSelectedRun } from "@/hooks/useSelectedRun";
import type { RunDetail } from "@/types/api";

import { uniqueMessages } from "./processingWorkspace/feedback";
import { useInvoiceSubmission } from "./processingWorkspace/useInvoiceSubmission";
import { useRunCatalog } from "./processingWorkspace/useRunCatalog";
import { useRunReview } from "./processingWorkspace/useRunReview";

export function useProcessingWorkspace() {
  const {
    acceptDetail,
    detailErrorFor,
    finishLoading,
    listError,
    loading,
    mergeRuns,
    recordDetailError,
    refresh,
    runs
  } = useRunCatalog();
  const [focusVersion, setFocusVersion] = useState(0);
  const focusRunIdRef = useRef<string | null>(null);

  const handleDetail = useCallback(
    (detail: RunDetail) => {
      acceptDetail(detail);
      if (focusRunIdRef.current === detail.run_id) {
        focusRunIdRef.current = null;
        setFocusVersion((current) => current + 1);
      }
    },
    [acceptDetail]
  );
  const {
    detail,
    loading: detailLoading,
    reconcileRun,
    selectedRunId,
    selectRun,
    selectRunIfNone
  } = useSelectedRun({
    onDetail: handleDetail,
    onError: recordDetailError
  });

  useEffect(() => {
    let active = true;
    void refresh()
      .then(({ applied, items }) => {
        if (active && applied) {
          const newestRunId = items[0]?.run_id;
          if (newestRunId) {
            selectRunIfNone(newestRunId);
          }
        }
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) {
          finishLoading();
        }
      });
    return () => {
      active = false;
    };
  }, [finishLoading, refresh, selectRunIfNone]);

  const selectRunWithFocus = useCallback(
    (runId: string) => {
      focusRunIdRef.current = runId;
      selectRun(runId);
    },
    [selectRun]
  );
  const upload = useInvoiceSubmission({
    mergeRuns,
    reconcileRun,
    refreshRuns: refresh,
    selectRun: selectRunWithFocus
  });
  const refocusDetail = useCallback(
    () => setFocusVersion((current) => current + 1),
    []
  );
  const review = useRunReview({
    detail,
    mergeRuns,
    onReconciled: refocusDetail,
    reconcileRun,
    refreshRuns: refresh,
    selectedRunId
  });

  const selectedRunName = useMemo(
    () =>
      detail?.source_filename ??
      runs.find((run) => run.run_id === selectedRunId)?.source_filename ??
      null,
    [detail?.source_filename, runs, selectedRunId]
  );
  const errors = uniqueMessages([
    upload.feedback.error,
    listError,
    review.selectedFeedback?.error,
    detailErrorFor(selectedRunId)
  ]);
  const notices = uniqueMessages([
    upload.feedback.notice,
    review.selectedFeedback?.notice
  ]);

  return {
    detail,
    detailLoading,
    errors,
    focusVersion,
    loadingRuns: loading,
    notices,
    reviewingSelectedRun: review.reviewingSelectedRun,
    runs,
    selectedRunId,
    selectedRunName,
    selectRun: selectRunWithFocus,
    submitInvoice: upload.submitInvoice,
    submitReview: review.submitReview,
    uploadPending: upload.pending
  };
}
