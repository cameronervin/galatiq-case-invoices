# Epic 3 — Approval and Payment

## Outcome

The system produces a bounded, explainable recommendation, applies deterministic
policy, obtains human review when needed, and records at most one mock payment.

## Stories

### US-10 — Produce and critique an approval recommendation

**As a** VP reviewer  
**I want** to receive a reasoned and self-checked recommendation  
**So that** the system demonstrates judgment without bypassing policy.

See the [master story](./_master-user-stories.md#us-10--produce-and-critique-an-approval-recommendation).

### US-11 — Review an exception

**As a** VP reviewer  
**I want** to approve or reject invoices requiring judgment  
**So that** high-risk decisions remain human-controlled and auditable.

See the [master story](./_master-user-stories.md#us-11--review-an-exception).

### US-12 — Execute an idempotent mock payment

**As a** member of accounts payable  
**I want** to record payment only after valid approval  
**So that** the workflow completes safely without touching a real bank.

See the [master story](./_master-user-stories.md#us-12--execute-an-idempotent-mock-payment).

### US-13 — Record rejection with reasoning

**As a** member of accounts payable  
**I want** to see why an invoice was rejected  
**So that** I can correct the source or explain the outcome.

See the [master story](./_master-user-stories.md#us-13--record-rejection-with-reasoning).

## Decision Table

| Condition | Route | Payment eligibility |
| --- | --- | --- |
| Any blocking finding | Reject | Never |
| Clean USD total `<= 10000.00` | Automatic approval | Immediate mock payment |
| Clean USD total `> 10000.00` | Human review | Only after human approval |
| Any warning | Human review | Only after human approval |
| Currency other than USD | Human review | Original currency after human approval |
| Human rejection | Reject | Never |

## Edge Cases

| Case | Expected behavior |
| --- | --- |
| Model recommends approval despite blocker | Guardrail overrides to rejection |
| Critique never accepts proposal | Stop after two revisions and apply deterministic route |
| Worker resumes the same approval twice | First persisted review wins; no duplicate payment |
| Payment task is redelivered | Return existing payment attempt by idempotency key |
| Payment fails after attempt creation | Persist failed attempt and retry safely |
| Non-USD reviewer approves | Record original amount/currency; no FX fields |
