from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

import app.shared_contracts as shared_contracts
from app.authorization import ResourceKind, Role
from app.shared_contracts import (
    ActorReference, ArtifactContract, ArtifactKind, ConfigurationBundleContract,
    ConfigurationLifecycle, EntityContract, EntityType, EventEnvelope, EventType,
    FieldType, IdentityDto, RelationContract, RelationType, RuleDefinition, RuleSeverity,
    TemplateContract, TypedField, VersionReference, ViewContract, WorkflowContract,
)


def reference(kind="invoice", identifier="invoice-1", version=1):
    return VersionReference(kind=kind,id=identifier,version=version)


def test_runtime_authorization_and_events_consume_generated_vocabulary():
    assert Role.NGO_APPROVER.value == "ngo_approver"
    assert ResourceKind.GOVERNMENT_DECISION.value == "government_decision"
    provenance_source=(Path(__file__).resolve().parent.parent/"app"/"provenance.py").read_text()
    assert "EVENT_TYPES = MATERIAL_EVENT_TYPES" in provenance_source
    assert "validation_completed" in {item.value for item in EventType}


def test_identity_dto_preserves_the_existing_public_api_shape():
    identity=IdentityDto(id="u1",display_name="Synthetic User",email="user@example.test",organization_id="o1",organization_name="Synthetic Org",role=Role.AUDITOR)
    assert identity.model_dump(by_alias=True)=={
        "id":"u1","displayName":"Synthetic User","email":"user@example.test",
        "organizationId":"o1","organizationName":"Synthetic Org","role":"auditor",
    }


def test_artifact_field_entity_and_relation_round_trip_to_camel_case():
    artifact=ArtifactContract(id="a1",contract_id="c1",organization_id="o1",kind=ArtifactKind.ORIGINAL,media_type="application/pdf",byte_size=2,sha256="0"*64,version=1)
    field=TypedField(name="amount",field_type=FieldType.DECIMAL,value="10.00",source=reference("artifact","a1"),confidence=.99)
    entity=EntityContract(id="invoice-1",entity_type=EntityType.INVOICE,version=1,fields=[field])
    relation=RelationContract(id="r1",relation_type=RelationType.SUPPORTS,source=reference("artifact","a1"),target=reference(),reason_code="REQUIRED_EVIDENCE")
    assert artifact.model_dump(by_alias=True)["contractId"]=="c1"
    assert entity.model_dump(by_alias=True)["fields"][0]["fieldType"]=="decimal"
    assert relation.model_dump(by_alias=True)["relationType"]=="supports"


def test_rules_workflow_views_templates_events_and_bundle_are_executable():
    actor=ActorReference(user_id="u1",organization_id="o1",role=Role.CONFIGURATION_ADMINISTRATOR)
    workflow=WorkflowContract(id="workflow-1",version=1,states=["draft","submitted"],transitions=[{"fromState":"draft","toState":"submitted","action":"submit","role":"ngo_approver"}])
    view=ViewContract(id="view-1",version=1,role=Role.NGO_PREPARER,fields=["amount"])
    template=TemplateContract(id="template-1",version=1,media_type="application/pdf",content_hash="1"*64)
    rule=RuleDefinition(code="SERVICE_PERIOD",version="v1",severity=RuleSeverity.BLOCKER,enabled=True,parameters={})
    bundle=ConfigurationBundleContract(id="config-1",version=1,lifecycle=ConfigurationLifecycle.APPROVED,scope={"contractId":"c1"},schemas=[reference("schema","s1")],mappings=[reference("mapping","m1")],rules=[rule],workflow=workflow,views=[view],templates=[template],test_evidence=reference("test_evidence","e1"),approval=actor)
    event=EventEnvelope(event_id="event-1",event_type=EventType.CONFIG_ACTIVATED,schema_version=1,actor=actor,organization_id="o1",contract_id="c1",aggregate=reference("configuration","config-1"),occurred_at=datetime.now(UTC),payload={},version_references=[reference("configuration","config-1")])
    assert bundle.model_dump(by_alias=True)["testEvidence"]["id"]=="e1"
    assert event.model_dump(by_alias=True)["schemaVersion"]==1


def test_contracts_reject_unknown_fields_and_invalid_hashes():
    with pytest.raises(ValidationError):
        VersionReference(kind="artifact",id="a1",version=1,sha256="bad")
    with pytest.raises(ValidationError):
        ArtifactContract(id="a1",contract_id="c1",organization_id="o1",kind="original",media_type="x",byte_size=0,sha256="0"*64,version=1,unexpected=True)
    with pytest.raises(ValidationError):
        VersionReference(kind="unknown",id="a1",version=1)
    with pytest.raises(ValidationError):
        RuleDefinition(code="UNKNOWN_RULE",version="v1",severity="blocker",enabled=True,parameters={})
    with pytest.raises(ValidationError):
        RelationContract(id="r1",relation_type="supports",source=reference(),target=reference(),reason_code="UNKNOWN_REASON:EXP-1")


def test_python_requiredness_matches_every_canonical_field_definition():
    for model_name, required_fields in shared_contracts.CONTRACT_REQUIRED_FIELDS.items():
        model=getattr(shared_contracts,model_name)
        actual={name for name,field in model.model_fields.items() if field.is_required()}
        assert actual==required_fields
