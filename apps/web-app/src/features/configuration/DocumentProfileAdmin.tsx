import { useEffect, useMemo, useState } from "react";
import type { VersionReference } from "../../generated/contracts";
import type {
  DocumentClusterView,
  DocumentProfileView,
  ProfileDraftCommand,
  StagedProfileReference,
} from "./types";

const metric = (value: number) => `${Math.round(value * 100)}%`;

function profileReference(profile: DocumentProfileView): VersionReference {
  return {
    kind: "document_profile",
    id: profile.profile.id,
    version: profile.profile.version,
    sha256: profile.profile.contentHash,
  };
}

export function DocumentProfileAdmin({
  profiles,
  clusters,
  rationale,
  onCreate,
  onTest,
  onApprove,
  onRetire,
  onStage,
  onConfirmCluster,
}: {
  profiles: DocumentProfileView[];
  clusters: DocumentClusterView[];
  rationale: string;
  onCreate: (command: ProfileDraftCommand) => void;
  onTest: (profileId: string, rationale: string) => void;
  onApprove: (profileId: string, rationale: string) => void;
  onRetire: (profileId: string, rationale: string) => void;
  onStage: (profile: StagedProfileReference) => void;
  onConfirmCluster: (clusterId: string, profileKey: string, rationale: string) => void;
}) {
  const orderedProfiles = useMemo(
    () => profiles.slice().sort((left, right) => {
      const key = left.profile.profileKey.localeCompare(right.profile.profileKey);
      return key || right.profile.version - left.profile.version;
    }),
    [profiles],
  );
  const [sourceId, setSourceId] = useState(orderedProfiles[0]?.profile.id || "");
  const source = orderedProfiles.find((item) => item.profile.id === sourceId) || null;
  const [profileKey, setProfileKey] = useState(source?.profile.profileKey || "");
  const [languageTag, setLanguageTag] = useState(source?.profile.languageTag || "en");
  const [vendorAliases, setVendorAliases] = useState(
    source?.profile.vendorAliases.join("\n") || "",
  );
  const [clusterTargets, setClusterTargets] = useState<Record<string, string>>({});

  useEffect(() => {
    if (source || !orderedProfiles.length) return;
    const first = orderedProfiles[0];
    setSourceId(first.profile.id);
    setProfileKey(first.profile.profileKey);
    setLanguageTag(first.profile.languageTag);
    setVendorAliases(first.profile.vendorAliases.join("\n"));
  }, [orderedProfiles, source]);

  const selectSource = (nextId: string) => {
    const next = orderedProfiles.find((item) => item.profile.id === nextId);
    setSourceId(nextId);
    if (!next) return;
    setProfileKey(next.profile.profileKey);
    setLanguageTag(next.profile.languageTag);
    setVendorAliases(next.profile.vendorAliases.join("\n"));
  };

  const createDraft = () => {
    if (!source) return;
    const aliases = vendorAliases
      .split("\n")
      .map((value) => value.trim())
      .filter(Boolean);
    const sameProfileKey = profileKey.trim() === source.profile.profileKey;
    onCreate({
      definition: {
        profileKey: profileKey.trim(),
        artifactClass: source.profile.artifactClass,
        languageTag: languageTag.trim(),
        vendorAliases: aliases,
        requiredFields: source.profile.requiredFields,
        ledgerMatchRule: source.profile.ledgerMatchRule,
        fingerprintSpecification: source.profile.fingerprintSpecification,
        ...(sameProfileKey ? { predecessorVersionId: source.profile.id } : {}),
      },
      fixtures: source.fixtureSet.cases,
      rationale,
    });
  };

  return (
    <div className="admin-section-stack">
      <section className="admin-card" aria-labelledby="profile-setup-title">
        <div className="section-action">
          <div>
            <h3 id="profile-setup-title">Profile setup</h3>
            <p>
              Start from a tested synthetic fixture contract. The editor exposes
              governed fields; it never asks for raw JSON.
            </p>
          </div>
          <span className="status-chip status-draft">creates draft only</span>
        </div>
        {orderedProfiles.length === 0 ? (
          <p role="status">No profile templates are available for this contract.</p>
        ) : (
          <div className="config-grid">
            <label>
              Profile template
              <select
                aria-label="Profile template"
                value={sourceId}
                onChange={(event) => selectSource(event.target.value)}
              >
                {orderedProfiles.map((item) => (
                  <option key={item.profile.id} value={item.profile.id}>
                    {item.profile.profileKey} v{item.profile.version} · {item.state}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Profile key
              <input
                aria-label="Profile key"
                value={profileKey}
                onChange={(event) => setProfileKey(event.target.value)}
              />
            </label>
            <label>
              Source language
              <input
                aria-label="Source language"
                value={languageTag}
                onChange={(event) => setLanguageTag(event.target.value)}
              />
            </label>
            <label>
              Recognized vendor aliases
              <textarea
                aria-label="Recognized vendor aliases"
                value={vendorAliases}
                onChange={(event) => setVendorAliases(event.target.value)}
              />
            </label>
          </div>
        )}
        <button
          className="primary"
          disabled={!source || !profileKey.trim() || !languageTag.trim() || !vendorAliases.trim() || !rationale.trim()}
          onClick={createDraft}
        >
          Create immutable profile draft
        </button>
      </section>

      <section className="admin-card" aria-labelledby="profile-history-title">
        <h3 id="profile-history-title">Profile history and evaluation</h3>
        <p>
          Fixture evidence, human approval, active assignment, and predecessor
          history remain attached to each immutable version.
        </p>
        {orderedProfiles.length === 0 ? (
          <p role="status">No document profile versions yet.</p>
        ) : (
          <div className="profile-grid">
            {orderedProfiles.map((item) => {
              const evidence = item.evaluationEvidence;
              const canStage = item.state === "approved" || item.state === "active";
              return (
                <article className="profile-card" key={item.profile.id}>
                  <div className="section-action">
                    <div>
                      <h4>{item.profile.profileKey} v{item.profile.version}</h4>
                      <p>{item.profile.languageTag} · {item.profile.artifactClass}</p>
                    </div>
                    <span className={`status-chip status-${item.state}`}>{item.state}</span>
                  </div>
                  <dl className="admin-facts">
                    <div><dt>Fixture set</dt><dd>{item.fixtureSet.cases.length} cases</dd></div>
                    <div><dt>Active bundle</dt><dd>{item.activeConfigurationVersionId || "not active"}</dd></div>
                    <div><dt>Content hash</dt><dd><code>{item.profile.contentHash}</code></dd></div>
                  </dl>
                  {evidence ? (
                    <div aria-label={`Evaluation for ${item.profile.profileKey} version ${item.profile.version}`}>
                      <p className={evidence.passed ? "evidence-pass" : "evidence-fail"}>
                        Evaluation {evidence.passed ? "passed" : "failed"} · result {evidence.resultHash}
                      </p>
                      <ul className="metric-list">
                        <li>Field exactness {metric(evidence.supportedFieldExactness)}</li>
                        <li>Source locations {metric(evidence.sourceLocationExactness)}</li>
                        <li>Safe changed/unknown routing {metric(evidence.unknownSafeRoutingRate)}</li>
                      </ul>
                      <details>
                        <summary>Fixture results</summary>
                        <ul>
                          {item.fixtureSet.cases.map((fixture) => {
                            const result = evidence.results.find((entry) => entry.fixtureId === fixture.id);
                            return (
                              <li key={fixture.id}>
                                {fixture.filename} · {fixture.caseKind} · {result?.passed ? "passed" : "failed"}
                              </li>
                            );
                          })}
                        </ul>
                      </details>
                    </div>
                  ) : (
                    <p>No immutable evaluation has been recorded.</p>
                  )}
                  {item.approval && (
                    <p>
                      Approved by {item.approval.approvedRole} and bound to evaluation {item.approval.evaluationId}.
                    </p>
                  )}
                  <div className="button-row">
                    {item.state === "draft" && (
                      <button disabled={!rationale.trim()} onClick={() => onTest(item.profile.id, rationale)}>
                        Test profile fixtures
                      </button>
                    )}
                    {item.state === "tested" && (
                      <button disabled={!rationale.trim()} onClick={() => onApprove(item.profile.id, rationale)}>
                        Approve tested profile
                      </button>
                    )}
                    {canStage && (
                      <button
                        onClick={() => onStage({ profileKey: item.profile.profileKey, reference: profileReference(item) })}
                      >
                        Use exact profile in configuration draft
                      </button>
                    )}
                    {(item.state === "approved" || item.state === "superseded") && !item.activeConfigurationVersionId && (
                      <button disabled={!rationale.trim()} onClick={() => onRetire(item.profile.id, rationale)}>
                        Retire profile version
                      </button>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <section className="admin-card" aria-labelledby="cluster-queue-title">
        <div className="section-action">
          <div>
            <h3 id="cluster-queue-title">Document exception queue</h3>
            <p>
              Changed and unknown layouts remain noncanonical. Confirmation creates
              a draft association only; profile testing, approval, and activation still apply.
            </p>
          </div>
          <span className="status-chip">{clusters.length} exceptions</span>
        </div>
        {clusters.length === 0 ? (
          <p role="status">No changed or unknown document layouts await setup.</p>
        ) : (
          <div className="cluster-list">
            {clusters.map((cluster) => (
              <article key={cluster.id} className="cluster-card">
                <div className="section-action">
                  <div>
                    <h4>{cluster.sourceArtifact.filename}</h4>
                    <p>{cluster.languageTag} · {cluster.memberCount} matching artifact(s)</p>
                  </div>
                  <span className={`status-chip status-${cluster.status}`}>
                    {cluster.status === "confirmed_as_draft" ? "confirmed draft" : "suggestion"}
                  </span>
                </div>
                <p><code>{cluster.fingerprint.sha256}</code></p>
                {cluster.association ? (
                  <p>
                    Draft association to <strong>{cluster.association.profileKey}</strong> confirmed by {cluster.association.confirmedRole}. It is not active configuration.
                  </p>
                ) : (
                  <div className="cluster-confirmation">
                    <label>
                      Draft profile key
                      <input
                        aria-label={`Draft profile key for ${cluster.sourceArtifact.filename}`}
                        value={clusterTargets[cluster.id] || ""}
                        onChange={(event) => setClusterTargets({ ...clusterTargets, [cluster.id]: event.target.value })}
                      />
                    </label>
                    <button
                      disabled={!rationale.trim() || !(clusterTargets[cluster.id] || "").trim()}
                      onClick={() => onConfirmCluster(cluster.id, clusterTargets[cluster.id].trim(), rationale)}
                    >
                      Confirm suggestion as draft association
                    </button>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
