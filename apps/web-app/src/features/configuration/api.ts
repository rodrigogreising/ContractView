import { apiRequest, contractQuery } from "../../api/client";
import type { ActiveConfigurationDto, GovernedConfigurationVersionDto } from "../../generated/contracts";
import type { Configuration } from "../../domain/types";

export const activeConfiguration = (contractId: string) => apiRequest<{ configuration: ActiveConfigurationDto | null }>(`/api/configuration/active?${contractQuery(contractId)}`);
export const configurationDraft = (contractId: string) => apiRequest<{ configuration: Configuration }>(`/api/configuration/draft?${contractQuery(contractId)}`);
export const configurationHistory = (contractId: string) => apiRequest<{ versions: GovernedConfigurationVersionDto[] }>(`/api/configuration/lifecycle?${contractQuery(contractId)}`);
export const saveConfigurationDraft = (contractId: string, value: Configuration) => apiRequest<{ configuration: Configuration }>(`/api/configuration/draft?${contractQuery(contractId)}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) });
export const governConfiguration = (path: string, payload: Record<string, string>) => apiRequest<unknown>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
