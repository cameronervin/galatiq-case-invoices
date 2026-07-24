"use client";

import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { getRun } from "@/lib/api/client";
import type { RunDetail } from "@/types/api";

const pollIntervalMs = 2000;

interface SelectedRunState {
  selectedRunId: string | null;
  detail: RunDetail | null;
  loading: boolean;
}

type SelectedRunAction =
  | { type: "select"; runId: string }
  | { type: "loading"; runId: string }
  | { type: "loaded"; detail: RunDetail }
  | { type: "failed"; runId: string };

interface UseSelectedRunOptions {
  onDetail: (detail: RunDetail) => void;
  onError: (error: unknown, runId: string) => void;
}

export function useSelectedRun({ onDetail, onError }: UseSelectedRunOptions) {
  const [state, dispatch] = useReducer(selectedRunReducer, {
    selectedRunId: null,
    detail: null,
    loading: false
  });
  const [pollAttempt, setPollAttempt] = useState(0);
  const selectedRunIdRef = useRef<string | null>(null);

  const selectRun = useCallback((runId: string) => {
    selectedRunIdRef.current = runId;
    dispatch({ type: "select", runId });
  }, []);

  const selectRunIfNone = useCallback(
    (runId: string) => {
      if (selectedRunIdRef.current === null) {
        selectRun(runId);
      }
    },
    [selectRun]
  );

  const acceptDetail = useCallback(
    (detail: RunDetail) => {
      if (selectedRunIdRef.current !== detail.run_id) {
        return false;
      }
      dispatch({ type: "loaded", detail });
      onDetail(detail);
      return true;
    },
    [onDetail]
  );

  const reconcileRun = useCallback(
    async (runId: string): Promise<RunDetail | null> => {
      const detail = await getRun(runId);
      return acceptDetail(detail) ? detail : null;
    },
    [acceptDetail]
  );

  useEffect(() => {
    const runId = state.selectedRunId;
    if (!runId) {
      return;
    }
    const controller = new AbortController();
    let ignore = false;
    dispatch({ type: "loading", runId });
    void getRun(runId, controller.signal)
      .then((detail) => {
        if (!ignore) {
          acceptDetail(detail);
        }
      })
      .catch((error: unknown) => {
        if (!ignore && !isAbortError(error)) {
          dispatch({ type: "failed", runId });
          onError(error, runId);
        }
      });
    return () => {
      ignore = true;
      controller.abort();
    };
  }, [acceptDetail, onError, state.selectedRunId]);

  useEffect(() => {
    const detail = state.detail;
    const runId = state.selectedRunId;
    if (!detail || detail.run_id !== runId || !shouldPoll(detail)) {
      return;
    }
    const controller = new AbortController();
    let ignore = false;
    const timer = globalThis.setTimeout(() => {
      void getRun(detail.run_id, controller.signal)
        .then((next) => {
          if (!ignore) {
            acceptDetail(next);
          }
        })
        .catch((error: unknown) => {
          if (!ignore && !isAbortError(error)) {
            onError(error, detail.run_id);
            setPollAttempt((attempt) => attempt + 1);
          }
        });
    }, pollIntervalMs);
    return () => {
      ignore = true;
      globalThis.clearTimeout(timer);
      controller.abort();
    };
  }, [acceptDetail, onError, pollAttempt, state.detail, state.selectedRunId]);

  return {
    detail: state.detail,
    loading: state.loading,
    reconcileRun,
    selectedRunId: state.selectedRunId,
    selectRun,
    selectRunIfNone
  };
}

function selectedRunReducer(
  state: SelectedRunState,
  action: SelectedRunAction
): SelectedRunState {
  switch (action.type) {
    case "select":
      return { selectedRunId: action.runId, detail: null, loading: true };
    case "loading":
      return state.selectedRunId === action.runId ? { ...state, loading: true } : state;
    case "loaded":
      return state.selectedRunId === action.detail.run_id
        ? { ...state, detail: action.detail, loading: false }
        : state;
    case "failed":
      return state.selectedRunId === action.runId
        ? { ...state, detail: null, loading: false }
        : state;
  }
}

function shouldPoll(detail: RunDetail): boolean {
  return (
    detail.status === "queued" ||
    detail.status === "running" ||
    (detail.status === "review_required" && Boolean(detail.review?.resume_pending))
  );
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}
