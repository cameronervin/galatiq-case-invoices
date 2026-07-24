"use client";

import { useCallback, useState } from "react";

import { ApiClientError, createRun } from "@/lib/api/client";
import type { RunDetail, RunSummary } from "@/types/api";

import { messageFor, type RunFeedback } from "./feedback";

interface UseInvoiceSubmissionOptions {
  mergeRuns: (runs: RunSummary[]) => void;
  reconcileRun: (runId: string) => Promise<RunDetail | null>;
  refreshRuns: () => Promise<unknown>;
  selectRun: (runId: string) => void;
}

export function useInvoiceSubmission({
  mergeRuns,
  reconcileRun,
  refreshRuns,
  selectRun
}: UseInvoiceSubmissionOptions) {
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState<RunFeedback>({});

  const submitInvoice = useCallback(
    async (file: File): Promise<boolean> => {
      setPending(true);
      setFeedback({});
      try {
        const created = await createRun(file);
        mergeRuns([created]);
        selectRun(created.run_id);
        setFeedback({
          notice: created.deduplicated
            ? "This invoice matched an existing run; no duplicate payment was created."
            : "Invoice accepted for processing."
        });
        void refreshRuns().catch(() => undefined);
        return true;
      } catch (error: unknown) {
        if (error instanceof ApiClientError && error.runId) {
          selectRun(error.runId);
          await Promise.allSettled([
            reconcileRun(error.runId),
            refreshRuns()
          ]);
        }
        setFeedback({ error: messageFor(error) });
        return false;
      } finally {
        setPending(false);
      }
    },
    [mergeRuns, reconcileRun, refreshRuns, selectRun]
  );

  return { feedback, pending, submitInvoice };
}
