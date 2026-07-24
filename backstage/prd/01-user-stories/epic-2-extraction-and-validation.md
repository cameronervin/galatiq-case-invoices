# Epic 2 — Extraction and Validation

## Outcome

Every supported document becomes a typed invoice or an explicit failure, and
deterministic validation blocks missing, malformed, unavailable, or suspicious
data before approval.

## Stories

### US-06 — Extract a normalized invoice

**As a** member of accounts payable  
**I want** to extract consistent fields from every supported format  
**So that** downstream rules do not depend on document layout.

See the [master story](./_master-user-stories.md#us-06--extract-a-normalized-invoice).

### US-07 — Surface missing or uncertain extraction

**As a** member of accounts payable  
**I want** to see missing and corrected fields explicitly  
**So that** the system never hides assumptions in financial data.

See the [master story](./_master-user-stories.md#us-07--surface-missing-or-uncertain-extraction).

### US-08 — Validate inventory availability

**As a** member of accounts payable  
**I want** to validate invoice items against mock inventory  
**So that** unknown, unavailable, or excessive quantities are stopped.

See the [master story](./_master-user-stories.md#us-08--validate-inventory-availability).

### US-09 — Validate integrity and suspicious data

**As a** member of accounts payable  
**I want** to detect malformed totals, dates, quantities, and payment language  
**So that** invalid or suspicious invoices cannot reach payment.

See the [master story](./_master-user-stories.md#us-09--validate-integrity-and-suspicious-data).

## Primary Journey

1. Ingestion loads bounded source data without putting raw content in graph state.
2. A deterministic loader handles structured formats; the configured provider
   extracts unstructured text into the same Pydantic contract.
3. Extraction assessment produces warnings or requests at most two repairs.
4. Validation aggregates normalized items and compares them with SQLite inventory.
5. Integrity and risk rules produce stable warning or blocking findings.

## Edge Cases

| Case | Expected behavior |
| --- | --- |
| Empty vendor or due date | Preserve `null`; blocking required-field finding |
| `Widget A` / `Gadget X` | Normalize through explicit alias and emit warning when appropriate |
| Repeated lines for one item | Aggregate quantity before checking stock |
| Negative quantity or total | Blocking data-integrity finding |
| Total discrepancy above $0.01 | Blocking total-mismatch finding |
| Text-bearing PDF with OCR-like `O/0` errors | Correct only with evidence; warning and review |
| Image-only or encrypted PDF | Explicit unsupported-PDF failure |
| XML entity expansion attempt | Reject during hardened parsing |
