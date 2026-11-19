// Independent browser observations for the M4.5-2L library review.
// Starts the real API + Codex's loopback RPC fixture, then drives Chromium via
// Playwright. Writes text observations and screenshots to docs/evidence only.
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "../../../../");
const web = resolve(root, "apps/web");
const py = resolve(root, ".venv/Scripts/python.exe");
const docs = resolve(root, "docs/evidence/m45-library-final-review/results");
mkdirSync(docs, { recursive: true });
const require = createRequire(resolve(web, "package.json"));
const { chromium } = require("playwright");

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const children = [];
function launch(command, args, cwd, env) {
  const child = spawn(command, args, { cwd, env, stdio: "ignore" });
  children.push(child);
  return child;
}
async function waitHealth(url, tries = 60) {
  for (let i = 0; i < tries; i++) {
    try {
      const res = await fetch(url);
      if (res.ok) return true;
    } catch {}
    await sleep(250);
  }
  return false;
}

const env = { ...process.env, FLIP_RPC_URL: "http://127.0.0.1:18762",
  FLIP_RPC_RETRIES: "0", FLIP_LOCAL_SOLVER: "1" };
launch(py, [resolve(web, "tests/rpc_fixture.py")], web, env);
launch(py, ["-m", "flip_api.local", "--port", "18761"], root, env);
const healthy = await waitHealth("http://127.0.0.1:18761/healthz");
if (!healthy) {
  children.forEach((c) => c.kill());
  throw new Error("API did not become healthy");
}

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await context.newPage();
const observations = { testedSha: "786cbca056c6cd61ca0e7a5b61ddbc772a55a800",
  apiHealthy: healthy, steps: [] };
const note = (name, value) => observations.steps.push({ name, value });

await page.goto("http://127.0.0.1:18761/");
await page.getByRole("button", { name: "Circuit Library", exact: true }).click();
await page.getByRole("status").filter({ hasText: "COMPLETE" }).waitFor();
note("statusLanguage", await page.getByRole("status").allTextContents());
note("initialList", (await page.locator(".library-list button").allTextContents()).slice(0, 5));

// Keyboard-only entry to the library after reload.
await page.reload();
await page.keyboard.press("Tab");
let focused = await page.evaluate(() => document.activeElement?.textContent?.trim() ?? "");
for (let i = 0; i < 12 && !focused.includes("Circuit Library"); i++) {
  await page.keyboard.press("Tab");
  focused = await page.evaluate(() => document.activeElement?.textContent?.trim() ?? "");
}
note("keyboardFocusReachedLibrary", focused.includes("Circuit Library"));
if (focused.includes("Circuit Library")) {
  await page.keyboard.press("Enter");
  await page.getByRole("heading", { name: "Circuit Library", exact: true }).waitFor();
  note("keyboardEnterOpenedLibrary", true);
}

await page.getByRole("button", { name: "Discover processors", exact: true }).click();
await page.getByRole("status").filter({ hasText: "COMPLETE" }).waitFor();
note("discoveryStatus", await page.getByRole("status").allTextContents());
await page.screenshot({ path: resolve(docs, "library-desktop-observed.png"), fullPage: true });

// Search by address then by circuit ID.
const search = page.getByLabel("Search library");
await search.fill("0x839bdd6fa7a66416a609a735e11de5411b98574e");
note("addressSearchCount", await page.locator(".library-list button").count());
await search.fill("1");
note("idSearchCount", await page.locator(".library-list button").count());
await search.fill("");

// Select, favorite, inspect provenance language.
await page.locator(".library-list button").first().click();
note("inspectorText", (await page.getByRole("region", { name: "Selected metadata" }).textContent())?.slice(0, 700));
await page.getByRole("button", { name: "Add favorite", exact: true }).click();
let favoriteAdded = true;
try {
  await page.getByRole("button", { name: "Remove favorite" }).waitFor({ timeout: 6000 });
} catch {
  favoriteAdded = false;
}
note("favoriteAdded", favoriteAdded);

// Corrupt the persisted favorites and reload.
await page.evaluate(() => {
  const key = "flip-library-m45-v1";
  const saved = JSON.parse(localStorage.getItem(key));
  saved.overlay.favorites = [{ label: "corrupt favorite" }];
  localStorage.setItem(key, JSON.stringify(saved));
});
await page.reload();
await page.getByRole("button", { name: "Circuit Library", exact: true }).click();
await sleep(1200);
note("corruptStorageAlert", await page.getByRole("alert").allTextContents());
note("corruptStorageListCount", await page.locator(".library-list button").count());
note("corruptStorageStatus", await page.getByRole("status").allTextContents());
note("F01RecoveryCopy", await page.evaluate(() => Boolean(localStorage.getItem("flip-library-m45-v1-recovery"))));
note("F01RecoveredRows", (await page.locator(".library-list button").allTextContents()).slice(0, 3));

// F-02: a favorite-only pointer must display USER_SUPPLIED provenance, never onchain metadata.
await page.evaluate(() => {
  localStorage.setItem("flip-library-m45-v1", JSON.stringify({
    schemaVersion: "m45-library-1.1.0", kind: "LIBRARY_CATALOG", records: [],
    overlay: { favorites: [{ identity: { chainId: 196,
      factory: "0x1f09daefa827f02cbb40967cc91b259763760761",
      processor: "0x7777777777777777777777777777777777777777", circuitId: "77" },
      label: "user pointer", description: "", tags: [] }], aliases: [], recents: [] } }));
});
await page.reload();
await page.getByRole("button", { name: "Circuit Library", exact: true }).click();
await page.getByRole("heading", { name: "Circuit Library", exact: true }).waitFor();
await page.getByRole("combobox", { name: "Collection", exact: true }).selectOption("favorites");
await page.locator(".library-list button").filter({ hasText: "Circuit #77" }).click();
note("F02Inspector", (await page.getByRole("region", { name: "Selected metadata" }).textContent())?.slice(0, 500));
note("F02Rows", (await page.locator(".library-list button").allTextContents()).slice(0, 5));

// Stale-favorite language via route interception (known-address fallback + STALE).
const fresh = await context.newPage();
await fresh.route("**/api/library/v1/execute", async (route) => {
  const body = route.request().postDataJSON();
  if (body.operation === "discover") {
    const response = await route.fetch();
    const result = await response.json();
    result.status = "UNKNOWN";
    result.errorCode = "RPC_UNAVAILABLE";
    result.catalog.records.forEach((r) => { r.freshness = "STALE"; });
    await route.fulfill({ json: result });
  } else await route.continue();
});
await fresh.goto("http://127.0.0.1:18761/");
await fresh.getByRole("button", { name: "Circuit Library", exact: true }).click();
await fresh.getByRole("button", { name: "Discover processors", exact: true }).click();
await fresh.getByRole("status").filter({ hasText: "UNKNOWN" }).waitFor({ timeout: 10000 }).catch(() => {});
note("fallbackText", await fresh.getByText(/Enumeration unavailable/).allTextContents());
note("fallbackStatus", await fresh.getByRole("status").allTextContents());
note("fallbackListSample", (await fresh.locator(".library-list button").allTextContents()).slice(0, 3));

// Narrow viewport.
await page.setViewportSize({ width: 390, height: 844 });
await sleep(400);
note("narrowOverflow", await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
await page.screenshot({ path: resolve(docs, "library-mobile-observed.png"), fullPage: true });

writeFileSync(resolve(docs, "browser-observations.json"),
  JSON.stringify(observations, null, 2) + "\n");
console.log(JSON.stringify({ steps: observations.steps.length,
  keyboard: observations.steps.find((s) => s.name === "keyboardFocusReachedLibrary")?.value,
  corruptCount: observations.steps.find((s) => s.name === "corruptStorageListCount")?.value }));
await browser.close();
children.forEach((c) => c.kill());
