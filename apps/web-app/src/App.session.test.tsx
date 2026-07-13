// @vitest-environment jsdom

import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

(globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean })
  .IS_REACT_ACT_ENVIRONMENT = true;

const session = vi.hoisted(() => ({
  authorizedContracts: vi.fn(),
  currentSession: vi.fn(),
  loginSession: vi.fn(),
  logoutSession: vi.fn(),
}));

const configurationApi = vi.hoisted(() => ({
  activeConfiguration: vi.fn(),
  configurationDraft: vi.fn(),
  configurationEvidence: vi.fn(),
  configurationHistory: vi.fn(),
  configurationProfiles: vi.fn(),
  confirmDocumentCluster: vi.fn(),
  createProfileDraft: vi.fn(),
  documentClusters: vi.fn(),
  governConfiguration: vi.fn(),
  governProfile: vi.fn(),
  saveConfigurationDraft: vi.fn(),
}));

vi.mock("./features/session/api", () => session);
vi.mock("./features/configuration/api", () => configurationApi);

import { App } from "./App";

const priorConfiguration = {
  servicePeriod: { start: "2026-06-01", end: "2026-06-30" },
  categories: [{ code: "prior", label: "Prior contract category", limit: "100.00" }],
  requiredEvidence: ["vendor_invoice"],
  ledgerControlTotal: "100.00",
  rules: [],
  workflowLabels: {
    draft: "Draft",
    submitted: "Submitted",
    returned: "Returned",
    approved: "Approved",
  },
  package: {
    label: "Prior package",
    invoiceTitle: "Prior invoice",
    includeValidationSummary: true,
    includeManifest: true,
  },
};

const administrator = (suffix: string) => ({
  id: `admin-${suffix}`,
  displayName: `Synthetic Administrator ${suffix}`,
  email: `admin-${suffix}@example.test`,
  organizationId: `agency-${suffix}`,
  organizationName: `Synthetic Agency ${suffix}`,
  role: "configuration_administrator" as const,
});

const contract = (suffix: string) => ({
  contractId: `contract-${suffix}`,
  contractName: `Synthetic Contract ${suffix}`,
  agencyOrganizationId: `agency-${suffix}`,
  agencyOrganizationName: `Synthetic Agency ${suffix}`,
  ngoOrganizationId: `ngo-${suffix}`,
  ngoOrganizationName: `Synthetic NGO ${suffix}`,
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((complete) => { resolve = complete; });
  return { promise, resolve };
}

async function settle() {
  await act(async () => {
    await new Promise((resolve) => window.setTimeout(resolve, 0));
  });
}

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (check()) return;
    await settle();
  }
  throw new Error("Timed out waiting for the expected UI state");
}

function change(input: HTMLInputElement, value: string) {
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
  setter?.call(input, value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

afterEach(() => {
  vi.clearAllMocks();
  document.body.replaceChildren();
});

describe("authenticated session isolation", () => {
  it("clears every prior contract projection before a later administrator renders", async () => {
    const secondActive = deferred<{ configuration: null }>();
    session.currentSession.mockRejectedValue(new Error("No session"));
    session.loginSession
      .mockResolvedValueOnce({ user: administrator("one") })
      .mockResolvedValueOnce({ user: administrator("two") });
    session.authorizedContracts
      .mockResolvedValueOnce({ contracts: [contract("one")] })
      .mockResolvedValueOnce({ contracts: [contract("two")] });
    session.logoutSession.mockResolvedValue(undefined);
    configurationApi.activeConfiguration.mockImplementation((contractId: string) =>
      contractId === "contract-one"
        ? Promise.resolve({ configuration: { id: "config-one", version: 1, activatedAt: "2026-07-13T00:00:00Z" } })
        : secondActive.promise,
    );
    configurationApi.configurationDraft.mockResolvedValue({
      configuration: priorConfiguration,
      revision: 7,
      payloadHash: "a".repeat(64),
      updatedAt: "2026-07-13T00:00:00Z",
    });
    configurationApi.configurationHistory.mockResolvedValue({ versions: [] });
    configurationApi.configurationProfiles.mockResolvedValue({ profiles: [] });
    configurationApi.documentClusters.mockResolvedValue({ clusters: [] });

    const host = document.createElement("div");
    document.body.append(host);
    const root = createRoot(host);
    await act(async () => root.render(<App />));
    await settle();

    const signIn = async (email: string) => {
      const emailInput = host.querySelector<HTMLInputElement>('input[type="email"]');
      const passwordInput = host.querySelector<HTMLInputElement>('input[type="password"]');
      expect(emailInput).not.toBeNull();
      expect(passwordInput).not.toBeNull();
      await act(async () => {
        change(emailInput!, email);
        change(passwordInput!, "synthetic-password");
      });
      await act(async () => {
        host.querySelector<HTMLFormElement>("form")?.dispatchEvent(
          new Event("submit", { bubbles: true, cancelable: true }),
        );
      });
    };

    await signIn("admin-one@example.test");
    await waitFor(() => host.textContent?.includes("Configuration Administrator workspace") ?? false);
    await act(async () => {
      Array.from(host.querySelectorAll<HTMLButtonElement>("button"))
        .find((button) => button.textContent === "Configuration lifecycle")
        ?.click();
    });
    await waitFor(() => host.textContent?.includes("Prior contract category") ?? false);

    await act(async () => {
      host.querySelector<HTMLButtonElement>("header.identity button")?.click();
    });
    await waitFor(() => host.textContent?.includes("Sign in") ?? false);

    await signIn("admin-two@example.test");
    await waitFor(() => host.textContent?.includes("Synthetic Administrator two") ?? false);
    expect(host.textContent).toContain("Loading governed configuration");
    expect(host.textContent).not.toContain("Prior contract category");
    expect(host.textContent).not.toContain("Prior package");

    await act(async () => {
      secondActive.resolve({ configuration: null });
      await secondActive.promise;
    });
    await act(async () => root.unmount());
  });
});
