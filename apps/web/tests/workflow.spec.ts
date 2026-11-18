import { spawnSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { expect, test } from "@playwright/test";

const py = resolve(
	process.platform === "win32"
		? "../../.venv/Scripts/python.exe"
		: "../../.venv/bin/python",
);
function cli(code: number, ...args: string[]) {
	const run = spawnSync(py, ["-m", "flip_cli", ...args], { encoding: "utf8" });
	expect(run.status, run.stderr || run.stdout).toBe(code);
	return JSON.parse(run.stdout);
}

test("historical sample, swapped outputs, repair, CLI parity and evidence replay", async ({
	page,
}, info) => {
	const errors: string[] = [];
	page.on("pageerror", (e) => errors.push(e.message));
	await page.goto("/");
	await expect(
		page.getByRole("heading", { name: "Sources", exact: true }),
	).toBeVisible();
	await page.screenshot({ path: info.outputPath("sources.png") });
	await page.getByRole("button", { name: "Open sample" }).click();
	await page.getByRole("button", { name: "Build netlist" }).click();
	await expect(page.getByText(/81 bytes · 8 expanded gates/)).toBeVisible();
	await page.getByText("Half-adder truth table", { exact: true }).click();
	await page.getByRole("button", { name: "Evaluate four inputs" }).click();
	await expect(
		page.getByText("VECTORS_MATCH · 4 rows evaluated"),
	).toBeVisible();
	await page.getByRole("button", { name: "Swap outputs" }).click();
	await page.getByRole("button", { name: "Wiring Canary" }).click();
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "DIFFERENT", exact: true }),
	).toBeVisible();
	await expect(page.getByText("≠ Different", { exact: true })).toHaveCount(2);
	const project = info.outputPath("project.json"),
		bundle = info.outputPath("evidence.json");
	const swapped = cli(0, "sample", "swapped", "--out", project);
	const reference = cli(1, "compare", "--project", project);
	await page.getByRole("button", { name: "Open evidence" }).click();
	const saved = page.waitForEvent("download");
	await page.getByRole("button", { name: "Run and export evidence" }).click();
	await (await saved).saveAs(bundle);
	const evidence = JSON.parse(await readFile(bundle, "utf8"));
	expect(evidence.comparison.report).toEqual(reference.report);
	expect(evidence.comparison.reproduction).toEqual(swapped);
	expect(
		cli(1, "verify-bundle", "--project", project, "--bundle", bundle).report,
	).toEqual(reference.report);
	await page.getByLabel("Replay evidence file").setInputFiles(bundle);
	await expect(
		page.getByRole("heading", { name: "Replay verified" }),
	).toBeVisible();
	await page.getByRole("button", { name: "Composition", exact: false }).click();
	await page.getByRole("button", { name: "Restore original" }).click();
	await page.getByRole("button", { name: "Wiring Canary" }).click();
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toBeVisible();
	const base = cli(0, "sample", "half-adder", "--out", project);
	const build = cli(0, "compose", "--project", project);
	expect(build.netlist.length).toBe(164);
	const bits = (v: string) => ({
		width: 2,
		bits: v,
		encoding: "tap02-lsb0-v1",
	});
	const rows = [
		["00", "00"],
		["01", "01"],
		["10", "01"],
		["11", "10"],
	].map(([a, b]) => ({ inputs: bits(a), outputs: bits(b) }));
	const vectors = info.outputPath("vectors.json");
	await writeFile(vectors, JSON.stringify({ ...base, vectors: rows }));
	expect(cli(0, "vectors", "--project", vectors).verdict).toBe("VECTORS_MATCH");
	await page.getByLabel("Timeout (ms)").fill("1");
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "UNKNOWN", exact: true }),
	).toBeVisible();
	await expect(page.getByText(/SOLVER_TIMEOUT/)).toBeVisible();
	expect(errors).toEqual([]);
});
test("keyboard and narrow screen, import, inspect, add source and revalidate", async ({
	page,
}) => {
	await page.setViewportSize({ width: 390, height: 844 });
	await page.emulateMedia({ reducedMotion: "reduce" });
	await page.goto("/");
	await page.keyboard.press("Tab");
	await expect(page.getByText("Skip to workspace")).toBeFocused();
	await page.getByRole("button", { name: "Import circuit" }).click();
	await expect(page.getByRole("alert")).toContainText("20-byte");
	await page
		.getByLabel("Processor address")
		.fill("0x839bdd6fa7a66416a609a735e11de5411b98574e");
	await page.getByRole("button", { name: "Import circuit" }).click();
	await expect(
		page.getByRole("heading", { name: "Pinned sources" }),
	).toBeVisible();
	await page.getByText("source1", { exact: false }).first().click();
	await expect(
		page.getByText("Manifest", { exact: true }).last(),
	).toBeVisible();
	await page.getByLabel(/Add to project/).check();
	await page.getByLabel("Circuit ID").fill("2");
	await page.getByRole("button", { name: "Import circuit" }).click();
	await expect(page.getByText(/source2/)).toBeVisible();
	await page.getByRole("button", { name: "Revalidate on chain" }).click();
	await expect(page.getByText(/#2 CURRENT at 100/)).toBeVisible();
	await page.getByRole("button", { name: "Open composition" }).click();
	await page
		.getByRole("combobox", { name: "Component", exact: true })
		.selectOption("source2");
	await page.getByRole("button", { name: "Add component" }).click();
	await page.getByLabel("Source for part2 [0]", { exact: true }).focus();
	await expect(page.locator("tr.selected")).toContainText("part2 [0]");
	await page.getByRole("button", { name: "Build netlist" }).click();
	await expect(
		page.getByRole("heading", { name: "Netlist built" }),
	).toBeVisible();
	expect(
		await page.evaluate(() => document.documentElement.scrollWidth),
	).toBeLessThanOrEqual(390);
});
