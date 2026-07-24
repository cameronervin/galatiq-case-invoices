# Epic 4 — Operations and Workspace

## Outcome

Local operators and business users can configure, observe, and operate the
prototype without exposure to internal model or filesystem details.

## Stories

### US-14 — Inspect an audit timeline

**As a** local operator  
**I want** to inspect sanitized workflow events  
**So that** I can diagnose progress and explain outcomes.

See the [master story](./_master-user-stories.md#us-14--inspect-an-audit-timeline).

### US-15 — Configure a replaceable model provider

**As a** local operator  
**I want** to configure Grok or OpenAI behind one contract  
**So that** development can switch providers without changing workflow rules.

See the [master story](./_master-user-stories.md#us-15--configure-a-replaceable-model-provider).

### US-16 — Use an accessible processing workspace

**As a** member of accounts payable or a VP reviewer  
**I want** to understand every workflow state and action  
**So that** I can operate the prototype confidently.

See the [master story](./_master-user-stories.md#us-16--use-an-accessible-processing-workspace).

## Workspace States

| State | Primary information | Available action |
| --- | --- | --- |
| Empty | Supported formats and upload limits | Choose invoice |
| Uploading | Filename and progress indicator | Cancel when feasible |
| Queued | Run ID and queued time | View recent runs |
| Processing | Current stage and timeline | None |
| Review required | Invoice summary, warnings, recommendation | Approve and mock pay / reject |
| Rejected | Reason codes and safe explanation | Submit corrected invoice |
| Failed | Safe error and retry eligibility | Retry |
| Completed | Decision and mock payment reference | View audit timeline |

## Edge Cases

| Case | Expected behavior |
| --- | --- |
| API polling temporarily fails | Preserve last known state and offer retry |
| Review action is pending | Disable repeated submission and announce progress |
| Narrow viewport | Stack panels without horizontal scrolling |
| Reduced-motion preference | Disable nonessential transitions |
| Missing provider key | Operator-facing configuration error; no secret value displayed |
| Sensitive provider or path detail in API error | Replace with stable safe code and generic message |
