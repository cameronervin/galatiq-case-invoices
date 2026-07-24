import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def sqlite_connection(database_path: Path) -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection without creating application tables."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()

