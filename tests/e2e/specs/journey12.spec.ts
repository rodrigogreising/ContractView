import { expect, test, type Page, type TestInfo } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = path.resolve(here, "../../../packages/test-fixtures/files");

const personas = {
  administrator: ["configuration.admin@example.test", "Demo-Config-2026!", "Synthetic Configuration Administrator", "Synthetic Platform Operations", "Configuration Administrator", "Configure, test, approve, and activate assigned contracts"],
  preparer: ["ngo.preparer@example.test", "Demo-Prepare-2026!", "Synthetic NGO Preparer", "Synthetic Community Nonprofit", "NGO Preparer", "Upload, correct, assemble, validate, and resolve assigned drafts"],
  approver: ["ngo.approver@example.test", "Demo-Approve-2026!", "Synthetic NGO Approver", "Synthetic Community Nonprofit", "NGO Approver", "Attest, package, and submit assigned invoice versions"],
  government: ["government.reviewer@example.test", "Demo-Review-2026!", "Synthetic Government Reviewer", "Synthetic Public Agency", "Government Reviewer", "Review, return, and approve assigned submissions"],
  auditor: ["auditor@example.test", "Demo-Audit-2026!", "Synthetic Auditor", "Synthetic Oversight Unit", "Auditor", "Read-only audit access to assigned submissions"],
} as const;

async function login(page: Page, persona: keyof typeof personas, testInfo: TestInfo) {
  const [email, password, user, organization, role, permissions] = personas[persona];
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.locator("header.identity")).toContainText(user);
  await expect(page.locator("header.identity")).toContainText(organization);
  await expect(page.locator("header.identity")).toContainText(role);
  await expect(page.getByLabel("Permissions")).toHaveText(`Permissions: ${permissions}`);
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
  if (persona !== "administrator") {
    await expect(page.getByRole("heading", { name: `${role} dashboard` })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Next action" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Not available in this role" })).toBeVisible();
  }
  await page.screenshot({ path: testInfo.outputPath(`${persona}-workspace.png`), fullPage: true });
}

async function logout(page: Page) {
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
}

async function resolveOpenFindings(page: Page) {
  const blocker = page.locator(".finding-card").filter({ hasText: "SERVICE_PERIOD" });
  if (await blocker.getByRole("button", { name: "Correct and revalidate" }).isVisible().catch(() => false)) {
    await blocker.getByLabel("Resolution reason").fill("Corrected against the synthetic service period");
    await blocker.getByLabel("Corrected service date").fill("2026-06-28");
    await blocker.getByRole("button", { name: "Correct and revalidate" }).click();
    await expect(page.getByText("Finding resolved and deterministic validation rerun.")).toBeVisible();
  }
  const warning = page.locator(".finding-card").filter({ hasText: "POSSIBLE_DUPLICATE" });
  if (await warning.getByRole("button", { name: "Dismiss and revalidate" }).isVisible().catch(() => false)) {
    await warning.getByLabel("Resolution reason").fill("Distinct supported synthetic expenses");
    await warning.getByRole("button", { name: "Dismiss and revalidate" }).click();
    await expect(page.getByText("Finding resolved and deterministic validation rerun.")).toBeVisible();
  }
}

test("Journey 12: role dashboards and configuration-to-audit certification", async ({ page }, testInfo) => {
  await page.goto("/");

  await test.step("Configuration Administrator governs and activates configuration", async () => {
    await login(page, "administrator", testInfo);
    expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(0);
    expect(await page.evaluate(async () => (await fetch("/api/invoices/draft?contractId=contract-synthetic-agency-ngo-2026", { method: "POST" })).status)).toBe(403);
    await page.getByRole("button", { name: "Configuration lifecycle" }).click();
    await page.getByRole("button", { name: "Save validated draft" }).click();
    await expect(page.getByText("Configuration draft saved and validated.")).toBeVisible();
    await page.getByLabel("Governance rationale").fill("Journey 12 deterministic configuration evidence");
    await page.getByRole("button", { name: "Test draft and retain evidence" }).click();
    await expect(page.getByRole("button", { name: "Record human approval" })).toBeVisible();
    await page.getByRole("button", { name: "Record human approval" }).click();
    await expect(page.getByText("Explicit activation confirmation")).toBeVisible();
    await page.getByLabel("I confirm this change applies to future intake only and preserves historical references.").check();
    await page.getByRole("button", { name: "Confirm and activate approved version" }).click();
    await expect(page.locator("header.identity")).toContainText("Active config v1");
    await page.getByRole("button", { name: "Profiles and exceptions" }).click();
    await expect(page.getByRole("heading", { name: "Profile history and evaluation" })).toBeVisible();
    await expect(page.getByText("Safe changed/unknown routing 100%").first()).toBeVisible();
    await expect(page.getByText("No changed or unknown document layouts await setup.")).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath("configuration-activated.png"), fullPage: true });
    await logout(page);
  });

  await test.step("NGO Preparer uploads, reviews, assembles, validates, and resolves", async () => {
    await login(page, "preparer", testInfo);
    for (const filename of [
      "ledger-june-2026.csv",
      "payroll-june-2026.xlsx",
      "vendor-invoice-exp-002.pdf",
      "vendor-invoice-exp-003.pdf",
      "vendor-invoice-exp-004.png",
      "vendor-invoice-exp-005.pdf",
      "synthetic-vendor-invoice-changed-layout.pdf",
      "synthetic-unknown-supporting-document.pdf",
      "synthetic-vendor-invoice-es-001.pdf",
    ]) {
      await page.getByLabel("Evidence file").setInputFiles(path.join(fixtures, filename));
      await page.getByRole("button", { name: "Upload and process" }).click();
      await expect(page.getByText("Upload queued for real background processing.")).toBeVisible();
    }
    const extraction = page.locator("article.extraction").filter({ hasText: "vendor-invoice-exp-003.pdf" });
    await expect(extraction).toBeVisible({ timeout: 120_000 });
    const amount = extraction.locator(".field-review").filter({ hasText: "Amount" });
    await amount.getByRole("textbox").fill("1280.00");
    await Promise.all([
      page.waitForResponse((response) => response.url().includes("/extractions/fields/") && response.status() === 200),
      amount.getByRole("button", { name: "Correct" }).click(),
    ]);
    for (const field of ["Vendor", "Date", "Source Reference"]) {
      const row = extraction.getByRole("textbox", { name: field }).locator(
        "xpath=ancestor::div[contains(@class, 'field-review')]",
      );
      await Promise.all([
        page.waitForResponse((response) => response.url().includes("/extractions/fields/") && response.status() === 200),
        row.getByRole("button", { name: "Accept" }).click(),
      ]);
    }
    const spanish = page.locator("article.extraction").filter({ hasText: "synthetic-vendor-invoice-es-001.pdf" });
    await expect(spanish).toContainText("Exact profile vendor_invoice_es v1", { timeout: 120_000 });
    await expect(spanish).toContainText("configuration");
    const changed = page.locator("article.extraction").filter({ hasText: "synthetic-vendor-invoice-changed-layout.pdf" });
    const unknown = page.locator("article.extraction").filter({ hasText: "synthetic-unknown-supporting-document.pdf" });
    await expect(changed).toContainText("No profile assigned", { timeout: 120_000 });
    await expect(changed).toContainText("no canonical expense created");
    await expect(unknown).toContainText("No profile assigned", { timeout: 120_000 });
    await expect(unknown).toContainText("no canonical expense created");
    await page.getByRole("button", { name: "Assemble draft" }).click();
    await expect(page.getByText("Invoice v1", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Run deterministic validation" }).click();
    await expect(page.getByText("Resolve findings")).toBeVisible();
    await resolveOpenFindings(page);
    await page.screenshot({ path: testInfo.outputPath("v1-validated.png"), fullPage: true });
    await logout(page);
  });

  let v1Hash = "";
  await test.step("NGO Approver attests, packages, and submits immutable v1", async () => {
    await login(page, "approver", testInfo);
    await expect(page.getByLabel("Exact assigned work context")).toContainText("Invoice v1 approval context");
    await expect(page.getByText("No open blockers")).toBeVisible();
    await page.getByLabel("I confirm this exact invoice version and evidence set.").check();
    await page.getByRole("button", { name: "Attest exact version" }).click();
    await expect(page.getByText("Current attestation")).toBeVisible();
    await page.getByRole("button", { name: "Generate immutable package" }).click();
    const packageReady = page.locator(".package-ready");
    await expect(packageReady).toBeVisible();
    v1Hash = (await packageReady.locator("code").textContent()) || "";
    expect(v1Hash).toMatch(/^[a-f0-9]{64}$/);
    await page.getByRole("button", { name: "Submit to government review" }).click();
    await expect(packageReady).toContainText("Submitted to government queue");
    await page.screenshot({ path: testInfo.outputPath("v1-submitted.png"), fullPage: true });
    await logout(page);
  });

  await test.step("Government Reviewer returns exact v1", async () => {
    await login(page, "government", testInfo);
    const v1 = page.locator("article.queue-item").filter({ hasText: "Invoice v1" });
    await v1.getByRole("button", { name: "Inspect exact package" }).click();
    await expect(page.getByLabel("Exact assigned work context")).toContainText("Invoice v1 review context");
    await page.getByLabel("Decision note").fill("Correct the EXP-004 service evidence and resubmit");
    await page.getByLabel("Affected expense").fill("EXP-004");
    await page.getByRole("button", { name: "Return version 1 with feedback" }).click();
    await expect(v1).toContainText("returned");
    await page.screenshot({ path: testInfo.outputPath("v1-returned.png"), fullPage: true });
    await logout(page);
  });

  await test.step("NGO Preparer corrects returned v2 and revalidates", async () => {
    await login(page, "preparer", testInfo);
    await expect(page.getByRole("heading", { name: "Government feedback on version 1" })).toBeVisible();
    const correction = page.getByLabel("Corrected description for EXP-004");
    await correction.fill("Equipment rental supported by corrected June service evidence");
    await page.getByRole("button", { name: "Apply correction to version 2" }).click();
    await expect(page.getByText("Government feedback correction recorded. Run validation.")).toBeVisible();
    await page.getByRole("button", { name: "Run deterministic validation" }).click();
    await expect(page.getByText("Deterministic validation completed.")).toBeVisible();
    await resolveOpenFindings(page);
    await page.screenshot({ path: testInfo.outputPath("v2-corrected.png"), fullPage: true });
    await logout(page);
  });

  let v2Hash = "";
  await test.step("NGO Approver separately attests and resubmits v2", async () => {
    await login(page, "approver", testInfo);
    await expect(page.getByText("Invoice v2", { exact: true })).toBeVisible();
    await page.getByLabel("I confirm this exact invoice version and evidence set.").check();
    await page.getByRole("button", { name: "Attest exact version" }).click();
    await expect(page.getByText("Current attestation")).toBeVisible();
    await page.getByRole("button", { name: "Generate immutable package" }).click();
    const packageReady = page.locator(".package-ready");
    await expect(packageReady).toBeVisible();
    v2Hash = (await packageReady.locator("code").textContent()) || "";
    expect(v2Hash).toMatch(/^[a-f0-9]{64}$/);
    expect(v2Hash).not.toBe(v1Hash);
    await page.getByRole("button", { name: "Submit to government review" }).click();
    await expect(packageReady).toContainText("Submitted to government queue");
    await page.screenshot({ path: testInfo.outputPath("v2-resubmitted.png"), fullPage: true });
    await logout(page);
  });

  await test.step("Government Reviewer approves corrected v2", async () => {
    await login(page, "government", testInfo);
    const v2 = page.locator("article.queue-item").filter({ hasText: "Invoice v2" });
    await v2.getByRole("button", { name: "Inspect exact package" }).click();
    await page.getByLabel("Decision note").fill("Corrected evidence reviewed and approved");
    await page.getByRole("button", { name: "Approve corrected version 2" }).click();
    await expect(v2).toContainText("approved");
    await page.screenshot({ path: testInfo.outputPath("v2-approved.png"), fullPage: true });
    await logout(page);
  });

  await test.step("Configuration Administrator governs a safe exception and activates a prospective successor", async () => {
    await login(page, "administrator", testInfo);
    await page.getByRole("button", { name: "Profiles and exceptions" }).click();
    await page.getByLabel("Profile governance rationale").fill("Create and evaluate the exact synthetic successor profile");
    await page.getByRole("button", { name: "Create immutable profile draft" }).click();
    await expect(page.getByText("Immutable profile draft created from governed fixture inputs.")).toBeVisible();
    const successorProfile = page.locator("article.profile-card").filter({ hasText: "vendor_invoice_en v2" });
    await expect(successorProfile).toBeVisible();
    await successorProfile.getByRole("button", { name: "Test profile fixtures" }).click();
    await expect(page.getByText("Immutable profile fixture evaluation recorded.")).toBeVisible();
    await successorProfile.getByRole("button", { name: "Approve tested profile" }).click();
    await expect(page.getByText("Human profile approval recorded.")).toBeVisible();
    await successorProfile.getByRole("button", { name: "Use exact profile in configuration draft" }).click();
    await expect(page.getByText("Exact vendor_invoice_en profile reference staged in the editable draft; save and test before activation.")).toBeVisible();
    await page.getByRole("button", { name: "Configuration lifecycle" }).click();
    await page.getByRole("button", { name: "Save validated draft" }).click();
    await expect(page.getByText("Configuration draft saved and validated.")).toBeVisible();
    await page.getByRole("button", { name: "Profiles and exceptions" }).click();
    const exception = page.locator("article.cluster-card").filter({ hasText: "synthetic-unknown-supporting-document.pdf" });
    await expect(exception).toBeVisible({ timeout: 120_000 });
    await page.getByLabel("Profile governance rationale").fill("Retain the unknown synthetic layout for governed profile setup");
    await exception.getByLabel("Draft profile key for synthetic-unknown-supporting-document.pdf").fill("vendor_invoice_candidate");
    await exception.getByRole("button", { name: "Confirm suggestion as draft association" }).click();
    await expect(page.getByText("Cluster suggestion confirmed as a draft association only; no profile was assigned or activated.")).toBeVisible();
    await expect(exception).toContainText("confirmed draft");
    await expect(exception).toContainText("It is not active configuration");
    await page.getByRole("button", { name: "Configuration lifecycle" }).click();
    await page.getByLabel("Governance rationale").fill("Activate the tested successor prospectively while preserving historical invoice and package evidence");
    await page.getByRole("button", { name: "Test draft and retain evidence" }).click();
    await expect(page.getByRole("heading", { name: "Configuration v2" })).toBeVisible();
    const successorConfiguration = page.getByRole("listitem").filter({ has: page.getByRole("heading", { name: "Configuration v2" }) });
    await successorConfiguration.getByRole("button", { name: "Record human approval" }).click();
    await successorConfiguration.getByRole("button", { name: "Review activation impact" }).click();
    await expect(page.getByText("Explicit activation confirmation")).toBeVisible();
    await page.getByLabel("I confirm this change applies to future intake only and preserves historical references.").check();
    await page.getByRole("button", { name: "Confirm and supersede active version" }).click();
    await expect(page.locator("header.identity")).toContainText("Active config v2");
    await page.screenshot({ path: testInfo.outputPath("configuration-exception-draft.png"), fullPage: true });
    await logout(page);
  });

  await test.step("NGO Preparer sees the prospective successor without historical reinterpretation", async () => {
    await login(page, "preparer", testInfo);
    const current = page.getByLabel("Current configuration context");
    const historical = page.getByLabel("Exact assigned work context");
    await expect(current).toContainText("@2");
    await expect(current).toContainText(/document_profile:profile-vendor_invoice_en-v2-[a-f0-9]+@2/);
    await expect(historical).toContainText("No assigned invoice or submitted package is available yet.");
    await logout(page);
  });

  await test.step("Auditor reconstructs both original packages after successor activation", async () => {
    await login(page, "auditor", testInfo);
    await expect(page.getByRole("heading", { name: "Source-to-approval timeline" })).toBeVisible({ timeout: 60_000 });
    await expect(page.getByText("Approved by government")).toBeVisible();
    await expect(page.getByText("2", { exact: true })).toBeVisible();
    const v1Package = page.locator(".audit-card").filter({ hasText: "Invoice v1 package" });
    const v2Package = page.locator(".audit-card").filter({ hasText: "Invoice v2 package" });
    await expect(v1Package).toContainText("@1");
    await expect(v2Package).toContainText("@1");
    await expect(v1Package).toContainText("profile-vendor-invoice-en-v1@1");
    await expect(v2Package).toContainText("profile-vendor-invoice-en-v1@1");
    await expect(page.getByText("EXP-004 · $950.00")).toHaveCount(2);
    const v1Trail = page.locator(".audit-card").filter({ hasText: "EXP-004 · $950.00" }).filter({ hasText: "Invoice v1" });
    const v2Trail = page.locator(".audit-card").filter({ hasText: "EXP-004 · $950.00" }).filter({ hasText: "Invoice v2" });
    await expect(v1Trail).toContainText(v1Hash);
    await expect(v2Trail).toContainText(v2Hash);
    await expect(page.getByLabel("Current configuration context")).toContainText("intentionally not exposed");
    await expect(page.getByLabel("Auditor workspace").locator("button")).toHaveCount(0);
    await expect(page.getByLabel("Auditor workspace").locator("form")).toHaveCount(0);
    expect(await page.evaluate(async () => (await fetch("/api/invoices/draft?contractId=contract-synthetic-agency-ngo-2026", { method: "POST" })).status)).toBe(403);
    await page.screenshot({ path: testInfo.outputPath("audit-reconstruction-after-successor.png"), fullPage: true });
    await logout(page);
  });
});
