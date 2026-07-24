from datetime import UTC, datetime

from sqlalchemy.dialects.sqlite import insert

from backend.app.infrastructure.db.session import Database
from backend.app.models import Base, InventoryItem, SchemaMigration

INVENTORY_SEED = (
    {
        "item_code": "WidgetA",
        "display_name": "Widget A",
        "stock": 15,
        "aliases": ["widgeta", "widget a", "widgeta (rush order)"],
    },
    {
        "item_code": "WidgetB",
        "display_name": "Widget B",
        "stock": 10,
        "aliases": ["widgetb", "widget b"],
    },
    {
        "item_code": "GadgetX",
        "display_name": "Gadget X",
        "stock": 5,
        "aliases": ["gadgetx", "gadget x"],
    },
    {
        "item_code": "FakeItem",
        "display_name": "Fake Item",
        "stock": 0,
        "aliases": ["fakeitem", "fake item"],
    },
)


def initialize_database(database: Database) -> None:
    Base.metadata.create_all(database.engine)
    with database.session(write=True) as session:
        session.execute(
            insert(InventoryItem)
            .values(INVENTORY_SEED)
            .on_conflict_do_nothing(index_elements=[InventoryItem.item_code])
        )
        session.execute(
            insert(SchemaMigration)
            .values(
                version=1,
                name="initial",
                applied_at=_timestamp(),
            )
            .on_conflict_do_nothing(index_elements=[SchemaMigration.version])
        )


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
