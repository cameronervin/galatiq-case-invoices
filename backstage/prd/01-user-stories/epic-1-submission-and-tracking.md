# Epic 1 — Submission and Tracking

## Outcome

An accounts-payable processor can submit a safe local document, receive one
authoritative run, and follow or retry that run without creating duplicate work.

## Stories

### US-01 — Submit an invoice from the CLI

**As a** member of accounts payable  
**I want** to submit a local invoice with the documented command  
**So that** I can receive a structured processing result without using the UI.

See the [master story](./_master-user-stories.md#us-01--submit-an-invoice-from-the-cli)
for binding acceptance criteria.

### US-02 — Upload an invoice in the workspace

**As a** member of accounts payable  
**I want** to upload a supported invoice in the browser  
**So that** I can start processing without terminal access.

See the [master story](./_master-user-stories.md#us-02--upload-an-invoice-in-the-workspace)
for binding acceptance criteria.

### US-03 — Track current and recent runs

**As a** member of accounts payable  
**I want** to see current progress and recent runs  
**So that** I know what needs attention and what has finished.

See the [master story](./_master-user-stories.md#us-03--track-current-and-recent-runs)
for binding acceptance criteria.

### US-04 — Deduplicate exact submissions

**As a** member of accounts payable  
**I want** to avoid processing an identical invoice twice  
**So that** retries and accidental resubmissions cannot duplicate payment.

See the [master story](./_master-user-stories.md#us-04--deduplicate-exact-submissions)
for binding acceptance criteria.

### US-05 — Retry a failed run

**As a** member of accounts payable  
**I want** to retry a failed run while its source remains available  
**So that** a transient provider or worker failure does not require re-entry.

See the [master story](./_master-user-stories.md#us-05--retry-a-failed-run)
for binding acceptance criteria.

## Primary Journey

1. The processor chooses a supported local file in the CLI or workspace.
2. The server validates size/type, computes the content hash, and either reuses
   an existing run or creates a new queued run.
3. The worker advances persisted stages while the client polls run detail.
4. Processing ends in completed, rejected, review-required, or failed.
5. Failed runs may be retried while the staged source remains eligible.

## Edge Cases

| Case | Expected behavior |
| --- | --- |
| Missing or unsupported CLI file | Structured invalid-input error; no run |
| API file larger than 10 MB | `413`; no staged file or run |
| Exact duplicate while original is active | Return original run and current state |
| Exact duplicate after completion | Return original terminal result; never pay again |
| Same invoice number with changed content | Create a new run |
| Retry after staged source expiry | `409 SOURCE_UNAVAILABLE` |
| Unknown run ID | `404 RUN_NOT_FOUND` |
