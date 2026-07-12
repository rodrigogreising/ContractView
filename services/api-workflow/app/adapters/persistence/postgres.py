"""PostgreSQL implementation of the application-owned unit-of-work port."""

from __future__ import annotations

import json
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Iterator

import psycopg

from ...application.ports.statements import Statement

CATALOG_PATH = Path(__file__).with_name("statements.json")


@lru_cache
def statement_catalog() -> dict[str, dict[str, object]]:
    return json.loads(CATALOG_PATH.read_text())


class PostgresRepository:
    def __init__(self, connection: psycopg.Connection, owner: str) -> None:
        self._connection = connection
        self._owner = owner

    def execute(self, statement: Statement, parameters: object = ()):
        if not isinstance(statement, Statement):
            raise TypeError("Persistence accepts Statement identifiers, never inline SQL")
        definition = statement_catalog().get(statement.value)
        if definition is None:
            raise KeyError(f"Unknown persistence statement: {statement}")
        if self._owner == "read_models":
            if definition["kind"] != "declared-read-model":
                raise PermissionError(f"Statement is not a declared read model: {statement}")
        elif definition["owner"] != self._owner or definition["kind"] == "declared-read-model":
            raise PermissionError(
                f"Repository {self._owner} cannot execute {statement} owned by {definition['owner']}"
            )
        return self._connection.execute(str(definition["sql"]), parameters)


class PostgresUnitOfWork:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection
        self._completed = False
        for owner in (
            "identity", "configuration", "artifacts", "extraction", "invoices",
            "validation", "packages", "workflow", "provenance", "platform",
            "read_models",
        ):
            setattr(self, owner, PostgresRepository(connection, owner))

    def commit(self) -> None:
        self._connection.commit()
        self._completed = True

    def rollback(self) -> None:
        self._connection.rollback()
        self._completed = True

    @property
    def completed(self) -> bool:
        return self._completed


@contextmanager
def postgres_transaction(database_url: str) -> Iterator[PostgresUnitOfWork]:
    connection = psycopg.connect(database_url)
    unit_of_work = PostgresUnitOfWork(connection)
    try:
        yield unit_of_work
    except BaseException:
        connection.rollback()
        raise
    finally:
        if not unit_of_work.completed:
            connection.rollback()
        connection.close()
