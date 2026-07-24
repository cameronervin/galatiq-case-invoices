# Workspace UX

The optional Next.js workspace supports upload, newest-run selection, active
polling, inspection, review, and final outcomes.

Desktop uses a recent-runs rail beside the selected run; narrow layouts stack
upload, selected run, and recent runs without horizontal scrolling.

## Required States

| State | Information | Action |
| --- | --- | --- |
| Empty | Supported formats and 10 MB limit | Choose invoice |
| Uploading/queued | Filename and status | None |
| Running | Stage and safe timeline | None |
| Review required | Invoice, warnings, recommendation | Approve and mock pay / reject |
| Rejected | Safe reason codes | Upload corrected invoice |
| Failed | Safe error | Upload invoice again |
| Completed | Approval and simulated payment | Inspect timeline |

There is no failed-workflow retry control. Active detail polls every two seconds
without overlap and stops on an undecided review or terminal status. A persisted
review waiting for worker resume continues polling. Transient polling errors keep
the selection safe and schedule another attempt; stale responses from a previous
selection are ignored.

Review requires a 3-500 character reason. Approval opens a confirmation that
explicitly says payment is simulated and preserves original currency. Pending
actions are disabled and announced; a `409` refreshes authoritative state. If the
decision was saved but queue dispatch failed, the persisted decision is shown with
one identical worker-resume retry action.

Use semantic headings, landmarks, labels, native controls, visible focus,
keyboard operation, status text in addition to color, `aria-live` for user
actions, focus movement after submission/action, 44px approximate targets, and
`prefers-reduced-motion`. Verify near 1440px, 768px, and 375px.
