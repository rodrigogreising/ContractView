import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ConfigurationAdmin, nextAdministratorAction } from "./ConfigurationAdmin";
import type { Configuration } from "../../domain/types";
import type { GovernedConfigurationVersionDto } from "../../generated/contracts";
import type { DocumentClusterView, DocumentProfileView } from "./types";

const configuration: Configuration = {
  servicePeriod: { start: "2026-06-01", end: "2026-06-30" },
  categories: [{ code: "program", label: "Program", limit: "1000.00" }],
  requiredEvidence: ["vendor_invoice"],
  ledgerControlTotal: "1000.00",
  rules: [
    { code: "SERVICE_PERIOD", severity: "blocker", enabled: true },
    { code: "POSSIBLE_DUPLICATE", severity: "warning", enabled: true, amountTolerance: "0.00", dayWindow: 2 },
  ],
  workflowLabels: { draft: "Draft", submitted: "Submitted", returned: "Returned", approved: "Approved" },
  package: { label: "Package", invoiceTitle: "Invoice", includeValidationSummary: true, includeManifest: true },
};

const version = (state: GovernedConfigurationVersionDto["state"]): GovernedConfigurationVersionDto => ({
  id: `config-${state}`,
  contractId: "contract-synthetic",
  version: 2,
  configuration,
  state,
  active: state === "active",
  payloadHash: "a".repeat(64),
  testEvidence: state === "draft" ? null : {
    id: "test-v2",
    suiteVersion: "configuration-suite-v1",
    payloadHash: "a".repeat(64),
    resultHash: "b".repeat(64),
    passed: true,
    checks: [{ code: "DOCUMENT_PROFILE_REFERENCES", passed: true }],
    testedBy: "admin",
    testedRole: "configuration_administrator",
    testedOrganizationId: "org-operations",
    rationale: "Exact evidence",
    createdAt: "2026-07-13T00:00:00Z",
  },
  approval: ["approved", "active", "superseded", "retired"].includes(state) ? {
    id: "approval-v2",
    testEvidenceId: "test-v2",
    approvedBy: "admin",
    approvedRole: "configuration_administrator",
    approvedOrganizationId: "org-operations",
    rationale: "Human approval",
    approvalHash: "c".repeat(64),
    approvedAt: "2026-07-13T00:01:00Z",
  } : null,
  history: [],
});

const profile = (state: DocumentProfileView["state"]): DocumentProfileView => ({
  profile: {
    id: "profile-vendor-en-v1",
    contractId: "contract-synthetic",
    profileKey: "vendor_invoice_en",
    version: 1,
    lifecycle: state,
    artifactClass: "vendor_invoice",
    languageTag: "en",
    vendorAliases: ["Synthetic Vendor A"],
    requiredFields: [
      { name: "vendor", fieldType: "string", required: true, sourceLabels: ["Vendor"], normalization: "trim" },
      { name: "date", fieldType: "date", required: true, sourceLabels: ["Date"], normalization: "iso_date" },
      { name: "amount", fieldType: "decimal", required: true, sourceLabels: ["Amount"], normalization: "decimal" },
      { name: "sourceReference", fieldType: "identifier", required: true, sourceLabels: ["Expense reference"], normalization: "identifier" },
    ],
    ledgerMatchRule: { sourceReferenceField: "sourceReference", amountField: "amount", dateField: "date", vendorField: "vendor", required: true },
    fingerprintSpecification: { id: "document-layout-signals", version: "document-layout-signals-v1", algorithm: "sha256-canonical-json-v1", signals: ["artifact_media_type"] },
    acceptedFingerprints: ["d".repeat(64)],
    fixtureSet: { kind: "profile_fixture_set", id: "fixtures-v1", version: "1", sha256: "e".repeat(64) },
    evaluationEvidence: { kind: "profile_evaluation", id: "evaluation-v1", version: "document-profile-fixtures-v1", sha256: "f".repeat(64) },
    contentHash: "1".repeat(64),
  },
  state,
  lastAction: "activate",
  lastRationale: "Synthetic fixture proof",
  lastEventHash: "2".repeat(64),
  lastTransitionAt: "2026-07-13T00:00:00Z",
  fixtureSet: {
    id: "fixtures-v1",
    version: "1",
    contentHash: "e".repeat(64),
    cases: [
      { id: "supported-1", caseKind: "supported_layout", filename: "synthetic-supported-1.pdf", mediaType: "application/pdf", ocrText: "private fixture transcript", expectedOutcome: "recognized_profile_draft", expectedFields: { vendor: "Synthetic Vendor A", date: "2026-06-01", amount: "10.00", sourceReference: "EXP-001" }, expectedSourceLocations: { vendor: "page=1", date: "page=1", amount: "page=1", sourceReference: "page=1" } },
      { id: "supported-2", caseKind: "supported_layout", filename: "synthetic-supported-2.pdf", mediaType: "application/pdf", ocrText: "second fixture transcript", expectedOutcome: "recognized_profile_draft", expectedFields: { vendor: "Synthetic Vendor A", date: "2026-06-02", amount: "11.00", sourceReference: "EXP-002" }, expectedSourceLocations: { vendor: "page=1", date: "page=1", amount: "page=1", sourceReference: "page=1" } },
      { id: "changed", caseKind: "changed_layout", filename: "synthetic-changed.pdf", mediaType: "application/pdf", ocrText: "changed fixture transcript", expectedOutcome: "needs_profile_review", expectedFields: {}, expectedSourceLocations: {} },
      { id: "unknown", caseKind: "unknown_layout", filename: "synthetic-unknown.pdf", mediaType: "application/pdf", ocrText: "unknown fixture transcript", expectedOutcome: "needs_profile_review", expectedFields: {}, expectedSourceLocations: {} },
    ],
  },
  evaluationEvidence: {
    id: "evaluation-v1",
    profileVersion: { kind: "document_profile", id: "profile-vendor-en-v1", version: 1, sha256: "1".repeat(64) },
    fixtureSet: { kind: "profile_fixture_set", id: "fixtures-v1", version: "1", sha256: "e".repeat(64) },
    suiteVersion: "document-profile-fixtures-v1",
    ocrVersion: "fixture-transcript-v1",
    parserVersion: "deterministic-document-profile-parser-v1",
    results: ["supported-1", "supported-2", "changed", "unknown"].map((fixtureId) => ({ fixtureId, passed: true, outcome: fixtureId.startsWith("supported") ? "recognized_profile_draft" : "needs_profile_review", fingerprint: "3".repeat(64), normalizedFieldsHash: "4".repeat(64), sourceLocationsHash: "5".repeat(64) })),
    supportedFieldExactness: 1,
    sourceLocationExactness: 1,
    unknownSafeRoutingRate: 1,
    passed: true,
    resultHash: "6".repeat(64),
  },
  approval: {
    id: "profile-approval-v1",
    evaluationId: "evaluation-v1",
    approvedBy: "admin",
    approvedRole: "configuration_administrator",
    approvedOrganizationId: "org-operations",
    rationale: "Exact fixtures",
    approvalHash: "7".repeat(64),
    approvedAt: "2026-07-13T00:00:00Z",
  },
  activeConfigurationVersionId: state === "active" ? "config-active" : null,
  activatedAt: state === "active" ? "2026-07-13T00:00:00Z" : null,
  createdBy: "admin",
  createdRole: "configuration_administrator",
  createdOrganizationId: "org-operations",
  createdAt: "2026-07-13T00:00:00Z",
});

const cluster = (confirmed: boolean): DocumentClusterView => ({
  id: confirmed ? "cluster-confirmed" : "cluster-suggested",
  clusterKey: confirmed ? "confirmed" : "suggested",
  languageTag: "und",
  status: confirmed ? "confirmed_as_draft" : "suggested",
  canonical: false,
  projectionHash: "8".repeat(64),
  createdAt: "2026-07-13T00:00:00Z",
  fingerprint: { id: "fingerprint-1", specificationVersion: "document-layout-signals-v1", sha256: "9".repeat(64) },
  sourceArtifact: { id: "artifact-1", filename: confirmed ? "synthetic-confirmed.pdf" : "synthetic-unknown.pdf", sha256: "a".repeat(64) },
  memberCount: 1,
  association: confirmed ? {
    id: "association-1",
    profileKey: "vendor_invoice_candidate",
    status: "draft",
    confirmedBy: "admin",
    confirmedRole: "configuration_administrator",
    confirmedOrganizationId: "org-operations",
    rationale: "Review this synthetic layout",
    associationHash: "b".repeat(64),
    createdAt: "2026-07-13T00:00:00Z",
  } : null,
});

const baseProps = {
  configuration,
  active: { id: "config-active", version: 1, activatedAt: "2026-07-13T00:00:00Z" },
  versions: [version("active")],
  message: "",
  onSave: () => {},
  onTest: () => {},
  onApprove: () => {},
  onActivate: () => {},
  onSupersede: () => {},
  onRetire: () => {},
  onRollback: () => {},
};

describe("Configuration Administrator workspace", () => {
  it("prioritizes safe exception review and clearly distinguishes every lifecycle state", () => {
    expect(nextAdministratorAction([version("approved")], [profile("active")], [cluster(false)]))
      .toBe("Review 1 changed or unknown document layout.");
    const html = renderToString(
      <ConfigurationAdmin {...baseProps} profiles={[profile("active")]} clusters={[cluster(false)]} />,
    );
    expect(html).toContain("Configuration control plane");
    expect(html).toContain("Safe exception queue");
    for (const state of ["draft", "tested", "approved", "active", "superseded", "retired"]) {
      expect(html).toContain(`status-${state}`);
    }
  });

  it("requires successful evidence, human approval, rationale, and explicit impact confirmation before activation", () => {
    const approved = version("approved");
    const html = renderToString(
      <ConfigurationAdmin
        {...baseProps}
        active={null}
        versions={[approved]}
        initialSection="configuration"
        evidence={{
          detail: approved,
          diff: { contractId: "contract-synthetic", baseVersionId: approved.id, targetVersionId: approved.id, changes: [], projectionHash: "c".repeat(64), canonical: false },
          impact: { configurationVersionId: approved.id, contractId: "contract-synthetic", wouldSupersedeVersionId: null, historicalReferenceVersionId: null, referenceCounts: {}, applicationScope: "future-intake-only", historicalReferencesPreserved: true, projectionHash: "d".repeat(64), canonical: false },
          references: { configurationVersionId: approved.id, references: [], projectionHash: "e".repeat(64), canonical: false },
        }}
      />,
    );
    expect(html).toContain("Explicit activation confirmation");
    expect(html).toContain("I confirm this change applies to future intake only");
    expect(html).toMatch(/<button[^>]*disabled=""[^>]*>Confirm and activate approved version<\/button>/);
    expect(html).not.toContain("Activate approved version</button>");
  });

  it("renders profile setup, fixture evaluation, active history, suggestions, and confirmed draft associations without fixture transcripts", () => {
    const html = renderToString(
      <ConfigurationAdmin
        {...baseProps}
        initialSection="profiles"
        profiles={[profile("active"), { ...profile("draft"), profile: { ...profile("draft").profile, id: "profile-draft", version: 2, lifecycle: "draft" }, evaluationEvidence: null, approval: null, activeConfigurationVersionId: null, activatedAt: null }]}
        clusters={[cluster(false), cluster(true)]}
      />,
    );
    expect(html).toContain("Profile setup");
    expect(html).toContain("Create immutable profile draft");
    expect(html).toContain("Field exactness");
    expect(html).toContain("Safe changed/unknown routing");
    expect(html).toContain("synthetic-supported-1.pdf");
    expect(html).toContain("Test profile fixtures");
    expect(html).toContain("Use exact profile in configuration draft");
    expect(html).toContain("Document exception queue");
    expect(html).toContain("Confirm suggestion as draft association");
    expect(html).toContain("confirmed draft");
    expect(html).toContain("It is not active configuration");
    expect(html).not.toContain("private fixture transcript");
  });

  it("exposes governance failures through an accessible alert", () => {
    const html = renderToString(
      <ConfigurationAdmin {...baseProps} message="Unauthorized configuration action failed" />,
    );
    expect(html).toContain('role="alert"');
    expect(html).toContain("Unauthorized configuration action failed");
  });
});
