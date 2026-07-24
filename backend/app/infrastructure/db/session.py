from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import Protocol

from sqlalchemy import URL, Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool


class SessionContext(Protocol):
    def __call__(self, *, write: bool = False) -> AbstractContextManager[Session]: ...


class Database:
    """Own the SQLAlchemy engine and short-lived application sessions."""

    def __init__(self, database_path: Path) -> None:
        resolved = database_path.expanduser().resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(
            URL.create(drivername="sqlite+pysqlite", database=str(resolved)),
            connect_args={
                "check_same_thread": False,
                "timeout": 5.0,
                "isolation_level": "IMMEDIATE",
            },
            poolclass=NullPool,
        )
        event.listen(self.engine, "connect", _enable_foreign_keys)
        self._session_factory: Callable[[], Session] = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
            close_resets_only=False,
        )

    @contextmanager
    def session(self, *, write: bool = False) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            if write:
                session.commit()
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        self.engine.dispose()


def _enable_foreign_keys(
    dbapi_connection: object,
    _connection_record: object,
) -> None:
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.setconfig(sqlite3.SQLITE_DBCONFIG_ENABLE_FKEY, True)
