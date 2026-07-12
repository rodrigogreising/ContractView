import { describe, expect, it } from "vitest";
import {
  ACTOR_ROLES, CONFIGURATION_LIFECYCLES, EVENT_TYPES, RELATION_TYPES,
  type IdentityDto,
} from "./contracts";

describe("generated shared contracts", () => {
  it("exposes closed lifecycle and authority vocabulary", () => {
    expect(ACTOR_ROLES).toEqual(["configuration_administrator", "ngo_preparer", "ngo_approver", "government_reviewer", "auditor"]);
    expect(CONFIGURATION_LIFECYCLES).toEqual(["draft", "tested", "approved", "active", "superseded", "retired"]);
    expect(RELATION_TYPES).toContain("approved_as");
    expect(EVENT_TYPES).toContain("validation_completed");
  });

  it("provides the identity DTO consumed by the app", () => {
    const identity: IdentityDto = {id:"user-1",displayName:"Synthetic User",email:"synthetic@example.test",organizationId:"org-1",organizationName:"Synthetic Org",role:"auditor"};
    expect(identity.organizationId).toBe("org-1");
    expect(identity.role).toBe("auditor");
  });
});
