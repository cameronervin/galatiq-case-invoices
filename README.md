# Galatiq Case: Invoice Processing Automation

This repository implements the case published in the
[upstream Galatiq repository](https://github.com/galatiq-ai/galatiq-case-invoices/tree/2f150152b962ccd24b35e515e56b04f673d410bc).
The contract comparison below is pinned to upstream commit `2f15015`.

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
python main.py --invoice_path=data/invoices/invoice_1001.txt
```

Output should include structured logs and results.

## Implemented Solution

The primary demo is deliberately broker-free: one command initializes SQLite,
processes an invoice synchronously through LangGraph, and prints a safe,
human-readable result. The deterministic offline provider is the default, so the
evaluator does not need a key, network connection, Valkey, or a web server.

```bash
uv sync
uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
```

Pretty output is the interactive default. Automation can request the original
compact `RunDetail` JSON contract explicitly:

```bash
uv run python main.py --invoice_path=data/invoices/invoice_1001.txt --format json
```

Use `--show-events` to expand every persisted event in pretty mode and
`--no-color` (or the `NO_COLOR` environment variable) for unstyled terminal
output. The conventional `--invoice-path` spelling is an alias; the upstream
`--invoice_path` spelling remains supported.

The graph exposes five roles: extraction, inventory-backed validation, approval,
critic, and deterministic mock payment. It uses structured artifacts, a bounded
repair/reflection loop, append-only audit events, exact decimal money, and one
idempotent payment per run. A requested Grok configuration never silently falls
back to offline mode.

### Upstream contract alignment

| Upstream requirement | Implementation evidence |
|---|---|
| Original `python main.py --invoice_path=...` entry point | Preserved as the broker-free pretty-output command; `--format json` provides machine output |
| PDF/text ingestion with vendor, amount, items, and due date | Typed document loaders and `InvoiceData` output |
| SQLite inventory validation | Read-only inventory tool with stable findings for stock and identity defects |
| VP approval rules with reflection or critique | Deterministic threshold policy, approval agent, critic, and one bounded revision |
| Approved payment or explained rejection | Idempotent mock payment and coded rejection events |
| LLM, orchestration, tool use, structured output, and self-correction | Offline/Grok provider boundary, LangGraph roles, inventory tool, typed artifacts, and bounded repair/revision |
| Local execution without external services | Offline CLI requires no network, API key, Valkey, API, worker, or frontend |

For an optional live Grok demonstration:

```bash
APP_LLM_PROVIDER=grok APP_LLM_MODEL=grok-4.5 XAI_API_KEY=your_key \
  uv run python main.py --invoice_path=data/invoices/invoice_1001.txt
```

The FastAPI, Celery, Valkey, and Next.js workspace are an above-and-beyond
asynchronous surface. Start each process in its own terminal:

```bash
pnpm install
make broker-up
make dev-worker
make dev-backend
make dev-frontend
```

Open `http://localhost:3000` to upload an invoice, inspect findings and the agent
timeline, and approve or reject human-review cases. Valkey carries only run IDs
and small task results; SQLite remains the source of truth.

### Supplied-fixture outcomes

| Route | Fixtures | Why |
|---|---|---|
| Automatic mock payment | INV-1001, INV-1004, revised INV-1004, INV-1006, INV-1010, INV-1011, INV-1015 | Valid, in-stock, USD invoices at or below the threshold |
| Human review | INV-1012, INV-1014 | Observable OCR-like correction or non-USD currency |
| Rejection | INV-1002, INV-1003, INV-1005, INV-1007, INV-1008, INV-1009, INV-1013, INV-1016 | Blocking stock, identity, date, quantity, or reconciliation defects |

Missing currency in the supplied CSV dialect defaults to configured USD and
emits an informational finding. Exact aliases and parenthetical descriptors also
emit informational findings. OCR-like corrections emit warnings and pause for
review; informational findings do not change routing.

### Business-facing demo narrative

- Straight-through processing turns clean invoices into explainable mock payments.
- Coded findings route genuine exceptions to a reviewer without hiding evidence.
- Every stage is timestamped so processing latency and decision paths are visible.
- Content/profile deduplication plus a payment uniqueness constraint produces zero duplicate mock payments.

Start with the [interviewer application overview](backstage/docs/00-application-overview.md)
for architecture, workflow, persistence, operations, decisions, and quality. The
[consolidated PRD](backstage/prd/README.md) records requirements and implementation
history.

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
