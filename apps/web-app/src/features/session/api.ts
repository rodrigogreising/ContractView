import type { ContractContextDto, IdentityDto } from "../../generated/contracts";
import { apiRequest } from "../../api/client";

export const currentSession = () =>
  apiRequest<{ user: IdentityDto }>("/api/auth/me");
export const loginSession = (email: string, password: string) =>
  apiRequest<{ user: IdentityDto }>("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
export const logoutSession = () =>
  apiRequest<void>("/api/auth/logout", { method: "POST" });
export const authorizedContracts = () =>
  apiRequest<{ contracts: ContractContextDto[] }>("/api/auth/contracts");
