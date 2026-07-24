from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.app.infrastructure.db.repositories.payments import PaymentRepository
from backend.app.infrastructure.db.repositories.runs import RunRepository
from backend.app.infrastructure.db.session import Database
from backend.app.schemas.domain import Money, RunStatus
from backend.tests.infrastructure.database_test_support import create_run


def test_only_one_concurrent_worker_can_claim_a_queued_run(
    database: Database,
    tmp_path: Path,
) -> None:
    repository = RunRepository(database.session)
    run, _ = create_run(repository, tmp_path, content_hash="claim")

    with ThreadPoolExecutor(max_workers=6) as executor:
        claims = list(
            executor.map(
                lambda _: repository.claim_execution(run.run_id),
                range(12),
            )
        )

    assert claims.count(True) == 1
    assert claims.count(False) == 11
    claimed = repository.get_internal(run.run_id)
    assert claimed is not None
    assert claimed.status == RunStatus.RUNNING


def test_concurrent_duplicate_submissions_create_one_active_run(
    database: Database,
    tmp_path: Path,
) -> None:
    repository = RunRepository(database.session)

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(
            executor.map(
                lambda _: create_run(repository, tmp_path, content_hash="shared"),
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
    run, _ = create_run(runs, tmp_path, content_hash="payment")
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
