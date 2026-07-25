from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCS = PROJECT_ROOT / "backstage" / "docs"
EXPECTED = {
    "00-application-overview.md": "Application Overview",
    "01-system-architecture.md": "System Architecture",
    "02-agent-workflow.md": "Agent Workflow",
    "03-data-and-persistence.md": "Data and Persistence",
    "04-interfaces-and-operations.md": "Interfaces and Operations",
    "05-decisions-and-tradeoffs.md": "Decisions and Tradeoffs",
    "06-quality-security-and-roadmap.md": "Quality, Security, and Roadmap",
}
LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def test_numbered_interviewer_document_set_is_complete_and_scoped() -> None:
    assert {path.name for path in DOCS.glob("*.md")} == set(EXPECTED)
    for filename, title in EXPECTED.items():
        content = (DOCS / filename).read_text()
        assert content.startswith(f"# {title}\n")
        assert "**Implemented" in content
        assert "**Take-home default" in content
        assert "**Production follow-up" in content


def test_interviewer_document_links_resolve() -> None:
    documents = [DOCS / filename for filename in EXPECTED]
    documents.extend(
        [
            PROJECT_ROOT / "README.md",
            PROJECT_ROOT / "backstage" / "architecture" / "overview.md",
            PROJECT_ROOT / "backstage" / "guides" / "setup.md",
        ]
    )
    for document in documents:
        for target in LINK.findall(document.read_text()):
            if "://" in target or target.startswith("#"):
                continue
            path = (document.parent / target.split("#", maxsplit=1)[0]).resolve()
            assert path.exists(), f"Broken link in {document}: {target}"


def test_overview_indexes_every_numbered_document() -> None:
    overview = (DOCS / "00-application-overview.md").read_text()
    for filename in EXPECTED:
        if filename != "00-application-overview.md":
            assert filename in overview

    assert (
        "backstage/docs/00-application-overview.md"
        in (PROJECT_ROOT / "README.md").read_text()
    )


def test_readme_records_upstream_contract_and_cli_formats() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text()

    assert "github.com/galatiq-ai/galatiq-case-invoices/tree/2f150152" in readme
    assert "python main.py --invoice_path=" in readme
    assert "--invoice-path" in readme
    assert "--format json" in readme
    assert "Upstream contract alignment" in readme
