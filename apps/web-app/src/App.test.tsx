import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  App,
  ApprovalPanel,
  AuthenticatedWorkspace,
  ConfigurationAdmin,
  ExtractionReview,
  FindingResolutionView,
  GovernmentWorkspace,
  InvoiceDraftView,
  ValidationView,
} from "./App";

describe("authentication shell", () => {
  it("offers every seeded persona through a normal login form", () => {
    const html = renderToString(<App />);
    expect(html).toContain("Synthetic role-based POC");
    expect(html).toContain("Configuration Administrator");
    expect(html).toContain("NGO Preparer");
    expect(html).toContain("Government Reviewer");
    expect(html).toContain('type="password"');
  });
  it("shows real upload controls and processing status only to the NGO preparer", () => {
    const html = renderToString(
      <AuthenticatedWorkspace
        user={{
          id: "preparer",
          displayName: "Synthetic NGO Preparer",
          email: "member@example.test",
          organizationId: "org-ngo",
          organizationName: "Synthetic Community Nonprofit",
          role: "ngo_preparer",
        }}
        jobs={[
          {
            id: "job-1",
            artifact_id: "a-1",
            job_type: "ledger_import",
            status: "running",
            error_message: null,
          },
        ]}
        extractions={[]}
        draft={null}
        configuration={null}
        activeConfiguration={{
          id: "config-v1",
          version: 1,
          activatedAt: "2026-07-11",
        }}
        configurationLifecycle={[]}
        validation={null}
        findings={[]}
        revisionFeedback={null}
        approvalPreview={null}
        attestation={null}
        generatedPackage={null}
        submission={null}
        message=""
        onLogout={() => {}}
        onUpload={() => {}}
        onReview={() => {}}
        onAssemble={() => {}}
        onValidate={() => {}}
        onResolveFinding={() => {}}
        onCorrectRevision={() => {}}
        onAttest={() => {}}
        onGeneratePackage={() => {}}
        onSubmitInvoice={() => {}}
        onSaveConfiguration={() => {}}
        onTestConfiguration={() => {}}
        onApproveConfiguration={() => {}}
        onActivateConfiguration={() => {}}
        onSupersedeConfiguration={() => {}}
        onRetireConfiguration={() => {}}
        onRollbackConfiguration={() => {}}
      />,
    );
    expect(html).toContain("Upload ledger and evidence");
    expect(html).toContain("Upload and process");
    expect(html).toContain("running");
    expect(html).toContain("Synthetic NGO Preparer");
    expect(html).toContain("Synthetic Community Nonprofit");
    expect(html).toContain("Active config v");
  });
  it("shows source, proposal, confidence, accept, and correct controls", () => {
    const html = renderToString(
      <ExtractionReview
        extractions={[
          {
            id: "run-1",
            sourceArtifactId: "artifact-1",
            filename: "vendor-invoice.pdf",
            provider: "tesseract-cli",
            model: "tesseract-5.5.0-eng",
            routingReason: "HUMAN_REVIEW_REQUIRED",
            fields: [
              {
                id: "field-1",
                name: "amount",
                proposedValue: "1820.00",
                reviewedValue: null,
                confidence: "0.9500",
                sourceLocation: "page=1",
                reviewStatus: "proposed",
              },
            ],
          },
        ]}
        onReview={() => {}}
      />,
    );
    expect(html).toContain("View source evidence");
    expect(html).toContain("Proposed:");
    expect(html).toContain("1820.00");
    expect(html).toContain("Confidence:");
    expect(html).toContain("95");
    expect(html).toContain("Accept");
    expect(html).toContain("Correct");
  });
  it("renders stable draft totals, budgets, evidence, extraction, and findings", () => {
    const html = renderToString(
      <InvoiceDraftView
        draft={{
          id: "invoice-1",
          version: 1,
          configurationVersionId: "config-v1",
          state: "draft",
          total: "10130.00",
          categories: [
            {
              name: "Personnel",
              claimed: "4200.00",
              limit: "60000.00",
              available: "55800.00",
            },
          ],
          lines: [
            {
              expenseKey: "EXP-003",
              date: "2026-06-18",
              vendor: "Synthetic Program Supplies Vendor B",
              description: "Workshop materials",
              category: "Program Supplies",
              amount: "1280.00",
              ledgerArtifactId: "ledger",
              ledgerSource: "CSV!F4",
              evidenceArtifactId: "evidence",
              extractionStatus: "corrected",
            },
          ],
          findings: [],
        }}
      />,
    );
    expect(html).toContain("Invoice v");
    expect(html).toContain("Total requested");
    expect(html).toContain("Budgeted");
    expect(html).toContain("Remaining");
    expect(html).toContain("10130.00");
    expect(html).toContain("CSV!F4");
    expect(html).toContain("corrected");
    expect(html).toContain("Supporting evidence");
    expect(html).toContain("No unresolved assembly findings");
  });
  it("renders bounded category, five-rule, labels, preview, save, and activation controls", () => {
    const html = renderToString(
      <ConfigurationAdmin
        configuration={{
          servicePeriod: { start: "2026-06-01", end: "2026-06-30" },
          categories: [
            { code: "personnel", label: "Personnel", limit: "60000.00" },
          ],
          requiredEvidence: ["vendor_invoice"],
          ledgerControlTotal: "10130.00",
          rules: [
            "SERVICE_PERIOD",
            "REQUIRED_EVIDENCE",
            "BUDGET_AVAILABLE",
            "TOTAL_RECONCILIATION",
            "POSSIBLE_DUPLICATE",
          ].map((code) => ({
            code,
            severity: code === "POSSIBLE_DUPLICATE" ? "warning" : "blocker",
            enabled: true,
            ...(code === "POSSIBLE_DUPLICATE"
              ? { amountTolerance: "0.00", dayWindow: 1 }
              : {}),
          })),
          workflowLabels: {
            draft: "NGO preparation",
            submitted: "Government review",
            returned: "Changes requested",
            approved: "Final approval",
          },
          package: {
            label: "Review package",
            invoiceTitle: "Invoice",
            includeValidationSummary: true,
            includeManifest: true,
          },
        }}
        active={{ id: "config-v1", version: 1, activatedAt: "now" }}
        versions={[
          {
            id: "config-v2",
            version: 2,
            configuration: {},
            state: "tested",
            active: false,
            history: [
              {
                state: "tested",
                action: "test",
                actorId: "admin",
                actorRole: "configuration_administrator",
                actorOrganizationId: "org-operations",
                rationale: "Validated deterministic configuration",
                testEvidenceId: "evidence-v2",
                approvalId: null,
                predecessorVersionId: "config-v1",
                successorVersionId: null,
                rollbackTargetVersionId: null,
                eventHash: "abcdef123456",
                occurredAt: "2026-07-12T12:00:00Z",
              },
            ],
          },
          {
            id: "config-v1",
            version: 1,
            configuration: {},
            state: "active",
            active: true,
            history: [],
          },
        ]}
        message=""
        onSave={() => {}}
        onTest={() => {}}
        onApprove={() => {}}
        onActivate={() => {}}
        onSupersede={() => {}}
        onRetire={() => {}}
        onRollback={() => {}}
      />,
    );
    expect(html).toContain("Active version 1");
    expect(html).toContain("Personnel limit");
    expect(html).toContain("POSSIBLE_DUPLICATE");
    expect(html).toContain("Amount tolerance");
    expect(html).toContain("Package label");
    expect(html).toContain("Preview configuration");
    expect(html).toContain("Save validated draft");
    expect(html).toContain("Test draft and retain evidence");
    expect(html).toContain("Record human approval");
    expect(html).toContain("Immutable lifecycle evidence");
    expect(html).toContain("Validated deterministic configuration");
    expect(html).not.toContain("Activate numbered version");
  });
  it("renders every governed transition only for its valid lifecycle state", () => {
    type AdminProps = Parameters<typeof ConfigurationAdmin>[0];
    const configuration: AdminProps["configuration"] = {
      servicePeriod: { start: "2026-06-01", end: "2026-06-30" },
      categories: [
        { code: "program", label: "Program", limit: "1000.00" },
      ],
      requiredEvidence: ["vendor_invoice"],
      ledgerControlTotal: "100.00",
      rules: [
        "SERVICE_PERIOD",
        "REQUIRED_EVIDENCE",
        "BUDGET_AVAILABLE",
        "TOTAL_RECONCILIATION",
        "POSSIBLE_DUPLICATE",
      ].map((code) => ({
        code,
        severity: code === "POSSIBLE_DUPLICATE" ? "warning" : "blocker",
        enabled: true,
        ...(code === "POSSIBLE_DUPLICATE"
          ? { amountTolerance: "0.00", dayWindow: 1 }
          : {}),
      })),
      workflowLabels: {
        draft: "Draft",
        submitted: "Submitted",
        returned: "Returned",
        approved: "Approved",
      },
      package: {
        label: "Package",
        invoiceTitle: "Invoice",
        includeValidationSummary: true,
        includeManifest: true,
      },
    };
    const renderStates = (
      versions: AdminProps["versions"],
      active: AdminProps["active"],
    ) =>
      renderToString(
        <ConfigurationAdmin
          configuration={configuration}
          versions={versions}
          active={active}
          message=""
          onSave={() => {}}
          onTest={() => {}}
          onApprove={() => {}}
          onActivate={() => {}}
          onSupersede={() => {}}
          onRetire={() => {}}
          onRollback={() => {}}
        />,
      );
    const version = (
      id: string,
      number: number,
      state: AdminProps["versions"][number]["state"],
      active = false,
    ): AdminProps["versions"][number] => ({
      id,
      version: number,
      configuration: {},
      state,
      active,
      history: [],
    });

    const activate = renderStates([version("v1", 1, "approved")], null);
    expect(activate).toContain("Activate approved version");
    expect(activate).not.toContain("Supersede active version");

    const supersede = renderStates(
      [version("v1", 1, "active", true), version("v2", 2, "approved")],
      { id: "v1", version: 1, activatedAt: "now" },
    );
    expect(supersede).toContain("Supersede active version");

    const retiredControls = renderStates(
      [version("v1", 1, "superseded"), version("v2", 2, "active", true)],
      { id: "v2", version: 2, activatedAt: "now" },
    );
    expect(retiredControls).toContain("Retire version");
    expect(retiredControls).toContain("Prepare tested rollback");

    const rollback = renderStates(
      [version("v1", 1, "retired"), version("v2", 2, "active", true)],
      { id: "v2", version: 2, activatedAt: "now" },
    );
    expect(rollback).toContain("Prepare tested rollback");
    expect(rollback).not.toContain("Retire version");
    expect(rollback).toMatch(
      /<button[^>]*disabled=""[^>]*>Test draft and retain evidence<\/button>/,
    );
  });
  it("renders explainable blocker and warning with deterministic hashes and versions", () => {
    const html = renderToString(
      <ValidationView
        validation={{
          id: "run",
          invoiceVersionId: "invoice-v1",
          configurationVersionId: "config-v1",
          engineVersion: "deterministic-validation-v1",
          normalizedInputs: {},
          inputHash: "1234567890abcdef",
          outputHash: "abcdef1234567890",
          status: "completed",
          results: [
            {
              ruleCode: "SERVICE_PERIOD",
              ruleVersion: "service-period-v1",
              severity: "blocker",
              reasonCode: "SERVICE_PERIOD:EXP-004",
              outcome: "fail",
              expenseKey: "EXP-004",
              normalizedInput: {},
              message: "Date is outside service period",
            },
            {
              ruleCode: "POSSIBLE_DUPLICATE",
              ruleVersion: "possible-duplicate-v1",
              severity: "warning",
              reasonCode: "POSSIBLE_DUPLICATE:EXP-005:EXP-002",
              outcome: "fail",
              expenseKey: "EXP-005",
              normalizedInput: {},
              message: "Possible duplicate",
            },
          ],
        }}
      />,
    );
    expect(html).toContain("deterministic-validation-v1");
    expect(html).toContain("SERVICE_PERIOD:EXP-004");
    expect(html).toContain("service-period-v1");
    expect(html).toContain("POSSIBLE_DUPLICATE:EXP-005:EXP-002");
    expect(html).toContain("warning");
  });
  it("renders finding evidence, normalized reason, remediation, correction, and warning actions", () => {
    const html = renderToString(
      <FindingResolutionView
        findings={[
          {
            id: "blocker",
            expenseKey: "EXP-004",
            code: "SERVICE_PERIOD:EXP-004",
            severity: "blocker",
            message: "Outside period",
            status: "open",
            normalizedInput: { date: "2026-07-03" },
            evidenceArtifactId: "artifact-4",
            remediation: "Correct the service date",
          },
          {
            id: "warning",
            expenseKey: "EXP-005",
            code: "POSSIBLE_DUPLICATE:EXP-005:EXP-002",
            severity: "warning",
            message: "Possible duplicate",
            status: "open",
            normalizedInput: { left: "EXP-002", right: "EXP-005" },
            evidenceArtifactId: "artifact-5",
            remediation: "Explain or dismiss",
          },
        ]}
        onResolve={() => {}}
      />,
    );
    expect(html).toContain("View affected evidence");
    expect(html).toContain("Corrected service date");
    expect(html).toContain("Correct and revalidate");
    expect(html).toContain("Explain warning");
    expect(html).toContain("Dismiss and revalidate");
    expect(html).toContain("Remediation:");
    expect(html).toContain("2026-07-03");
  });
  it("renders exact-version approval context and gates attestation on confirmation", () => {
    const html = renderToString(
      <ApprovalPanel
        preview={{
          invoice: {
            id: "invoice-1",
            version: 1,
            configurationVersionId: "config-v1",
            state: "draft",
            total: "100.00",
            categories: [
              {
                name: "Program",
                claimed: "100.00",
                limit: "1000.00",
                available: "900.00",
              },
            ],
            lines: [],
            findings: [],
          },
          validationRunId: "validation-1",
          validationOutputHash: "1234567890abcdef",
          validationFresh: true,
          materialRevision: 2,
          findings: [],
          hasOpenBlockers: false,
          packagePreview: {
            files: [
              "invoice.pdf",
              "manifest.json",
              "validation-summary.json",
              "evidence/",
            ],
            evidenceCount: 1,
          },
          attestationVersion: "ngo-approver-attestation-v1",
          attestationText: "I attest to this exact invoice version.",
        }}
        attestation={null}
        generatedPackage={null}
        submission={null}
        message=""
        onAttest={() => {}}
        onGeneratePackage={() => {}}
        onSubmit={() => {}}
      />,
    );
    expect(html).toContain("Material revision");
    expect(html).toContain("validation-1");
    expect(html).toContain("Validation is fresh");
    expect(html).toContain("No open blockers");
    expect(html).toContain("manifest.json");
    expect(html).toContain("I attest to this exact invoice version.");
    expect(html).toContain("Attest exact version");
    expect(html).toContain("disabled");
  });
  it("shows an agency-scoped queue and exact review context", () => {
    const html = renderToString(
      <GovernmentWorkspace
        user={{
          id: "reviewer",
          displayName: "Synthetic Government Reviewer",
          email: "synthetic@example.test",
          organizationId: "org-government",
          organizationName: "Synthetic Public Agency",
          role: "government_reviewer",
        }}
        activeConfiguration={{
          id: "config-v1",
          version: 1,
          activatedAt: "now",
        }}
        queue={[
          {
            id: "queue-1",
            status: "submitted",
            ngo: "Synthetic Community Nonprofit",
            contract: "Community services contract",
            invoiceVersion: 1,
            amount: "10130.00",
            submittedAt: "now",
            zipArtifactId: "zip",
            servicePeriod: { start: "2026-06-01", end: "2026-06-30" },
            openFindingCount: 0,
          },
        ]}
        review={{
          queueId: "queue-1",
          status: "submitted",
          invoiceVersion: 1,
          amount: "10130.00",
          ngo: "Synthetic Community Nonprofit",
          contract: "Community services contract",
          configurationVersionId: "config-v1",
          zipArtifactId: "zip",
          validation: {
            id: "run",
            engineVersion: "deterministic-validation-v1",
            inputHash: "1234567890abcdef",
            outputHash: "abcdef1234567890",
          },
          findings: [
            {
              code: "POSSIBLE_DUPLICATE",
              severity: "warning",
              message: "Reviewed warning",
              status: "dismissed",
            },
          ],
          artifacts: [
            {
              path: "package.zip",
              artifactId: "zip",
              sha256: "1234567890abcdef",
              mediaType: "application/zip",
            },
          ],
          provenance: [
            { eventType: "submitted", actorId: "approver", occurredAt: "now" },
          ],
        }}
        onInspect={() => {}}
        onDecision={() => {}}
        message=""
        onLogout={() => {}}
      />,
    );
    expect(html).toContain("Synthetic Government Reviewer");
    expect(html).toContain("Government Reviewer");
    expect(html).toContain("Synthetic Community Nonprofit");
    expect(html).toContain("Inspect exact package");
    expect(html).toContain("Download exact package ZIP");
    expect(html).toContain("deterministic-validation-v1");
    expect(html).toContain("Return version 1 with feedback");
  });
});
