import { readFile } from "node:fs/promises";
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const body = (operation: string, fields: Record<string, unknown>) => ({
	schemaVersion: "flip-portable-project-1.1.0",
	kind: "PORTABLE_REQUEST",
	operation,
	...fields,
});
const bits = (bits: string) => ({
	encoding: "tap02-lsb0-v1",
	width: bits.length,
	bits,
});

test("portable CLI-compatible package, tests, revision save, refresh and explicit downgrade", async ({
	page,
}, info) => {
	const execution = await (
		await page.request.get("/api/v1/sample/half-adder")
	).json();
	const tests = [
		{
			name: "halfAdder",
			declaredIntent: "Carry and sum at pins zero and one",
			expectedCoverage: "EXHAUSTIVE_DECLARED_DOMAIN",
			vectors: [
				["00", "00"],
				["01", "01"],
				["10", "01"],
				["11", "10"],
			].map(([input, output]) => ({
				inputs: bits(input),
				outputs: bits(output),
			})),
		},
	];
	const response = await page.request.post("/api/v1/portable", {
		data: body("wrap", { executionRequest: execution, tests }),
	});
	expect(response.ok()).toBeTruthy();
	const portable = await response.json();
	await page.goto("/");
	await page
		.getByLabel("Open project file")
		.setInputFiles({
			name: "portable.json",
			mimeType: "application/json",
			buffer: Buffer.from(JSON.stringify(portable)),
		});
	await expect(
		page.getByRole("heading", { name: "Composition", exact: true }),
	).toBeVisible();
	await page
		.getByRole("button", { name: "Build netlist", exact: true })
		.click();
	await expect(page.getByText(/81 bytes/)).toBeVisible();
	await page.getByRole("button", { name: "Evidence", exact: true }).click();
	await page.getByText("Named tests", { exact: true }).click();
	await expect(page.getByRole("heading", { name: "halfAdder" })).toBeVisible();
	await page
		.getByRole("button", { name: "Run named tests", exact: true })
		.click();
	await expect(
		page.getByRole("status").filter({ hasText: "VECTORS_MATCH" }),
	).toBeVisible();
	const saved = page.waitForEvent("download");
	await page
		.getByRole("button", {
			name: "Save complete portable project",
			exact: true,
		})
		.click();
	const download = await saved;
	const path = info.outputPath("portable.json");
	await download.saveAs(path);
	const actual = JSON.parse(await readFile(path, "utf8"));
	expect(actual.tests).toEqual(tests);
	expect(actual.executionRequestHash).toEqual(portable.executionRequestHash);
	expect(actual.ancestors[0]).toEqual(portable.revision);
	expect(actual.revision.sequence).toBe(2);
	await page.reload();
	await expect(
		page.getByText("Project restored from this browser session."),
	).toBeVisible();
	await page.getByRole("button", { name: "Evidence", exact: true }).click();
	await expect(page.getByText(/Saved revision 2/)).toBeVisible();
	await page.getByText("Revision history", { exact: true }).click();
	await expect(page.getByText(/Revision 0:/)).toBeVisible();
	await page.getByText("Convert to legacy project", { exact: true }).click();
	await expect(
		page.getByRole("button", { name: "Export legacy project", exact: true }),
	).toBeDisabled();
	await page.getByLabel("I acknowledge the loss of portable metadata").check();
	const legacyDownload = page.waitForEvent("download");
	await page
		.getByRole("button", { name: "Export legacy project", exact: true })
		.click();
	await (await legacyDownload).saveAs(info.outputPath("legacy.json"));
	expect(
		JSON.parse(await readFile(info.outputPath("legacy.json"), "utf8")),
	).toEqual(execution);
	await expect(
		page.getByRole("status").filter({ hasText: "LOSSY_DOWNGRADE" }),
	).toBeVisible();
	await page.screenshot({
		path: info.outputPath("portable-desktop.png"),
		fullPage: true,
	});
	expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
	await page.setViewportSize({ width: 390, height: 844 });
	await page.screenshot({
		path: info.outputPath("portable-mobile.png"),
		fullPage: true,
	});
	expect(
		await page.evaluate(
			() => document.documentElement.scrollWidth <= innerWidth,
		),
	).toBeTruthy();
});

test("portable import rejects tampering and preserves the open project", async ({
	page,
}) => {
	await page.goto("/");
	await page.getByRole("button", { name: "Open sample" }).click();
	await page.getByRole("button", { name: "Sources", exact: true }).click();
	await page
		.getByLabel("Open project file")
		.setInputFiles({
			name: "future.json",
			mimeType: "application/json",
			buffer: Buffer.from(
				JSON.stringify({
					kind: "PORTABLE_PROJECT",
					schemaVersion: "flip-portable-project-9.0.0",
				}),
			),
		});
	await expect(page.getByRole("alert")).toContainText(
		"UNSUPPORTED_SCHEMA_VERSION",
	);
	await expect(page.getByRole("alert")).toBeFocused();
	await page.getByRole("button", { name: "Evidence", exact: true }).click();
	await expect(
		page.getByRole("heading", { name: "Portable project", exact: true }),
	).toBeVisible();
});
