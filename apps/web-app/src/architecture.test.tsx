import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiRequest } from "./api/client";
import { App } from "./App";
import { demoMode, demoPersonas } from "./demo/personas";
import appSource from "./App.tsx?raw";
import { AuditorWorkspace } from "./workspaces/AuditorWorkspace";
import type { AuditTimelineDto } from "./generated/contracts";

afterEach(() => vi.unstubAllGlobals());

describe("web module boundaries", () => {
  it("keeps transport and fixed contract selection out of the application shell", () => {
    expect(appSource).not.toContain("fetch(");
    expect(appSource).not.toContain("contract-synthetic-agency-ngo-2026");
    expect(appSource).not.toContain("Demo-Config-2026!");
    expect(appSource).toContain("authorizedContracts");
  });

  it("clears and epoch-guards every contract-scoped projection", () => {
    expect(appSource).toContain("currentContract.current === requested");
    for (const reset of [
      "setJobs([])", "setExtractions([])", "setConfiguration(null)",
      "setActiveConfiguration(null)", "setConfigurationLifecycle([])",
      "setDraft(null)", "setValidation(null)", "setFindings([])",
      "setRevisionFeedback(null)",
    ]) expect(appSource).toContain(reset);
  });

  it("isolates synthetic credentials behind the explicit demo/test boundary", () => {
    expect(demoMode).toBe(true);
    expect(demoPersonas).toHaveLength(5);
    expect(demoPersonas.every((persona) => persona[2].endsWith("@example.test"))).toBe(true);
  });

  it("normalizes API failures instead of letting feature modules parse responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: "Permission denied" }),
    }));
    await expect(apiRequest("/api/protected")).rejects.toEqual(
      new ApiError(403, "Permission denied"),
    );
  });

  it("renders an accessible authentication landmark and live status", () => {
    const html = renderToString(<App />);
    expect(html).toContain("<main>");
    expect(html).toContain("<h1>Sign in</h1>");
    expect(html).toContain("<label>Email");
    expect(html).toContain("<label>Password");
    expect(html).toContain('aria-live="polite"');
    expect(html).toContain('type="password"');
  });

  it("keeps the auditor workspace explicitly read-only", () => {
    const html = renderToString(<AuditorWorkspace />);
    expect(html).toContain("Read-only audit workspace");
    expect(html).toContain('aria-label="Auditor workspace"');
    expect(html).not.toContain("<button");
    expect(html).not.toContain("<form");
  });

  it("renders exact actor, version, source, validation, and package evidence", () => {
    const timeline = {
      contractId: "contract-synthetic",
      events: [{ id: 1, event: {
        eventId: "event-1", eventType: "approved", schemaVersion: 1,
        actor: { userId: "reviewer-1", organizationId: "agency-1", role: "government_reviewer" },
        organizationId: "ngo-1", contractId: "contract-synthetic",
        aggregate: { kind: "invoice", id: "invoice-v2", version: 2 },
        occurredAt: "2026-07-12T12:00:00Z", payload: {},
        versionReferences: [{ kind: "package", id: "package-v2", version: 2 }],
      }, eventHash: "a".repeat(64) }],
      lineage: [], relations: [], snapshots: [], packages: [],
      claimedAmountTrails: [1, 2].map((version) => ({
        expenseKey: "EXP-004", claimedAmount: "280.00", sourceArtifactId: "ledger-1",
        sourceLocation: "row=5", validationRunId: `validation-v${version}`,
        invoiceSnapshotId: `snapshot-v${version}`, invoiceVersionId: `invoice-v${version}`,
        invoiceVersion: version, packageId: `package-v${version}`,
        packageManifestHash: String(version).repeat(64), archiveSha256: String(version + 2).repeat(64),
      })),
    } as AuditTimelineDto;
    const html = renderToString(<AuditorWorkspace timeline={timeline} />);
    expect(html).toContain("Claimed amount to both packages");
    expect(html).toContain("reviewer-1 · agency-1 · government_reviewer");
    expect(html).toContain("validation-v1");
    expect(html).toContain("package-v2");
    expect(html).toContain("Approved by government");
    expect(html).not.toContain("<button");
    expect(html).not.toContain("<form");
  });
});
