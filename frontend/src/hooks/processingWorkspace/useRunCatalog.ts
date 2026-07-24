"use client";

import { useCallback, useRef, useState } from "react";

import { listRuns } from "@/lib/api/client";
import type { RunDetail, RunSummary } from "@/types/api";

import { messageFor } from "./feedback";
import { mergeRunSummaries, withoutKey } from "./runSummaries";

export function useRunCatalog() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [detailErrors, setDetailErrors] = useState<Record<string, string>>({});
  const listRequestIdRef = useRef(0);

  const mergeRuns = useCallback((incoming: RunSummary[]) => {
    setRuns((current) => mergeRunSummaries(current, incoming));
  }, []);

  const acceptDetail = useCallback((detail: RunDetail) => {
    setRuns((current) => mergeRunSummaries(current, [detail]));
    setDetailErrors((current) => withoutKey(current, detail.run_id));
  }, []);

  const recordDetailError = useCallback((error: unknown, runId: string) => {
    setDetailErrors((current) => ({ ...current, [runId]: messageFor(error) }));
  }, []);

  const refresh = useCallback(async () => {
    const requestId = ++listRequestIdRef.current;
    try {
      const response = await listRuns({ limit: 20 });
      const applied = requestId === listRequestIdRef.current;
      if (applied) {
        mergeRuns(response.items);
        setListError("");
        setLoading(false);
      }
      return { applied, items: response.items };
    } catch (error: unknown) {
      if (requestId === listRequestIdRef.current) {
        setListError(messageFor(error));
      }
      throw error;
    }
  }, [mergeRuns]);
  const detailErrorFor = useCallback(
    (runId: string | null) => (runId ? detailErrors[runId] : undefined),
    [detailErrors]
  );
  const finishLoading = useCallback(() => setLoading(false), []);

  return {
    acceptDetail,
    detailErrorFor,
    finishLoading,
    listError,
    loading,
    mergeRuns,
    recordDetailError,
    refresh,
    runs
  };
}
