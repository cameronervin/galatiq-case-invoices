"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { RecentRuns } from "@/components/features/RecentRuns";
import { RunDetailPanel } from "@/components/features/RunDetailPanel";
import {
  ApiClientError,
  createRun,
  getRun,
  listRuns,
  reviewRun
} from "@/lib/api/client";
import type { RunDetail, RunSummary } from "@/types/api";

const acceptedExtensions = new Set(["csv", "json", "xml", "txt", "pdf"]);
const maxFileBytes = 10 * 1024 * 1024;

export function ProcessingWorkspace() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [focusVersion, setFocusVersion] = useState(0);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refreshRuns = useCallback(async () => {
    const response = await listRuns({ limit: 20 });
    setRuns(response.items);
    setSelectedRunId((current) => current ?? response.items[0]?.run_id ?? null);
  }, []);

  useEffect(() => {
    let active = true;
    void listRuns({ limit: 20 })
      .then((response) => {
        if (active) {
          setRuns(response.items);
          setSelectedRunId(response.items[0]?.run_id ?? null);
        }
      })
      .catch((requestError: unknown) => {
        if (active) {
          setError(messageFor(requestError));
        }
      })
      .finally(() => {
        if (active) {
          setLoadingRuns(false);
        }
      });
    return () => {
      active = false;
    };
  }, [refreshRuns]);

  useEffect(() => {
    if (!selectedRunId) {
      return;
    }
    const controller = new AbortController();
    void getRun(selectedRunId, controller.signal)
      .then(setDetail)
      .catch((requestError: unknown) => {
        if (!(requestError instanceof DOMException && requestError.name === "AbortError")) {
          setError(messageFor(requestError));
        }
      });
    return () => controller.abort();
  }, [selectedRunId]);

  useEffect(() => {
    if (!detail || !["queued", "running"].includes(detail.status)) {
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      void getRun(detail.run_id, controller.signal)
        .then((next) => {
          setDetail(next);
          setRuns((current) => replaceSummary(current, next));
        })
        .catch((requestError: unknown) => {
          if (!(requestError instanceof DOMException && requestError.name === "AbortError")) {
            setError(messageFor(requestError));
          }
        });
    }, 2000);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [detail]);

  async function submitInvoice(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    if (!file) {
      setError("Choose an invoice before processing.");
      return;
    }
    const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
    if (!acceptedExtensions.has(extension)) {
      setError("Choose a CSV, JSON, XML, TXT, or PDF invoice.");
      return;
    }
    if (file.size > maxFileBytes) {
      setError("The invoice must be 10 MB or smaller.");
      return;
    }

    setSubmitting(true);
    try {
      const created = await createRun(file);
      const nextDetail = await getRun(created.run_id);
      setSelectedRunId(created.run_id);
      setDetail(nextDetail);
      setFocusVersion((current) => current + 1);
      setRuns((current) => replaceSummary(current, created));
      setNotice(
        created.deduplicated
          ? "This invoice matched an existing run; no duplicate payment was created."
          : "Invoice accepted for processing."
      );
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      await refreshRuns();
    } catch (requestError: unknown) {
      setError(messageFor(requestError));
    } finally {
      setSubmitting(false);
    }
  }

  async function submitReview(decision: "approve" | "reject", reason: string) {
    if (!detail) {
      return;
    }
    setReviewing(true);
    setError("");
    setNotice("");
    try {
      await reviewRun(detail.run_id, { decision, reason });
      const nextDetail = await getRun(detail.run_id);
      setDetail(nextDetail);
      setRuns((current) => replaceSummary(current, nextDetail));
      setFocusVersion((current) => current + 1);
      setNotice("Review recorded. The worker will resume this run.");
    } catch (requestError: unknown) {
      if (requestError instanceof ApiClientError && requestError.status === 409) {
        const nextDetail = await getRun(detail.run_id);
        setDetail(nextDetail);
      }
      setError(messageFor(requestError));
    } finally {
      setReviewing(false);
    }
  }

  return (
    <main className="workspace">
      <header className="workspace-header">
        <div>
          <p className="eyebrow">Accounts payable · local prototype</p>
          <h1>Invoice processing workspace</h1>
          <p className="lede">
            Process a supplied invoice, inspect every decision, and resolve only the
            exceptions that need a person.
          </p>
        </div>
        <div className="environment-chip">
          <span aria-hidden="true" /> Offline-ready
        </div>
      </header>

      <form className="upload-card" onSubmit={submitInvoice}>
        <div>
          <p className="panel-kicker">New run</p>
          <h2>Process an invoice</h2>
          <p>CSV, JSON, XML, TXT, or PDF · up to 10 MB</p>
        </div>
        <div className="upload-actions">
          <label className="file-picker" htmlFor="invoice-file">
            <span>{file?.name ?? "Choose invoice"}</span>
            <input
              ref={fileInputRef}
              id="invoice-file"
              type="file"
              accept=".csv,.json,.xml,.txt,.pdf"
              aria-label="Choose invoice"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <button className="button button-primary" disabled={submitting} type="submit">
            {submitting ? "Submitting…" : "Process invoice"}
          </button>
        </div>
      </form>

      <div className="announcement" aria-live="polite" aria-atomic="true">
        {error ? <p className="alert alert-error">{error}</p> : null}
        {notice ? <p className="alert alert-success">{notice}</p> : null}
      </div>

      <div className="workspace-grid">
        <RunDetailPanel
          detail={detail}
          focusVersion={focusVersion}
          reviewPending={reviewing}
          onReview={submitReview}
        />
        <RecentRuns
          loading={loadingRuns}
          runs={runs}
          selectedRunId={selectedRunId}
          onSelect={(runId) => {
            setSelectedRunId(runId);
            setFocusVersion((current) => current + 1);
          }}
        />
      </div>
    </main>
  );
}

function replaceSummary(runs: RunSummary[], summary: RunSummary): RunSummary[] {
  return [summary, ...runs.filter((item) => item.run_id !== summary.run_id)]
    .sort((left, right) => right.created_at.localeCompare(left.created_at))
    .slice(0, 20);
}

function messageFor(error: unknown): string {
  return error instanceof Error ? error.message : "The request could not be completed.";
}
