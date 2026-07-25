# Agent Workflow

## Roles and routing

```text
ingest -> extraction -> validation -> approval -> critic -> policy
                                                        | blocking -> reject
                                                        | exception -> review
                                                        | clean -> payment -> finalize
```

1. Ingest loads bounded PDF, TXT, JSON, CSV, or XML input. Structured formats use
   deterministic adapters; TXT and text-bearing PDF use the selected provider.
2. Extraction produces typed `InvoiceData` and permits one repair, for at most
   two provider attempts.
3. Validation applies invoice-integrity rules and a read-only inventory lookup,
   then records ordered findings and observable tool events.
4. Approval proposes a route and reason codes; the critic may request one
   revision.
5. Deterministic policy owns the final route and records any model override.
6. Review checkpoints exceptions for a human decision. Payment creates and
   succeeds one simulated payment after an automatic or human approval.

## Deterministic controls

- Any blocking finding rejects.
- A warning, non-USD currency, or total above $10,000 requires human review.
- Otherwise the run proceeds to simulated payment.

The model may explain and critique, but cannot weaken these controls or invoke
payment. The whole workflow has a configurable 300-second default deadline.
Typed graph state excludes credentials, prompts, source paths, raw provider
payloads, documents, and hidden reasoning.

## Human review and resume

Review changes the run to `review_required` and checkpoints under
`thread_id=run_id`. The API atomically stores the first approve/reject decision
with `resume_pending=true`. An identical unresolved submission may redispatch;
a conflicting or completed decision returns `409`. The worker claims the pending
review before resuming the checkpointed graph.

## Provider boundary

Offline mode is deterministic and covers the fixture demo without network
access. Optional Grok mode uses structured Pydantic output, provider storage
disabled, a 45-second request timeout, one adapter-level transient retry, and no
provider-hosted tools. A requested live provider never silently falls back.

## Scope boundary

- **Implemented:** explicit workflow roles, typed artifacts, bounded repair and
  revision, deterministic routing, human interrupt/resume, and provider adapters.
- **Take-home default:** offline inference plus local inventory and payment tools
  make evaluation reproducible.
- **Production follow-up:** OCR, prompt/model evaluation and versioning, richer
  document handling, monitoring, and integration-specific approval policy.

See [quality, security, and roadmap](06-quality-security-and-roadmap.md) for test
coverage and known limitations.
