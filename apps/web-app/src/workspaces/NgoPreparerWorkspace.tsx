import type { FormEvent } from "react";
import type { ActiveConfigurationDto, ContractContextDto, ValidationRunDto } from "../generated/contracts";
import type { Extraction, Finding, InvoiceDraft, Job, RevisionFeedback } from "../domain/types";
import { ExtractionReview } from "../features/ingestion/ExtractionReview";
import { InvoiceDraftView } from "../features/invoices/InvoiceDraftView";
import { RevisionFeedbackPanel } from "../features/revision/RevisionFeedbackPanel";
import { FindingResolutionView } from "../features/validation/FindingResolutionView";
import { ValidationView } from "../features/validation/ValidationView";
import { RoleDashboard } from "../presentation/RoleDashboard";

function nextAction(jobs: Job[], extractions: Extraction[], draft: InvoiceDraft | null, validation: ValidationRunDto | null, findings: Finding[], feedback: RevisionFeedback | null) {
  if (feedback) return "Apply the government feedback to a new invoice version, then revalidate it.";
  if (jobs.length === 0) return "Upload the ledger and supporting evidence for background processing.";
  if (extractions.some((item) => item.fields.some((field) => field.reviewStatus === "proposed"))) return "Review every proposed extraction value against its source evidence.";
  if (!draft) return "Assemble the reviewed evidence into the canonical invoice draft.";
  if (!validation) return "Run deterministic validation on the exact draft version.";
  if (findings.some((finding) => finding.status === "open")) return "Resolve the open deterministic findings and revalidate.";
  return "Validation is ready; wait for the NGO Approver to attest this exact version.";
}

export function NgoPreparerWorkspace({ contract, activeConfiguration, jobs, extractions, draft, validation, findings, feedback, message, onUpload, onReview, onAssemble, onValidate, onResolve, onCorrect }: { contract: ContractContextDto | null; activeConfiguration: ActiveConfigurationDto | null; jobs: Job[]; extractions: Extraction[]; draft: InvoiceDraft | null; validation: ValidationRunDto | null; findings: Finding[]; feedback: RevisionFeedback | null; message: string; onUpload: (event: FormEvent<HTMLFormElement>) => void; onReview: (id: string, decision: "accept" | "correct", value: string) => void; onAssemble: () => void; onValidate: () => void; onResolve: (id: string, action: "correct" | "explain" | "dismiss", reason: string, correctionValue?: string) => void; onCorrect: (expenseKey: string, description: string, reason: string) => void }) {
  return <>
    <RoleDashboard title="NGO Preparer dashboard" nextAction={nextAction(jobs, extractions, draft, validation, findings, feedback)} authority="You may upload source artifacts, review draft extraction values, assemble the canonical invoice, run deterministic validation, and correct returned drafts for this assigned NGO contract." unavailable={["You cannot attest, generate a submission package, or submit an invoice.", "You cannot return or approve government decisions.", "You cannot test, approve, or activate configuration or document profiles."]} contract={contract} activeConfiguration={activeConfiguration} exactContext={draft ? { label: `Invoice v${draft.version} context`, configuration: draft.configurationVersion || { kind: "configuration", id: draft.configurationVersionId, version: draft.configurationVersionId }, documentProfiles: draft.documentProfiles || [], note: "This invoice retains these exact references even after a successor becomes active." } : null} workTarget="preparer-work" />
    {feedback && draft && <RevisionFeedbackPanel feedback={feedback} draft={draft} onCorrect={onCorrect} />}
    <section className="panel" id="preparer-work"><h2>Upload ledger and evidence</h2><p>CSV, XLSX, PDF, PNG, or JPEG. Maximum 10 MB each.</p><form onSubmit={onUpload}><label>Evidence file<input name="file" type="file" accept=".csv,.xlsx,.pdf,.png,.jpg,.jpeg" required /></label><button className="primary" type="submit">Upload and process</button></form><p aria-live="polite">{message}</p><h3>Processing jobs</h3>{jobs.length === 0 ? <p>No uploads yet.</p> : <ul className="jobs">{jobs.map((job) => <li key={job.id}><span>{job.job_type === "ledger_import" ? "Ledger import" : "Evidence extraction"}</span><strong className={`job-${job.status}`}>{job.status}</strong>{job.error_message && <small>{job.error_message}</small>}</li>)}</ul>}</section>
    <ExtractionReview extractions={extractions} onReview={onReview} />
    <section className="panel"><div className="section-action"><div><h2>Evidence-linked invoice draft</h2><p>Assemble from reviewed values, immutable evidence, and the active configuration.</p></div><button className="primary" onClick={onAssemble}>Assemble draft</button></div>{draft && <><InvoiceDraftView draft={draft} /><button className="primary validation-action" onClick={onValidate}>Run deterministic validation</button>{validation && <ValidationView validation={validation} />}<FindingResolutionView findings={findings} onResolve={onResolve} /></>}</section>
  </>;
}
