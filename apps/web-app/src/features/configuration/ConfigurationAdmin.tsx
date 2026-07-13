import { useEffect, useState } from "react";
import type { ActiveConfigurationDto as ActiveConfiguration, GovernedConfigurationVersionDto as GovernedConfigurationVersion } from "../../generated/contracts";
import type { Configuration } from "../../domain/types";
import { roleLabel } from "../../presentation/roleLabel";
import type { ConfigurationEvidenceView } from "./api";

export function ConfigurationAdmin({
  configuration,
  draftRevision = 0,
  evidence = null,
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
  draftRevision?: number;
  evidence?: ConfigurationEvidenceView | null;
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
          <p>Editable draft revision {draftRevision}; stale writes are rejected.</p>
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
                  {version.testEvidence && (
                    <p>
                      Deterministic suite {version.testEvidence.suiteVersion}:{" "}
                      {version.testEvidence.passed ? "passed" : "failed"}; result hash{" "}
                      {version.testEvidence.resultHash}
                    </p>
                  )}
                  {version.approval && (
                    <p>
                      Human approval {version.approval.id} by {version.approval.approvedRole};
                      bound to test evidence {version.approval.testEvidenceId}.
                    </p>
                  )}
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
      {evidence && (
        <section aria-label="Derived configuration evidence">
          <h3>Derived version evidence</h3>
          <p>
            Showing version {evidence.detail.version}. Diff, impact, and references are
            read-only projections from immutable records; projection hashes make replay
            comparison explicit.
          </p>
          <details open>
            <summary>Human-readable change from prior version</summary>
            {evidence.diff.changes.length ? (
              <ul>
                {evidence.diff.changes.map((change) => (
                  <li key={change.path}>{change.description}</li>
                ))}
              </ul>
            ) : (
              <p>No material configuration changes.</p>
            )}
            <small>projection hash {evidence.diff.projectionHash}</small>
          </details>
          <details>
            <summary>Prospective activation impact</summary>
            <p>
              Scope: {evidence.impact.applicationScope}; historical references preserved:{" "}
              {evidence.impact.historicalReferencesPreserved ? "yes" : "no"}.
            </p>
            {evidence.impact.historicalReferenceVersionId && (
              <p>
                Counts below remain bound to version{" "}
                {evidence.impact.historicalReferenceVersionId}.
              </p>
            )}
            <ul>
              {Object.entries(evidence.impact.referenceCounts).map(([kind, count]) => (
                <li key={kind}>{kind}: {count}</li>
              ))}
            </ul>
            <small>projection hash {evidence.impact.projectionHash}</small>
          </details>
          <details>
            <summary>Historical runtime references</summary>
            {evidence.references.references.length ? (
              <ul>
                {evidence.references.references.map((reference) => (
                  <li key={`${reference.resourceKind}:${reference.resourceId}`}>
                    {reference.resourceKind} {reference.resourceId} version{" "}
                    {reference.resourceVersion} ({reference.state})
                  </li>
                ))}
              </ul>
            ) : (
              <p>No runtime record references this version yet.</p>
            )}
            <small>projection hash {evidence.references.projectionHash}</small>
          </details>
        </section>
      )}
      <p aria-live="polite">{message}</p>
    </section>
  );
}
