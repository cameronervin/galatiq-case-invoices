# Integration Specification

## Integration Boundaries

All integrations are replaceable local boundaries. Grok and OpenAI are the only
network-capable dependencies; file parsing, SQLite, inventory, payment, Celery,
and Valkey behavior remain local.

## Configuration

Environment examples contain names and safe defaults only—never real keys.

| Setting | Default | Rules |
| --- | --- | --- |
| `APP_DATABASE_PATH` | `inventory.db` | SQLite application/checkpoint file; ignored by git |
| `APP_UPLOAD_DIR` | `.local/invoices` | Generated local staging path; ignored by git |
| `APP_MAX_UPLOAD_BYTES` | `10485760` | 10 MB hard limit |
| `APP_MAX_PDF_PAGES` | `20` | Reject larger PDFs |
| `APP_FAILED_SOURCE_RETENTION_HOURS` | `24` | Retry retention |
| `APP_LLM_PROVIDER` | `openai` | API/UI provider: `openai` or `grok` |
| `APP_GROK_MODEL` | `grok-4.5` | Configurable CLI/default Grok model |
| `APP_OPENAI_MODEL` | `gpt-5.6-sol` | Configurable development model |
| `APP_LLM_TIMEOUT_SECONDS` | `45` | Positive bounded request timeout |
| `APP_LLM_MAX_RETRIES` | `2` | Transient retries only; maximum 2 |
| `XAI_API_KEY` | none | Required for Grok and all CLI runs |
| `OPENAI_API_KEY` | none | Required when API/UI selects OpenAI |

CLI provider selection is server-owned and always Grok. API clients cannot send
a provider/model field.

## LLM Provider Protocol

```python
class LLMProvider(Protocol):
    provider_name: str
    model_name: str

    def extract_invoice(self, *, document_text: str) -> InvoiceExtraction: ...
    def repair_invoice(
        self, *, document_text: str, current: InvoiceExtraction,
        feedback: list[str]
    ) -> InvoiceExtraction: ...
    def propose_approval(
        self, *, invoice: InvoiceData, findings: list[ValidationFinding]
    ) -> ApprovalProposal: ...
    def critique_approval(
        self, *, invoice: InvoiceData, findings: list[ValidationFinding],
        proposal: ApprovalProposal
    ) -> ApprovalCritique: ...
```

Use the OpenAI Python SDK's Responses API for both adapters:

- `OpenAIProvider`: default API base URL and `OPENAI_API_KEY`.
- `GrokProvider`: xAI-compatible base URL and `XAI_API_KEY`.
- `store=False` on every request.
- Generate strict JSON schemas from Pydantic output models.
- Set explicit model, timeout, and bounded retry policy.
- Map refusals, invalid output, authentication, rate-limit, timeout, and service
  failures to provider-neutral exceptions.
- Do not enable provider-hosted web/search/code tools; invoice processing uses
  only local bounded tools.

The fake provider used by tests implements the same protocol with deterministic
fixtures and scripted failures. It is not selectable in normal runtime settings.

## File Loaders

| Format | Loader behavior |
| --- | --- |
| JSON | Standard JSON parse with size/depth bounds; support documented fixture object shape |
| CSV | Support key/value and row-per-line-item fixture shapes; reject mixed/ambiguous shapes |
| XML | Hardened parser with DTD/entities/network disabled; map documented invoice elements |
| TXT | UTF-8 text with explicit replacement/error policy and bounded character count |
| PDF | PyMuPDF text extraction; reject encrypted, image-only, over-page-limit, or empty text |

All loaders return transient `LoadedDocument(format, text_or_object,
normalization_signals)`. Raw values are not logged. The ingestion service, not
the graph state, owns source file access.

Recommended direct runtime dependencies to evaluate and pin during the provider
phase: `openai`, `pymupdf`, `defusedxml`, and a supported
`langgraph-checkpoint-sqlite` version. Do not add them during docs-only work.

## Celery and Valkey

### Tasks

| Task name | JSON-safe input | Result |
| --- | --- | --- |
| `invoice_processing.agent_runs.execute` | `{ "run_id": "uuid" }` | Public/sanitized run state |
| `invoice_processing.agent_runs.resume` | `{ "run_id": "uuid" }` | Public/sanitized run state |

Review details are read from SQLite after API persistence; they are not copied
into arbitrary client-controlled task payloads. Retry dispatch uses `execute`
after the service returns the run to queued.

Worker requirements:

- Local development concurrency is one.
- Worker process initializes repositories, provider, tools, SQLite checkpointer,
  and compiled graph once; shutdown closes resources.
- Celery accepts and emits JSON only.
- Task redelivery is expected and safe.
- Valkey result expiration remains operational metadata and cannot answer run
  API queries.

## Mock Payment Adapter

```python
class PaymentAdapter(Protocol):
    def pay(
        self,
        *,
        run_id: str,
        vendor_name: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> PaymentResult: ...
```

The local mock adapter:

- Performs no network call.
- Creates a deterministic-safe mock reference.
- Uses the payment repository's unique idempotency key before side effects.
- Returns the existing succeeded/failed attempt on duplicate invocation.
- Can be scripted to fail in tests.
- Never prints vendor or amount to logs; those remain application data visible
  only through authorized local run detail.

## SQLite and Checkpointing

- Application repositories use short parameterized transactions and explicit
  connection boundaries.
- Enable WAL, foreign keys, and 5-second busy timeout on every connection.
- Use the supported synchronous SQLite LangGraph saver because Celery tasks and
  provider adapters execute synchronously in the worker.
- Each worker process owns its connection/saver. The API never executes the graph.
- `thread_id` equals `run_id`; node side effects remain idempotent on resume.

## External Failure Matrix

| Failure | Behavior | Retryable |
| --- | --- | --- |
| Missing/invalid key | Reject configuration before queue when known; otherwise fail safely | No until config changes |
| Provider timeout/429/5xx | Adapter retries at most twice, then run fails | Yes |
| Provider refusal/invalid schema | Run fails with safe provider-output code | Yes after source review/config change |
| Valkey unavailable on creation | Persist failed run and safe queue error | Yes |
| Valkey unavailable on review | Leave run review-required and decision persisted | Yes |
| SQLite busy beyond timeout | Fail current operation safely; never partially pay | Yes |
| Source removed/expired | Retry returns `SOURCE_UNAVAILABLE` | No |
| Mock payment failure | Persist failed payment/run; idempotent retry | Yes |

