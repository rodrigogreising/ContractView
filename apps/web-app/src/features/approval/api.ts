import { apiRequest } from "../../api/client";
import type { ApprovalPreview, Attestation, GeneratedPackage, Submission } from "../../domain/types";

export const approvalPreview = (invoiceId: string) => apiRequest<{ preview: ApprovalPreview; attestation: Attestation | null }>(`/api/invoices/${invoiceId}/approval-preview`);
export const attestInvoice = (invoiceId: string, text: string) => apiRequest<{ attestation: Attestation }>(`/api/invoices/${invoiceId}/attest`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
export const generateInvoicePackage = (invoiceId: string) => apiRequest<{ package: GeneratedPackage }>(`/api/invoices/${invoiceId}/package`, { method: "POST" });
export const submitInvoice = (invoiceId: string) => apiRequest<{ submission: Submission }>(`/api/invoices/${invoiceId}/submit`, { method: "POST" });
