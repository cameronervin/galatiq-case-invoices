from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import InvalidRequestError

from backend.app.infrastructure.db.migrations import initialize_database
from backend.app.infrastructure.db.session import Database
from backend.app.models import InventoryItem
from backend.app.repositories.sqlalchemy import (
    InventoryRepository,
    PaymentRepository,
    RunRepository,
)
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


@pytest.fixture
def database(tmp_path: Path) -> Database:
    value = Database(tmp_path / "app.db")
    initialize_database(value)
    yield value
    value.close()


def test_metadata_creation_is_repeatable_and_preserves_schema(
    tmp_path: Path,
) -> None:
    database = Database(tmp_path / "app.db")

    initialize_database(database)
    initialize_database(database)

    schema = inspect(database.engine)
    assert set(schema.get_table_names()) == {
        "schema_migrations",
        "inventory_items",
        "agent_runs",
        "run_results",
        "payments",
        "run_events",
    }
    active_profile = next(
        index
        for index in schema.get_indexes("agent_runs")
        if index["name"] == "idx_agent_runs_active_profile"
    )
    assert active_profile["unique"] == 1
    assert active_profile["column_names"] == [
        "content_hash",
        "provider_name",
        "provider_model",
    ]
    assert schema.get_foreign_keys("run_results")[0]["referred_table"] == "agent_runs"
    assert schema.get_foreign_keys("payments")[0]["referred_table"] == "agent_runs"
    assert schema.get_foreign_keys("run_events")[0]["referred_table"] == "agent_runs"
    assert schema.get_check_constraints("agent_runs")
    assert schema.get_check_constraints("payments")
    database.close()


def test_inventory_seed_and_alias_lookup_are_idempotent(database: Database) -> None:
    initialize_database(database)
    inventory = InventoryRepository(database.session)

    assert inventory.resolve_item("Widget A") == ("WidgetA", 15, True)
    assert inventory.resolve_item("WidgetA (rush order)") == ("WidgetA", 15, True)
    assert inventory.resolve_item("not-real") is None

    with database.session() as session:
        assert len(session.scalars(select(InventoryItem)).all()) == 4


def test_session_context_commits_writes_rolls_back_errors_and_closes(
    database: Database,
) -> None:
    with database.session(write=True) as committed:
        committed.add(
            InventoryItem(
                item_code="Committed",
                display_name="Committed",
                stock=1,
                aliases=["committed"],
            )
        )

    with pytest.raises(InvalidRequestError):
        committed.get(InventoryItem, "Committed")

    with pytest.raises(RuntimeError, match="rollback"):
        with database.session(write=True) as rolled_back:
            rolled_back.add(
                InventoryItem(
                    item_code="RolledBack",
                    display_name="Rolled back",
                    stock=1,
                    aliases=["rolledback"],
                )
            )
            raise RuntimeError("rollback")

    with pytest.raises(InvalidRequestError):
        rolled_back.get(InventoryItem, "RolledBack")

    with database.session() as session:
        assert session.get(InventoryItem, "Committed") is not None
        assert session.get(InventoryItem, "RolledBack") is None


def test_repositories_use_injected_context_without_retaining_sessions(
    database: Database,
) -> None:
    repository = RunRepository(database.session)

    repository.list_summaries()
    repository.list_summaries()

    assert repository.sessions == database.session
    assert not hasattr(repository, "session")
    assert not hasattr(repository, "database_path")


def test_run_repository_deduplicates_by_content_provider_and_model(
    database: Database,
    tmp_path: Path,
) -> None:
    repository = RunRepository(database.session)

    first, first_deduplicated = _create(repository, tmp_path, content_hash="abc")
    duplicate, duplicate_deduplicated = _create(
        repository,
        tmp_path,
        content_hash="abc",
        filename="renamed.txt",
        origin="api",
    )
    other_profile, other_deduplicated = _create(
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
    run, _ = _create(repository, tmp_path, content_hash="abc")
    repository.transition(
        run.run_id,
        status=RunStatus.FAILED,
        stage=RunStage.FINALIZE,
        event_code="RUN_FAILED",
        message="Processing failed.",
        error_code="TEST_FAILURE",
    )

    replacement, deduplicated = _create(repository, tmp_path, content_hash="abc")

    assert deduplicated is False
    assert replacement.run_id != run.run_id


def test_workflow_json_artifacts_round_trip_through_pydantic(
    database: Database,
    tmp_path: Path,
) -> None:
    repository = RunRepository(database.session)
    run, _ = _create(repository, tmp_path, content_hash="artifacts")
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


def test_concurrent_duplicate_submissions_create_one_active_run(
    database: Database,
    tmp_path: Path,
) -> None:
    repository = RunRepository(database.session)

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(
            executor.map(
                lambda _: _create(repository, tmp_path, content_hash="shared"),
                range(12),
            )
        )

    assert len({record.run_id for record, _ in results}) == 1
    assert sum(not deduplicated for _, deduplicated in results) == 1


def test_concurrent_payment_deliveries_are_idempotent(
    database: Database,
    tmp_path: Path,
) -> None:
    runs = RunRepository(database.session)
    payments = PaymentRepository(database.session)
    run, _ = _create(runs, tmp_path, content_hash="payment")
    money = Money(amount="125.50", currency="USD")

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(
            executor.map(
                lambda _: payments.create_or_get(
                    run.run_id, money, f"run:{run.run_id}"
                ),
                range(12),
            )
        )

    assert {result.status for result in results} == {"pending"}
    assert {result.amount.amount for result in results} == {money.amount}


def _create(
    repository: RunRepository,
    tmp_path: Path,
    *,
    content_hash: str,
    filename: str = "invoice.txt",
    origin: str = "cli",
    provider_name: str = "offline",
    provider_model: str = "deterministic-v1",
):
    return repository.create_run(
        content_hash=content_hash,
        source_filename=filename,
        source_path=str(tmp_path / filename),
        source_format="txt",
        source_origin=origin,
        provider_name=provider_name,
        provider_model=provider_model,
    )
