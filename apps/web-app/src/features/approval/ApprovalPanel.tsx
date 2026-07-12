import { useState } from "react";
import type { ApprovalPreview, Attestation, GeneratedPackage, Submission } from "../../domain/types";
import { InvoiceDraftView } from "../invoices/InvoiceDraftView";

export function ApprovalPanel({
  preview,
  attestation,
  generatedPackage,
  submission,
  message,
  onAttest,
  onGeneratePackage,
  onSubmit,
}: {
  preview: ApprovalPreview;
  attestation: Attestation | null;
  generatedPackage: GeneratedPackage | null;
  submission: Submission | null;
  message: string;
  onAttest: (text: string) => void;
  onGeneratePackage: () => void;
  onSubmit: () => void;
}) {
  const [confirmed, setConfirmed] = useState(false);
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
          {!submission && (
            <button className="primary" onClick={onSubmit}>
              Submit to government review
            </button>
          )}
          {submission && (
            <strong>
              Submitted to government queue · {submission.queueItemId}
            </strong>
          )}
        </div>
      )}
      <p aria-live="polite">{message}</p>
    </section>
  );
}
