import pytest
from sqlalchemy import select
from sqlalchemy.exc import InvalidRequestError

from backend.app.infrastructure.db.migrations import initialize_database
from backend.app.infrastructure.db.models import InventoryItem
from backend.app.infrastructure.db.repositories.inventory import InventoryRepository
from backend.app.infrastructure.db.repositories.runs import RunRepository
from backend.app.infrastructure.db.session import Database


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
