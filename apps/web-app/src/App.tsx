import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import type {
  ActiveConfigurationDto as ActiveConfiguration,
  AuditTimelineDto,
  ContractContextDto,
  GovernedConfigurationVersionDto as GovernedConfigurationVersion,
  IdentityDto as User,
  ValidationRunDto as ValidationRun,
} from "./generated/contracts";
import type { ApprovalPreview, Attestation, Configuration, Extraction, Finding, GeneratedPackage, InvoiceDraft, Job, QueueItem, ReviewContext, RevisionFeedback, Submission } from "./domain/types";
import { AuthenticatedWorkspace } from "./workspaces/AuthenticatedWorkspace";
import { GovernmentWorkspace } from "./features/government/GovernmentWorkspace";
import { demoMode, demoPersonas } from "./demo/personas";
import { authorizedContracts, currentSession, loginSession, logoutSession } from "./features/session/api";
import { listExtractions, listJobs, reviewExtraction, uploadEvidence } from "./features/ingestion/api";
import { assembleDraft, latestDraft } from "./features/invoices/api";
import {
  activeConfiguration as loadActiveConfiguration,
  configurationDraft,
  configurationEvidence as loadConfigurationEvidence,
  configurationHistory,
  configurationProfiles as loadConfigurationProfiles,
  confirmDocumentCluster,
  createProfileDraft,
  documentClusters as loadDocumentClusters,
  governConfiguration as governConfigurationRequest,
  governProfile,
  saveConfigurationDraft,
  type ConfigurationEvidenceView,
} from "./features/configuration/api";
import type {
  DocumentClusterView,
  DocumentProfileView,
  ProfileDraftCommand,
  StagedProfileReference,
} from "./features/configuration/types";
import { findings as loadFindings, latestValidation, resolveFinding as resolveFindingRequest, runValidation } from "./features/validation/api";
import { approvalPreview as loadApprovalPreview, attestInvoice, generateInvoicePackage, submitInvoice as submitInvoiceRequest } from "./features/approval/api";
import { decideGovernmentQueue, governmentQueue, inspectGovernmentQueue } from "./features/government/api";
import { correctRevision, revisionFeedback as loadRevisionFeedback } from "./features/revision/api";
import { auditTimeline as loadAuditTimeline } from "./features/audit/api";

const errorText = (error: unknown, fallback: string) =>
  error instanceof Error ? error.message : fallback;

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [contractContexts, setContractContexts] = useState<ContractContextDto[]>([]);
  const [contractId, setContractId] = useState<string | null>(null);
  const currentContract = useRef<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("Checking session…");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [extractions, setExtractions] = useState<Extraction[]>([]);
  const [draft, setDraft] = useState<InvoiceDraft | null>(null);
  const [configuration, setConfiguration] = useState<Configuration | null>(null);
  const [configurationDraftRevision, setConfigurationDraftRevision] = useState(0);
  const [activeConfiguration, setActiveConfiguration] = useState<ActiveConfiguration | null>(null);
  const [configurationLifecycle, setConfigurationLifecycle] = useState<GovernedConfigurationVersion[]>([]);
  const [configurationEvidence, setConfigurationEvidence] = useState<ConfigurationEvidenceView | null>(null);
  const [configurationProfiles, setConfigurationProfiles] = useState<DocumentProfileView[]>([]);
  const [documentClusters, setDocumentClusters] = useState<DocumentClusterView[]>([]);
  const [validation, setValidation] = useState<ValidationRun | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [approvalPreview, setApprovalPreview] = useState<ApprovalPreview | null>(null);
  const [attestation, setAttestation] = useState<Attestation | null>(null);
  const [generatedPackage, setGeneratedPackage] = useState<GeneratedPackage | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [reviewContext, setReviewContext] = useState<ReviewContext | null>(null);
  const [revisionFeedback, setRevisionFeedback] = useState<RevisionFeedback | null>(null);
  const [auditTimeline, setAuditTimeline] = useState<AuditTimelineDto | null>(null);

  const establishContext = useCallback(async (resolvedUser: User) => {
    const contexts = (await authorizedContracts()).contracts;
    if (contexts.length === 0) throw new Error("No authorized contract context is assigned.");
    setContractContexts(contexts);
    currentContract.current = contexts[0].contractId;
    setContractId(contexts[0].contractId);
    setUser(resolvedUser);
    setMessage("");
  }, []);
  const refreshJobs = useCallback(async () => {
    const requested = contractId;
    if (requested) { const result = await listJobs(requested); if (currentContract.current === requested) setJobs(result.jobs); }
  }, [contractId]);
  const refreshExtractions = useCallback(async () => {
    const requested = contractId;
    if (requested) { const result = await listExtractions(requested); if (currentContract.current === requested) setExtractions(result.extractions); }
  }, [contractId]);
  const refreshDraft = useCallback(async () => {
    const requested = contractId;
    if (requested) { const result = await latestDraft(requested); if (currentContract.current === requested) setDraft(result.invoice); }
  }, [contractId]);
  const refreshConfiguration = useCallback(async (role?: string) => {
    const requested = contractId;
    if (!requested) return;
    const active = await loadActiveConfiguration(requested);
    if (currentContract.current !== requested) return;
    setActiveConfiguration(active.configuration);
    if (role === "configuration_administrator") {
      const [draftResult, history, profiles, clusters] = await Promise.all([
        configurationDraft(requested),
        configurationHistory(requested),
        loadConfigurationProfiles(requested),
        loadDocumentClusters(requested),
      ]);
      if (currentContract.current !== requested) return;
      setConfiguration(draftResult.configuration);
      setConfigurationDraftRevision(draftResult.revision);
      setConfigurationLifecycle(history.versions || []);
      setConfigurationProfiles(profiles.profiles || []);
      setDocumentClusters(clusters.clusters || []);
      const ordered = (history.versions || []).slice().sort((left, right) => left.version - right.version);
      const target = ordered.at(-1);
      if (target) {
        const resolvedEvidence = await loadConfigurationEvidence(ordered, target.id);
        if (currentContract.current !== requested) return;
        setConfigurationEvidence(resolvedEvidence);
      } else {
        setConfigurationEvidence(null);
      }
    }
  }, [contractId]);

  useEffect(() => {
    currentSession().then(({ user: resolved }) => establishContext(resolved)).catch(() => setMessage(demoMode ? "Choose a persona to begin." : "Sign in to continue."));
  }, [establishContext]);
  useEffect(() => { if (user && contractId) refreshConfiguration(user.role).catch((e) => setMessage(errorText(e, "Configuration load failed"))); }, [user, contractId, refreshConfiguration]);
  useEffect(() => { if (user?.role === "ngo_approver" && contractId) refreshDraft().catch((e) => setMessage(errorText(e, "Draft load failed"))); }, [user, contractId, refreshDraft]);
  useEffect(() => { if (user?.role === "ngo_approver" && draft) refreshApproval(draft.id); }, [user, draft]);
  useEffect(() => { if (user?.role === "government_reviewer") governmentQueue().then(({ items }) => setQueue(items)).catch((e) => setMessage(errorText(e, "Queue load failed"))); }, [user]);
  useEffect(() => {
    if (user?.role !== "auditor" || !contractId) return;
    const requested = contractId;
    loadAuditTimeline(requested).then((timeline) => {
      if (currentContract.current === requested) setAuditTimeline(timeline);
    }).catch((e) => setMessage(errorText(e, "Audit reconstruction failed")));
  }, [user, contractId]);
  useEffect(() => {
    if (user?.role !== "ngo_preparer" || !contractId) return;
    refreshJobs(); refreshExtractions(); refreshDraft();
    const requested = contractId;
    loadRevisionFeedback(requested).then(({ feedback }) => { if (currentContract.current === requested) setRevisionFeedback(feedback); }).catch((e) => setMessage(errorText(e, "Revision feedback load failed")));
    const timer = window.setInterval(() => { refreshJobs(); refreshExtractions(); }, 500);
    return () => window.clearInterval(timer);
  }, [user, contractId, refreshJobs, refreshExtractions, refreshDraft]);

  async function login(event: FormEvent) {
    event.preventDefault(); setMessage("Signing in…");
    try { await establishContext((await loginSession(email, password)).user); }
    catch (error) { setMessage(errorText(error, "Invalid email or password.")); }
  }
  async function logout() {
    try { await logoutSession(); } finally {
      currentContract.current = null; setUser(null); setContractId(null); setContractContexts([]); setEmail(""); setPassword(""); setDraft(null);
      setValidation(null); setFindings([]); setApprovalPreview(null); setAttestation(null);
      setGeneratedPackage(null); setSubmission(null); setReviewContext(null); setConfigurationLifecycle([]); setConfigurationEvidence(null); setConfigurationProfiles([]); setDocumentClusters([]); setConfigurationDraftRevision(0); setAuditTimeline(null);
      setMessage(demoMode ? "Signed out. Choose a persona to continue." : "Signed out.");
    }
  }
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!contractId) return; const form = event.currentTarget;
    setMessage("Uploading and queueing…");
    try { await uploadEvidence(contractId, new FormData(form)); form.reset(); await refreshJobs(); setMessage("Upload queued for real background processing."); }
    catch (error) { setMessage(errorText(error, "Upload failed")); }
  }
  async function review(fieldId: string, decision: "accept" | "correct", value: string) {
    try { await reviewExtraction(fieldId, decision, value); await refreshExtractions(); setMessage(decision === "correct" ? "Correction recorded with provenance." : "Proposal accepted with provenance."); }
    catch (error) { setMessage(errorText(error, "Review failed")); }
  }
  async function assemble() {
    if (!contractId) return;
    try { setDraft((await assembleDraft(contractId)).invoice); setMessage("Evidence-linked draft assembled."); }
    catch (error) { setMessage(errorText(error, "Draft assembly failed")); }
  }
  async function saveConfiguration(value: Configuration) {
    if (!contractId) return;
    try { const saved = await saveConfigurationDraft(contractId, configurationDraftRevision, value); setConfiguration(saved.configuration); setConfigurationDraftRevision(saved.revision); setMessage("Configuration draft saved and validated."); }
    catch (error) { await refreshConfiguration("configuration_administrator").catch(() => undefined); setMessage(errorText(error, "Configuration save failed")); }
  }
  async function govern(path: string, payload: Record<string, string | number>, success: string) {
    try { await governConfigurationRequest(path, payload); await refreshConfiguration("configuration_administrator"); setMessage(success); }
    catch (error) { setMessage(errorText(error, "Configuration governance action failed")); }
  }
  const testConfiguration = (rationale: string) => contractId ? govern(`/api/configuration/test?contractId=${encodeURIComponent(contractId)}`, { rationale, expectedDraftRevision: configurationDraftRevision }, "Immutable configuration test evidence recorded.") : Promise.resolve();
  const approveConfiguration = (versionId: string, rationale: string) => govern(`/api/configuration/versions/${versionId}/approve`, { rationale }, "Human configuration approval recorded.");
  const activateConfiguration = (versionId: string, rationale: string) => govern("/api/configuration/activate", { versionId, rationale }, "Approved configuration activated prospectively.");
  const supersedeConfiguration = (activeVersionId: string, successorVersionId: string, rationale: string) => govern(`/api/configuration/versions/${activeVersionId}/supersede`, { successorVersionId, rationale }, "Active configuration superseded by its approved successor.");
  const retireConfiguration = (versionId: string, rationale: string) => govern(`/api/configuration/versions/${versionId}/retire`, { rationale }, "Superseded configuration retired with retained history.");
  const rollbackConfiguration = (versionId: string, rationale: string) => contractId ? govern(`/api/configuration/rollback?contractId=${encodeURIComponent(contractId)}`, { targetVersionId: versionId, rationale }, "Rollback candidate tested; approval and supersession are still required.") : Promise.resolve();
  async function selectConfigurationVersion(versionId: string) {
    try {
      setConfigurationEvidence(
        await loadConfigurationEvidence(configurationLifecycle, versionId),
      );
      setMessage("Read-only configuration history and prospective impact loaded.");
    } catch (error) {
      setMessage(errorText(error, "Configuration evidence load failed"));
    }
  }
  async function createDocumentProfile(command: ProfileDraftCommand) {
    if (!contractId) return;
    try {
      await createProfileDraft(contractId, command);
      await refreshConfiguration("configuration_administrator");
      setMessage("Immutable profile draft created from governed fixture inputs.");
    } catch (error) {
      setMessage(errorText(error, "Profile draft creation failed"));
    }
  }
  async function runProfileAction(
    profileId: string,
    action: "test" | "approve" | "retire",
    rationale: string,
  ) {
    try {
      await governProfile(profileId, action, rationale);
      await refreshConfiguration("configuration_administrator");
      setMessage(
        action === "test"
          ? "Immutable profile fixture evaluation recorded."
          : action === "approve"
            ? "Human profile approval recorded."
            : "Profile version retired with history preserved.",
      );
    } catch (error) {
      setMessage(errorText(error, `Profile ${action} failed`));
    }
  }
  function stageProfileReference(staged: StagedProfileReference) {
    setConfiguration((current) => {
      if (!current) return current;
      const existing = Array.isArray(current.documentProfiles)
        ? current.documentProfiles as StagedProfileReference["reference"][]
        : [];
      const retained = existing.filter((reference) => {
        const known = configurationProfiles.find(
          (item) => item.profile.id === reference.id,
        );
        return !known || known.profile.profileKey !== staged.profileKey;
      });
      return { ...current, documentProfiles: [...retained, staged.reference] };
    });
    setMessage(
      `Exact ${staged.profileKey} profile reference staged in the editable draft; save and test before activation.`,
    );
  }
  async function confirmCluster(
    clusterId: string,
    profileKey: string,
    rationale: string,
  ) {
    try {
      await confirmDocumentCluster(clusterId, profileKey, rationale);
      await refreshConfiguration("configuration_administrator");
      setMessage(
        "Cluster suggestion confirmed as a draft association only; no profile was assigned or activated.",
      );
    } catch (error) {
      setMessage(errorText(error, "Cluster confirmation failed"));
    }
  }
  async function refreshFindings(invoiceId: string) { setFindings((await loadFindings(invoiceId)).findings); }
  async function validate() {
    if (!draft) return;
    try { setValidation((await runValidation(draft.id)).validation); await refreshFindings(draft.id); setMessage("Deterministic validation completed."); }
    catch (error) { setMessage(errorText(error, "Validation failed")); }
  }
  async function resolveFinding(id: string, action: "correct" | "explain" | "dismiss", reason: string, correctionValue?: string) {
    if (!draft) return;
    try { setFindings((await resolveFindingRequest(id, action, reason, correctionValue)).resolution.findings); setValidation((await latestValidation(draft.id)).validation); setMessage("Finding resolved and deterministic validation rerun."); }
    catch (error) { setMessage(errorText(error, "Resolution failed")); }
  }
  async function refreshApproval(invoiceId: string) {
    try { const result = await loadApprovalPreview(invoiceId); setApprovalPreview(result.preview); setAttestation(result.attestation); }
    catch (error) { setMessage(errorText(error, "Approval context failed")); }
  }
  async function submitAttestation(text: string) { if (draft) try { setAttestation((await attestInvoice(draft.id, text)).attestation); setMessage("Exact invoice version attested."); } catch (e) { setMessage(errorText(e, "Attestation failed")); } }
  async function generatePackage() { if (draft) try { setGeneratedPackage((await generateInvoicePackage(draft.id)).package); setMessage("Immutable invoice package generated."); } catch (e) { setMessage(errorText(e, "Package generation failed")); } }
  async function submitInvoice() { if (draft) try { setSubmission((await submitInvoiceRequest(draft.id)).submission); setMessage("Immutable version submitted to the government queue."); } catch (e) { setMessage(errorText(e, "Submission failed")); } }
  async function inspectQueue(id: string) { try { setReviewContext((await inspectGovernmentQueue(id)).review); } catch (e) { setMessage(errorText(e, "Queue inspection failed")); } }
  async function decideQueue(queueId: string, decision: "returned" | "approved", reasonCode: string, note: string, lineKeys: string[]) {
    try { await decideGovernmentQueue(queueId, decision, reasonCode, note, lineKeys); setQueue((await governmentQueue()).items); setReviewContext(null); setMessage(decision === "returned" ? "Version returned with structured feedback." : "Corrected version approved."); }
    catch (e) { setMessage(errorText(e, "Decision failed")); }
  }
  async function correctReturnedRevision(expenseKey: string, description: string, reason: string) {
    if (!draft) return;
    try { await correctRevision(draft.id, expenseKey, description, reason); await refreshDraft(); setMessage("Government feedback correction recorded. Run validation."); }
    catch (e) { setMessage(errorText(e, "Revision correction failed")); }
  }

  function selectContract(nextContractId: string) {
    currentContract.current = nextContractId; setContractId(nextContractId);
    setJobs([]); setExtractions([]); setConfiguration(null); setConfigurationDraftRevision(0); setActiveConfiguration(null); setConfigurationLifecycle([]); setConfigurationEvidence(null); setConfigurationProfiles([]); setDocumentClusters([]);
    setDraft(null); setValidation(null); setFindings([]);
    setApprovalPreview(null); setAttestation(null); setGeneratedPackage(null); setSubmission(null);
    setReviewContext(null); setQueue([]); setRevisionFeedback(null); setAuditTimeline(null); setMessage("");
  }

  if (user?.role === "government_reviewer") return <GovernmentWorkspace user={user} activeConfiguration={activeConfiguration} queue={queue} review={reviewContext} onInspect={inspectQueue} onDecision={decideQueue} message={message} onLogout={logout} />;
  if (user) return <AuthenticatedWorkspace user={user} contractContexts={contractContexts} contractId={contractId || ""} onSelectContract={selectContract} jobs={jobs} extractions={extractions} draft={draft} configuration={configuration} configurationDraftRevision={configurationDraftRevision} configurationEvidence={configurationEvidence} configurationProfiles={configurationProfiles} documentClusters={documentClusters} activeConfiguration={activeConfiguration} configurationLifecycle={configurationLifecycle} validation={validation} findings={findings} revisionFeedback={revisionFeedback} auditTimeline={auditTimeline} approvalPreview={approvalPreview} attestation={attestation} generatedPackage={generatedPackage} submission={submission} message={message} onLogout={logout} onUpload={upload} onReview={review} onAssemble={assemble} onValidate={validate} onResolveFinding={resolveFinding} onCorrectRevision={correctReturnedRevision} onAttest={submitAttestation} onGeneratePackage={generatePackage} onSubmitInvoice={submitInvoice} onSaveConfiguration={saveConfiguration} onTestConfiguration={testConfiguration} onApproveConfiguration={approveConfiguration} onActivateConfiguration={activateConfiguration} onSupersedeConfiguration={supersedeConfiguration} onRetireConfiguration={retireConfiguration} onRollbackConfiguration={rollbackConfiguration} onSelectConfigurationVersion={selectConfigurationVersion} onCreateProfile={createDocumentProfile} onTestProfile={(id, rationale) => runProfileAction(id, "test", rationale)} onApproveProfile={(id, rationale) => runProfileAction(id, "approve", rationale)} onRetireProfile={(id, rationale) => runProfileAction(id, "retire", rationale)} onStageProfile={stageProfileReference} onConfirmCluster={confirmCluster} />;
  return <main>
    <p className="eyebrow">Synthetic role-based POC</p><h1>Sign in</h1>
    <p className="summary">{demoMode ? "Select a seeded persona. The card fills credentials; the normal server login still runs." : "Use your assigned account. Contract context is resolved by the authenticated server session."}</p>
    {demoMode && <div className="persona-grid">{demoPersonas.map(([role, name, personaEmail, personaPassword]) => <button className="persona" key={role} onClick={() => { setEmail(personaEmail); setPassword(personaPassword); }}><strong>{role}</strong><span>{name}</span></button>)}</div>}
    <form onSubmit={login}><label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required /></label><label>Password<input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required /></label><button className="primary" type="submit">Sign in</button></form>
    <p aria-live="polite">{message}</p>
  </main>;
}

export { AuthenticatedWorkspace } from "./workspaces/AuthenticatedWorkspace";
export { RevisionFeedbackPanel } from "./features/revision/RevisionFeedbackPanel";
export { GovernmentWorkspace } from "./features/government/GovernmentWorkspace";
export { ExtractionReview } from "./features/ingestion/ExtractionReview";
export { InvoiceDraftView } from "./features/invoices/InvoiceDraftView";
export { ConfigurationAdmin } from "./features/configuration/ConfigurationAdmin";
export { ValidationView } from "./features/validation/ValidationView";
export { FindingResolutionView } from "./features/validation/FindingResolutionView";
export { ApprovalPanel } from "./features/approval/ApprovalPanel";
