import { apiRequest, contractQuery } from "../../api/client";
import type { Extraction, Job } from "../../domain/types";

export const listJobs = (contractId: string) => apiRequest<{ jobs: Job[] }>(`/api/ingestion/jobs?${contractQuery(contractId)}`);
export const listExtractions = (contractId: string) => apiRequest<{ extractions: Extraction[] }>(`/api/extractions/review?${contractQuery(contractId)}`);
export const uploadEvidence = (contractId: string, form: FormData) => {
  form.set("contractId", contractId);
  return apiRequest<unknown>("/api/ingestion/uploads", { method: "POST", body: form });
};
export const reviewExtraction = (fieldId: string, decision: "accept" | "correct", value: string) => apiRequest<unknown>(`/api/extractions/fields/${fieldId}/review`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision, value, reason: decision === "correct" ? "Corrected against the approved claim total" : "Accepted against source evidence" }) });
