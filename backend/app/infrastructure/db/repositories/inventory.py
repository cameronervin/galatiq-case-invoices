from sqlalchemy import select

from backend.app.infrastructure.db.models import InventoryItem
from backend.app.infrastructure.db.repositories.base import SessionRepository


class InventoryRepository(SessionRepository):
    def resolve_item(self, source_name: str) -> tuple[str, int, bool] | None:
        normalized = " ".join(source_name.strip().lower().split())
        with self.sessions(write=False) as session:
            items = session.scalars(select(InventoryItem)).all()
            for item in items:
                if normalized in item.aliases:
                    canonical = normalized == item.item_code.lower()
                    return item.item_code, item.stock, not canonical
        return None
