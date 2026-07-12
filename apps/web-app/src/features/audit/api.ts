import type { AuditTimelineDto } from "../../generated/contracts";
import { apiRequest } from "../../api/client";

export const auditTimeline = (contractId: string) =>
  apiRequest<AuditTimelineDto>(
    `/api/audit/timeline?contractId=${encodeURIComponent(contractId)}`,
  );
