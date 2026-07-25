# Galatiq Case: Invoice Processing Automation

This repository implements the invoice-processing take-home published in the
[upstream Galatiq repository](https://github.com/galatiq-ai/galatiq-case-invoices/tree/2f150152b962ccd24b35e515e56b04f673d410bc).
It turns supplied invoice files into typed data, validates them against local
inventory, records an explainable approval decision, routes exceptions to a
reviewer, and creates an idempotent simulated payment for approved invoices.

> Start with the [interviewer application overview](backstage/docs/00-application-overview.md)
> for deeper context. The numbered `backstage/docs/` set covers architecture,
> agent workflow, persistence, operations, decisions, security, and roadmap.

## Quick start: broker-free CLI

Prerequisites: Python 3.12+ and [`uv`](https://docs.astral.sh/uv/). The default
offline provider needs no API key, network connection, Docker, Valkey, backend,
worker, or frontend.

```bash
uv sync
uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
```

The application automatically creates and seeds the local SQLite database.
Pretty terminal output is the default; automation can request the compact public
`RunDetail` contract:

```bash
uv run python main.py --invoice-path=data/invoices/invoice_1001.txt --format json
```

Use `--show-events` for the full persisted timeline and `--no-color` or
`NO_COLOR` for unstyled output. Both `--invoice_path` and `--invoice-path` are
accepted.

Optional live Grok mode requires a valid key and never silently falls back to
offline inference:

```bash
APP_LLM_PROVIDER=grok APP_LLM_MODEL=grok-4.5 XAI_API_KEY=your_key \
  uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
```

## Optional full workspace

The asynchronous workspace adds FastAPI, Celery, Valkey, and Next.js around the
same workflow. It requires Node.js 20.9+, `pnpm`, and Docker in addition to the
CLI prerequisites.

Install from the repository root:

```bash
uv sync
pnpm install
```

The checked-in examples document every setting, but copying them is optional
because local defaults already match the commands below:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

Start each process in its own terminal, in this order:

```bash
make broker-up
make dev-worker
make dev-backend
make dev-frontend
```

Open the workspace at `http://localhost:3000`. FastAPI runs at
`http://127.0.0.1:8000`, with interactive OpenAPI documentation at
`http://127.0.0.1:8000/docs`. The UI supports upload, recent-run triage, selected
run polling, findings and decision-history inspection, and human review.
Approval requires an explicit second-step confirmation before a simulated
payment. SQLite remains the source of truth; Valkey transports only run IDs and
small task results.

Stop local queue infrastructure with:

```bash
make broker-down
```

## How it works

```text
CLI ------------------------> InvoiceProcessingService ----> LangGraph
                                      |                         |
Next.js -> FastAPI -> Celery ---------+                         +-> providers
              |                       |                         +-> inventory tool
              +-> Valkey: run IDs     +-> SQLAlchemy/SQLite     +-> mock payment
```

The typed LangGraph exposes extraction, inventory-backed validation, approval,
critic, deterministic policy, review, and payment steps. Extraction and critique
loops are bounded. Policy—not the model—owns final routing, and payment is a
server-owned idempotent simulation. Audit events expose stage transitions and
safe reason codes without storing prompts, provider payloads, or hidden
reasoning.

## Demo scenarios

| Outcome | Fixture | Expected behavior |
| --- | --- | --- |
| Automatic payment | `invoice_1001.txt` | Completes with one simulated payment |
| Human review | `invoice_1012.txt` | Pauses on an OCR-like correction warning |
| Rejection | `invoice_1002.txt` | Rejects with an inventory mismatch finding |

The full supplied-fixture matrix is recorded in the
[quality and roadmap guide](backstage/docs/06-quality-security-and-roadmap.md#fixture-matrix).

## Upstream contract alignment

| Upstream requirement | Implemented solution |
| --- | --- |
| `python main.py --invoice_path=...` | Preserved as the synchronous, broker-free entry point |
| PDF/text extraction with structured fields | Bounded document loaders and typed `InvoiceData` |
| SQLite inventory validation | Automatically created and seeded inventory with stable findings |
| VP approval with reflection | Approval agent, critic, one bounded revision, and deterministic policy |
| Approved payment or explained rejection | Idempotent mock payment and coded rejection events |
| LLM, orchestration, tools, structured output | Offline/Grok provider boundary, LangGraph roles, inventory tool, and typed artifacts |
| Local execution | Default demo needs no external service or network access |
| Above-and-beyond UI/UX | Optional API, worker, broker, and review workspace |

## Verification

Run the complete local suite from the repository root:

```bash
make verify
```

This checks generated API artifacts, backend tests and branch coverage, Python
lint, frontend tests and lint, TypeScript types, and a production frontend build.
The [operations guide](backstage/docs/04-interfaces-and-operations.md) documents
the Docker-backed execute and review/resume smoke test.

## More documentation

- [Application overview](backstage/docs/00-application-overview.md)
- [Interfaces and operations](backstage/docs/04-interfaces-and-operations.md)
- [Consolidated PRD and implementation history](backstage/prd/README.md)

<details>
<summary>Original take-home assessment</summary>

The text below preserves the assignment at upstream commit `2f15015` for reviewer
reference.

## Background

Acme Corp is a PE-backed manufacturing firm losing **$2M/year** on manual invoice processing. Invoices arrive via email as PDFs in messy formats with frequent errors. Staff manually extract data, validate against a legacy inventory database (inconsistent), obtain VP approval (via email chains), and process payment (via a banking API).

**Current pain points:**

- 30% error rate
- 5-day processing delays
- Frustrated stakeholders

## Objective

Build a **multi-agent system** that automates the end-to-end invoice processing workflow. The system must run as a working prototype — not just designs or slides.

## Workflow

The system should handle four stages:

1. **Ingestion** — Extract structured data from invoice documents (PDFs, text files). Fields include: Vendor, Amount, Items (with quantities), and Due Date. Expect unstructured text, typos, missing data, and potentially fraudulent entries.

2. **Validation** — Verify extracted data against a mock inventory database (SQLite). Flag mismatches such as quantity exceeding available stock or items not found in inventory.

3. **Approval** — Simulate VP-level review with rule-based decision-making (e.g., invoices over $10K require additional scrutiny). The agent should reason through approval/rejection with a reflection or critique loop.

4. **Payment** — If approved, call a mock payment function. If rejected, log the rejection with reasoning.

## Technical Requirements

- **LLM Integration**: Use xAI's Grok as the core reasoning engine (via the xAI API at https://grok.x.ai). Other models are acceptable if you don't have an API key.
- **Multi-Agent Orchestration**: Use a framework such as LangGraph, CrewAI, AutoGen, or a custom solution.
- **Agent Capabilities**: Function calling / tool use, structured outputs, and self-correction loops.
- **Runtime**: Assume no internet for external APIs — simulate everything locally.
- **Tech Stack**: Python (preferred), with libraries like `langchain`, `crewai`, `autogen`, `pdfplumber`, `PyMuPDF`, etc. Run locally — no cloud deployment.

## Provided Resources

### Mock Invoice Data

Sample invoices are provided in the `data/invoices/` directory in various formats (PDF, CSV, JSON, TXT). Use these as inputs for testing. The data intentionally includes a mix of clean entries and problematic ones — identifying and handling issues is part of the challenge.

### Mock Inventory Database (Required Setup)

Before running the system, you **must** create a local SQLite database that the validation agent will check invoices against. The sample invoices in `data/invoices/` reference specific items and quantities — your database needs to contain matching inventory records so the validation stage can flag mismatches, out-of-stock items, and unknown products.

Below is a starter schema and seed data that covers the core items referenced across the provided invoices:

```python
import sqlite3

conn = sqlite3.connect('inventory.db')  # Persist to file so all agents can access it
cursor = conn.cursor()

cursor.execute('CREATE TABLE IF NOT EXISTS inventory (item TEXT PRIMARY KEY, stock INTEGER)')
cursor.execute("""
    INSERT INTO inventory VALUES
    ('WidgetA', 15),
    ('WidgetB', 10),
    ('GadgetX', 5),
    ('FakeItem', 0)
""")
conn.commit()
```

**Why this matters:** The sample invoices are designed to test your validation logic against this database. For example:

| Scenario | Invoice | What should happen |
|---|---|---|
| Normal order within stock | INV-1001, INV-1004, INV-1006 | Items found, quantities valid — passes validation |
| Quantity exceeds stock | INV-1002 (requests 20× GadgetX, only 5 in stock) | Flagged as stock mismatch |
| Fraudulent / zero-stock item | INV-1003 (references FakeItem, 0 stock) | Flagged as out of stock or suspicious |
| Item not in database at all | INV-1008 (SuperGizmo, MegaSprocket), INV-1016 (WidgetC) | Flagged as unknown item |
| Invalid data | INV-1009 (negative quantity) | Flagged as data integrity issue |

You may extend the seed data with additional items or columns (e.g., unit price, category) to support richer validation — the above is the minimum needed to exercise the provided test invoices. If you want your system to also validate pricing or vendor information, consider adding tables for those as well.

### Mock Payment API

```python
def mock_payment(vendor, amount):
    print(f"Paid {amount} to {vendor}")
    return {"status": "success"}
```

### Grok API Setup

```python
from xai import Grok

client = Grok(api_key="your_key")
response = client.chat.completions.create(
    model="grok-3",
    messages=[{"role": "user", "content": "Reason about this..."}]
)
```

## Running the System

The system should be executable from the command line:

```bash
python main.py --invoice_path=data/invoices/invoice1.txt
```

Output should include structured logs and results.

## Evaluation Criteria

- **Functionality** — Does the system work end-to-end?
- **Code Quality** — Clean, testable, well-structured code with error handling and observability
- **Agentic Sophistication** — LLM integration, multi-agent flow, tool use, self-correction loops
- **Shipping Mindset** — Valuable MVP delivered under ambiguity; scope ruthlessly cut where needed
- **Presentation** — Clear translation of technical decisions to business impact
- **Above/Beyond** - Have you made it your own? Implemented additional features that make the solution feel great? Expanded assumptions? Added to test cases?
- **UI/UX** - Users will understand and enjoy using this system.

## Submission

Submit your solution as a link to a public GitHub repository — GitHub only (github.com).

</details>
