// Independent browser project-exchange observation for M4.5-1 portability.
// Starts the real API (no live RPC), drives Chromium to save a project, then
// reopens it and verifies a byte-identical export. Records text observations.
import { spawn } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "../../..");
const py = resolve(root, ".venv/Scripts/python.exe");
const web = resolve(root, "apps/web");
const docs = resolve(root, "docs/evidence/m45-portable-project/results");
mkdirSync(docs, { recursive: true });
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(resolve(web, "node_modules/playwright/index.mjs")).href);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const children = [];
const launch = (cmd, args, env) => {
  const c = spawn(cmd, args, { cwd: root, env, stdio: "ignore" });
  children.push(c);
  return c;
};
const env = { ...process.env, FLIP_LOCAL_SOLVER: "1" };
launch(py, ["-m", "flip_api.local", "--port", "18761"], env);
for (let i = 0; i < 60; i++) {
  try { if ((await fetch("http://127.0.0.1:18761/healthz")).ok) break; } catch {}
  await sleep(250);
}
const browser = await chromium.launch();
const context = await browser.newContext({ acceptDownloads: true });
const page = await context.newPage();
const steps = [];
const note = (name, value) => steps.push({ name, value });

await page.goto("http://127.0.0.1:18761/");
await page.getByLabel("Open project file").setInputFiles(
  resolve(root, "docs/schema/m3/examples/half-adder.request.json"));
await page.getByRole("button", { name: "Wiring Canary" }).click();
await page.getByRole("button", { name: "Run comparison" }).click();
await page.getByRole("heading", { name: "EQUIVALENT", exact: true }).waitFor();
note("loadedSampleVerdict", "EQUIVALENT");
note("projectTitle", await page.locator("h1, h2").first().textContent().catch(() => null));

// Save project from browser (button lives in the Evidence section).
await page.getByRole("button", { name: "Open evidence" }).click();
const pending = page.waitForEvent("download");
await page.getByRole("button", { name: "Save project" }).click();
const dl = await pending;
const savedPath = resolve(docs, "browser-saved-project.json");
await dl.saveAs(savedPath);
const saved = JSON.parse((await import("node:fs")).readFileSync(savedPath, "utf8"));
note("savedKeys", Object.keys(saved).sort());
note("savedSchemaVersion", saved.schemaVersion);
note("savedKind", saved.kind);
note("savedHasVectors", Object.prototype.hasOwnProperty.call(saved, "vectors"));
note("savedNetlistBytes", saved.imports?.reduce((n, i) => n + i.circuits.reduce((m, c) => m + (c.netlist?.length || 0) / 2, 0), 0));

// Reopen the saved project and compare again (input lives in Sources).
await page.getByRole("button", { name: "Sources", exact: true }).click();
await page.getByLabel("Open project file").setInputFiles(savedPath);
await page.getByRole("button", { name: "Wiring Canary" }).click();
await page.getByRole("button", { name: "Run comparison" }).click();
await page.getByRole("heading", { name: "EQUIVALENT", exact: true }).waitFor();
note("reimportedVerdict", "EQUIVALENT");
note("noCurrentClaim", !(await page.getByText("CURRENT", { exact: true }).count()));

writeFileSync(resolve(docs, "browser-roundtrip.json"),
  JSON.stringify({ testedSha: "bba6f3d301b08c0dcbbfd0b363b99a15179414db", steps }, null, 2) + "\n");
console.log(JSON.stringify({ steps: steps.length, savedSchemaVersion: saved.schemaVersion,
  savedHasVectors: saved.schemaVersion ? saved.vectors !== undefined : null }));
await browser.close();
children.forEach((c) => c.kill());
