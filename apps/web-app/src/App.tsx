import { FormEvent, useCallback, useEffect, useState } from "react";
import type {
  ActiveConfigurationDto as ActiveConfiguration,
  GovernedConfigurationVersionDto as GovernedConfigurationVersion,
  IdentityDto as User,
  ValidationRunDto as ValidationRun,
} from "./generated/contracts";
type Job = {
  id: string;
  artifact_id: string;
  job_type: string;
  status: "queued" | "running" | "completed" | "failed";
  error_message: string | null;
};
type ExtractionField = {
  id: string;
  name: string;
  proposedValue: string;
  reviewedValue: string | null;
  confidence: string;
  sourceLocation: string;
  reviewStatus: string;
};
type Extraction = {
  id: string;
  sourceArtifactId: string;
  filename: string;
  provider: string;
  model: string;
  routingReason: string;
  fields: ExtractionField[];
};
type InvoiceDraft = {
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
type Configuration = {
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
type Finding = {
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
type ApprovalPreview = {
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
type Attestation = {
  id: string;
  actorId: string;
  actorRole: string;
  attestationVersion: string;
  createdAt: string;
  current: boolean;
  fingerprint: string;
};
type GeneratedPackage = {
  id: string;
  invoiceVersionId: string;
  artifacts: Record<string, { id: string; sha256: string }>;
  zip: { id: string; sha256: string };
};
type Submission = {
  id: string;
  invoiceVersionId: string;
  packageId: string;
  queueItemId: string;
  state: string;
};
type RevisionFeedback = {
  invoiceVersionId: string;
  predecessorInvoiceVersionId: string;
  decisionId: string;
  reasonCode: string;
  note: string;
  lineKeys: string[];
};
type QueueItem = {
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
type ReviewContext = {
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
const CONTRACT_ID = "contract-synthetic-agency-ngo-2026";
const personas = [
  [
    "Configuration Administrator",
    "Synthetic Configuration Administrator",
    "configuration.admin@example.test",
    "Demo-Config-2026!",
  ],
  [
    "NGO Preparer",
    "Synthetic NGO Preparer",
    "ngo.preparer@example.test",
    "Demo-Prepare-2026!",
  ],
  [
    "NGO Approver",
    "Synthetic NGO Approver",
    "ngo.approver@example.test",
    "Demo-Approve-2026!",
  ],
  [
    "Government Reviewer",
    "Synthetic Government Reviewer",
    "government.reviewer@example.test",
    "Demo-Review-2026!",
  ],
  ["Auditor", "Synthetic Auditor", "auditor@example.test", "Demo-Audit-2026!"],
] as const;
const roleLabel = (role: string) =>
  role
    .split("_")
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("Checking session…");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [extractions, setExtractions] = useState<Extraction[]>([]);
  const [draft, setDraft] = useState<InvoiceDraft | null>(null);
  const [configuration, setConfiguration] = useState<Configuration | null>(
    null,
  );
  const [activeConfiguration, setActiveConfiguration] =
    useState<ActiveConfiguration | null>(null);
  const [configurationLifecycle, setConfigurationLifecycle] = useState<
    GovernedConfigurationVersion[]
  >([]);
  const [validation, setValidation] = useState<ValidationRun | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [approvalPreview, setApprovalPreview] =
    useState<ApprovalPreview | null>(null);
  const [attestation, setAttestation] = useState<Attestation | null>(null);
  const [generatedPackage, setGeneratedPackage] =
    useState<GeneratedPackage | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [reviewContext, setReviewContext] = useState<ReviewContext | null>(
    null,
  );
  const [revisionFeedback, setRevisionFeedback] =
    useState<RevisionFeedback | null>(null);
  const refreshJobs = useCallback(async () => {
    const response = await fetch(
      `/api/ingestion/jobs?contractId=${CONTRACT_ID}`,
    );
    if (response.ok) setJobs((await response.json()).jobs);
  }, []);
  const refreshExtractions = useCallback(async () => {
    const response = await fetch(
      `/api/extractions/review?contractId=${CONTRACT_ID}`,
    );
    if (response.ok) setExtractions((await response.json()).extractions);
  }, []);
  const refreshDraft = useCallback(async () => {
    const response = await fetch(
      `/api/invoices/draft?contractId=${CONTRACT_ID}`,
    );
    if (response.ok) setDraft((await response.json()).invoice);
  }, []);
  const refreshConfiguration = useCallback(async (role?: string) => {
    const active = await fetch(
      `/api/configuration/active?contractId=${CONTRACT_ID}`,
    );
    if (active.ok) setActiveConfiguration((await active.json()).configuration);
    if (role === "configuration_administrator") {
      const [draftResponse, lifecycleResponse] = await Promise.all([
        fetch(`/api/configuration/draft?contractId=${CONTRACT_ID}`),
        fetch(`/api/configuration/lifecycle?contractId=${CONTRACT_ID}`),
      ]);
      if (draftResponse.ok)
        setConfiguration((await draftResponse.json()).configuration);
      if (lifecycleResponse.ok)
        setConfigurationLifecycle(
          (await lifecycleResponse.json()).versions || [],
        );
    }
  }, []);
  useEffect(() => {
    fetch("/api/auth/me")
      .then(async (r) => {
        if (!r.ok) throw new Error();
        setUser((await r.json()).user);
        setMessage("");
      })
      .catch(() => setMessage("Choose a persona to begin."));
  }, []);
  useEffect(() => {
    if (user) refreshConfiguration(user.role);
  }, [user, refreshConfiguration]);
  useEffect(() => {
    if (user?.role === "ngo_approver") refreshDraft();
  }, [user, refreshDraft]);
  useEffect(() => {
    if (user?.role === "ngo_approver" && draft) refreshApproval(draft.id);
  }, [user, draft]);
  useEffect(() => {
    if (user?.role === "government_reviewer")
      fetch("/api/government/queue")
        .then((response) => response.json())
        .then((result) => setQueue(result.items || []));
  }, [user]);
  useEffect(() => {
    if (user?.role !== "ngo_preparer") return;
    refreshJobs();
    refreshExtractions();
    refreshDraft();
    fetch(`/api/revisions/feedback?contractId=${CONTRACT_ID}`)
      .then((response) => response.json())
      .then((result) => setRevisionFeedback(result.feedback || null));
    const timer = window.setInterval(() => {
      refreshJobs();
      refreshExtractions();
    }, 500);
    return () => window.clearInterval(timer);
  }, [user, refreshJobs, refreshExtractions, refreshDraft]);
  async function login(event: FormEvent) {
    event.preventDefault();
    setMessage("Signing in…");
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
      setMessage("Invalid email or password.");
      return;
    }
    setUser((await response.json()).user);
    setMessage("");
  }
  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
    setEmail("");
    setPassword("");
    setDraft(null);
    setValidation(null);
    setFindings([]);
    setApprovalPreview(null);
    setAttestation(null);
    setGeneratedPackage(null);
    setSubmission(null);
    setReviewContext(null);
    setConfigurationLifecycle([]);
    setMessage("Signed out. Choose a persona to continue.");
  }
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    data.set("contractId", CONTRACT_ID);
    setMessage("Uploading and queueing…");
    const response = await fetch("/api/ingestion/uploads", {
      method: "POST",
      body: data,
    });
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Upload failed");
      return;
    }
    setMessage("Upload queued for real background processing.");
    form.reset();
    await refreshJobs();
  }
  async function review(
    fieldId: string,
    decision: "accept" | "correct",
    value: string,
  ) {
    const response = await fetch(`/api/extractions/fields/${fieldId}/review`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        decision,
        value,
        reason:
          decision === "correct"
            ? "Corrected against the approved claim total"
            : "Accepted against source evidence",
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Review failed");
      return;
    }
    setMessage(
      decision === "correct"
        ? "Correction recorded with provenance."
        : "Proposal accepted with provenance.",
    );
    await refreshExtractions();
  }
  async function assemble() {
    const response = await fetch(
      `/api/invoices/draft?contractId=${CONTRACT_ID}`,
      { method: "POST" },
    );
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Draft assembly failed");
      return;
    }
    setDraft(result.invoice);
    setMessage("Evidence-linked draft assembled.");
  }
  async function saveConfiguration(value: Configuration) {
    const response = await fetch(
      `/api/configuration/draft?contractId=${CONTRACT_ID}`,
      {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(value),
      },
    );
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Configuration save failed");
      return;
    }
    setConfiguration(result.configuration);
    setMessage("Configuration draft saved and validated.");
  }
  async function governConfiguration(
    path: string,
    payload: Record<string, string>,
    successMessage: string,
  ) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Configuration governance action failed");
      return;
    }
    await refreshConfiguration("configuration_administrator");
    setMessage(successMessage);
  }
  async function testConfiguration(rationale: string) {
    await governConfiguration(
      `/api/configuration/test?contractId=${CONTRACT_ID}`,
      { rationale },
      "Immutable configuration test evidence recorded.",
    );
  }
  async function approveConfiguration(versionId: string, rationale: string) {
    await governConfiguration(
      `/api/configuration/versions/${versionId}/approve`,
      { rationale },
      "Human configuration approval recorded.",
    );
  }
  async function activateConfiguration(versionId: string, rationale: string) {
    await governConfiguration(
      "/api/configuration/activate",
      { versionId, rationale },
      "Approved configuration activated prospectively.",
    );
  }
  async function supersedeConfiguration(
    activeVersionId: string,
    successorVersionId: string,
    rationale: string,
  ) {
    await governConfiguration(
      `/api/configuration/versions/${activeVersionId}/supersede`,
      { successorVersionId, rationale },
      "Active configuration superseded by its approved successor.",
    );
  }
  async function retireConfiguration(versionId: string, rationale: string) {
    await governConfiguration(
      `/api/configuration/versions/${versionId}/retire`,
      { rationale },
      "Superseded configuration retired with retained history.",
    );
  }
  async function rollbackConfiguration(versionId: string, rationale: string) {
    await governConfiguration(
      `/api/configuration/rollback?contractId=${CONTRACT_ID}`,
      { targetVersionId: versionId, rationale },
      "Rollback candidate tested; approval and supersession are still required.",
    );
  }
  async function refreshFindings(invoiceId: string) {
    const response = await fetch(`/api/invoices/${invoiceId}/findings`);
    if (response.ok) setFindings((await response.json()).findings);
  }
  async function validate() {
    if (!draft) return;
    const response = await fetch(`/api/invoices/${draft.id}/validation`, {
      method: "POST",
    });
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Validation failed");
      return;
    }
    setValidation(result.validation);
    await refreshFindings(draft.id);
    setMessage("Deterministic validation completed.");
  }
  async function resolveFinding(
    id: string,
    action: "correct" | "explain" | "dismiss",
    reason: string,
    correctionValue?: string,
  ) {
    const response = await fetch(`/api/findings/${id}/resolve`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action, reason, correctionValue }),
    });
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Resolution failed");
      return;
    }
    setFindings(result.resolution.findings);
    const validationResponse = await fetch(
      `/api/invoices/${draft!.id}/validation`,
    );
    if (validationResponse.ok)
      setValidation((await validationResponse.json()).validation);
    setMessage("Finding resolved and deterministic validation rerun.");
  }
  async function refreshApproval(invoiceId: string) {
    const response = await fetch(`/api/invoices/${invoiceId}/approval-preview`);
    if (response.ok) {
      const result = await response.json();
      setApprovalPreview(result.preview);
      setAttestation(result.attestation);
    }
  }
  async function submitAttestation(text: string) {
    if (!draft) return;
    const response = await fetch(`/api/invoices/${draft.id}/attest`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Attestation failed");
      return;
    }
    setAttestation(result.attestation);
    setMessage("Exact invoice version attested.");
  }
  async function generatePackage() {
    if (!draft) return;
    const response = await fetch(`/api/invoices/${draft.id}/package`, {
      method: "POST",
    });
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Package generation failed");
      return;
    }
    setGeneratedPackage(result.package);
    setMessage("Immutable invoice package generated.");
  }
  async function submitInvoice() {
    if (!draft) return;
    const response = await fetch(`/api/invoices/${draft.id}/submit`, {
      method: "POST",
    });
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Submission failed");
      return;
    }
    setSubmission(result.submission);
    setMessage("Immutable version submitted to the government queue.");
  }
  async function inspectQueue(id: string) {
    const response = await fetch(`/api/government/queue/${id}`);
    if (response.ok) setReviewContext((await response.json()).review);
  }
  async function decideQueue(
    queueId: string,
    decision: "returned" | "approved",
    reasonCode: string,
    note: string,
    lineKeys: string[],
  ) {
    const response = await fetch(`/api/government/queue/${queueId}/decision`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ decision, reasonCode, note, lineKeys }),
    });
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Decision failed");
      return;
    }
    setMessage(
      decision === "returned"
        ? "Version returned with structured feedback."
        : "Corrected version approved.",
    );
    const queueResponse = await fetch("/api/government/queue");
    if (queueResponse.ok) setQueue((await queueResponse.json()).items);
    setReviewContext(null);
  }
  async function correctReturnedRevision(
    expenseKey: string,
    description: string,
    reason: string,
  ) {
    if (!draft) return;
    const response = await fetch(
      `/api/invoices/${draft.id}/revision-correction`,
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ expenseKey, description, reason }),
      },
    );
    const result = await response.json();
    if (!response.ok) {
      setMessage(result.detail || "Revision correction failed");
      return;
    }
    await refreshDraft();
    setMessage("Government feedback correction recorded. Run validation.");
  }
  if (user?.role === "government_reviewer")
    return (
      <GovernmentWorkspace
        user={user}
        activeConfiguration={activeConfiguration}
        queue={queue}
        review={reviewContext}
        onInspect={inspectQueue}
        onDecision={decideQueue}
        message={message}
        onLogout={logout}
      />
    );
  if (user)
    return (
      <AuthenticatedWorkspace
        user={user}
        jobs={jobs}
        extractions={extractions}
        draft={draft}
        configuration={configuration}
        activeConfiguration={activeConfiguration}
        configurationLifecycle={configurationLifecycle}
        validation={validation}
        findings={findings}
        revisionFeedback={revisionFeedback}
        approvalPreview={approvalPreview}
        attestation={attestation}
        generatedPackage={generatedPackage}
        submission={submission}
        message={message}
        onLogout={logout}
        onUpload={upload}
        onReview={review}
        onAssemble={assemble}
        onValidate={validate}
        onResolveFinding={resolveFinding}
        onCorrectRevision={correctReturnedRevision}
        onAttest={submitAttestation}
        onGeneratePackage={generatePackage}
        onSubmitInvoice={submitInvoice}
        onSaveConfiguration={saveConfiguration}
        onTestConfiguration={testConfiguration}
        onApproveConfiguration={approveConfiguration}
        onActivateConfiguration={activateConfiguration}
        onSupersedeConfiguration={supersedeConfiguration}
        onRetireConfiguration={retireConfiguration}
        onRollbackConfiguration={rollbackConfiguration}
      />
    );
  return (
    <main>
      <p className="eyebrow">Synthetic role-based POC</p>
      <h1>Sign in</h1>
      <p className="summary">
        Select a seeded persona. The card fills credentials; the normal server
        login still runs.
      </p>
      <div className="persona-grid">
        {personas.map(([role, name, personaEmail, personaPassword]) => (
          <button
            className="persona"
            key={role}
            onClick={() => {
              setEmail(personaEmail);
              setPassword(personaPassword);
            }}
          >
            <strong>{role}</strong>
            <span>{name}</span>
          </button>
        ))}
      </div>
      <form onSubmit={login}>
        <label>
          Email
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
          />
        </label>
        <label>
          Password
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            required
          />
        </label>
        <button className="primary" type="submit">
          Sign in
        </button>
      </form>
      <p aria-live="polite">{message}</p>
    </main>
  );
}

export function AuthenticatedWorkspace({
  user,
  jobs,
  extractions,
  draft,
  configuration,
  activeConfiguration,
  configurationLifecycle,
  validation,
  findings,
  revisionFeedback,
  approvalPreview,
  attestation,
  generatedPackage,
  submission,
  message,
  onLogout,
  onUpload,
  onReview,
  onAssemble,
  onValidate,
  onResolveFinding,
  onCorrectRevision,
  onAttest,
  onGeneratePackage,
  onSubmitInvoice,
  onSaveConfiguration,
  onTestConfiguration,
  onApproveConfiguration,
  onActivateConfiguration,
  onSupersedeConfiguration,
  onRetireConfiguration,
  onRollbackConfiguration,
}: {
  user: User;
  jobs: Job[];
  extractions: Extraction[];
  draft: InvoiceDraft | null;
  configuration: Configuration | null;
  activeConfiguration: ActiveConfiguration | null;
  configurationLifecycle: GovernedConfigurationVersion[];
  validation: ValidationRun | null;
  findings: Finding[];
  revisionFeedback: RevisionFeedback | null;
  approvalPreview: ApprovalPreview | null;
  attestation: Attestation | null;
  generatedPackage: GeneratedPackage | null;
  submission: Submission | null;
  message: string;
  onLogout: () => void;
  onUpload: (event: FormEvent<HTMLFormElement>) => void;
  onReview: (
    fieldId: string,
    decision: "accept" | "correct",
    value: string,
  ) => void;
  onAssemble: () => void;
  onValidate: () => void;
  onResolveFinding: (
    id: string,
    action: "correct" | "explain" | "dismiss",
    reason: string,
    correctionValue?: string,
  ) => void;
  onCorrectRevision: (
    expenseKey: string,
    description: string,
    reason: string,
  ) => void;
  onAttest: (text: string) => void;
  onGeneratePackage: () => void;
  onSubmitInvoice: () => void;
  onSaveConfiguration: (value: Configuration) => void;
  onTestConfiguration: (rationale: string) => void;
  onApproveConfiguration: (versionId: string, rationale: string) => void;
  onActivateConfiguration: (versionId: string, rationale: string) => void;
  onSupersedeConfiguration: (
    activeVersionId: string,
    successorVersionId: string,
    rationale: string,
  ) => void;
  onRetireConfiguration: (versionId: string, rationale: string) => void;
  onRollbackConfiguration: (versionId: string, rationale: string) => void;
}) {
  return (
    <>
      <header className="identity">
        <div>
          <strong>{user.displayName}</strong>
          <span>{user.organizationName}</span>
        </div>
        <span className="role-badge">{roleLabel(user.role)}</span>
        {activeConfiguration && (
          <span className="config-badge">
            Active config v{activeConfiguration.version}
          </span>
        )}
        <button onClick={onLogout}>Log out</button>
      </header>
      <main>
        <p className="eyebrow">Synthetic role-based POC</p>
        <h1>Workspace</h1>
        <p className="summary">
          Your navigation and available actions are scoped to the signed-in
          persona. The API enforces the same boundaries independently.
        </p>
        {user.role === "configuration_administrator" && configuration && (
          <ConfigurationAdmin
            configuration={configuration}
            active={activeConfiguration}
            versions={configurationLifecycle}
            message={message}
            onSave={onSaveConfiguration}
            onTest={onTestConfiguration}
            onApprove={onApproveConfiguration}
            onActivate={onActivateConfiguration}
            onSupersede={onSupersedeConfiguration}
            onRetire={onRetireConfiguration}
            onRollback={onRollbackConfiguration}
          />
        )}{" "}
        {user.role === "ngo_preparer" && (
          <>
            {revisionFeedback && draft && (
              <RevisionFeedbackPanel
                feedback={revisionFeedback}
                draft={draft}
                onCorrect={onCorrectRevision}
              />
            )}
            <section className="panel">
              <h2>Upload ledger and evidence</h2>
              <p>CSV, XLSX, PDF, PNG, or JPEG. Maximum 10 MB each.</p>
              <form onSubmit={onUpload}>
                <label>
                  Evidence file
                  <input
                    name="file"
                    type="file"
                    accept=".csv,.xlsx,.pdf,.png,.jpg,.jpeg"
                    required
                  />
                </label>
                <button className="primary" type="submit">
                  Upload and process
                </button>
              </form>
              <p aria-live="polite">{message}</p>
              <h3>Processing jobs</h3>
              {jobs.length === 0 ? (
                <p>No uploads yet.</p>
              ) : (
                <ul className="jobs">
                  {jobs.map((job) => (
                    <li key={job.id}>
                      <span>
                        {job.job_type === "ledger_import"
                          ? "Ledger import"
                          : "Evidence extraction"}
                      </span>
                      <strong className={`job-${job.status}`}>
                        {job.status}
                      </strong>
                      {job.error_message && <small>{job.error_message}</small>}
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <ExtractionReview extractions={extractions} onReview={onReview} />
            <section className="panel">
              <div className="section-action">
                <div>
                  <h2>Evidence-linked invoice draft</h2>
                  <p>
                    Assemble from reviewed values, immutable evidence, and the
                    active configuration.
                  </p>
                </div>
                <button className="primary" onClick={onAssemble}>
                  Assemble draft
                </button>
              </div>
              {draft && (
                <>
                  <InvoiceDraftView draft={draft} />
                  <button
                    className="primary validation-action"
                    onClick={onValidate}
                  >
                    Run deterministic validation
                  </button>
                  {validation && <ValidationView validation={validation} />}
                  <FindingResolutionView
                    findings={findings}
                    onResolve={onResolveFinding}
                  />
                </>
              )}
            </section>
          </>
        )}
        {user.role === "ngo_approver" && approvalPreview && (
          <ApprovalPanel
            preview={approvalPreview}
            attestation={attestation}
            generatedPackage={generatedPackage}
            message={message}
            onAttest={onAttest}
            onGeneratePackage={onGeneratePackage}
          />
        )}
      </main>
    </>
  );
}

export function RevisionFeedbackPanel({
  feedback,
  draft,
  onCorrect,
}: {
  feedback: RevisionFeedback;
  draft: InvoiceDraft;
  onCorrect: (expenseKey: string, description: string, reason: string) => void;
}) {
  const expenseKey = feedback.lineKeys[0] || draft.lines[0]?.expenseKey || "";
  const source = draft.lines.find((line) => line.expenseKey === expenseKey);
  const [description, setDescription] = useState(
    source?.description || "Corrected per government feedback",
  );
  return (
    <section className="panel feedback-panel">
      <h2>Government feedback on version 1</h2>
      <strong>{feedback.reasonCode}</strong>
      <p>{feedback.note}</p>
      <p>
        Immutable predecessor: {feedback.predecessorInvoiceVersionId} · Editable
        invoice v{draft.version}
      </p>
      <label>
        Corrected description for {expenseKey}
        <input
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
      </label>
      <button
        className="primary"
        onClick={() =>
          onCorrect(expenseKey, description, "Resolved government feedback")
        }
      >
        Apply correction to version {draft.version}
      </button>
    </section>
  );
}

export function GovernmentWorkspace({
  user,
  activeConfiguration,
  queue,
  review,
  onInspect,
  onDecision,
  message,
  onLogout,
}: {
  user: User;
  activeConfiguration: ActiveConfiguration | null;
  queue: QueueItem[];
  review: ReviewContext | null;
  onInspect: (id: string) => void;
  onDecision: (
    queueId: string,
    decision: "returned" | "approved",
    reasonCode: string,
    note: string,
    lineKeys: string[],
  ) => void;
  message: string;
  onLogout: () => void;
}) {
  const [note, setNote] = useState("");
  const [lineKey, setLineKey] = useState("EXP-004");
  return (
    <>
      <header className="identity">
        <div>
          <strong>{user.displayName}</strong>
          <span>{user.organizationName}</span>
        </div>
        <span className="role-badge">{roleLabel(user.role)}</span>
        {activeConfiguration && (
          <span className="config-badge">
            Active config v{activeConfiguration.version}
          </span>
        )}
        <button onClick={onLogout}>Log out</button>
      </header>
      <main>
        <p className="eyebrow">Synthetic role-based POC</p>
        <h1>Government queue</h1>
        <section className="panel">
          <h2>Submitted reimbursement packages</h2>
          {queue.length === 0 ? (
            <p>No assigned submissions.</p>
          ) : (
            queue.map((item) => (
              <article className="queue-item" key={item.id}>
                <div>
                  <strong>
                    {item.ngo} · Invoice v{item.invoiceVersion}
                  </strong>
                  <span>{item.contract}</span>
                  <span>
                    {item.servicePeriod.start} to {item.servicePeriod.end}
                  </span>
                  <span>
                    ${item.amount} · {item.openFindingCount} open findings
                  </span>
                  <span>
                    {item.status} · {item.submittedAt}
                  </span>
                </div>
                <button className="primary" onClick={() => onInspect(item.id)}>
                  Inspect exact package
                </button>
              </article>
            ))
          )}
        </section>
        {review && (
          <section className="panel">
            <h2>Exact review context</h2>
            <p>
              Invoice v{review.invoiceVersion} · Configuration{" "}
              {review.configurationVersionId} · ${review.amount}
            </p>
            <div className="validation-meta">
              <strong>{review.validation.engineVersion}</strong>
              <span>Input {review.validation.inputHash.slice(0, 12)}</span>
              <span>Output {review.validation.outputHash.slice(0, 12)}</span>
            </div>
            <h3>Package and evidence</h3>
            <a href={`/api/artifacts/${review.zipArtifactId}`}>
              Download exact package ZIP
            </a>
            <ul>
              {review.artifacts.map((item) => (
                <li key={item.path}>
                  <a href={`/api/artifacts/${item.artifactId}`}>{item.path}</a>{" "}
                  <code>{item.sha256.slice(0, 16)}</code>
                </li>
              ))}
            </ul>
            <h3>Validation findings</h3>
            <ul>
              {review.findings.map((item) => (
                <li key={item.code}>
                  <strong>
                    {item.severity}: {item.code}
                  </strong>{" "}
                  {item.status} · {item.message}
                </li>
              ))}
            </ul>
            <h3>Provenance summary</h3>
            <ol>
              {review.provenance.map((item, index) => (
                <li key={`${item.eventType}-${index}`}>
                  {item.eventType} · {item.actorId} · {item.occurredAt}
                </li>
              ))}
            </ol>
            <div className="government-actions">
              <label>
                Decision note
                <input
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                />
              </label>
              {review.invoiceVersion === 1 ? (
                <>
                  <label>
                    Affected expense
                    <input
                      value={lineKey}
                      onChange={(event) => setLineKey(event.target.value)}
                    />
                  </label>
                  <button
                    className="primary"
                    disabled={!note.trim()}
                    onClick={() =>
                      onDecision(
                        review.queueId,
                        "returned",
                        "EVIDENCE_CORRECTION",
                        note,
                        [lineKey],
                      )
                    }
                  >
                    Return version 1 with feedback
                  </button>
                </>
              ) : (
                <button
                  className="primary"
                  disabled={!note.trim()}
                  onClick={() =>
                    onDecision(
                      review.queueId,
                      "approved",
                      "APPROVED_AS_CORRECTED",
                      note,
                      [],
                    )
                  }
                >
                  Approve corrected version {review.invoiceVersion}
                </button>
              )}
            </div>
            <p aria-live="polite">{message}</p>
          </section>
        )}
      </main>
    </>
  );
}

export function ExtractionReview({
  extractions,
  onReview,
}: {
  extractions: Extraction[];
  onReview: (
    fieldId: string,
    decision: "accept" | "correct",
    value: string,
  ) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  if (extractions.length === 0) return null;
  return (
    <section className="panel">
      <h2>Review proposed extraction</h2>
      <p>
        OCR output is draft-only. Compare every value with the source before
        accepting or correcting it.
      </p>
      {extractions.map((extraction) => (
        <article className="extraction" key={extraction.id}>
          <div className="extraction-head">
            <div>
              <strong>{extraction.filename}</strong>
              <small>
                {extraction.provider} · {extraction.model} ·{" "}
                {extraction.routingReason}
              </small>
            </div>
            <a
              href={`/api/artifacts/${extraction.sourceArtifactId}`}
              target="_blank"
              rel="noreferrer"
            >
              View source evidence
            </a>
          </div>
          {extraction.fields.map((field) => {
            const current =
              values[field.id] ?? field.reviewedValue ?? field.proposedValue;
            return (
              <div className="field-review" key={field.id}>
                <label>
                  {roleLabel(field.name)}
                  <input
                    value={current}
                    disabled={field.reviewStatus !== "proposed"}
                    onChange={(event) =>
                      setValues({ ...values, [field.id]: event.target.value })
                    }
                  />
                </label>
                <span>Proposed: {field.proposedValue}</span>
                <span>
                  Confidence: {Math.round(Number(field.confidence) * 100)}%
                </span>
                <span>Source: {field.sourceLocation}</span>
                {field.reviewStatus === "proposed" ? (
                  <div>
                    <button
                      onClick={() =>
                        onReview(field.id, "accept", field.proposedValue)
                      }
                    >
                      Accept
                    </button>
                    <button
                      className="primary"
                      onClick={() => onReview(field.id, "correct", current)}
                    >
                      Correct
                    </button>
                  </div>
                ) : (
                  <strong>
                    {field.reviewStatus}: {field.reviewedValue}
                  </strong>
                )}
              </div>
            );
          })}
        </article>
      ))}
    </section>
  );
}

const sumMoney = (values: string[]) => {
  const cents = values.reduce((sum, value) => {
    const [whole, fraction = "00"] = value.split(".");
    return (
      sum + BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0").slice(0, 2))
    );
  }, 0n);
  return `${cents / 100n}.${String(cents % 100n).padStart(2, "0")}`;
};
export function InvoiceDraftView({ draft }: { draft: InvoiceDraft }) {
  const budgeted = sumMoney(draft.categories.map((item) => item.limit));
  const remaining = sumMoney(draft.categories.map((item) => item.available));
  return (
    <div className="draft">
      <div className="draft-summary">
        <strong>Invoice v{draft.version}</strong>
        <span>Configuration {draft.configurationVersionId}</span>
        <b>${draft.total}</b>
      </div>
      <h3>Budget summary</h3>
      <div className="budget-total">
        <strong>Total requested ${draft.total}</strong>
        <span>Budgeted ${budgeted}</span>
        <span>Remaining ${remaining}</span>
      </div>
      <div className="category-grid">
        {draft.categories.map((item) => (
          <div key={item.name}>
            <strong>{item.name}</strong>
            <span>Requested ${item.claimed}</span>
            <span>Budgeted ${item.limit}</span>
            <span>Remaining ${item.available}</span>
          </div>
        ))}
      </div>
      <h3>Claimed expenses</h3>
      <div className="line-table">
        {draft.lines.map((line) => (
          <div key={line.expenseKey}>
            <strong>
              {line.expenseKey} · {line.vendor}
            </strong>
            <span>
              {line.category} · ${line.amount}
            </span>
            <span>Ledger: {line.ledgerSource}</span>
            <span>Extraction: {line.extractionStatus}</span>
            {line.evidenceArtifactId ? (
              <a
                href={`/api/artifacts/${line.evidenceArtifactId}`}
                target="_blank"
                rel="noreferrer"
              >
                Supporting evidence
              </a>
            ) : (
              <em>Evidence missing</em>
            )}
          </div>
        ))}
      </div>
      <h3>Unresolved findings</h3>
      {draft.findings.length === 0 ? (
        <p>No unresolved assembly findings.</p>
      ) : (
        <ul>
          {draft.findings.map((finding, index) => (
            <li key={`${finding.code}-${index}`}>
              <strong>{finding.code}</strong> {finding.expenseKey}:{" "}
              {finding.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function ConfigurationAdmin({
  configuration,
  active,
  versions,
  message,
  onSave,
  onTest,
  onApprove,
  onActivate,
  onSupersede,
  onRetire,
  onRollback,
}: {
  configuration: Configuration;
  active: ActiveConfiguration | null;
  versions: GovernedConfigurationVersion[];
  message: string;
  onSave: (value: Configuration) => void;
  onTest: (rationale: string) => void;
  onApprove: (versionId: string, rationale: string) => void;
  onActivate: (versionId: string, rationale: string) => void;
  onSupersede: (
    activeVersionId: string,
    successorVersionId: string,
    rationale: string,
  ) => void;
  onRetire: (versionId: string, rationale: string) => void;
  onRollback: (versionId: string, rationale: string) => void;
}) {
  const [value, setValue] = useState(configuration);
  const [rationale, setRationale] = useState("");
  useEffect(() => setValue(configuration), [configuration]);
  const activeVersion = versions.find((version) => version.active);
  const canGovern = rationale.trim().length > 0;
  const category = (index: number, limit: string) =>
    setValue({
      ...value,
      categories: value.categories.map((item, i) =>
        i === index ? { ...item, limit } : item,
      ),
    });
  const rule = (
    index: number,
    change: Partial<Configuration["rules"][number]>,
  ) =>
    setValue({
      ...value,
      rules: value.rules.map((item, i) =>
        i === index ? { ...item, ...change } : item,
      ),
    });
  return (
    <section className="panel">
      <div className="section-action">
        <div>
          <h2>Reimbursement configuration</h2>
          <p>
            Bounded POC settings only.{" "}
            {active ? `Active version ${active.version}` : "No active version"}
          </p>
        </div>
      </div>
      <h3>Categories and limits</h3>
      <div className="config-grid">
        {value.categories.map((item, index) => (
          <label key={item.code}>
            {item.label}
            <input
              aria-label={`${item.label} limit`}
              value={item.limit}
              onChange={(event) => category(index, event.target.value)}
            />
          </label>
        ))}
      </div>
      <h3>Deterministic rules</h3>
      {value.rules.map((item, index) => (
        <div className="rule-row" key={item.code}>
          <strong>{item.code}</strong>
          <label>
            Enabled
            <input
              type="checkbox"
              checked={item.enabled}
              onChange={(event) =>
                rule(index, { enabled: event.target.checked })
              }
            />
          </label>
          <label>
            Severity
            <select
              value={item.severity}
              onChange={(event) =>
                rule(index, { severity: event.target.value })
              }
            >
              <option>blocker</option>
              <option>warning</option>
            </select>
          </label>
          {item.code === "POSSIBLE_DUPLICATE" && (
            <>
              <label>
                Amount tolerance
                <input
                  value={item.amountTolerance}
                  onChange={(event) =>
                    rule(index, { amountTolerance: event.target.value })
                  }
                />
              </label>
              <label>
                Day window
                <input
                  type="number"
                  value={item.dayWindow}
                  onChange={(event) =>
                    rule(index, { dayWindow: Number(event.target.value) })
                  }
                />
              </label>
            </>
          )}
        </div>
      ))}
      <h3>Workflow and package labels</h3>
      <div className="config-grid">
        {Object.entries(value.workflowLabels).map(([key, label]) => (
          <label key={key}>
            {roleLabel(key)}
            <input
              value={label}
              onChange={(event) =>
                setValue({
                  ...value,
                  workflowLabels: {
                    ...value.workflowLabels,
                    [key]: event.target.value,
                  },
                })
              }
            />
          </label>
        ))}
        <label>
          Package label
          <input
            value={value.package.label}
            onChange={(event) =>
              setValue({
                ...value,
                package: { ...value.package, label: event.target.value },
              })
            }
          />
        </label>
        <label>
          Invoice title
          <input
            value={value.package.invoiceTitle}
            onChange={(event) =>
              setValue({
                ...value,
                package: { ...value.package, invoiceTitle: event.target.value },
              })
            }
          />
        </label>
      </div>
      <div className="section-action">
        <button className="primary" onClick={() => onSave(value)}>
          Save validated draft
        </button>
        <details>
          <summary>Preview configuration</summary>
          <pre>{JSON.stringify(value, null, 2)}</pre>
        </details>
      </div>
      <h3>Governed lifecycle</h3>
      <p>
        Saving remains editable. Testing creates an immutable numbered version;
        a recorded human approval is required before prospective activation.
      </p>
      <label>
        Governance rationale
        <textarea
          aria-label="Governance rationale"
          value={rationale}
          onChange={(event) => setRationale(event.target.value)}
          placeholder="Explain the evidence and reason for this action"
        />
      </label>
      <button
        className="primary"
        disabled={!canGovern}
        onClick={() => onTest(rationale)}
      >
        Test draft and retain evidence
      </button>
      {versions.length === 0 ? (
        <p>No governed versions yet.</p>
      ) : (
        <ol className="jobs">
          {versions
            .slice()
            .sort((left, right) => right.version - left.version)
            .map((version) => (
              <li key={version.id}>
                <div className="section-action">
                  <div>
                    <strong>Configuration v{version.version}</strong>{" "}
                    <span className="role-badge">{version.state}</span>
                    {version.active && <span> current active version</span>}
                  </div>
                  <div>
                    {version.state === "tested" && (
                      <button
                        disabled={!canGovern}
                        onClick={() => onApprove(version.id, rationale)}
                      >
                        Record human approval
                      </button>
                    )}
                    {version.state === "approved" && !activeVersion && (
                      <button
                        disabled={!canGovern}
                        onClick={() => onActivate(version.id, rationale)}
                      >
                        Activate approved version
                      </button>
                    )}
                    {version.state === "approved" && activeVersion && (
                      <button
                        disabled={!canGovern}
                        onClick={() =>
                          onSupersede(activeVersion.id, version.id, rationale)
                        }
                      >
                        Supersede active version
                      </button>
                    )}
                    {version.state === "superseded" && (
                      <button
                        disabled={!canGovern}
                        onClick={() => onRetire(version.id, rationale)}
                      >
                        Retire version
                      </button>
                    )}
                    {(version.state === "superseded" ||
                      version.state === "retired") && (
                      <button
                        disabled={!canGovern}
                        onClick={() => onRollback(version.id, rationale)}
                      >
                        Prepare tested rollback
                      </button>
                    )}
                  </div>
                </div>
                <details>
                  <summary>Immutable lifecycle evidence</summary>
                  <ol>
                    {version.history.map((event) => (
                      <li key={event.eventHash}>
                        <strong>{event.state}</strong> by {event.actorRole} at{" "}
                        {event.occurredAt}: {event.rationale}
                        <br />
                        <small>
                          evidence {event.testEvidenceId || "n/a"}; approval{" "}
                          {event.approvalId || "n/a"}; event hash{" "}
                          {event.eventHash}
                        </small>
                        {(event.predecessorVersionId ||
                          event.successorVersionId ||
                          event.rollbackTargetVersionId) && (
                          <small>
                            {" "}
                            predecessor {event.predecessorVersionId || "n/a"};
                            successor {event.successorVersionId || "n/a"};
                            rollback target{" "}
                            {event.rollbackTargetVersionId || "n/a"}
                          </small>
                        )}
                      </li>
                    ))}
                  </ol>
                </details>
              </li>
            ))}
        </ol>
      )}
      <p aria-live="polite">{message}</p>
    </section>
  );
}

export function ValidationView({ validation }: { validation: ValidationRun }) {
  const findings = validation.results.filter((item) => item.outcome === "fail");
  return (
    <div className="validation">
      <div className="validation-meta">
        <strong>{validation.engineVersion}</strong>
        <span>Input {validation.inputHash.slice(0, 12)}</span>
        <span>Output {validation.outputHash.slice(0, 12)}</span>
      </div>
      <h3>Validation findings</h3>
      {findings.length === 0 ? (
        <p>All deterministic checks passed.</p>
      ) : (
        <ul>
          {findings.map((item) => (
            <li className={`finding-${item.severity}`} key={item.reasonCode}>
              <strong>
                {item.severity}: {item.reasonCode}
              </strong>
              <span>
                {item.ruleCode} · {item.ruleVersion}
              </span>
              <p>{item.message}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function FindingResolutionView({
  findings,
  onResolve,
}: {
  findings: Finding[];
  onResolve: (
    id: string,
    action: "correct" | "explain" | "dismiss",
    reason: string,
    correctionValue?: string,
  ) => void;
}) {
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [dates, setDates] = useState<Record<string, string>>({});
  if (findings.length === 0) return null;
  return (
    <div className="finding-resolution">
      <h3>Resolve findings</h3>
      {findings.map((item) => (
        <article
          key={item.id}
          className={`finding-card finding-${item.severity}`}
        >
          <strong>
            {item.severity}: {item.code}
          </strong>
          <span>Affected line: {item.expenseKey || "invoice"}</span>
          <p>{item.message}</p>
          <p>
            <b>Remediation:</b> {item.remediation}
          </p>
          <pre>{JSON.stringify(item.normalizedInput, null, 2)}</pre>
          {item.evidenceArtifactId && (
            <a
              href={`/api/artifacts/${item.evidenceArtifactId}`}
              target="_blank"
              rel="noreferrer"
            >
              View affected evidence
            </a>
          )}
          {item.status === "open" && (
            <>
              <label>
                Resolution reason
                <input
                  value={reasons[item.id] || ""}
                  onChange={(event) =>
                    setReasons({ ...reasons, [item.id]: event.target.value })
                  }
                />
              </label>
              {item.severity === "blocker" ? (
                <>
                  <label>
                    Corrected service date
                    <input
                      type="date"
                      value={dates[item.id] || ""}
                      onChange={(event) =>
                        setDates({ ...dates, [item.id]: event.target.value })
                      }
                    />
                  </label>
                  <button
                    className="primary"
                    onClick={() =>
                      onResolve(
                        item.id,
                        "correct",
                        reasons[item.id] || "",
                        dates[item.id],
                      )
                    }
                  >
                    Correct and revalidate
                  </button>
                </>
              ) : (
                <div>
                  <button
                    onClick={() =>
                      onResolve(item.id, "explain", reasons[item.id] || "")
                    }
                  >
                    Explain warning
                  </button>
                  <button
                    className="primary"
                    onClick={() =>
                      onResolve(item.id, "dismiss", reasons[item.id] || "")
                    }
                  >
                    Dismiss and revalidate
                  </button>
                </div>
              )}
            </>
          )}
        </article>
      ))}
    </div>
  );
}

export function ApprovalPanel({
  preview,
  attestation,
  generatedPackage,
  message,
  onAttest,
  onGeneratePackage,
}: {
  preview: ApprovalPreview;
  attestation: Attestation | null;
  generatedPackage: GeneratedPackage | null;
  message: string;
  onAttest: (text: string) => void;
  onGeneratePackage: () => void;
}) {
  const [confirmed, setConfirmed] = useState(false);
  const [submitted, setSubmitted] = useState<Submission | null>(null);
  async function submitExactVersion() {
    const response = await fetch(`/api/invoices/${preview.invoice.id}/submit`, {
      method: "POST",
    });
    if (response.ok) setSubmitted((await response.json()).submission);
  }
  return (
    <section className="panel">
      <h2>NGO approval and attestation</h2>
      <p>
        Review the exact invoice, validation, configuration, findings, and
        package contents before authorizing generation.
      </p>
      <InvoiceDraftView draft={preview.invoice} />
      <div className="approval-facts">
        <span>Material revision {preview.materialRevision}</span>
        <span>Validation {preview.validationRunId}</span>
        <span>Output {preview.validationOutputHash?.slice(0, 12)}</span>
        <strong>
          {preview.validationFresh
            ? "Validation is fresh"
            : "Validation is stale"}
        </strong>
        <strong>
          {preview.hasOpenBlockers ? "Open blockers" : "No open blockers"}
        </strong>
      </div>
      <h3>Package preview</h3>
      <ul>
        {preview.packagePreview.files.map((file) => (
          <li key={file}>{file}</li>
        ))}
      </ul>
      <h3>Attestation</h3>
      <blockquote>{preview.attestationText}</blockquote>
      <label className="attestation-check">
        <input
          type="checkbox"
          checked={confirmed}
          onChange={(event) => setConfirmed(event.target.checked)}
        />
        I confirm this exact invoice version and evidence set.
      </label>
      <button
        className="primary"
        disabled={
          !confirmed || !preview.validationFresh || preview.hasOpenBlockers
        }
        onClick={() => onAttest(preview.attestationText)}
      >
        Attest exact version
      </button>
      {attestation && (
        <p
          className={
            attestation.current ? "attestation-current" : "attestation-stale"
          }
        >
          {attestation.current ? "Current attestation" : "Stale attestation"} ·{" "}
          {attestation.attestationVersion} · {attestation.actorRole} ·{" "}
          {attestation.createdAt}
        </p>
      )}
      {attestation?.current && !generatedPackage && (
        <button className="primary" onClick={onGeneratePackage}>
          Generate immutable package
        </button>
      )}
      {generatedPackage && (
        <div className="package-ready">
          <strong>Immutable package ready</strong>
          <a href={`/api/artifacts/${generatedPackage.zip.id}`}>
            Download package ZIP
          </a>
          <code>{generatedPackage.zip.sha256}</code>
          {!submitted && (
            <button className="primary" onClick={submitExactVersion}>
              Submit to government review
            </button>
          )}
          {submitted && (
            <strong>
              Submitted to government queue · {submitted.queueItemId}
            </strong>
          )}
        </div>
      )}
      <p aria-live="polite">{message}</p>
    </section>
  );
}
