# Canonical User Stories

## US-01 — Process an invoice from the CLI

The processor can run the documented command without Valkey or network access.
Supported, non-empty local files produce one safe pretty result by default or one
compact JSON result with `--format json`. Invalid input, configuration, workflow
failure, and timeout use documented exit codes. Local paths never appear in
output.

## US-02 — Upload and track a run

The workspace accepts supported files, creates or deduplicates an authoritative
run, lists the newest runs, and polls active detail. A new run returns `202`; a
same-profile duplicate returns `200` with `deduplicated=true`.

## US-03 — Extract normalized invoice data

Structured formats load deterministically. TXT and PDF use the configured
provider. Money is exact, missing values remain explicit, raw source/model data
does not enter graph state, and extraction repair is limited to one attempt.

## US-04 — Validate inventory and integrity

The validation agent invokes the read-only inventory tool, applies exact aliases,
aggregates repeated items, and emits ordered stable findings for missing/invalid
data, totals, dates, suspicious language, unknown items, zero stock, and excessive
stock. Validation never mutates inventory.

## US-05 — Recommend and critique approval

The approval agent proposes a typed route and safe explanation from normalized
data and findings. The critic checks completeness, policy consistency, and
unsupported claims. At most one revision is allowed. Raw reasoning is not stored.

## US-06 — Enforce deterministic policy

Any blocker rejects. Any warning, non-USD currency, or total above $10,000
requires review. Otherwise the invoice is automatically approved. Model
disagreement is recorded as `POLICY_OVERRIDE` and cannot weaken policy.

## US-07 — Review an exception

Review requires `approve` or `reject` and a 3-500 character reason. The first
decision wins. Repeating the same pending decision redispatches resume
idempotently; a conflicting or completed decision returns `409`. Approval clearly
confirms that the next action is simulated payment.

## US-08 — Execute mock payment or rejection

Only an approved persisted run may invoke payment. One payment record per run
prevents duplicate execution. Rejection and payment outcomes contain stable codes
and safe summaries. Every terminal result deletes its staged source.

## US-09 — Inspect safe observability

The run detail and UI show status, stage, normalized invoice, findings,
recommendation, review, payment, and ordered events when available. Logs and
public outputs exclude sensitive/internal fields.

## US-10 — Configure offline or Grok inference

Offline inference is deterministic and requires no key. Grok requires an explicit
provider setting and `XAI_API_KEY`; configuration errors never fall back silently.
Tests never require network access or paid credentials.

## US-11 — Use an accessible workspace

Upload, active, review, rejected, failed, and completed states are distinct and
usable by keyboard at narrow and desktop widths. Status is not color-only,
reduced-motion is respected, and approval requires explicit mock-payment
confirmation.

## Cross-Story Edge Cases

| Case | Required behavior |
| --- | --- |
| Same bytes and provider/model | Reuse the existing non-failed run |
| Changed revision or provider/model | Create a new run |
| Same bytes after failure | Create a new run |
| Duplicate worker delivery | Reuse persisted state and payment |
| Repeated identical pending review | Redispatch resume without changing decision |
| Conflicting review | Return `409` |
| Total exactly $10,000 | Automatic payment when otherwise clean |
| Total $10,000.01 | Human review |
| Current date after due date | Do not reject solely from wall-clock date |
