import type { ActiveConfigurationDto, AuditTimelineDto, ContractContextDto } from "../generated/contracts";
import { AuditTimeline } from "../features/audit/AuditTimeline";
import { RoleDashboard } from "../presentation/RoleDashboard";

export function AuditorWorkspace({ contract = null, activeConfiguration = null, timeline = null }: { contract?: ContractContextDto | null; activeConfiguration?: ActiveConfigurationDto | null; timeline?: AuditTimelineDto | null }) {
  const latest = timeline?.packages.at(-1);
  return <>
  <RoleDashboard title="Auditor dashboard" nextAction={timeline ? "Reconstruct the source-to-approval trail and compare immutable package evidence." : "Wait for submitted evidence to load from the canonical audit projection."} authority="You have read-only access to submitted evidence for explicitly assigned contracts. The workspace exposes no mutation command." unavailable={["You cannot upload, edit, validate, attest, submit, return, or approve invoices.", "You cannot read or mutate configuration drafts or activate document profiles.", "You cannot reinterpret historical packages against the current active configuration."]} contract={contract} activeConfiguration={activeConfiguration} activeConfigurationVisible={false} exactContext={latest ? { label: `Latest submitted invoice v${latest.invoiceVersion} context`, configuration: latest.configurationVersion || null, documentProfiles: latest.documentProfiles || [], note: "Every package below retains its own exact configuration and profile evidence." } : null} workTarget="auditor-work" />
  <section className="panel" aria-label="Auditor workspace" id="auditor-work">
    <h2>Read-only audit workspace</h2>
    <p>Submitted evidence is reconstructed from canonical server assignments. This workspace contains no mutation command.</p>
    <AuditTimeline timeline={timeline} />
  </section>
  </>;
}
