# Technical-Debt Tracker

The take-home implementation intentionally defers the following production work:

- Authentication, authorization, tenant isolation, and audit-log export.
- Durable object storage, malware scanning, OCR service integration, and retention policy.
- Live inventory/pricing/vendor systems, FX conversion, and inventory mutation.
- A real banking integration, payment reconciliation, and human maker/checker controls.
- Horizontal worker scaling and database/server upgrades beyond local SQLite.

These are out of V1 scope rather than hidden prerequisites for the local demo.
