import { apiRequest, contractQuery } from "../../api/client";
import type { InvoiceDraft } from "../../domain/types";

export const latestDraft = (contractId: string) => apiRequest<{ invoice: InvoiceDraft | null }>(`/api/invoices/draft?${contractQuery(contractId)}`);
export const assembleDraft = (contractId: string) => apiRequest<{ invoice: InvoiceDraft }>(`/api/invoices/draft?${contractQuery(contractId)}`, { method: "POST" });
