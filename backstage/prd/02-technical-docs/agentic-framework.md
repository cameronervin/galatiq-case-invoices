# Agentic Framework Specification

## Purpose

LangGraph owns the bounded invoice-processing workflow. It coordinates typed
nodes and routes; it does not replace deterministic business rules. Model output
is advisory and schema-validated. Only services, repositories, and guarded tools
perform persistence or payment-like side effects.

## Topology

```text
START
  → ingest
  → extract
  → assess_extraction
      ├─ repairable and attempts < 2 → repair_extraction → assess_extraction
      ├─ unrecoverable → fail
      └─ acceptable → validate
  → approval_proposal
  → approval_critique
      ├─ revise and reflections < 2 → revise_approval → approval_critique
      └─ accepted/limit → decision_gate
  → decision_gate
      ├─ blocking findings → reject
      ├─ warnings / total > $10K / non-USD → human_review interrupt
      │     ├─ approve → payment
      │     └─ reject → reject
      └─ clean USD total <= $10K → payment
  → finalize
  → END
```

Use one routing mechanism per node. Conditional edges select branches; side-effect
nodes do not also define competing static routes. Invocation sets a recursion
limit high enough for two extraction repairs and two approval revisions, but low
enough to prevent unbounded execution.

## Typed State

The implementation may split nested values into Pydantic models, but the graph
state must be equivalent to:

```python
class InvoiceProcessingState(TypedDict):
    run_id: str
    status: RunStatus
    current_stage: str
    invoice: InvoiceData | None
    findings: list[ValidationFinding]
    extraction_feedback: list[str]
    extraction_attempts: int
    approval: ApprovalDecision | None
    approval_feedback: list[str]
    reflection_count: int
    human_review: HumanReviewDecision | None
    payment: PaymentResult | None
    error: WorkflowError | None
```

State must not contain:

- Raw document bytes or extracted full text.
- Local source paths.
- Prompts, API keys, raw provider payloads, or hidden reasoning.
- SQLite connections, SDK clients, or callables.

## Runtime Context

```python
@dataclass(frozen=True)
class AgentRuntimeContext:
    settings: Settings
    run_repository: AgentRunRepository
    invoice_repository: InvoiceRepository
    inventory_repository: InventoryRepository
    finding_repository: FindingRepository
    decision_repository: DecisionRepository
    payment_repository: PaymentRepository
    event_repository: RunEventRepository
    llm_provider: LLMProvider
    tool_registry: ToolRegistry
    clock: Clock
```

Context is created in the Celery worker process and supplied at invocation. CLI,
API clients, and graph state cannot replace these dependencies.

## Node Contracts

| Node | Reads | Produces | Side effects |
| --- | --- | --- | --- |
| `ingest` | run ID/context | status/stage | Validates retained source; loads bounded content transiently; event |
| `extract` | transient source/context | invoice, initial extraction findings | Persists invoice/findings/event |
| `assess_extraction` | invoice/findings | route, bounded feedback | Event only |
| `repair_extraction` | invoice/feedback | revised invoice/findings, attempt count | Provider call; replaces invoice/findings; event |
| `validate` | invoice | ordered findings | Inventory tool calls; replaces findings; event |
| `approval_proposal` | invoice/findings | proposed decision | Provider call; decision version/event |
| `approval_critique` | proposal/invoice/findings | accept/revise feedback | Provider call; no raw output persistence |
| `revise_approval` | proposal/feedback | revised decision/count | Provider call; decision version/event |
| `decision_gate` | invoice/findings/proposal | policy-enforced route | Persists final policy decision/event |
| `human_review` | safe review payload | interrupt or human decision | Durable interrupt; decision/event on resume |
| `payment` | approved state | payment result | Idempotent mock payment tool; payment/event |
| `reject` | findings/review | rejected state | Decision/event; source cleanup |
| `finalize` | result | terminal state | Final status/event; source cleanup |
| `fail` | sanitized error | failed state | Status/event; retain retry-eligible source |

All side effects must be idempotent because checkpoint resume or task delivery may
re-execute a node.

## Finding Catalog

The following codes are stable public contracts. Implementations may add codes
only after updating the API and user-story specifications.

| Code | Default severity | Meaning |
| --- | --- | --- |
| `MISSING_VENDOR` | blocking | Vendor is absent or empty |
| `MISSING_DUE_DATE` | blocking | Due date is absent |
| `INVALID_DUE_DATE` | blocking | Date is unparseable, relative, or before invoice date |
| `MISSING_ITEMS` | blocking | No invoice items exist |
| `INVALID_QUANTITY` | blocking | Quantity is absent, non-integral, zero, or negative |
| `INVALID_UNIT_PRICE` | blocking | Unit price is absent or non-positive |
| `INVALID_TOTAL` | blocking | Total is absent or non-positive |
| `TOTAL_MISMATCH` | blocking | Arithmetic differs by more than one cent |
| `UNKNOWN_ITEM` | blocking | No explicit alias/inventory match exists |
| `OUT_OF_STOCK` | blocking | Normalized inventory stock is zero |
| `QUANTITY_EXCEEDS_STOCK` | blocking | Aggregated quantity is above stock |
| `SUSPICIOUS_PAYMENT_LANGUAGE` | blocking | Source requests urgent/wire behavior matching bounded rules |
| `OCR_NORMALIZATION` | warning | Evidence-backed OCR-like correction occurred |
| `ITEM_ALIAS_NORMALIZATION` | warning | Source item used an explicit alias |
| `LOW_EXTRACTION_CONFIDENCE` | warning | Required review due to extraction uncertainty |
| `UNSUPPORTED_CURRENCY` | warning | Currency is not USD and no FX policy exists |
| `HIGH_VALUE_INVOICE` | warning | Total is above $10,000 |

`HIGH_VALUE_INVOICE` is created by policy after validation, not by the model.

## Extraction and Repair

- Structured loaders map JSON, CSV, and XML without a model when their fields are
  unambiguous.
- TXT and PDF loaders produce bounded text for the provider. The system prompt
  treats the document as untrusted data and forbids following embedded requests.
- Provider returns an `InvoiceExtraction` JSON schema with nullable values and
  `evidence_notes`; absence never becomes a guessed value.
- Assessment checks schema, required fields, money arithmetic, date shape, and
  unsupported corrections.
- Repair feedback lists only specific schema/consistency defects. Maximum two
  repairs; no conversational history or raw reasoning is persisted.

## Approval and Critique

Provider input contains:

- Normalized invoice summary.
- Ordered finding codes/severities and safe messages.
- Approval policy and allowed routes.

Provider output contains:

```text
proposed_route: approve | review | reject
reason_codes: list[str]
summary: str
```

Critique output contains `accepted`, `feedback`, and `unsupported_claims`.
Revision is bounded to two attempts. The policy gate then computes the final route
independently:

1. Any blocking finding → reject.
2. Any warning, non-USD, or total above $10,000 → review.
3. Otherwise clean USD at or below $10,000 → approve.

If the model disagrees, store the policy route with `decided_by=policy` and a
`POLICY_OVERRIDE` reason; never weaken policy.

## Human Review Interrupt

- Compile the graph with the supported SQLite checkpointer.
- Invoke with `thread_id=run_id`.
- `human_review` interrupts with JSON-safe data only: run ID, invoice summary,
  safe findings, recommendation, and allowed decisions.
- API persists the review decision before enqueueing a resume command.
- Resume uses `Command(resume={decision, reason})` and the same thread ID.
- The node validates the persisted decision and is safe when restarted from its
  beginning.

## Tool Registry

| Tool | Inputs | Output | Authority |
| --- | --- | --- | --- |
| `lookup_inventory` | normalized item codes | stock snapshot/missing codes | Read-only repository tool |
| `mock_payment` | approved run ID, vendor, money, idempotency key | payment result | Guarded side effect; callable only from payment node |

Provider-driven arbitrary function selection is unnecessary. Nodes call the
bounded registry explicitly; tool use remains observable and deterministic.

## Failure Behavior

- Transient provider failures retry inside the adapter at most twice.
- Schema/refusal failures do not repeat indefinitely; extraction repair remains
  a separate bounded graph loop.
- Every exception is mapped to `WorkflowError(code, safe_message, retryable)`.
- The worker catches terminal graph errors, persists `failed`, and returns a
  JSON-safe result.
- Payment never runs from a failed, rejected, or unpersisted approval state.

## Evaluation

Tests must visualize or inspect graph topology, cover every conditional route,
prove both loop bounds, resume approve/reject interrupts, replay payment safely,
and show that model output cannot override blocking policy.

