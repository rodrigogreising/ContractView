import type { FormEvent } from "react";
import type { ActiveConfigurationDto as ActiveConfiguration, AuditTimelineDto, ContractContextDto, GovernedConfigurationVersionDto as GovernedConfigurationVersion, IdentityDto as User, ValidationRunDto as ValidationRun } from "../generated/contracts";
import type { ApprovalPreview, Attestation, Configuration, Extraction, Finding, GeneratedPackage, InvoiceDraft, Job, RevisionFeedback, Submission } from "../domain/types";
import { AuditorWorkspace } from "./AuditorWorkspace";
import { ConfigurationWorkspace } from "./ConfigurationWorkspace";
import { NgoApproverWorkspace } from "./NgoApproverWorkspace";
import { NgoPreparerWorkspace } from "./NgoPreparerWorkspace";
import { ContractSelector } from "../presentation/ContractSelector";
import { IdentityHeader } from "../presentation/IdentityHeader";

export function AuthenticatedWorkspace({
  user,
  contractContexts = [],
  contractId = "",
  onSelectContract = () => {},
  jobs,
  extractions,
  draft,
  configuration,
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
}: {
  user: User;
  contractContexts?: ContractContextDto[];
  contractId?: string;
  onSelectContract?: (contractId: string) => void;
  jobs: Job[];
  extractions: Extraction[];
  draft: InvoiceDraft | null;
  configuration: Configuration | null;
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
}) {
  return (
    <>
      <IdentityHeader user={user} activeConfiguration={activeConfiguration} onLogout={onLogout}>
        {contractId && <ContractSelector contexts={contractContexts} value={contractId} onChange={onSelectContract} />}
      </IdentityHeader>
      <main>
        <p className="eyebrow">Synthetic role-based POC</p>
        <h1>Workspace</h1>
        <p className="summary">
          Your navigation and available actions are scoped to the signed-in
          persona. The API enforces the same boundaries independently.
        </p>
        {user.role === "configuration_administrator" && configuration && <ConfigurationWorkspace configuration={configuration} active={activeConfiguration} versions={configurationLifecycle} message={message} onSave={onSaveConfiguration} onTest={onTestConfiguration} onApprove={onApproveConfiguration} onActivate={onActivateConfiguration} onSupersede={onSupersedeConfiguration} onRetire={onRetireConfiguration} onRollback={onRollbackConfiguration} />}
        {user.role === "ngo_preparer" && <NgoPreparerWorkspace jobs={jobs} extractions={extractions} draft={draft} validation={validation} findings={findings} feedback={revisionFeedback} message={message} onUpload={onUpload} onReview={onReview} onAssemble={onAssemble} onValidate={onValidate} onResolve={onResolveFinding} onCorrect={onCorrectRevision} />}
        {user.role === "ngo_approver" && approvalPreview && <NgoApproverWorkspace preview={approvalPreview} attestation={attestation} generatedPackage={generatedPackage} submission={submission} message={message} onAttest={onAttest} onGeneratePackage={onGeneratePackage} onSubmit={onSubmitInvoice} />}
        {user.role === "auditor" && <AuditorWorkspace timeline={auditTimeline} />}
      </main>
    </>
  );
}
