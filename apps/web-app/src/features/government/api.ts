import { apiRequest } from "../../api/client";
import type { QueueItem, ReviewContext } from "../../domain/types";

export const governmentQueue = () => apiRequest<{ items: QueueItem[] }>("/api/government/queue");
export const inspectGovernmentQueue = (id: string) => apiRequest<{ review: ReviewContext }>(`/api/government/queue/${id}`);
export const decideGovernmentQueue = (queueId: string, decision: "returned" | "approved", reasonCode: string, note: string, lineKeys: string[]) => apiRequest<unknown>(`/api/government/queue/${queueId}/decision`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision, reasonCode, note, lineKeys }) });
