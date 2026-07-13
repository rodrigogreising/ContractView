import type {
  ActiveConfigurationDto,
  GovernedConfigurationVersionDto,
} from "../generated/contracts";
import type { Configuration } from "../domain/types";
import { ConfigurationAdmin } from "../features/configuration/ConfigurationAdmin";
import type { ConfigurationEvidenceView } from "../features/configuration/api";
import type {
  DocumentClusterView,
  DocumentProfileView,
  ProfileDraftCommand,
  StagedProfileReference,
} from "../features/configuration/types";

export function ConfigurationWorkspace(props: {
  configuration: Configuration;
  draftRevision?: number;
  evidence?: ConfigurationEvidenceView | null;
  profiles?: DocumentProfileView[];
  clusters?: DocumentClusterView[];
  active: ActiveConfigurationDto | null;
  versions: GovernedConfigurationVersionDto[];
  message: string;
  onSave: (value: Configuration) => void;
  onTest: (rationale: string) => void;
  onApprove: (id: string, rationale: string) => void;
  onActivate: (id: string, rationale: string) => void;
  onSupersede: (activeId: string, successorId: string, rationale: string) => void;
  onRetire: (id: string, rationale: string) => void;
  onRollback: (id: string, rationale: string) => void;
  onSelectVersion?: (id: string) => void;
  onCreateProfile?: (command: ProfileDraftCommand) => void;
  onTestProfile?: (id: string, rationale: string) => void;
  onApproveProfile?: (id: string, rationale: string) => void;
  onRetireProfile?: (id: string, rationale: string) => void;
  onStageProfile?: (profile: StagedProfileReference) => void;
  onConfirmCluster?: (clusterId: string, profileKey: string, rationale: string) => void;
}) {
  return <ConfigurationAdmin {...props} />;
}
