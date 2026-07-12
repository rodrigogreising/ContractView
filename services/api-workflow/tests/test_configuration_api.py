import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.http.api import app
from app.runtime import database


CONTRACT = "contract-synthetic-agency-ngo-2026"
FIXTURE = Path("/app/fixtures/scenario.json")


def _governance_count() -> tuple[int, int, int, int]:
    with database() as connection:
        return tuple(
            connection.execute(f"select count(*) from {table}").fetchone()[0]
            for table in (
                "configuration_versions",
                "configuration_test_evidence",
                "configuration_approvals",
                "configuration_lifecycle_events",
            )
        )


def test_normal_session_drives_configuration_api_without_direct_activation_shortcut():
    payload = json.loads(FIXTURE.read_text())["initialConfiguration"]
    payload["package"]["label"] = "HTTP-governed synthetic package"

    with TestClient(app) as client:
        login = client.post(
            "/auth/login",
            json={
                "email": "configuration.admin@example.test",
                "password": "Demo-Config-2026!",
            },
        )
        assert login.status_code == 200
        assert login.json()["user"]["role"] == "configuration_administrator"
        contexts = client.get("/auth/contracts")
        assert contexts.status_code == 200
        assert contexts.json()["contracts"] == [{
            "contractId": CONTRACT,
            "contractName": "Synthetic Community Services Contract 2026",
            "agencyOrganizationId": "org-government",
            "agencyOrganizationName": "Synthetic Public Agency",
            "ngoOrganizationId": "org-ngo",
            "ngoOrganizationName": "Synthetic Community Nonprofit",
        }]

        saved = client.put(
            f"/configuration/draft?contractId={CONTRACT}", json=payload
        )
        assert saved.status_code == 200

        before = _governance_count()
        prohibited = client.post(f"/configuration/activate?contractId={CONTRACT}")
        assert prohibited.status_code == 422
        assert _governance_count() == before

        tested = client.post(
            f"/configuration/test?contractId={CONTRACT}",
            json={"rationale": "HTTP deterministic suite passed"},
        )
        assert tested.status_code == 200
        candidate = tested.json()["configurationVersion"]
        assert candidate["state"] == "tested"
        assert candidate["testEvidence"]["passed"] is True

        preactivation = client.get(f"/configuration/lifecycle?contractId={CONTRACT}")
        assert preactivation.status_code == 200
        tested_version = {
            item["id"]: item for item in preactivation.json()["versions"]
        }[candidate["id"]]
        assert tested_version["active"] is False
        assert tested_version["state"] == "tested"

        approved = client.post(
            f"/configuration/versions/{candidate['id']}/approve",
            json={"rationale": "Human administrator approved HTTP evidence"},
        )
        assert approved.status_code == 200
        assert approved.json()["configurationVersion"]["approvalId"]

        current = client.get(f"/configuration/active?contractId={CONTRACT}")
        assert current.status_code == 200
        active = current.json()["configuration"]
        if active:
            promoted = client.post(
                f"/configuration/versions/{active['id']}/supersede",
                json={
                    "successorVersionId": candidate["id"],
                    "rationale": "Promote approved HTTP successor prospectively",
                },
            )
        else:
            promoted = client.post(
                "/configuration/activate",
                json={
                    "versionId": candidate["id"],
                    "rationale": "Initial prospective HTTP activation",
                },
            )
        assert promoted.status_code == 200

        lifecycle = client.get(f"/configuration/lifecycle?contractId={CONTRACT}")
        assert lifecycle.status_code == 200
        governed = {
            item["id"]: item for item in lifecycle.json()["versions"]
        }[candidate["id"]]
        assert governed["active"] is True
        assert [event["state"] for event in governed["history"]] == [
            "tested",
            "approved",
            "active",
        ]
        assert all(event["actorRole"] == "configuration_administrator" for event in governed["history"])

        assert client.post("/auth/logout").status_code == 204
        assert client.get("/auth/contracts").status_code == 401
        assert client.get(f"/configuration/lifecycle?contractId={CONTRACT}").status_code == 401
