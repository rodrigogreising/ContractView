import type { AuditTimelineDto } from "../generated/contracts";
import { AuditTimeline } from "../features/audit/AuditTimeline";

export function AuditorWorkspace({ timeline = null }: { timeline?: AuditTimelineDto | null }) {
  return <section className="panel" aria-label="Auditor workspace">
    <h2>Read-only audit workspace</h2>
    <p>Submitted evidence is reconstructed from canonical server assignments. This workspace contains no mutation command.</p>
    <AuditTimeline timeline={timeline} />
  </section>;
}
