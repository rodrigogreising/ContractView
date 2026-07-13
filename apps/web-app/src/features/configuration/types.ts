import type {
  ActorRole,
  DocumentProfileVersionContract,
  ProfileEvaluationEvidenceContract,
  ProfileFixtureCaseContract,
  ProfileFixtureSetContract,
  VersionReference,
} from "../../generated/contracts";

export interface ProfileApprovalView {
  id: string;
  evaluationId: string;
  approvedBy: string;
  approvedRole: ActorRole;
  approvedOrganizationId: string;
  rationale: string;
  approvalHash: string;
  approvedAt: string;
}

export interface DocumentProfileView {
  profile: DocumentProfileVersionContract;
  state: DocumentProfileVersionContract["lifecycle"];
  lastAction: string;
  lastRationale: string;
  lastEventHash: string;
  lastTransitionAt: string;
  fixtureSet: ProfileFixtureSetContract;
  evaluationEvidence: ProfileEvaluationEvidenceContract | null;
  approval: ProfileApprovalView | null;
  activeConfigurationVersionId: string | null;
  activatedAt: string | null;
  createdBy: string;
  createdRole: ActorRole;
  createdOrganizationId: string;
  createdAt: string;
}

export interface DocumentClusterView {
  id: string;
  clusterKey: string;
  languageTag: string;
  status: "suggested" | "confirmed_as_draft";
  canonical: false;
  projectionHash: string;
  createdAt: string;
  fingerprint: {
    id: string;
    specificationVersion: string;
    sha256: string;
  };
  sourceArtifact: { id: string; filename: string; sha256: string };
  memberCount: number;
  association: {
    id: string;
    profileKey: string;
    status: "draft";
    confirmedBy: string;
    confirmedRole: ActorRole;
    confirmedOrganizationId: string;
    rationale: string;
    associationHash: string;
    createdAt: string;
  } | null;
}

export interface ProfileDraftDefinition {
  profileKey: string;
  artifactClass: string;
  languageTag: string;
  vendorAliases: string[];
  requiredFields: DocumentProfileVersionContract["requiredFields"];
  ledgerMatchRule: DocumentProfileVersionContract["ledgerMatchRule"];
  fingerprintSpecification: DocumentProfileVersionContract["fingerprintSpecification"];
  predecessorVersionId?: string;
}

export interface ProfileDraftCommand {
  definition: ProfileDraftDefinition;
  fixtures: ProfileFixtureCaseContract[];
  rationale: string;
}

export interface StagedProfileReference {
  profileKey: string;
  reference: VersionReference;
}
