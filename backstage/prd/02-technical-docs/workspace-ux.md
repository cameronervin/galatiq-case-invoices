# Workspace UX Specification

## Product Experience

The frontend is an operational invoice-processing workspace, not a marketing
page. It supports one clear loop: upload, monitor, inspect, review when required,
and understand the final outcome.

## Information Architecture

Desktop:

```text
┌──────────────────────────────────────────────────────────────┐
│ Invoice Processing                         API status        │
├──────────────────────┬───────────────────────────────────────┤
│ Upload               │ Selected run                          │
│ Recent runs          │ Stage timeline                        │
│                      │ Invoice summary                       │
│                      │ Findings / review / final outcome     │
└──────────────────────┴───────────────────────────────────────┘
```

Narrow layouts stack upload, selected run, and recent runs without horizontal
scrolling. Keep current neutral design tokens and introduce semantic workflow
tokens only for implemented states.

## Required Components

| Component | Responsibility |
| --- | --- |
| `InvoiceUploader` | Drag/drop and file picker, format/size hint, local validation, submit state |
| `RecentRuns` | Newest-first run summaries, selection, status labels |
| `RunWorkspace` | Empty/loading/error container and polling lifecycle |
| `StageTimeline` | Ordered safe events and current stage |
| `InvoiceSummary` | Vendor, number, dates, money, and line items with restrained disclosure |
| `FindingsPanel` | Warning/blocking grouping, codes, plain explanations, expected/actual where safe |
| `ReviewPanel` | Recommendation, reasons, approve-and-mock-pay/reject actions, required reason |
| `OutcomePanel` | Completed payment reference, rejection reasons, or failed retry action |
| Local UI primitives | Button, badge, panel, form field, alert, dialog/confirmation |

Do not add a state-management or design-system dependency. Use component state,
typed API functions, and existing CSS/Tailwind capabilities.

## State Behavior

### Empty

- Explain supported formats and 10 MB limit.
- Primary action is `Choose invoice`.
- Do not imply processing has begun.

### Uploading and queued

- Disable duplicate upload submission while request is pending.
- Announce success/error in an accessible live region.
- On creation/deduplication, select the returned run and show queued state.

### Processing

- Display current stage and completed timeline events.
- Poll run detail every two seconds.
- Prevent overlapping polls and stop when unmounted or inactive.
- Preserve the last successful state on transient polling failure and offer retry.

### Review required

- Lead with why human judgment is required.
- Show invoice summary, warnings, and approval recommendation.
- Require a 3–500 character reason for either decision.
- Approval button label is `Approve and mock pay`.
- Before approval, show an explicit confirmation naming that payment is simulated
  and will retain the original currency.
- Disable both decisions while a request is pending; announce the result.

### Rejected

- Distinguish policy rejection from human rejection.
- Show reason codes/plain explanations and a path to upload a corrected invoice.
- Never show a payment action.

### Failed

- Show a safe error and whether retry is eligible.
- Retry requires confirmation, then returns the view to queued.
- Configuration errors direct the operator to local setup without exposing keys.

### Completed

- Show approval source, mock payment status/reference, and completion time.
- Clearly label the payment as simulated.

## Status Presentation

| Status | Label | Tone |
| --- | --- | --- |
| queued | Queued | Neutral |
| extracting / validating / deciding / paying | In progress | Accent |
| review_required | Review required | Warning |
| rejected | Rejected | Danger |
| failed | Failed | Danger |
| completed | Completed | Success |

Color is never the only status indicator. Pair semantic color with text and,
where used, a local icon or shape.

## Accessibility

- Use semantic headings, landmarks, labels, lists, tables, and buttons.
- Maintain visible `:focus-visible` treatment and logical tab order.
- Drop zone remains a labeled native file input interaction.
- Associate review reason errors with the field.
- Use `aria-live` for upload/review/retry results, not continuous polling noise.
- Move focus to the selected run heading after a new submission and to the
  review/result heading after a completed action.
- Respect `prefers-reduced-motion`; no essential information depends on animation.
- Preserve readable contrast and 44px approximate interactive targets.

## API Client Contract

Frontend types mirror API response models. Network functions live behind the
existing API client boundary:

```text
createRun(file)
listRuns({limit, offset, status?})
getRun(runId)
reviewRun(runId, {decision, reason})
retryRun(runId)
```

`ApiClientError` retains HTTP status and safe API error code/message. Components
do not parse unknown provider or server payloads.

## Responsive and Visual QA

Verify at representative widths near 1440px, 768px, and 375px. Inspect empty,
active, review, rejected, failed, and completed states. Confirm no clipped text,
unreadable tables, overflow, ambiguous controls, focus loss, or layout shift that
hides the current status.

