export type Job = {
  id: string;
  artifact_id: string;
  job_type: string;
  status: "queued" | "running" | "completed" | "failed";
  error_message: string | null;
};
export type ExtractionField = {
  id: string;
  name: string;
  proposedValue: string;
  reviewedValue: string | null;
  confidence: string;
  sourceLocation: string;
  reviewStatus: string;
};
export type Extraction = {
  id: string;
  sourceArtifactId: string;
  filename: string;
  provider: string;
  model: string;
  routingReason: string;
  fields: ExtractionField[];
};
export type InvoiceDraft = {
  id: string;
  version: number;
  configurationVersionId: string;
  state: string;
  total: string;
  lines: Array<{
    expenseKey: string;
    date: string;
    vendor: string;
    description: string;
    category: string;
    amount: string;
    ledgerArtifactId: string;
    ledgerSource: string;
    evidenceArtifactId: string | null;
    extractionStatus: string;
  }>;
  categories: Array<{
    name: string;
    claimed: string;
    limit: string;
    available: string;
  }>;
  findings: Array<{
    expenseKey: string | null;
    code: string;
    message: string;
    status: string;
  }>;
};
export type Configuration = {
  servicePeriod: { start: string; end: string };
  categories: Array<{ code: string; label: string; limit: string }>;
  requiredEvidence: string[];
  ledgerControlTotal: string;
  rules: Array<{
    code: string;
    severity: string;
    enabled: boolean;
    amountTolerance?: string;
    dayWindow?: number;
  }>;
  workflowLabels: Record<string, string>;
  package: {
    label: string;
    invoiceTitle: string;
    includeValidationSummary: boolean;
    includeManifest: boolean;
  };
  [key: string]: unknown;
};
export type Finding = {
  id: string;
  expenseKey: string | null;
  code: string;
  severity: "blocker" | "warning";
  message: string;
  status: string;
  normalizedInput: Record<string, unknown>;
  evidenceArtifactId: string | null;
  remediation: string;
};
export type ApprovalPreview = {
  invoice: InvoiceDraft;
  validationRunId: string | null;
  validationOutputHash: string | null;
  validationFresh: boolean;
  materialRevision: number;
  findings: Finding[];
  hasOpenBlockers: boolean;
  packagePreview: { files: string[]; evidenceCount: number };
  attestationVersion: string;
  attestationText: string;
};
export type Attestation = {
  id: string;
  actorId: string;
  actorRole: string;
  attestationVersion: string;
  createdAt: string;
  current: boolean;
  fingerprint: string;
};
export type GeneratedPackage = {
  id: string;
  invoiceVersionId: string;
  artifacts: Record<string, { id: string; sha256: string }>;
  zip: { id: string; sha256: string };
};
export type Submission = {
  id: string;
  invoiceVersionId: string;
  packageId: string;
  queueItemId: string;
  state: string;
};
export type RevisionFeedback = {
  invoiceVersionId: string;
  predecessorInvoiceVersionId: string;
  decisionId: string;
  reasonCode: string;
  note: string;
  lineKeys: string[];
};
export type QueueItem = {
  id: string;
  status: string;
  ngo: string;
  contract: string;
  invoiceVersion: number;
  amount: string;
  submittedAt: string;
  zipArtifactId: string;
  servicePeriod: { start: string; end: string };
  openFindingCount: number;
};
export type ReviewContext = {
  queueId: string;
  status: string;
  invoiceVersion: number;
  amount: string;
  ngo: string;
  contract: string;
  configurationVersionId: string;
  zipArtifactId: string;
  validation: {
    id: string;
    engineVersion: string;
    inputHash: string;
    outputHash: string;
  };
  findings: Array<{
    code: string;
    severity: string;
    message: string;
    status: string;
  }>;
  artifacts: Array<{
    path: string;
    artifactId: string;
    sha256: string;
    mediaType: string;
  }>;
  provenance: Array<{ eventType: string; actorId: string; occurredAt: string }>;
};
