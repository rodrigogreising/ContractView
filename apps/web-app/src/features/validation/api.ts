import { apiRequest } from "../../api/client";
import type { ValidationRunDto } from "../../generated/contracts";
import type { Finding } from "../../domain/types";

export const findings = (invoiceId: string) => apiRequest<{ findings: Finding[] }>(`/api/invoices/${invoiceId}/findings`);
export const runValidation = (invoiceId: string) => apiRequest<{ validation: ValidationRunDto }>(`/api/invoices/${invoiceId}/validation`, { method: "POST" });
export const latestValidation = (invoiceId: string) => apiRequest<{ validation: ValidationRunDto | null }>(`/api/invoices/${invoiceId}/validation`);
export const resolveFinding = (id: string, action: string, reason: string, correctionValue?: string) => apiRequest<{ resolution: { findings: Finding[] } }>(`/api/findings/${id}/resolve`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action, reason, correctionValue }) });
