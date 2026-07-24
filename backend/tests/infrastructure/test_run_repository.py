from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from backend.app.infrastructure.db.repositories.runs import RunRepository
from backend.app.infrastructure.db.session import Database
from backend.app.ports.repositories import RunTransitionConflict
from backend.app.schemas.domain import (
    ApprovalRecommendation,
    DecisionRoute,
    FindingSeverity,
    HumanReview,
    InvoiceData,
    InvoiceItem,
    Money,
    RunStage,
    RunStatus,
    ValidationFinding,
)
from backend.tests.infrastructure.database_test_support import create_run


def test_run_repository_deduplicates_by_content_provider_and_model(
    database: Database,
    tmp_path: Path,
) -> None:
    repository = RunRepository(database.session)

    first, first_deduplicated = create_run(repository, tmp_path, content_hash="abc")
    duplicate, duplicate_deduplicated = create_run(
        repository,
        tmp_path,
        content_hash="abc",
        filename="renamed.txt",
        origin="api",
    )
    other_profile, other_deduplicated = create_run(
        repository,
        tmp_path,
        content_hash="abc",
        provider_name="grok",
        provider_model="grok-4.5",
    )

    assert first_deduplicated is False
    assert duplicate_deduplicated is True
    assert duplicate.run_id == first.run_id
    assert other_deduplicated is False
    assert other_profile.run_id != first.run_id


def test_failed_content_can_create_a_new_run(
    database: Database,
    tmp_path: Path,
) -> None:
    repository = RunRepository(database.session)
    run, _ = create_run(repository, tmp_path, content_hash="abc")
    repository.transition(
        run.run_id,
        status=RunStatus.FAILED,
        stage=RunStage.FINALIZE,
        event_code="RUN_FAILED",
        message="Processing failed.",
        error_code="TEST_FAILURE",
    )

    replacement, deduplicated = create_run(repository, tmp_path, content_hash="abc")

    assert deduplicated is False
    assert replacement.run_id != run.run_id


def test_terminal_run_cannot_regress_or_append_an_invalid_event(
    database: Database,
    tmp_path: Path,
) -> None:
    repository = RunRepository(database.session)
    run, _ = create_run(repository, tmp_path, content_hash="terminal")
    repository.transition(
        run.run_id,
        status=RunStatus.FAILED,
        stage=RunStage.FINALIZE,
        event_code="RUN_FAILED",
        message="Processing failed.",
        error_code="TEST_FAILURE",
    )

    with pytest.raises(RunTransitionConflict):
        repository.transition(
            run.run_id,
            status=RunStatus.RUNNING,
            stage=RunStage.INGEST,
            event_code="INGEST_STARTED",
            message="Invoice ingestion started.",
        )

    detail = repository.get_detail(run.run_id)
    assert detail is not None
    assert detail.status == RunStatus.FAILED
    assert [event.code for event in detail.events] == ["RUN_QUEUED", "RUN_FAILED"]


def test_queued_run_cannot_skip_directly_to_a_terminal_success(
    database: Database,
    tmp_path: Path,
) -> None:
    repository = RunRepository(database.session)
    run, _ = create_run(repository, tmp_path, content_hash="invalid-transition")

    with pytest.raises(RunTransitionConflict):
        repository.transition(
            run.run_id,
            status=RunStatus.COMPLETED,
            stage=RunStage.FINALIZE,
            event_code="PAYMENT_SUCCEEDED",
            message="Simulated payment completed.",
        )

    detail = repository.get_detail(run.run_id)
    assert detail is not None
    assert detail.status == RunStatus.QUEUED
    assert [event.code for event in detail.events] == ["RUN_QUEUED"]


def test_workflow_json_artifacts_round_trip_through_pydantic(
    database: Database,
    tmp_path: Path,
) -> None:
    repository = RunRepository(database.session)
    run, _ = create_run(repository, tmp_path, content_hash="artifacts")
    invoice = InvoiceData(
        invoice_number="INV-ROUNDTRIP",
        vendor_name="Fixture Vendor",
        invoice_date=date(2026, 1, 1),
        due_date=date(2026, 1, 31),
        currency="USD",
        items=[
            InvoiceItem(
                line_number=1,
                source_name="WidgetA",
                normalized_item_code="WidgetA",
                quantity=1,
                unit_price=Money(amount="10.00", currency="USD"),
                line_total=Money(amount="10.00", currency="USD"),
            )
        ],
        total=Money(amount="10.00", currency="USD"),
    )
    finding = ValidationFinding(
        code="ITEM_ALIAS_NORMALIZATION",
        severity=FindingSeverity.INFO,
        item_line_number=1,
        message="Item alias normalized.",
        expected="WidgetA",
        actual="Widget A",
    )
    recommendation = ApprovalRecommendation(
        proposed_route=DecisionRoute.APPROVE,
        final_route=DecisionRoute.APPROVE,
        reason_codes=["VALID_INVOICE"],
        summary="Invoice satisfies the approval policy.",
    )
    repository.save_result(
        run.run_id,
        invoice=invoice,
        findings=[finding],
        recommendation=recommendation,
        extraction_attempts=1,
        reflection_count=0,
    )
    assert repository.claim_execution(run.run_id)
    repository.transition(
        run.run_id,
        status=RunStatus.REVIEW_REQUIRED,
        stage=RunStage.REVIEW,
        event_code="REVIEW_REQUIRED",
        message="Human review required.",
    )
    review = HumanReview(
        decision="approve",
        reason="Validated fixture evidence.",
        decided_at=datetime.now(UTC),
    )
    repository.persist_review(run.run_id, review)

    detail = repository.get_detail(run.run_id)

    assert detail is not None
    assert detail.invoice == invoice
    assert detail.findings == [finding]
    assert detail.recommendation == recommendation
    assert detail.review == review
    assert [event.code for event in detail.events] == [
        "RUN_QUEUED",
        "REVIEW_REQUIRED",
    ]
