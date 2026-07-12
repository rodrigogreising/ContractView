import type { ReactNode } from "react";
import type {
  ActiveConfigurationDto,
  ActorRole,
  IdentityDto,
} from "../generated/contracts";
import { roleLabel } from "./roleLabel";

const PERMISSION_SUMMARIES = {
  configuration_administrator:
    "Configure, test, approve, and activate assigned contracts",
  ngo_preparer:
    "Upload, correct, assemble, validate, and resolve assigned drafts",
  ngo_approver: "Attest, package, and submit assigned invoice versions",
  government_reviewer: "Review, return, and approve assigned submissions",
  auditor: "Read-only audit access to assigned submissions",
} satisfies Record<ActorRole, string>;

export const permissionSummary = (role: ActorRole) =>
  PERMISSION_SUMMARIES[role];

export function IdentityHeader({
  user,
  activeConfiguration,
  onLogout,
  children,
}: {
  user: IdentityDto;
  activeConfiguration: ActiveConfigurationDto | null;
  onLogout: () => void;
  children?: ReactNode;
}) {
  return (
    <header className="identity">
      <div className="identity-person">
        <strong>{user.displayName}</strong>
        <span>{user.organizationName}</span>
      </div>
      <span className="role-badge">{roleLabel(user.role)}</span>
      <span className="permission-summary" aria-label="Permissions">
        Permissions: {permissionSummary(user.role)}
      </span>
      {activeConfiguration && (
        <span className="config-badge">
          Active config v{activeConfiguration.version}
        </span>
      )}
      {children}
      <button onClick={onLogout}>Log out</button>
    </header>
  );
}
