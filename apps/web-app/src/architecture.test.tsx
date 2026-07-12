import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiRequest } from "./api/client";
import { App } from "./App";
import { demoMode, demoPersonas } from "./demo/personas";
import appSource from "./App.tsx?raw";
import { AuditorWorkspace } from "./workspaces/AuditorWorkspace";

afterEach(() => vi.unstubAllGlobals());

describe("web module boundaries", () => {
  it("keeps transport and fixed contract selection out of the application shell", () => {
    expect(appSource).not.toContain("fetch(");
    expect(appSource).not.toContain("contract-synthetic-agency-ngo-2026");
    expect(appSource).not.toContain("Demo-Config-2026!");
    expect(appSource).toContain("authorizedContracts");
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
});
