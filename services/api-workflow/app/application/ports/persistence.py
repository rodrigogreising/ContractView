"""Application-owned persistence and transaction interfaces."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol

from .statements import Statement


class ResultPort(Protocol):
    def fetchone(self) -> tuple[Any, ...] | None: ...
    def fetchall(self) -> list[tuple[Any, ...]]: ...


class RepositoryPort(Protocol):
    def execute(self, statement: Statement, parameters: object = ()) -> ResultPort: ...


class UnitOfWork(Protocol):
    """Explicit capability repositories coordinated by one local transaction."""

    identity: RepositoryPort
    configuration: RepositoryPort
    artifacts: RepositoryPort
    extraction: RepositoryPort
    invoices: RepositoryPort
    validation: RepositoryPort
    packages: RepositoryPort
    workflow: RepositoryPort
    provenance: RepositoryPort
    platform: RepositoryPort
    read_models: RepositoryPort

    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> AbstractContextManager[UnitOfWork]: ...
