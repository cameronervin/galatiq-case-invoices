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
          <p className="eyebrow">Accounts payable</p>
          <h1>Invoice processing</h1>
          <p className="lede">
            Review processing outcomes and resolve the exceptions that need attention.
          </p>
        </div>
      </header>

      <UploadPanel
        pending={workspace.uploadPending}
        onUpload={workspace.submitInvoice}
      />

      {workspace.errors.length || workspace.notices.length ? (
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
      ) : null}

      <div className="workspace-grid">
        <RecentRuns
          loading={workspace.loadingRuns}
          runs={workspace.runs}
          selectedRunId={workspace.selectedRunId}
          onSelect={workspace.selectRun}
        />
        <RunDetailPanel
          detail={workspace.detail}
          focusVersion={workspace.focusVersion}
          loading={workspace.detailLoading}
          reviewPending={workspace.reviewingSelectedRun}
          selectedRunName={workspace.selectedRunName}
          onReview={workspace.submitReview}
        />
      </div>
    </main>
  );
}
