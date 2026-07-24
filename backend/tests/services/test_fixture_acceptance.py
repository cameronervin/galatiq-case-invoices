from pathlib import Path

import pytest

from backend.app.schemas.domain import RunStatus
from backend.tests.services.workflow_support import PROJECT_ROOT, service_for

FIXTURE_OUTCOMES = [
    ("invoice_1001.txt", RunStatus.COMPLETED),
    ("invoice_1004.json", RunStatus.COMPLETED),
    ("invoice_1004_revised.json", RunStatus.COMPLETED),
    ("invoice_1006.csv", RunStatus.COMPLETED),
    ("invoice_1010.txt", RunStatus.COMPLETED),
    ("invoice_1011.txt", RunStatus.COMPLETED),
    ("invoice_1011.pdf", RunStatus.COMPLETED),
    ("invoice_1015.csv", RunStatus.COMPLETED),
    ("invoice_1012.txt", RunStatus.REVIEW_REQUIRED),
    ("invoice_1012.pdf", RunStatus.REVIEW_REQUIRED),
    ("invoice_1014.xml", RunStatus.REVIEW_REQUIRED),
    ("invoice_1002.txt", RunStatus.REJECTED),
    ("invoice_1003.txt", RunStatus.REJECTED),
    ("invoice_1005.json", RunStatus.REJECTED),
    ("invoice_1007.csv", RunStatus.REJECTED),
    ("invoice_1008.txt", RunStatus.REJECTED),
    ("invoice_1009.json", RunStatus.REJECTED),
    ("invoice_1013.json", RunStatus.REJECTED),
    ("invoice_1013.pdf", RunStatus.REJECTED),
    ("invoice_1016.json", RunStatus.REJECTED),
]


def test_fixture_acceptance_matrix_covers_every_supplied_invoice() -> None:
    fixture_names = {
        path.name
        for path in (PROJECT_ROOT / "data/invoices").iterdir()
        if path.is_file()
    }

    assert {filename for filename, _ in FIXTURE_OUTCOMES} == fixture_names


@pytest.mark.parametrize(("filename", "expected"), FIXTURE_OUTCOMES)
def test_fixture_acceptance_matrix(
    tmp_path: Path, filename: str, expected: RunStatus
) -> None:
    service = service_for(tmp_path)

    detail = service.process_path(
        PROJECT_ROOT / "data/invoices" / filename,
        origin="cli",
    )

    assert detail.status == expected, [
        (finding.code, finding.message) for finding in detail.findings
    ]
