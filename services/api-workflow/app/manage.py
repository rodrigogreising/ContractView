import argparse
import json
import os
from pathlib import Path
from argon2 import PasswordHasher
from .runtime import clear_bucket, database, ensure_bucket

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"
FIXTURES = Path(os.environ.get("FIXTURE_ROOT", "packages/test-fixtures"))

def migrate() -> None:
    with database() as connection:
        connection.execute("create table if not exists schema_migrations (version text primary key, applied_at timestamptz not null default now())")
        for migration in sorted(MIGRATIONS.glob("*.sql")):
            exists = connection.execute("select 1 from schema_migrations where version = %s", (migration.name,)).fetchone()
            if exists:
                continue
            connection.execute(migration.read_text())
            connection.execute("insert into schema_migrations(version) values (%s)", (migration.name,))
        connection.commit()
    ensure_bucket()

def seed() -> None:
    migrate()
    scenario = json.loads((FIXTURES / "scenario.json").read_text())
    password_hasher = PasswordHasher()
    with database() as connection:
        connection.execute("insert into poc_metadata(key, value) values ('fixture_version', 'poc-v1') on conflict (key) do update set value = excluded.value")
        for organization in scenario["organizations"]:
            connection.execute(
                "insert into organizations(id, name, kind) values (%s, %s, %s) on conflict (id) do update set name = excluded.name, kind = excluded.kind",
                (organization["id"], organization["name"], organization["kind"]),
            )
        for persona in scenario["personas"]:
            exists = connection.execute("select 1 from users where id = %s", (persona["id"],)).fetchone()
            if not exists:
                connection.execute(
                    "insert into users(id, organization_id, display_name, email, role, password_hash) values (%s, %s, %s, %s, %s, %s)",
                    (persona["id"], persona["organizationId"], persona["displayName"], persona["email"], persona["role"], password_hasher.hash(persona["password"])),
                )
        contract = scenario["contract"]
        connection.execute(
            "insert into contracts(id, name, agency_organization_id, ngo_organization_id, contract_start, contract_end, service_period_start, service_period_end, currency) values (%s,%s,%s,%s,%s,%s,%s,%s,%s) on conflict (id) do update set name=excluded.name, service_period_start=excluded.service_period_start, service_period_end=excluded.service_period_end",
            (contract["id"], contract["name"], contract["agencyOrganizationId"], contract["ngoOrganizationId"], contract["contractStart"], contract["contractEnd"], contract["servicePeriodStart"], contract["servicePeriodEnd"], contract["currency"]),
        )
        for category in scenario["budgetCategories"]:
            connection.execute(
                "insert into budget_categories(id, contract_id, name, budget_limit) values (%s,%s,%s,%s) on conflict (id) do update set name=excluded.name, budget_limit=excluded.budget_limit",
                (category["id"], contract["id"], category["name"], category["limit"]),
            )
        configuration = scenario["initialConfiguration"]
        connection.execute(
            "insert into configuration_drafts(contract_id, payload, updated_by) values (%s,%s,%s) on conflict (contract_id) do update set payload=excluded.payload, updated_by=excluded.updated_by, updated_at=now()",
            (contract["id"], json.dumps(configuration), "user-config-admin"),
        )
        connection.commit()

def reset() -> None:
    with database() as connection:
        connection.execute("drop schema public cascade")
        connection.execute("create schema public")
        connection.commit()
    clear_bucket()
    migrate()
    seed()

def main() -> None:
    parser = argparse.ArgumentParser(description="ContractView POC database management")
    parser.add_argument("command", choices=("migrate", "seed", "reset"))
    command = parser.parse_args().command
    {"migrate": migrate, "seed": seed, "reset": reset}[command]()

if __name__ == "__main__":
    main()
