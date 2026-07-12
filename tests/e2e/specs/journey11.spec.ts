import { expect, test, type Page, type TestInfo } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = path.resolve(here, "../../../packages/test-fixtures/files");

const personas = {
  administrator: ["configuration.admin@example.test", "Demo-Config-2026!", "Synthetic Configuration Administrator", "Synthetic Platform Operations", "Configuration Administrator"],
  preparer: ["ngo.preparer@example.test", "Demo-Prepare-2026!", "Synthetic NGO Preparer", "Synthetic Community Nonprofit", "NGO Preparer"],
  approver: ["ngo.approver@example.test", "Demo-Approve-2026!", "Synthetic NGO Approver", "Synthetic Community Nonprofit", "NGO Approver"],
  government: ["government.reviewer@example.test", "Demo-Review-2026!", "Synthetic Government Reviewer", "Synthetic Public Agency", "Government Reviewer"],
  auditor: ["auditor@example.test", "Demo-Audit-2026!", "Synthetic Auditor", "Synthetic Oversight Unit", "Auditor"],
} as const;

async function login(page: Page, persona: keyof typeof personas, testInfo: TestInfo) {
  const [email, password, user, organization, role] = personas[persona];
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.locator("header.identity")).toContainText(user);
  await expect(page.locator("header.identity")).toContainText(organization);
  await expect(page.locator("header.identity")).toContainText(role);
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
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

test("Journey 11: configuration through immutable approval and audit reconstruction", async ({ page }, testInfo) => {
  await page.goto("/");

  await test.step("Configuration Administrator governs and activates configuration", async () => {
    await login(page, "administrator", testInfo);
    expect(await page.evaluate(async () => (await fetch("/api/invoices/draft?contractId=contract-synthetic-agency-ngo-2026", { method: "POST" })).status)).toBe(403);
    await page.getByRole("button", { name: "Save validated draft" }).click();
    await expect(page.getByText("Configuration draft saved and validated.")).toBeVisible();
    await page.getByLabel("Governance rationale").fill("Journey 11 deterministic configuration evidence");
    await page.getByRole("button", { name: "Test draft and retain evidence" }).click();
    await expect(page.getByRole("button", { name: "Record human approval" })).toBeVisible();
    await page.getByRole("button", { name: "Record human approval" }).click();
    await expect(page.getByRole("button", { name: "Activate approved version" })).toBeVisible();
    await page.getByRole("button", { name: "Activate approved version" }).click();
    await expect(page.locator("header.identity")).toContainText("Active config v1");
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
    await page.getByRole("button", { name: "Assemble draft" }).click();
    await expect(page.getByText("Invoice v1")).toBeVisible();
    await page.getByRole("button", { name: "Run deterministic validation" }).click();
    await expect(page.getByText("Resolve findings")).toBeVisible();
    await resolveOpenFindings(page);
    await page.screenshot({ path: testInfo.outputPath("v1-validated.png"), fullPage: true });
    await logout(page);
  });

  let v1Hash = "";
  await test.step("NGO Approver attests, packages, and submits immutable v1", async () => {
    await login(page, "approver", testInfo);
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
    await expect(page.getByText("Invoice v2")).toBeVisible();
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

  await test.step("Auditor reconstructs both packages without mutation authority", async () => {
    await login(page, "auditor", testInfo);
    await expect(page.getByRole("heading", { name: "Source-to-approval timeline" })).toBeVisible({ timeout: 60_000 });
    await expect(page.getByText("Approved by government")).toBeVisible();
    await expect(page.getByText("2", { exact: true })).toBeVisible();
    await expect(page.getByText("Invoice v1 package")).toBeVisible();
    await expect(page.getByText("Invoice v2 package")).toBeVisible();
    await expect(page.getByText("EXP-004 · $950.00")).toHaveCount(2);
    const v1Trail = page.locator(".audit-card").filter({ hasText: "EXP-004 · $950.00" }).filter({ hasText: "Invoice v1" });
    const v2Trail = page.locator(".audit-card").filter({ hasText: "EXP-004 · $950.00" }).filter({ hasText: "Invoice v2" });
    await expect(v1Trail).toContainText(v1Hash);
    await expect(v2Trail).toContainText(v2Hash);
    await expect(page.getByLabel("Auditor workspace").locator("button")).toHaveCount(0);
    await expect(page.getByLabel("Auditor workspace").locator("form")).toHaveCount(0);
    expect(await page.evaluate(async () => (await fetch("/api/invoices/draft?contractId=contract-synthetic-agency-ngo-2026", { method: "POST" })).status)).toBe(403);
    await page.screenshot({ path: testInfo.outputPath("audit-reconstruction.png"), fullPage: true });
    await logout(page);
  });
});
