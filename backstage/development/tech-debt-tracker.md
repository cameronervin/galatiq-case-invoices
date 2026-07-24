# Technical-Debt Tracker

The take-home implementation intentionally defers the following production work:

- Authentication, authorization, tenant isolation, and audit-log export.
- Durable object storage, malware scanning, OCR service integration, and retention policy.
- Live inventory/pricing/vendor systems, FX conversion, and inventory mutation.
- A real banking integration, payment reconciliation, and human maker/checker controls.
- Horizontal worker scaling and database/server upgrades beyond local SQLite.

These are out of V1 scope rather than hidden prerequisites for the local demo.

## Architecture audit follow-ups

The July 2026 architecture cleanup deliberately deferred changes that alter
durability or production operating semantics:

- Add recoverable execution and review-resume leases so worker death after a
  claim cannot leave a run permanently `running` or consume `resume_pending`.
- Make mock-payment finalization and terminal run/event persistence atomic, or
  add explicit reconciliation for crashes between those writes.
- Enforce the workflow time budget after provider calls and immediately before
  payment; pass critique feedback and the rejected proposal into an explicit
  approval-revision operation.
- Replace manually maintained frontend runtime decoders with generated runtime
  schemas when the API toolchain supports them; add automated accessibility and
  1440/768/375 browser coverage before further visual-system changes.
- Populate event `duration_ms` from a clock-backed stage recorder so the public
  latency field matches the observability documentation.
