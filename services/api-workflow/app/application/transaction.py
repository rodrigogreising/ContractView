"""Application-side unit-of-work provider configured by the composition root."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from .ports.persistence import UnitOfWork, UnitOfWorkFactory

_factory: UnitOfWorkFactory | None = None


def configure_transaction_factory(factory: UnitOfWorkFactory) -> None:
    global _factory
    _factory = factory


@contextmanager
def transaction() -> Iterator[UnitOfWork]:
    if _factory is None:
        raise RuntimeError("ContractView composition root has not configured persistence")
    with _factory() as unit_of_work:
        yield unit_of_work
