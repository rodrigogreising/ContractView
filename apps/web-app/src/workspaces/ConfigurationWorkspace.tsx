import type { ActiveConfigurationDto, GovernedConfigurationVersionDto } from "../generated/contracts";
import type { Configuration } from "../domain/types";
import { ConfigurationAdmin } from "../features/configuration/ConfigurationAdmin";

export function ConfigurationWorkspace(props: { configuration: Configuration; active: ActiveConfigurationDto | null; versions: GovernedConfigurationVersionDto[]; message: string; onSave: (value: Configuration) => void; onTest: (rationale: string) => void; onApprove: (id: string, rationale: string) => void; onActivate: (id: string, rationale: string) => void; onSupersede: (activeId: string, successorId: string, rationale: string) => void; onRetire: (id: string, rationale: string) => void; onRollback: (id: string, rationale: string) => void }) {
  return <ConfigurationAdmin {...props} />;
}
