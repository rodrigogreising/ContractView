import { useEffect, useMemo, useState } from "react";
import type {
  ActiveConfigurationDto as ActiveConfiguration,
  GovernedConfigurationVersionDto as GovernedConfigurationVersion,
} from "../../generated/contracts";
import type { Configuration } from "../../domain/types";
import { roleLabel } from "../../presentation/roleLabel";
import type { ConfigurationEvidenceView } from "./api";
import { DocumentProfileAdmin } from "./DocumentProfileAdmin";
import type {
  DocumentClusterView,
  DocumentProfileView,
  ProfileDraftCommand,
  StagedProfileReference,
} from "./types";

export type ConfigurationAdminSection = "overview" | "configuration" | "profiles";

const isErrorMessage = (message: string) =>
  /(failed|forbidden|denied|unauthorized|invalid|stale|error)/i.test(message);

export function nextAdministratorAction(
  versions: GovernedConfigurationVersion[],
  profiles: DocumentProfileView[],
  clusters: DocumentClusterView[],
): string {
  const suggested = clusters.filter((cluster) => cluster.status === "suggested").length;
  if (suggested) return `Review ${suggested} changed or unknown document layout${suggested === 1 ? "" : "s"}.`;
  if (profiles.some((profile) => profile.state === "draft")) return "Test the draft document profile against its fixed fixture set.";
  if (profiles.some((profile) => profile.state === "tested")) return "Approve the tested document profile evidence.";
  if (versions.some((version) => version.state === "tested")) return "Review and approve the tested configuration version.";
  if (versions.some((version) => version.state === "approved")) return "Review prospective impact and explicitly confirm activation.";
  return "Edit the draft and run deterministic configuration tests.";
}

function ConfigurationEditor({
  value,
  onChange,
  onSave,
}: {
  value: Configuration;
  onChange: (value: Configuration) => void;
  onSave: (value: Configuration) => void;
}) {
  const category = (index: number, limit: string) =>
    onChange({
      ...value,
      categories: value.categories.map((item, itemIndex) =>
        itemIndex === index ? { ...item, limit } : item,
      ),
    });
  const rule = (
    index: number,
    change: Partial<Configuration["rules"][number]>,
  ) =>
    onChange({
      ...value,
      rules: value.rules.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...change } : item,
      ),
    });

  return (
    <section className="admin-card" aria-labelledby="draft-editor-title">
      <div className="section-action">
        <div>
          <h3 id="draft-editor-title">Editable configuration draft</h3>
          <p>Change governed business fields directly. Raw configuration JSON is not exposed.</p>
        </div>
        <span className="status-chip status-draft">draft</span>
      </div>
      <h4>Categories and limits</h4>
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
      <h4>Deterministic rules</h4>
      {value.rules.map((item, index) => (
        <div className="rule-row" key={item.code}>
          <strong>{item.code}</strong>
          <label>
            Enabled
            <input
              type="checkbox"
              checked={item.enabled}
              onChange={(event) => rule(index, { enabled: event.target.checked })}
            />
          </label>
          <label>
            Severity
            <select
              value={item.severity}
              onChange={(event) => rule(index, { severity: event.target.value })}
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
                  onChange={(event) => rule(index, { amountTolerance: event.target.value })}
                />
              </label>
              <label>
                Day window
                <input
                  type="number"
                  value={item.dayWindow}
                  onChange={(event) => rule(index, { dayWindow: Number(event.target.value) })}
                />
              </label>
            </>
          )}
        </div>
      ))}
      <h4>Workflow and package labels</h4>
      <div className="config-grid">
        {Object.entries(value.workflowLabels).map(([key, label]) => (
          <label key={key}>
            {roleLabel(key)}
            <input
              value={label}
              onChange={(event) =>
                onChange({
                  ...value,
                  workflowLabels: { ...value.workflowLabels, [key]: event.target.value },
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
              onChange({ ...value, package: { ...value.package, label: event.target.value } })
            }
          />
        </label>
        <label>
          Invoice title
          <input
            value={value.package.invoiceTitle}
            onChange={(event) =>
              onChange({ ...value, package: { ...value.package, invoiceTitle: event.target.value } })
            }
          />
        </label>
      </div>
      <button className="primary" onClick={() => onSave(value)}>
        Save validated draft
      </button>
    </section>
  );
}

function VersionSummary({ version }: { version: GovernedConfigurationVersion }) {
  const configuration = version.configuration as Partial<Configuration>;
  const enabledRules = configuration.rules?.filter((rule) => rule.enabled).length || 0;
  return (
    <dl className="admin-facts">
      <div><dt>Service period</dt><dd>{configuration.servicePeriod ? `${configuration.servicePeriod.start} to ${configuration.servicePeriod.end}` : "not recorded"}</dd></div>
      <div><dt>Categories</dt><dd>{configuration.categories?.length || 0}</dd></div>
      <div><dt>Enabled rules</dt><dd>{enabledRules}</dd></div>
      <div><dt>Payload hash</dt><dd><code>{version.payloadHash}</code></dd></div>
    </dl>
  );
}

export function ConfigurationAdmin({
  configuration,
  draftRevision = 0,
  evidence = null,
  active,
  versions,
  profiles = [],
  clusters = [],
  message,
  initialSection = "overview",
  onSave,
  onTest,
  onApprove,
  onActivate,
  onSupersede,
  onRetire,
  onRollback,
  onSelectVersion = () => {},
  onCreateProfile = () => {},
  onTestProfile = () => {},
  onApproveProfile = () => {},
  onRetireProfile = () => {},
  onStageProfile = () => {},
  onConfirmCluster = () => {},
}: {
  configuration: Configuration;
  draftRevision?: number;
  evidence?: ConfigurationEvidenceView | null;
  active: ActiveConfiguration | null;
  versions: GovernedConfigurationVersion[];
  profiles?: DocumentProfileView[];
  clusters?: DocumentClusterView[];
  message: string;
  initialSection?: ConfigurationAdminSection;
  onSave: (value: Configuration) => void;
  onTest: (rationale: string) => void;
  onApprove: (versionId: string, rationale: string) => void;
  onActivate: (versionId: string, rationale: string) => void;
  onSupersede: (activeVersionId: string, successorVersionId: string, rationale: string) => void;
  onRetire: (versionId: string, rationale: string) => void;
  onRollback: (versionId: string, rationale: string) => void;
  onSelectVersion?: (versionId: string) => void;
  onCreateProfile?: (command: ProfileDraftCommand) => void;
  onTestProfile?: (profileId: string, rationale: string) => void;
  onApproveProfile?: (profileId: string, rationale: string) => void;
  onRetireProfile?: (profileId: string, rationale: string) => void;
  onStageProfile?: (profile: StagedProfileReference) => void;
  onConfirmCluster?: (clusterId: string, profileKey: string, rationale: string) => void;
}) {
  const [value, setValue] = useState(configuration);
  const [rationale, setRationale] = useState("");
  const [section, setSection] = useState<ConfigurationAdminSection>(initialSection);
  const [activationConfirmed, setActivationConfirmed] = useState(false);
  useEffect(() => setValue(configuration), [configuration]);
  useEffect(() => setActivationConfirmed(false), [evidence?.detail.id]);

  const orderedVersions = useMemo(
    () => versions.slice().sort((left, right) => right.version - left.version),
    [versions],
  );
  const activeVersion = versions.find((version) => version.active);
  const canGovern = rationale.trim().length > 0;
  const activationCandidate = evidence?.detail.state === "approved" ? evidence.detail : null;
  const canActivateCandidate = Boolean(
    activationCandidate?.testEvidence?.passed &&
      activationCandidate.approval &&
      activationConfirmed &&
      canGovern,
  );
  const nextAction = nextAdministratorAction(versions, profiles, clusters);
  const latest = orderedVersions[0] || null;
  const suggestedClusters = clusters.filter((cluster) => cluster.status === "suggested").length;

  return (
    <section className="panel admin-workspace" aria-labelledby="configuration-workspace-title">
      <div className="section-action">
        <div>
          <p className="eyebrow">Configuration control plane</p>
          <h2 id="configuration-workspace-title">Configuration Administrator workspace</h2>
          <p>
            Govern deterministic reimbursement settings and document profiles for
            future intake. The server independently enforces every action.
          </p>
        </div>
        <span className="status-chip status-active">
          {active ? `active v${active.version}` : "no active version"}
        </span>
      </div>

      <nav className="admin-nav" aria-label="Configuration workspace sections">
        {([
          ["overview", "Overview"],
          ["configuration", "Configuration lifecycle"],
          ["profiles", "Profiles and exceptions"],
        ] as const).map(([id, label]) => (
          <button key={id} aria-pressed={section === id} onClick={() => setSection(id)}>
            {label}
          </button>
        ))}
      </nav>

      {section === "overview" && (
        <div className="admin-section-stack">
          <section className="admin-overview" aria-label="Configuration overview">
            <div><span>Current control</span><strong>{active ? `Configuration v${active.version}` : "Activation required"}</strong></div>
            <div><span>Editable draft</span><strong>Revision {draftRevision}</strong></div>
            <div><span>Immutable history</span><strong>{versions.length} versions</strong></div>
            <div><span>Document profiles</span><strong>{profiles.length} versions</strong></div>
            <div><span>Safe exception queue</span><strong>{suggestedClusters} suggestions</strong></div>
          </section>
          <section className="admin-card next-action" aria-labelledby="next-action-title">
            <h3 id="next-action-title">Next required action</h3>
            <p>{nextAction}</p>
            <button onClick={() => setSection(suggestedClusters ? "profiles" : "configuration")}>
              Open the required workspace
            </button>
          </section>
          <section className="admin-card" aria-labelledby="current-impact-title">
            <h3 id="current-impact-title">Current and prospective impact</h3>
            {evidence ? (
              <>
                <p>
                  Latest inspected version: v{evidence.detail.version}. Application scope is
                  <strong> {evidence.impact.applicationScope}</strong>; historical references are
                  {evidence.impact.historicalReferencesPreserved ? " preserved" : " not preserved"}.
                </p>
                <ul>
                  {Object.entries(evidence.impact.referenceCounts).map(([kind, count]) => (
                    <li key={kind}>{kind}: {count}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p role="status">Create a tested version to calculate prospective impact.</p>
            )}
          </section>
          <section className="admin-card" aria-labelledby="status-guide-title">
            <h3 id="status-guide-title">Lifecycle status guide</h3>
            <div className="status-guide">
              {(["draft", "tested", "approved", "active", "superseded", "retired"] as const).map((state) => (
                <span key={state} className={`status-chip status-${state}`}>{state}</span>
              ))}
            </div>
            {latest && <p>Latest immutable configuration is v{latest.version} ({latest.state}).</p>}
          </section>
        </div>
      )}

      {section === "configuration" && (
        <div className="admin-section-stack">
          <ConfigurationEditor value={value} onChange={setValue} onSave={onSave} />
          <section className="admin-card" aria-labelledby="governance-title">
            <h3 id="governance-title">Test and govern</h3>
            <p>
              Saving remains editable. Testing freezes an immutable version; human
              approval and explicit impact confirmation are required before activation.
            </p>
            <p>Editable draft revision {draftRevision}; stale save and test requests are rejected by the server.</p>
            <label>
              Governance rationale
              <textarea
                aria-label="Governance rationale"
                value={rationale}
                onChange={(event) => setRationale(event.target.value)}
                placeholder="Explain the evidence and reason for this action"
              />
            </label>
            <button className="primary" disabled={!canGovern} onClick={() => onTest(rationale)}>
              Test draft and retain evidence
            </button>
          </section>

          <section className="admin-card" aria-labelledby="history-title">
            <h3 id="history-title">Immutable configuration history</h3>
            {orderedVersions.length === 0 ? (
              <p role="status">No governed versions yet.</p>
            ) : (
              <ol className="version-list">
                {orderedVersions.map((version) => (
                  <li key={version.id}>
                    <div className="section-action">
                      <div>
                        <h4>Configuration v{version.version}</h4>
                        <span className={`status-chip status-${version.state}`}>{version.state}</span>
                        {version.active && <span> current active version</span>}
                      </div>
                      <div className="button-row">
                        <button onClick={() => onSelectVersion(version.id)}>Inspect history and impact</button>
                        {version.state === "tested" && (
                          <button disabled={!canGovern} onClick={() => onApprove(version.id, rationale)}>
                            Record human approval
                          </button>
                        )}
                        {version.state === "approved" && (
                          <button onClick={() => onSelectVersion(version.id)}>Review activation impact</button>
                        )}
                        {version.state === "superseded" && (
                          <button disabled={!canGovern} onClick={() => onRetire(version.id, rationale)}>
                            Retire version
                          </button>
                        )}
                        {(version.state === "superseded" || version.state === "retired") && (
                          <button disabled={!canGovern} onClick={() => onRollback(version.id, rationale)}>
                            Prepare tested rollback
                          </button>
                        )}
                      </div>
                    </div>
                    <VersionSummary version={version} />
                    <details>
                      <summary>Lifecycle evidence</summary>
                      {version.testEvidence && (
                        <p>
                          Deterministic suite {version.testEvidence.suiteVersion}: {version.testEvidence.passed ? "passed" : "failed"}; result hash {version.testEvidence.resultHash}
                        </p>
                      )}
                      {version.approval && (
                        <p>
                          Human approval by {version.approval.approvedRole}, bound to test evidence {version.approval.testEvidenceId}.
                        </p>
                      )}
                      <ol>
                        {version.history.map((event) => (
                          <li key={event.eventHash}>
                            <strong>{event.state}</strong> by {event.actorRole} at {event.occurredAt}: {event.rationale}
                            <small> event hash {event.eventHash}</small>
                          </li>
                        ))}
                      </ol>
                    </details>
                  </li>
                ))}
              </ol>
            )}
          </section>

          <section className="admin-card" aria-label="Derived configuration evidence">
            <h3>Read-only version detail, comparison, and impact</h3>
            {evidence ? (
              <>
                <p>
                  Inspecting configuration v{evidence.detail.version}. These projections
                  are derived from immutable server records and are never authority.
                </p>
                <VersionSummary version={evidence.detail} />
                <details open>
                  <summary>Human-readable change from prior version</summary>
                  {evidence.diff.changes.length ? (
                    <ul>{evidence.diff.changes.map((change) => <li key={change.path}>{change.description}</li>)}</ul>
                  ) : (
                    <p>No material configuration changes.</p>
                  )}
                  <small>projection hash {evidence.diff.projectionHash}</small>
                </details>
                <details open>
                  <summary>Prospective activation impact</summary>
                  <p>
                    Scope: {evidence.impact.applicationScope}; historical references preserved: {evidence.impact.historicalReferencesPreserved ? "yes" : "no"}.
                  </p>
                  <ul>{Object.entries(evidence.impact.referenceCounts).map(([kind, count]) => <li key={kind}>{kind}: {count}</li>)}</ul>
                  <small>projection hash {evidence.impact.projectionHash}</small>
                </details>
                <details>
                  <summary>Historical runtime references</summary>
                  {evidence.references.references.length ? (
                    <ul>
                      {evidence.references.references.map((reference) => (
                        <li key={`${reference.resourceKind}:${reference.resourceId}`}>
                          {reference.resourceKind} {reference.resourceId} version {reference.resourceVersion} ({reference.state})
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No runtime record references this version yet.</p>
                  )}
                  <small>projection hash {evidence.references.projectionHash}</small>
                </details>
                {activationCandidate && (
                  <div className="activation-confirmation">
                    <h4>Explicit activation confirmation</h4>
                    <p>
                      Test evidence {activationCandidate.testEvidence?.id || "missing"} is {activationCandidate.testEvidence?.passed ? "successful" : "not successful"}; human approval is {activationCandidate.approval ? "recorded" : "missing"}.
                    </p>
                    <label className="confirmation-check">
                      <input
                        type="checkbox"
                        checked={activationConfirmed}
                        onChange={(event) => setActivationConfirmed(event.target.checked)}
                      />
                      I confirm this change applies to future intake only and preserves historical references.
                    </label>
                    <button
                      className="primary"
                      disabled={!canActivateCandidate}
                      onClick={() =>
                        activeVersion
                          ? onSupersede(activeVersion.id, activationCandidate.id, rationale)
                          : onActivate(activationCandidate.id, rationale)
                      }
                    >
                      {activeVersion ? "Confirm and supersede active version" : "Confirm and activate approved version"}
                    </button>
                  </div>
                )}
              </>
            ) : (
              <p role="status">Choose a governed version to inspect its history, comparison, references, and impact.</p>
            )}
          </section>
        </div>
      )}

      {section === "profiles" && (
        <>
          <section className="admin-card">
            <h3>Profile governance rationale</h3>
            <label>
              Governance rationale
              <textarea
                aria-label="Profile governance rationale"
                value={rationale}
                onChange={(event) => setRationale(event.target.value)}
                placeholder="Explain the fixture evidence, exception, and prospective change"
              />
            </label>
          </section>
          <DocumentProfileAdmin
            profiles={profiles}
            clusters={clusters}
            rationale={rationale}
            onCreate={onCreateProfile}
            onTest={onTestProfile}
            onApprove={onApproveProfile}
            onRetire={onRetireProfile}
            onStage={onStageProfile}
            onConfirmCluster={onConfirmCluster}
          />
        </>
      )}

      <p aria-live="polite" role={isErrorMessage(message) ? "alert" : "status"}>{message}</p>
    </section>
  );
}
