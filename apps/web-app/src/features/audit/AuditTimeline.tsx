import type {
  ActorReference,
  AuditTimelineDto,
  VersionReference,
} from "../../generated/contracts";

const labels: Record<string, string> = {
  config_activated: "Configuration activated",
  artifact_uploaded: "Source uploaded",
  extraction_drafted: "Extraction drafted",
  field_corrected: "Human extraction correction",
  field_reviewed: "Human extraction review",
  validation_completed: "Deterministic validation",
  invoice_line_corrected: "Invoice line corrected",
  finding_resolved: "Finding resolved",
  attested: "Human attestation",
  package_generated: "Immutable package generated",
  submitted: "Submitted",
  returned: "Returned by government",
  revision_created: "Revision created",
  resubmitted: "Resubmitted",
  approved: "Approved by government",
};

const reference = (value: VersionReference) =>
  `${value.kind}:${value.id}@${value.version}`;
const actor = (value: ActorReference) =>
  `${value.userId} · ${value.organizationId} · ${value.role}`;

export function AuditTimeline({ timeline }: { timeline: AuditTimelineDto | null }) {
  if (!timeline) {
    return <p aria-live="polite">Loading submitted audit evidence…</p>;
  }
  return (
    <>
      <section className="audit-summary" aria-label="Audit evidence summary">
        <div><b>{timeline.events.length}</b><span>material events</span></div>
        <div><b>{timeline.packages.length}</b><span>immutable packages</span></div>
        <div><b>{timeline.claimedAmountTrails.length}</b><span>claim-to-package trails</span></div>
      </section>

      <section className="audit-section" aria-labelledby="claim-trails-heading">
        <h3 id="claim-trails-heading">Claimed amount to both packages</h3>
        <div className="audit-grid">
          {timeline.claimedAmountTrails.map((trail) => (
            <article key={`${trail.packageId}-${trail.expenseKey}`} className="audit-card">
              <strong>{trail.expenseKey} · ${trail.claimedAmount}</strong>
              <ol className="audit-path">
                <li>Source <code>{trail.sourceArtifactId}</code><small>{trail.sourceLocation}</small></li>
                <li>Validation <code>{trail.validationRunId}</code></li>
                <li>Snapshot <code>{trail.invoiceSnapshotId}</code></li>
                <li>Invoice v{trail.invoiceVersion} <code>{trail.invoiceVersionId}</code></li>
                <li>Package <code>{trail.packageId}</code></li>
              </ol>
              <dl className="hashes">
                <dt>Package manifest</dt><dd><code>{trail.packageManifestHash}</code></dd>
                <dt>Archive SHA-256</dt><dd><code>{trail.archiveSha256}</code></dd>
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className="audit-section" aria-labelledby="timeline-heading">
        <h3 id="timeline-heading">Source-to-approval timeline</h3>
        <ol className="audit-timeline">
          {timeline.events.map(({ id, event, eventHash }) => (
            <li key={id}>
              <div><strong>{labels[event.eventType] || event.eventType}</strong><time dateTime={event.occurredAt}>{new Date(event.occurredAt).toISOString()}</time></div>
              <p>{actor(event.actor)}</p>
              <p>Aggregate <code>{reference(event.aggregate)}</code></p>
              <small>Event SHA-256 <code>{eventHash}</code></small>
            </li>
          ))}
        </ol>
      </section>

      <section className="audit-section" aria-labelledby="evidence-heading">
        <h3 id="evidence-heading">Versioned evidence</h3>
        <div className="audit-grid">
          {timeline.packages.map((item) => (
            <article key={item.packageId} className="audit-card">
              <strong>Invoice v{item.invoiceVersion} package</strong>
              <p><code>{item.packageId}</code></p>
              {item.configurationVersion && <p>Configuration <code>{reference(item.configurationVersion)}</code></p>}
              <ul className="context-references">
                {(item.documentProfiles || []).map((profile) => (
                  <li key={`${profile.id}:${profile.version}`}><code>{reference(profile)}</code>{profile.sha256 && <small>SHA-256 {profile.sha256}</small>}</li>
                ))}
              </ul>
              <p>Template <code>{item.templateId}@{item.templateVersion}</code></p>
              <dl className="hashes">
                <dt>Validation input</dt><dd><code>{item.validationInputManifestHash}</code></dd>
                <dt>Build input</dt><dd><code>{item.buildInputHash}</code></dd>
                <dt>Reproduction</dt><dd><code>{item.reproductionManifestHash}</code></dd>
              </dl>
            </article>
          ))}
        </div>
        <details>
          <summary>Lineage, snapshots, and typed relations</summary>
          <p>{timeline.lineage.length} lineage records · {timeline.snapshots.length} immutable snapshots · {timeline.relations.length} typed relations</p>
          <ul className="audit-records">
            {timeline.relations.map((item) => (
              <li key={item.id}><strong>{item.relationType}</strong> {reference(item.source)} → {reference(item.target)}<small>{actor(item.actor)} · {new Date(item.createdAt).toISOString()} · SHA-256 <code>{item.relationHash}</code></small></li>
            ))}
          </ul>
          <h4>Immutable invoice snapshots</h4>
          <ul className="audit-records">
            {timeline.snapshots.map((item) => (
              <li key={item.id}><strong>Invoice v{item.invoiceVersion} · revision {item.materialRevision} · {item.stage}</strong> <code>{item.id}</code><small>{actor(item.actor)} · {new Date(item.createdAt).toISOString()} · SHA-256 <code>{item.snapshotHash}</code></small></li>
            ))}
          </ul>
          <h4>Field lineage</h4>
          <ul className="audit-records">
            {timeline.lineage.map((item) => (
              <li key={item.id}><strong>{item.fieldName}</strong> → {String(item.fieldValue)}<small>source {item.sourceArtifactId || "retained predecessor"} · {item.sourceLocation || "n/a"} · importer {item.importerVersion || "n/a"} · extractor {item.extractorProvider || "n/a"}/{item.extractorModel || "n/a"} · parser {item.parserVersion || "n/a"} · mapping {item.mappingVersion || "n/a"} · predecessor {item.predecessorLineageId || "root"} · {new Date(item.recordedAt).toISOString()}{item.correctionActor ? ` · ${actor(item.correctionActor)}` : ""}</small></li>
            ))}
          </ul>
        </details>
      </section>
    </>
  );
}
