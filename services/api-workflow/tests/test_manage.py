from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"

def test_migrations_are_numbered_and_nonempty() -> None:
    migrations = sorted(MIGRATIONS.glob("*.sql"))
    assert migrations
    assert migrations[0].name == "001_runtime.sql"
    assert all(Path(migration).read_text().strip() for migration in migrations)
    assert [int(migration.name.split("_", 1)[0]) for migration in migrations] == list(
        range(1, len(migrations) + 1)
    )
