"use client";

import { RecentRuns } from "@/components/features/RecentRuns";
import { RunDetailPanel } from "@/components/features/RunDetailPanel";
import { UploadPanel } from "@/components/features/UploadPanel";
import { useProcessingWorkspace } from "@/hooks/useProcessingWorkspace";

export function ProcessingWorkspace() {
  const workspace = useProcessingWorkspace();

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

      <UploadPanel
        pending={workspace.uploadPending}
        onUpload={workspace.submitInvoice}
      />

      <div className="announcement" aria-live="polite" aria-atomic="true">
        {workspace.errors.map((error) => (
          <p className="alert alert-error" key={error}>
            {error}
          </p>
        ))}
        {workspace.notices.map((notice) => (
          <p className="alert alert-success" key={notice}>
            {notice}
          </p>
        ))}
      </div>

      <div className="workspace-grid">
        <RunDetailPanel
          detail={workspace.detail}
          focusVersion={workspace.focusVersion}
          loading={workspace.detailLoading}
          reviewPending={workspace.reviewingSelectedRun}
          selectedRunName={workspace.selectedRunName}
          onReview={workspace.submitReview}
        />
        <RecentRuns
          loading={workspace.loadingRuns}
          runs={workspace.runs}
          selectedRunId={workspace.selectedRunId}
          onSelect={workspace.selectRun}
        />
      </div>
    </main>
  );
}
