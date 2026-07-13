import { apiRequest, contractQuery } from "../../api/client";
import type {
  ActiveConfigurationDto,
  ConfigurationActivationImpactDto,
  ConfigurationDiffDto,
  ConfigurationDraftDto,
  ConfigurationReferencesDto,
  GovernedConfigurationVersionDto,
  ProfileAssociationDto,
} from "../../generated/contracts";
import type { Configuration } from "../../domain/types";
import type {
  DocumentClusterView,
  DocumentProfileView,
  ProfileDraftCommand,
} from "./types";

export interface ConfigurationEvidenceView {
  detail: GovernedConfigurationVersionDto;
  diff: ConfigurationDiffDto;
  impact: ConfigurationActivationImpactDto;
  references: ConfigurationReferencesDto;
}

export type ConfigurationDraftResponse = Omit<ConfigurationDraftDto, "configuration"> & {
  configuration: Configuration;
};

export const activeConfiguration = (contractId: string) => apiRequest<{ configuration: ActiveConfigurationDto | null }>(`/api/configuration/active?${contractQuery(contractId)}`);
export const configurationDraft = (contractId: string) => apiRequest<ConfigurationDraftResponse>(`/api/configuration/draft?${contractQuery(contractId)}`);
export const configurationHistory = (contractId: string) => apiRequest<{ versions: GovernedConfigurationVersionDto[] }>(`/api/configuration/lifecycle?${contractQuery(contractId)}`);
export const configurationVersion = (versionId: string) => apiRequest<{ configurationVersion: GovernedConfigurationVersionDto }>(`/api/configuration/versions/${encodeURIComponent(versionId)}`);
export const compareConfigurationVersions = (baseVersionId: string, targetVersionId: string) => apiRequest<ConfigurationDiffDto>(`/api/configuration/compare?baseVersionId=${encodeURIComponent(baseVersionId)}&targetVersionId=${encodeURIComponent(targetVersionId)}`);
export const configurationActivationImpact = (versionId: string) => apiRequest<ConfigurationActivationImpactDto>(`/api/configuration/versions/${encodeURIComponent(versionId)}/activation-impact`);
export const configurationReferences = (versionId: string) => apiRequest<ConfigurationReferencesDto>(`/api/configuration/versions/${encodeURIComponent(versionId)}/references`);
export const saveConfigurationDraft = (contractId: string, expectedRevision: number, value: Configuration) => apiRequest<ConfigurationDraftResponse>(`/api/configuration/draft?${contractQuery(contractId)}&expectedRevision=${expectedRevision}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) });
export const governConfiguration = (path: string, payload: Record<string, string | number>) => apiRequest<unknown>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });

export const configurationProfiles = (contractId: string) =>
  apiRequest<{ profiles: DocumentProfileView[] }>(
    `/api/configuration/profiles?${contractQuery(contractId)}`,
  );

export const documentClusters = (contractId: string) =>
  apiRequest<{ clusters: DocumentClusterView[] }>(
    `/api/configuration/document-clusters?${contractQuery(contractId)}`,
  );

export const createProfileDraft = (
  contractId: string,
  command: ProfileDraftCommand,
) =>
  apiRequest<{ profile: DocumentProfileView }>(
    `/api/configuration/profiles/draft?${contractQuery(contractId)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(command),
    },
  );

export const governProfile = (profileId: string, action: "test" | "approve" | "retire", rationale: string) =>
  apiRequest<{ profile: DocumentProfileView }>(
    `/api/configuration/profiles/${encodeURIComponent(profileId)}/${action}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rationale }),
    },
  );

export const confirmDocumentCluster = (
  clusterId: string,
  profileKey: string,
  rationale: string,
) =>
  apiRequest<{ association: ProfileAssociationDto }>(
    `/api/configuration/document-clusters/${encodeURIComponent(clusterId)}/confirm`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profileKey, rationale }),
    },
  );

export async function configurationEvidence(
  versions: GovernedConfigurationVersionDto[],
  targetVersionId: string,
): Promise<ConfigurationEvidenceView> {
  const ordered = versions.slice().sort((left, right) => left.version - right.version);
  const targetIndex = ordered.findIndex((version) => version.id === targetVersionId);
  if (targetIndex < 0) throw new Error("Configuration version is not in the authorized history");
  const target = ordered[targetIndex];
  const base = ordered[Math.max(0, targetIndex - 1)];
  const [detail, diff, impact] = await Promise.all([
    configurationVersion(target.id),
    compareConfigurationVersions(base.id, target.id),
    configurationActivationImpact(target.id),
  ]);
  const references = await configurationReferences(
    impact.historicalReferenceVersionId || target.id,
  );
  return { detail: detail.configurationVersion, diff, impact, references };
}
