import pytest

from app.adapters.persistence.postgres import (
    PostgresRepository,
    PostgresUnitOfWork,
    postgres_transaction,
    statement_catalog,
)
from app.application.ports.statements import Statement


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def execute(self, sql, parameters=()):
        self.executed.append((sql, parameters))
        return self

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def statement_where(predicate):
    name = next(name for name, definition in statement_catalog().items() if predicate(definition))
    return Statement(name)


def test_repository_rejects_inline_sql_and_unknown_statement_types():
    repository = PostgresRepository(FakeConnection(), "artifacts")
    with pytest.raises(TypeError):
        repository.execute("select * from artifacts")


def test_repository_cannot_execute_another_capability_statement():
    validation_statement = statement_where(
        lambda definition: definition["owner"] == "validation"
        and definition["kind"] != "declared-read-model"
    )
    with pytest.raises(PermissionError):
        PostgresRepository(FakeConnection(), "artifacts").execute(validation_statement)


def test_declared_read_models_use_the_read_model_repository_only():
    read_model = statement_where(lambda definition: definition["kind"] == "declared-read-model")
    with pytest.raises(PermissionError):
        PostgresRepository(FakeConnection(), statement_catalog()[read_model.value]["owner"]).execute(read_model)
    connection = FakeConnection()
    PostgresRepository(connection, "read_models").execute(read_model)
    assert len(connection.executed) == 1


def test_unit_of_work_exposes_every_capability_repository_and_transaction_control():
    connection = FakeConnection()
    unit_of_work = PostgresUnitOfWork(connection)
    for name in (
        "identity", "configuration", "artifacts", "extraction", "invoices",
        "validation", "packages", "workflow", "provenance", "platform", "read_models",
    ):
        assert isinstance(getattr(unit_of_work, name), PostgresRepository)
    unit_of_work.commit()
    unit_of_work.rollback()
    assert connection.committed and connection.rolled_back


def test_transaction_rolls_back_uncommitted_work_and_closes(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr("app.adapters.persistence.postgres.psycopg.connect", lambda _: connection)
    with postgres_transaction("postgresql://synthetic"):
        pass
    assert connection.rolled_back and connection.closed and not connection.committed


def test_transaction_preserves_explicit_commit_and_closes(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr("app.adapters.persistence.postgres.psycopg.connect", lambda _: connection)
    with postgres_transaction("postgresql://synthetic") as unit_of_work:
        unit_of_work.commit()
    assert connection.committed and connection.closed and not connection.rolled_back


def test_transaction_rolls_back_exceptions_and_closes(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr("app.adapters.persistence.postgres.psycopg.connect", lambda _: connection)
    with pytest.raises(RuntimeError, match="synthetic failure"):
        with postgres_transaction("postgresql://synthetic"):
            raise RuntimeError("synthetic failure")
    assert connection.rolled_back and connection.closed and not connection.committed


def test_every_write_statement_has_exactly_one_capability_owner():
    for definition in statement_catalog().values():
        if definition["operation"] == "write":
            assert definition["writeTables"]
            assert definition["owner"] in definition["sourceOwners"]
