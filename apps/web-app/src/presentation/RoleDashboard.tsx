import type {
  ActiveConfigurationDto,
  ContractContextDto,
  VersionReference,
} from "../generated/contracts";

export type ExactRuntimeContext = {
  label: string;
  configuration: VersionReference | null;
  documentProfiles: VersionReference[];
  note: string;
};

function referenceLabel(reference: VersionReference) {
  return `${reference.kind}:${reference.id}@${reference.version}`;
}

function ProfileReferences({ references }: { references: VersionReference[] }) {
  if (references.length === 0) {
    return <p>No document profile applies to this exact context.</p>;
  }
  return (
    <ul className="context-references">
      {references.map((reference) => (
        <li key={`${reference.kind}:${reference.id}:${reference.version}`}>
          <code>{referenceLabel(reference)}</code>
          {reference.sha256 && <small>SHA-256 {reference.sha256}</small>}
        </li>
      ))}
    </ul>
  );
}

export function RoleDashboard({
  title,
  nextAction,
  authority,
  unavailable,
  contract,
  activeConfiguration,
  exactContext = null,
  workTarget,
  activeConfigurationVisible = true,
}: {
  title: string;
  nextAction: string;
  authority: string;
  unavailable: string[];
  contract: ContractContextDto | null;
  activeConfiguration: ActiveConfigurationDto | null;
  exactContext?: ExactRuntimeContext | null;
  workTarget: string;
  activeConfigurationVisible?: boolean;
}) {
  return (
    <section className="panel role-dashboard" aria-label={title}>
      <p className="eyebrow">Role landing page</p>
      <h2>{title}</h2>
      <div className="next-action role-next-action">
        <h3>Next action</h3>
        <p>{nextAction}</p>
        <a href={`#${workTarget}`}>Open assigned work</a>
      </div>
      <div className="role-context-grid">
        <section aria-label="Assigned authority">
          <h3>Your authority</h3>
          <p>{authority}</p>
          <h4>Not available in this role</h4>
          <ul>{unavailable.map((item) => <li key={item}>{item}</li>)}</ul>
        </section>
        <section aria-label="Authorized contract context">
          <h3>Authorized contract</h3>
          {contract ? (
            <dl className="context-facts">
              <div><dt>Contract</dt><dd>{contract.contractName}</dd></div>
              <div><dt>Contract ID</dt><dd><code>{contract.contractId}</code></dd></div>
              <div><dt>Agency</dt><dd>{contract.agencyOrganizationName}</dd></div>
              <div><dt>NGO</dt><dd>{contract.ngoOrganizationName}</dd></div>
            </dl>
          ) : <p>No authorized contract is selected.</p>}
        </section>
      </div>
      <div className="role-context-grid">
        <section aria-label="Current configuration context">
          <h3>Current intake context</h3>
          {activeConfigurationVisible && activeConfiguration ? (
            <>
              <p><code>{`configuration:${activeConfiguration.id}@${activeConfiguration.version}`}</code></p>
              <ProfileReferences references={activeConfiguration.documentProfiles || []} />
              <small>Activated {activeConfiguration.activatedAt}. This context applies prospectively.</small>
            </>
          ) : (
            <p>
              {activeConfigurationVisible
                ? "No active configuration is available for this contract."
                : "Current draft or active configuration is intentionally not exposed here; submitted historical evidence is the auditor authority."}
            </p>
          )}
        </section>
        <section aria-label="Exact assigned work context">
          <h3>{exactContext?.label || "Exact assigned work context"}</h3>
          {exactContext?.configuration ? (
            <>
              <p><code>{referenceLabel(exactContext.configuration)}</code></p>
              {exactContext.configuration.sha256 && <small>SHA-256 {exactContext.configuration.sha256}</small>}
              <ProfileReferences references={exactContext.documentProfiles} />
              <p>{exactContext.note}</p>
            </>
          ) : <p>{exactContext?.note || "No assigned invoice or submitted package is available yet."}</p>}
        </section>
      </div>
    </section>
  );
}
