import type { FormEvent } from "react";
import type { ActiveConfigurationDto as ActiveConfiguration, AuditTimelineDto, ContractContextDto, GovernedConfigurationVersionDto as GovernedConfigurationVersion, IdentityDto as User, ValidationRunDto as ValidationRun } from "../generated/contracts";
import type { ApprovalPreview, Attestation, Configuration, Extraction, Finding, GeneratedPackage, InvoiceDraft, Job, RevisionFeedback, Submission } from "../domain/types";
import { AuditorWorkspace } from "./AuditorWorkspace";
import { ConfigurationWorkspace } from "./ConfigurationWorkspace";
import { NgoApproverWorkspace } from "./NgoApproverWorkspace";
import { NgoPreparerWorkspace } from "./NgoPreparerWorkspace";
import { ContractSelector } from "../presentation/ContractSelector";
import { IdentityHeader } from "../presentation/IdentityHeader";
import type { ConfigurationEvidenceView } from "../features/configuration/api";
import type {
  DocumentClusterView,
  DocumentProfileView,
  ProfileDraftCommand,
  StagedProfileReference,
} from "../features/configuration/types";

export function AuthenticatedWorkspace({
  user,
  contractContexts = [],
  contractId = "",
  onSelectContract = () => {},
  jobs,
  extractions,
  draft,
  configuration,
  configurationDraftRevision = 0,
  configurationEvidence = null,
  configurationProfiles = [],
  documentClusters = [],
  activeConfiguration,
  configurationLifecycle,
  validation,
  findings,
  revisionFeedback,
  auditTimeline = null,
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
  onSelectConfigurationVersion = () => {},
  onCreateProfile = () => {},
  onTestProfile = () => {},
  onApproveProfile = () => {},
  onRetireProfile = () => {},
  onStageProfile = () => {},
  onConfirmCluster = () => {},
}: {
  user: User;
  contractContexts?: ContractContextDto[];
  contractId?: string;
  onSelectContract?: (contractId: string) => void;
  jobs: Job[];
  extractions: Extraction[];
  draft: InvoiceDraft | null;
  configuration: Configuration | null;
  configurationDraftRevision?: number;
  configurationEvidence?: ConfigurationEvidenceView | null;
  configurationProfiles?: DocumentProfileView[];
  documentClusters?: DocumentClusterView[];
  activeConfiguration: ActiveConfiguration | null;
  configurationLifecycle: GovernedConfigurationVersion[];
  validation: ValidationRun | null;
  findings: Finding[];
  revisionFeedback: RevisionFeedback | null;
  auditTimeline?: AuditTimelineDto | null;
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
  onSelectConfigurationVersion?: (versionId: string) => void;
  onCreateProfile?: (command: ProfileDraftCommand) => void;
  onTestProfile?: (profileId: string, rationale: string) => void;
  onApproveProfile?: (profileId: string, rationale: string) => void;
  onRetireProfile?: (profileId: string, rationale: string) => void;
  onStageProfile?: (profile: StagedProfileReference) => void;
  onConfirmCluster?: (clusterId: string, profileKey: string, rationale: string) => void;
}) {
  const selectedContract = contractContexts.find((context) => context.contractId === contractId) || null;
  return (
    <>
      <IdentityHeader user={user} activeConfiguration={activeConfiguration} onLogout={onLogout}>
        {contractId && <ContractSelector contexts={contractContexts} value={contractId} onChange={onSelectContract} />}
      </IdentityHeader>
      <main className="workspace-shell">
        <p className="eyebrow">Synthetic role-based POC</p>
        <h1>Workspace</h1>
        <p className="summary">
          Your navigation and available actions are scoped to the signed-in
          persona. The API enforces the same boundaries independently.
        </p>
        {user.role === "configuration_administrator" && !configuration && (
          <section className="panel" aria-label="Configuration workspace status">
            <h2>Configuration Administrator workspace</h2>
            <p
              role={/(failed|forbidden|denied|unauthorized|error)/i.test(message) ? "alert" : "status"}
            >
              {message || "Loading governed configuration, profile, and exception evidence…"}
            </p>
          </section>
        )}
        {user.role === "configuration_administrator" && configuration && <ConfigurationWorkspace configuration={configuration} draftRevision={configurationDraftRevision} evidence={configurationEvidence} profiles={configurationProfiles} clusters={documentClusters} active={activeConfiguration} versions={configurationLifecycle} message={message} onSave={onSaveConfiguration} onTest={onTestConfiguration} onApprove={onApproveConfiguration} onActivate={onActivateConfiguration} onSupersede={onSupersedeConfiguration} onRetire={onRetireConfiguration} onRollback={onRollbackConfiguration} onSelectVersion={onSelectConfigurationVersion} onCreateProfile={onCreateProfile} onTestProfile={onTestProfile} onApproveProfile={onApproveProfile} onRetireProfile={onRetireProfile} onStageProfile={onStageProfile} onConfirmCluster={onConfirmCluster} />}
        {user.role === "ngo_preparer" && <NgoPreparerWorkspace contract={selectedContract} activeConfiguration={activeConfiguration} jobs={jobs} extractions={extractions} draft={draft} validation={validation} findings={findings} feedback={revisionFeedback} message={message} onUpload={onUpload} onReview={onReview} onAssemble={onAssemble} onValidate={onValidate} onResolve={onResolveFinding} onCorrect={onCorrectRevision} />}
        {user.role === "ngo_approver" && <NgoApproverWorkspace contract={selectedContract} activeConfiguration={activeConfiguration} preview={approvalPreview} attestation={attestation} generatedPackage={generatedPackage} submission={submission} message={message} onAttest={onAttest} onGeneratePackage={onGeneratePackage} onSubmit={onSubmitInvoice} />}
        {user.role === "auditor" && <AuditorWorkspace contract={selectedContract} activeConfiguration={activeConfiguration} timeline={auditTimeline} />}
      </main>
    </>
  );
}
