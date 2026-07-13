import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from argon2 import PasswordHasher
from .runtime import clear_bucket, database, ensure_bucket
from .domain.document_intake import content_hash

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
    profile_catalog = json.loads((FIXTURES / "document-intake-catalog.json").read_text())
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
        for assignment in scenario["accessAssignments"]:
            connection.execute(
                """insert into contract_role_assignments
                   (contract_id, user_id, role, agency_organization_id)
                   values (%s,%s,%s,%s)
                   on conflict (contract_id,user_id,role) do update
                   set agency_organization_id=excluded.agency_organization_id""",
                (
                    assignment["contractId"],
                    assignment["userId"],
                    assignment["role"],
                    assignment["agencyOrganizationId"],
                ),
            )
        for category in scenario["budgetCategories"]:
            connection.execute(
                "insert into budget_categories(id, contract_id, name, budget_limit) values (%s,%s,%s,%s) on conflict (id) do update set name=excluded.name, budget_limit=excluded.budget_limit",
                (category["id"], contract["id"], category["name"], category["limit"]),
            )
        profile_references = []
        for catalog_item in profile_catalog["profiles"]:
            profile = catalog_item["profile"]
            fixture_set = catalog_item["fixtureSet"]
            evaluation = catalog_item["evaluationEvidence"]
            profile_references.append(
                {
                    "kind": "document_profile",
                    "id": profile["id"],
                    "version": profile["version"],
                    "sha256": profile["contentHash"],
                }
            )
            connection.execute(
                """insert into document_profile_versions
                   (id,contract_id,profile_key,version,payload,content_hash,created_by,created_role,created_organization_id)
                   values (%s,%s,%s,%s,%s,%s,'user-config-admin','configuration_administrator','org-operations')
                   on conflict (id) do nothing""",
                (
                    profile["id"], contract["id"], profile["profileKey"],
                    profile["version"], json.dumps(profile), profile["contentHash"],
                ),
            )
            connection.execute(
                """insert into document_profile_fixture_sets
                   (id,profile_version_id,contract_id,version,cases,content_hash,created_by)
                   values (%s,%s,%s,%s,%s,%s,'user-config-admin')
                   on conflict (id) do nothing""",
                (
                    fixture_set["id"], profile["id"], contract["id"],
                    fixture_set["version"], json.dumps(fixture_set["cases"]),
                    fixture_set["contentHash"],
                ),
            )
            connection.execute(
                """insert into document_profile_evaluations
                   (id,profile_version_id,fixture_set_id,contract_id,suite_version,ocr_version,parser_version,results,
                    supported_field_exactness,source_location_exactness,unknown_safe_routing_rate,passed,result_hash,
                    tested_by,tested_role,tested_organization_id,rationale)
                   values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                           'user-config-admin','configuration_administrator','org-operations',%s)
                   on conflict (id) do nothing""",
                (
                    evaluation["id"], profile["id"], fixture_set["id"], contract["id"],
                    evaluation["suiteVersion"], evaluation["ocrVersion"],
                    evaluation["parserVersion"], json.dumps(evaluation["results"]),
                    evaluation["supportedFieldExactness"],
                    evaluation["sourceLocationExactness"],
                    evaluation["unknownSafeRoutingRate"], evaluation["passed"],
                    evaluation["resultHash"], "Closed synthetic fixture evaluation",
                ),
            )
            approval_id = f"profile-approval-{profile['profileKey']}-v{profile['version']}"
            approval_body = {
                "id": approval_id,
                "profileVersionId": profile["id"],
                "evaluationId": evaluation["id"],
                "approvedBy": "user-config-admin",
                "approvedRole": "configuration_administrator",
                "approvedOrganizationId": "org-operations",
                "rationale": "Approve closed synthetic document profile",
            }
            connection.execute(
                """insert into document_profile_approvals
                   (id,profile_version_id,evaluation_id,contract_id,approved_by,approved_role,
                    approved_organization_id,rationale,approval_hash)
                   values (%s,%s,%s,%s,'user-config-admin','configuration_administrator','org-operations',%s,%s)
                   on conflict (id) do nothing""",
                (
                    approval_id, profile["id"], evaluation["id"], contract["id"],
                    approval_body["rationale"], content_hash(approval_body),
                ),
            )
            lifecycle = [
                ("draft", "create", None, None, "Create closed synthetic profile draft"),
                ("tested", "test", evaluation["id"], None, "Test closed synthetic fixtures"),
                ("approved", "approve_configuration", evaluation["id"], approval_id, "Approve exact tested profile"),
            ]
            for state, action, evaluation_id, lifecycle_approval_id, rationale in lifecycle:
                event_id = f"profile-lifecycle-{profile['profileKey']}-v{profile['version']}-{state}"
                event_body = {
                    "id": event_id,
                    "profileVersionId": profile["id"],
                    "state": state,
                    "action": action,
                    "actorId": "user-config-admin",
                    "actorRole": "configuration_administrator",
                    "actorOrganizationId": "org-operations",
                    "rationale": rationale,
                    "evaluationId": evaluation_id,
                    "approvalId": lifecycle_approval_id,
                }
                connection.execute(
                    """insert into document_profile_lifecycle_events
                       (id,profile_version_id,contract_id,state,action,actor_id,actor_role,
                        actor_organization_id,rationale,evaluation_id,approval_id,event_hash)
                       values (%s,%s,%s,%s,%s,'user-config-admin','configuration_administrator','org-operations',%s,%s,%s,%s)
                       on conflict (id) do nothing""",
                    (
                        event_id, profile["id"], contract["id"], state, action,
                        rationale, evaluation_id, lifecycle_approval_id,
                        content_hash(event_body),
                    ),
                )
        configuration = {
            **scenario["initialConfiguration"],
            "documentProfiles": profile_references,
        }
        connection.execute(
            "insert into configuration_drafts(contract_id, payload, updated_by, revision) values (%s,%s,%s,1) on conflict (contract_id) do update set payload=excluded.payload, updated_by=excluded.updated_by, updated_at=now(), revision=configuration_drafts.revision + case when configuration_drafts.payload is distinct from excluded.payload then 1 else 0 end",
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


def fingerprint() -> None:
    """Print a stable fingerprint of the synthetic reset state."""
    queries = {
        "migrations": "select version from schema_migrations order by version",
        "organizations": "select id,name,kind from organizations order by id",
        "users": "select id,organization_id,email,role from users order by id",
        "contracts": "select id,agency_organization_id,ngo_organization_id,contract_start,contract_end,service_period_start,service_period_end,currency from contracts order by id",
        "assignments": "select contract_id,user_id,role,agency_organization_id from contract_role_assignments order by contract_id,user_id,role",
        "budgets": "select id,contract_id,name,budget_limit::text from budget_categories order by id",
        "configuration": "select contract_id,payload,revision from configuration_drafts order by contract_id",
        "document_profiles": "select id,contract_id,profile_key,version,content_hash from document_profile_versions order by id",
        "profile_fixtures": "select id,profile_version_id,version,content_hash from document_profile_fixture_sets order by id",
        "profile_evaluations": "select id,profile_version_id,result_hash,passed from document_profile_evaluations order by id",
    }
    with database() as connection:
        state = {
            name: [list(row) for row in connection.execute(query).fetchall()]
            for name, query in queries.items()
        }
    canonical = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str)
    print(sha256(canonical.encode()).hexdigest())

def main() -> None:
    parser = argparse.ArgumentParser(description="ContractView POC database management")
    parser.add_argument("command", choices=("migrate", "seed", "reset", "fingerprint"))
    command = parser.parse_args().command
    {"migrate": migrate, "seed": seed, "reset": reset, "fingerprint": fingerprint}[command]()

if __name__ == "__main__":
    main()
