import json
from pathlib import Path
import uuid

import psycopg
import pytest

from app.access_scope import artifact_scope, configuration_scope
from app.artifacts import download_artifact
from app.authorization import Action, Actor, ForbiddenError, Role, is_allowed
from app.configuration import update_draft
from app.runtime import database


FIXTURE = Path("/app/fixtures/scenario.json")
APP_ROOT = Path(__file__).resolve().parent.parent / "app"
CONTRACT = "contract-metro-harbor-2026"
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
AUDITOR = Actor("user-auditor", "org-oversight", Role.AUDITOR)
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)


def test_application_scope_construction_is_centralized() -> None:
    constructors = [
        path.relative_to(APP_ROOT).as_posix()
        for path in APP_ROOT.rglob("*.py")
        if "ResourceScope(" in path.read_text()
    ]
    assert constructors == ["application/commands/access_scope.py"]


def _draft_payload() -> dict:
    return json.loads(FIXTURE.read_text())["initialConfiguration"]


def _mutation_fingerprint() -> tuple:
    tables = (
        "configuration_drafts", "configuration_versions", "configuration_test_evidence",
        "configuration_approvals", "configuration_lifecycle_events",
        "configuration_active_versions", "artifacts", "artifact_relations",
        "ingestion_jobs", "extraction_field_reviews", "invoice_versions", "invoice_lines",
        "validation_runs", "attestations", "packages", "submissions", "government_decisions",
        "domain_events", "field_lineage",
    )
    with database() as connection:
        return tuple(
            (
                table,
                *connection.execute(
                    f"""select count(*),md5(coalesce(string_agg(to_jsonb(t)::text,'|'
                         order by to_jsonb(t)::text),'')) from {table} t"""
                ).fetchone(),
            )
            for table in tables
        )


def _other_contract() -> tuple[str, str]:
    suffix = uuid.uuid4().hex[:10]
    organization_id = f"org-other-{suffix}"
    contract_id = f"contract-other-{suffix}"
    with database() as connection:
        connection.execute(
            "insert into organizations(id,name,kind) values (%s,%s,'ngo')",
            (organization_id, f"Other synthetic NGO {suffix}"),
        )
        connection.execute(
            """insert into contracts
               (id,name,agency_organization_id,ngo_organization_id,contract_start,contract_end,
                service_period_start,service_period_end,currency)
               values (%s,%s,'org-government',%s,'2026-01-01','2026-12-31','2026-06-01','2026-06-30','USD')""",
            (contract_id, f"Other synthetic contract {suffix}", organization_id),
        )
        connection.commit()
    return contract_id, organization_id


def test_configuration_admin_scope_requires_persisted_assignment() -> None:
    assigned = configuration_scope(ADMIN, CONTRACT)
    assert assigned.canonical is True
    assert assigned.owner_organization_id == "org-government"
    assert assigned.actor_assigned is True
    assert is_allowed(ADMIN, Action.UPDATE, assigned)

    unassigned = Actor("user-ngo-preparer", "org-ngo", Role.CONFIGURATION_ADMINISTRATOR)
    denied = configuration_scope(unassigned, CONTRACT)
    assert denied.actor_assigned is False
    assert not is_allowed(unassigned, Action.UPDATE, denied)


def test_assignment_migration_rejects_noncanonical_agency() -> None:
    before = _mutation_fingerprint()
    with pytest.raises(psycopg.errors.RaiseException, match="canonical contract"):
        with database() as connection:
            connection.execute(
                """insert into contract_role_assignments
                   (contract_id,user_id,role,agency_organization_id)
                   values (%s,%s,%s,%s)""",
                (CONTRACT, "user-config-admin", "configuration_administrator", "org-ngo"),
            )
    assert _mutation_fingerprint() == before


def test_cross_tenant_contract_denial_has_zero_database_mutation() -> None:
    other_contract, _ = _other_contract()
    before = _mutation_fingerprint()
    with pytest.raises(ForbiddenError):
        update_draft(ADMIN, other_contract, _draft_payload())
    assert _mutation_fingerprint() == before


def test_unassigned_admin_denial_preserves_existing_row_content() -> None:
    unassigned = Actor("user-ngo-preparer", "org-ngo", Role.CONFIGURATION_ADMINISTRATOR)
    payload = _draft_payload()
    payload["package"]["label"] = "unauthorized same-row update"
    before = _mutation_fingerprint()
    with pytest.raises(ForbiddenError):
        update_draft(unassigned, CONTRACT, payload)
    assert _mutation_fingerprint() == before


def test_indirect_artifact_reference_denial_has_zero_database_mutation() -> None:
    other_contract, other_ngo = _other_contract()
    artifact_id = f"artifact-other-{uuid.uuid4().hex}"
    with database() as connection:
        connection.execute(
            """insert into artifacts
               (id,contract_id,organization_id,agency_organization_id,object_key,filename,
                media_type,byte_size,sha256,artifact_kind,created_by)
               values (%s,%s,%s,'org-government',%s,'other.txt','text/plain',0,%s,'original','user-ngo-preparer')""",
            (artifact_id, other_contract, other_ngo, f"other/{artifact_id}", "0" * 64),
        )
        connection.commit()
    before = _mutation_fingerprint()
    with pytest.raises(ForbiddenError):
        download_artifact(PREPARER, artifact_id)
    assert _mutation_fingerprint() == before


def test_auditor_assignment_does_not_expose_unsubmitted_artifact() -> None:
    artifact_id = f"artifact-unsubmitted-{uuid.uuid4().hex}"
    with database() as connection:
        connection.execute(
            """insert into artifacts
               (id,contract_id,organization_id,agency_organization_id,object_key,filename,
                media_type,byte_size,sha256,artifact_kind,created_by)
               values (%s,%s,'org-ngo','org-government',%s,'draft.txt','text/plain',0,%s,'original','user-ngo-preparer')""",
            (artifact_id, CONTRACT, f"draft/{artifact_id}", "0" * 64),
        )
        connection.commit()
    draft_scope = artifact_scope(AUDITOR, artifact_id)
    assert draft_scope.actor_assigned is True
    assert draft_scope.submitted is False
    assert not is_allowed(AUDITOR, Action.READ, draft_scope)

    with database() as connection:
        connection.execute("update artifacts set submitted=true where id=%s", (artifact_id,))
        connection.commit()
    assert is_allowed(AUDITOR, Action.READ, artifact_scope(AUDITOR, artifact_id))
