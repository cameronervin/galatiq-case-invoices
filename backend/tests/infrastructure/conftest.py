from collections.abc import Iterator
from pathlib import Path

import pytest

from backend.app.infrastructure.db.migrations import initialize_database
from backend.app.infrastructure.db.session import Database


@pytest.fixture
def database(tmp_path: Path) -> Iterator[Database]:
    value = Database(tmp_path / "app.db")
    initialize_database(value)
    yield value
    value.close()
