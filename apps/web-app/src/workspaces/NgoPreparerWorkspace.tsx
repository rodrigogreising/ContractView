import type { FormEvent } from "react";
import type { ValidationRunDto } from "../generated/contracts";
import type { Extraction, Finding, InvoiceDraft, Job, RevisionFeedback } from "../domain/types";
import { ExtractionReview } from "../features/ingestion/ExtractionReview";
import { InvoiceDraftView } from "../features/invoices/InvoiceDraftView";
import { RevisionFeedbackPanel } from "../features/revision/RevisionFeedbackPanel";
import { FindingResolutionView } from "../features/validation/FindingResolutionView";
import { ValidationView } from "../features/validation/ValidationView";

export function NgoPreparerWorkspace({ jobs, extractions, draft, validation, findings, feedback, message, onUpload, onReview, onAssemble, onValidate, onResolve, onCorrect }: { jobs: Job[]; extractions: Extraction[]; draft: InvoiceDraft | null; validation: ValidationRunDto | null; findings: Finding[]; feedback: RevisionFeedback | null; message: string; onUpload: (event: FormEvent<HTMLFormElement>) => void; onReview: (id: string, decision: "accept" | "correct", value: string) => void; onAssemble: () => void; onValidate: () => void; onResolve: (id: string, action: "correct" | "explain" | "dismiss", reason: string, correctionValue?: string) => void; onCorrect: (expenseKey: string, description: string, reason: string) => void }) {
  return <>
    {feedback && draft && <RevisionFeedbackPanel feedback={feedback} draft={draft} onCorrect={onCorrect} />}
    <section className="panel"><h2>Upload ledger and evidence</h2><p>CSV, XLSX, PDF, PNG, or JPEG. Maximum 10 MB each.</p><form onSubmit={onUpload}><label>Evidence file<input name="file" type="file" accept=".csv,.xlsx,.pdf,.png,.jpg,.jpeg" required /></label><button className="primary" type="submit">Upload and process</button></form><p aria-live="polite">{message}</p><h3>Processing jobs</h3>{jobs.length === 0 ? <p>No uploads yet.</p> : <ul className="jobs">{jobs.map((job) => <li key={job.id}><span>{job.job_type === "ledger_import" ? "Ledger import" : "Evidence extraction"}</span><strong className={`job-${job.status}`}>{job.status}</strong>{job.error_message && <small>{job.error_message}</small>}</li>)}</ul>}</section>
    <ExtractionReview extractions={extractions} onReview={onReview} />
    <section className="panel"><div className="section-action"><div><h2>Evidence-linked invoice draft</h2><p>Assemble from reviewed values, immutable evidence, and the active configuration.</p></div><button className="primary" onClick={onAssemble}>Assemble draft</button></div>{draft && <><InvoiceDraftView draft={draft} /><button className="primary validation-action" onClick={onValidate}>Run deterministic validation</button>{validation && <ValidationView validation={validation} />}<FindingResolutionView findings={findings} onResolve={onResolve} /></>}</section>
  </>;
}
