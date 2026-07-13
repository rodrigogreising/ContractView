import { useState } from "react";
import type { ActiveConfigurationDto as ActiveConfiguration, ContractContextDto, IdentityDto as User } from "../../generated/contracts";
import type { QueueItem, ReviewContext } from "../../domain/types";
import { IdentityHeader } from "../../presentation/IdentityHeader";
import { RoleDashboard } from "../../presentation/RoleDashboard";

export function GovernmentWorkspace({
  user,
  contract = null,
  activeConfiguration,
  queue,
  review,
  onInspect,
  onDecision,
  message,
  onLogout,
}: {
  user: User;
  contract?: ContractContextDto | null;
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
  const reviewConfiguration = review ? review.configurationVersion || { kind: "configuration" as const, id: review.configurationVersionId, version: review.configurationVersionId } : null;
  return (
    <>
      <IdentityHeader user={user} activeConfiguration={activeConfiguration} onLogout={onLogout} />
      <main className="workspace-shell">
        <p className="eyebrow">Synthetic role-based POC</p>
        <h1>Government queue</h1>
        <RoleDashboard title="Government Reviewer dashboard" nextAction={review ? `Review the exact evidence for invoice v${review.invoiceVersion} and record a return or approval decision.` : queue.some((item) => item.status === "submitted") ? "Inspect the next submitted package in your assigned government queue." : "No submitted package awaits a decision; retain read-only queue access."} authority="You alone may inspect assigned submitted packages and record a structured return or final government approval." unavailable={["You cannot upload, correct, validate, attest, package, or submit NGO invoice drafts.", "You cannot test, approve, or activate configuration or document profiles.", "You cannot review unsubmitted or cross-agency invoice evidence."]} contract={contract} activeConfiguration={activeConfiguration} exactContext={review ? { label: `Invoice v${review.invoiceVersion} review context`, configuration: reviewConfiguration, documentProfiles: review.documentProfiles || [], note: "The decision binds to this submitted historical context even if a successor is currently active." } : null} workTarget="government-work" />
        <section className="panel" id="government-work">
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
            <p>Invoice v{review.invoiceVersion} · <code>configuration:{reviewConfiguration?.id}@{reviewConfiguration?.version}</code> · ${review.amount}</p>
            <ul className="context-references">
              {(review.documentProfiles || []).map((profile) => <li key={`${profile.id}:${profile.version}`}><code>{profile.kind}:{profile.id}@{profile.version}</code>{profile.sha256 && <small>SHA-256 {profile.sha256}</small>}</li>)}
            </ul>
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
