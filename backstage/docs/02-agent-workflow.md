# Agent Workflow

## Roles and graph

The graph makes each responsibility observable rather than hiding the workflow in
one model call:

```text
ingest -> extraction -> validation -> approval -> critic -> policy
                                                        | blocking -> reject
                                                        | exception -> review
                                                        | clean -> payment -> finalize
```

1. The extraction agent produces typed `InvoiceData`. Structured JSON, CSV, and
   XML use deterministic loaders; TXT and text-bearing PDF use the selected
   provider.
2. The validation agent calls the registered read-only inventory lookup and adds
   deterministic integrity, normalization, stock, date, and reconciliation
   findings. Loader evidence supplies bounded suspicious-language findings, so
   validation never re-reads staged binary content. Start and successful lookup
   events are recorded separately.
3. The approval agent proposes a route and reason codes.
4. The critic evaluates that proposal. One revision is allowed.
5. Deterministic policy owns the final route and records an override when it
   differs from the proposal.
6. The payment agent creates and succeeds one simulated payment only after an
   approved route or persisted human approval.

## Typed state and bounded correction

Graph state contains public workflow artifacts and loop counts, not the source
path, provider credentials, prompts, raw provider payloads, or hidden reasoning.
Runtime dependencies are supplied separately through `AgentRuntimeContext`.
Graph nodes adapt those dependencies; deterministic policy and validation live in
focused modules that can be tested without LangGraph or SQLite.
The adapters are grouped by responsibility under `backend/app/agents/nodes`:
extraction owns ingest and bounded repair, validation owns deterministic checks,
approval owns critique and policy routing, review owns the durable interrupt, and
payment owns terminal payment or rejection. Shared state preconditions and the
workflow deadline are centralized in a small helper module.

Extraction permits at most one repair, for two provider attempts total. Approval
permits at most one revision after critique. The whole workflow has a 300-second
default deadline. These bounds make failure and cost behavior predictable.

## Deterministic policy

Policy runs after critique:

- Any blocking finding rejects.
- A warning, non-USD currency, or total above $10,000 requires human review.
- Otherwise the run is approved for mock payment.

The model can explain and critique, but it cannot weaken these controls or invoke
payment. Informational findings preserve provenance without changing the route.

## Human interrupt and resume

Review transitions the run to `review_required` and LangGraph checkpoints the
thread under `thread_id=run_id`. The API atomically stores the first review with
`resume_pending=true`. An identical unresolved submission may redispatch; a
conflicting or completed decision returns `409`. The worker claims the pending
review before resuming from the graph checkpoint.

## Provider boundary

The offline provider is deterministic and supports the full fixture demo without
network access. Optional Grok mode uses one owned client per provider/model
profile, Pydantic structured output, provider storage disabled, a 45-second
request timeout, one adapter-level transient retry, and no provider-hosted tools.
Static policy remains in trusted instructions; invoice content, repair feedback,
and current extraction remain untrusted input data. A requested Grok run never
silently falls back.

## Scope boundary

- **Implemented:** explicit extraction, validation, approval, critic, policy,
  review, rejection, payment, repair, and revision behavior.
- **Take-home default:** deterministic offline inference and local inventory/payment
  tools make the evaluation reproducible.
- **Production follow-up:** prompt/version evaluation, richer document/OCR
  handling, model monitoring, and integration-specific approval policies.

See [quality and security](06-quality-security-and-roadmap.md) for branch coverage
and [decisions](05-decisions-and-tradeoffs.md) for why policy owns payment routing.
