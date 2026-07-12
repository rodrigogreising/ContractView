import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

const artifacts = path.resolve(process.env.JOURNEY11_ARTIFACT_DIR || "../../artifacts/journey11");

export default defineConfig({
  testDir: "./specs",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  timeout: 12 * 60 * 1000,
  expect: { timeout: 30_000 },
  outputDir: path.join(artifacts, "test-results"),
  reporter: [
    ["line"],
    ["json", { outputFile: path.join(artifacts, "results.json") }],
    ["html", { outputFolder: path.join(artifacts, "html"), open: "never" }],
  ],
  use: {
    baseURL: process.env.JOURNEY11_BASE_URL || "http://127.0.0.1:4173",
    headless: process.env.JOURNEY11_HEADED !== "true",
    launchOptions: { slowMo: Number(process.env.JOURNEY11_SLOW_MO_MS || "0") },
    screenshot: "only-on-failure",
    trace: "on",
    video: "on",
  },
  projects: [{ name: "journey11-chromium", use: { ...devices["Desktop Chrome"] } }],
});
