import { apiRequest, contractQuery } from "../../api/client";
import type {
  ActiveConfigurationDto,
  ConfigurationActivationImpactDto,
  ConfigurationDiffDto,
  ConfigurationDraftDto,
  ConfigurationReferencesDto,
  GovernedConfigurationVersionDto,
} from "../../generated/contracts";
import type { Configuration } from "../../domain/types";

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
