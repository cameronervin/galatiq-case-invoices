from sqlalchemy import JSON, CheckConstraint, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.infrastructure.db.models.base import Base


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"

    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    applied_at: Mapped[str] = mapped_column(Text, nullable=False)


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    item_code: Mapped[str] = mapped_column(Text, primary_key=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    aliases: Mapped[list[str]] = mapped_column(
        "aliases_json",
        JSON(none_as_null=True),
        nullable=False,
    )


InventoryItem.__table__.append_constraint(
    CheckConstraint(InventoryItem.__table__.c.stock >= 0, name="ck_inventory_stock")
)
