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
          displayName: "Maya Chen",
          email: "m@demo",
          organizationName: "Harbor Community Services",
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
        onActivateConfiguration={() => {}}
      />,
    );
    expect(html).toContain("Upload ledger and evidence");
    expect(html).toContain("Upload and process");
    expect(html).toContain("running");
    expect(html).toContain("Maya Chen");
    expect(html).toContain("Harbor Community Services");
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
              vendor: "Northstar Learning Supply",
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
        message=""
        onSave={() => {}}
        onActivate={() => {}}
      />,
    );
    expect(html).toContain("Active version 1");
    expect(html).toContain("Personnel limit");
    expect(html).toContain("POSSIBLE_DUPLICATE");
    expect(html).toContain("Amount tolerance");
    expect(html).toContain("Package label");
    expect(html).toContain("Preview configuration");
    expect(html).toContain("Save validated draft");
    expect(html).toContain("Activate numbered version");
  });
  it("renders explainable blocker and warning with deterministic hashes and versions", () => {
    const html = renderToString(
      <ValidationView
        validation={{
          id: "run",
          engineVersion: "deterministic-validation-v1",
          inputHash: "1234567890abcdef",
          outputHash: "abcdef1234567890",
          results: [
            {
              ruleCode: "SERVICE_PERIOD",
              ruleVersion: "service-period-v1",
              severity: "blocker",
              reasonCode: "SERVICE_PERIOD:EXP-004",
              outcome: "fail",
              expenseKey: "EXP-004",
              message: "Date is outside service period",
            },
            {
              ruleCode: "POSSIBLE_DUPLICATE",
              ruleVersion: "possible-duplicate-v1",
              severity: "warning",
              reasonCode: "POSSIBLE_DUPLICATE:EXP-005:EXP-002",
              outcome: "fail",
              expenseKey: "EXP-005",
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
        message=""
        onAttest={() => {}}
        onGeneratePackage={() => {}}
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
          displayName: "Samira Patel",
          email: "s@demo",
          organizationName: "Metro Public Programs Agency",
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
            ngo: "Harbor Community Services",
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
          ngo: "Harbor Community Services",
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
    expect(html).toContain("Samira Patel");
    expect(html).toContain("Government Reviewer");
    expect(html).toContain("Harbor Community Services");
    expect(html).toContain("Inspect exact package");
    expect(html).toContain("Download exact package ZIP");
    expect(html).toContain("deterministic-validation-v1");
    expect(html).toContain("Return version 1 with feedback");
  });
});
