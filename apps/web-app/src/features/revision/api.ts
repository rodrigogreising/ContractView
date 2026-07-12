import { apiRequest, contractQuery } from "../../api/client";
import type { RevisionFeedback } from "../../domain/types";

export const revisionFeedback = (contractId: string) => apiRequest<{ feedback: RevisionFeedback | null }>(`/api/revisions/feedback?${contractQuery(contractId)}`);
export const correctRevision = (invoiceId: string, expenseKey: string, description: string, reason: string) => apiRequest<unknown>(`/api/invoices/${invoiceId}/revision-correction`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ expenseKey, description, reason }) });
