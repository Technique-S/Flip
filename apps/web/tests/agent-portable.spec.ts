import { spawnSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const priorFile = resolve(
	"../../docs/schema/m45-debugging/examples/swapped-prior.execution.json",
);
const py = resolve(
	process.platform === "win32"
		? "../../.venv/Scripts/python.exe"
		: "../../.venv/bin/python",
);
const bits = (bits: string) => ({ encoding: "tap02-lsb0-v1", width: 2, bits });
const portable = (operation: string, fields: Record<string, unknown>) => ({
	schemaVersion: "flip-portable-project-1.1.0",
	kind: "PORTABLE_REQUEST",
	operation,
	...fields,
});

async function packageFixture(page: import("@playwright/test").Page) {
	const raw = JSON.parse(await readFile(priorFile, "utf8"));
	const tests = [
		{
			name: "halfAdder",
			declaredIntent: "Carry and sum on numeric pins",
			expectedCoverage: "EXHAUSTIVE_DECLARED_DOMAIN",
			vectors: [
				["00", "00"],
				["01", "01"],
				["10", "01"],
				["11", "10"],
			].map(([i, o]) => ({ inputs: bits(i), outputs: bits(o) })),
		},
	];
	const response = await page.request.post("/api/v1/portable", {
		data: portable("wrap", { executionRequest: raw, tests }),
	});
	expect(response.ok()).toBeTruthy();
	const packageValue = await response.json();
	await page.goto("/");
	await page
		.getByLabel("Open project file")
		.setInputFiles({
			name: "portable.json",
			mimeType: "application/json",
			buffer: Buffer.from(JSON.stringify(packageValue)),
		});
	await expect(
		page.getByRole("heading", { name: "Composition", exact: true }),
	).toBeVisible();
	await page.getByRole("button", { name: "Evidence", exact: true }).click();
	return { raw, packageValue };
}

test("combined named tests, correction, explicit new revision, CLI replay and authorization stop", async ({
	page,
}, info) => {
	const { raw, packageValue } = await packageFixture(page);
	const stopped = page.waitForResponse((r) =>
		r.url().endsWith("/api/agent/v1/portable"),
	);
	await page
		.getByRole("button", { name: "Propose and verify correction", exact: true })
		.click();
	const mismatch = await (await stopped).json();
	expect(mismatch.status).toBe("DIFFERENT");
	expect(mismatch.revisionCreated).toBe(false);
	await expect(
		page.getByRole("status").filter({ hasText: "Workflow: DIFFERENT" }),
	).toBeVisible();
	await page
		.getByLabel("Continue to correction when declared tests differ")
		.check();
	const completed = page.waitForResponse((r) =>
		r.url().endsWith("/api/agent/v1/portable"),
	);
	await page
		.getByRole("button", { name: "Propose and verify correction", exact: true })
		.click();
	const result = await (await completed).json();
	expect(result.status).toBe("COMPLETE");
	await expect(
		page.getByRole("status").filter({ hasText: "Workflow: COMPLETE" }),
	).toBeVisible();
	expect(result.originalPackage).toEqual(packageValue);
	expect(result.revisedPackage.revision.parentHash).toBe(
		packageValue.revision.revisionHash,
	);
	const old = await page.evaluate(() =>
		JSON.parse(sessionStorage.getItem("flip-project") || "null"),
	);
	expect(old).toEqual(raw);
	const saved = page.waitForEvent("download");
	await page
		.getByRole("button", { name: "Download verified revision", exact: true })
		.click();
	await (await saved).saveAs(info.outputPath("new-project.json"));
	expect(
		JSON.parse(await readFile(info.outputPath("new-project.json"), "utf8")),
	).toEqual(result.revisedPackage);
	const receipt = page.waitForEvent("download");
	await page
		.getByRole("button", { name: "Download workflow receipt", exact: true })
		.click();
	await (await receipt).saveAs(info.outputPath("receipt.json"));
	expect(
		JSON.parse(await readFile(info.outputPath("receipt.json"), "utf8")),
	).toEqual(result.receipt);
	const request = info.outputPath("replay.json");
	await writeFile(
		request,
		JSON.stringify(
			portable("replay-evidence", {
				package: result.revisedPackage,
				artifacts: result.evidenceArtifacts,
			}),
		),
	);
	const replay = spawnSync(
		py,
		["-m", "flip_cli", "portable", "--request", request],
		{ encoding: "utf8" },
	);
	expect(replay.status, replay.stderr || replay.stdout).toBe(0);
	const proof = JSON.parse(replay.stdout).results[0];
	expect(proof.status).toBe("REPLAYED");
	expect(proof.result.report.verification.verdict).toBe("EQUIVALENT");
	expect(proof.result.report.integrity.freshness).toBe("HISTORICAL");
	await page.screenshot({
		path: info.outputPath("integration-desktop.png"),
		fullPage: true,
	});
	expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
	await page.setViewportSize({ width: 390, height: 844 });
	await page.screenshot({
		path: info.outputPath("integration-mobile.png"),
		fullPage: true,
	});
	expect(
		await page.evaluate(
			() => document.documentElement.scrollWidth <= innerWidth,
		),
	).toBeTruthy();
	await page
		.getByRole("button", { name: "Open verified revision", exact: true })
		.click();
	await expect(page.getByText(/Saved revision 1/)).toBeVisible();
	const publication = page.waitForResponse((r) =>
		r.url().endsWith("/api/agent/v1/portable"),
	);
	await page
		.getByRole("button", { name: "Request publication handoff", exact: true })
		.click();
	const boundary = await (await publication).json();
	expect(boundary.status).toBe("STOP_AUTHORIZATION");
	expect(boundary.receipt.logs).toHaveLength(1);
	expect(boundary.revisedPackage).toBeNull();
	await expect(
		page
			.getByRole("status")
			.filter({ hasText: "Workflow: STOP_AUTHORIZATION" }),
	).toBeVisible();
	await page.reload();
	await expect(
		page.getByText("Project restored from this browser session.", {
			exact: true,
		}),
	).toBeVisible();
	await page.getByRole("button", { name: "Evidence", exact: true }).click();
	await expect(page.getByText(/Saved revision 1/)).toBeVisible();
	await expect(
		page.getByRole("button", { name: "Open verified revision", exact: true }),
	).toHaveCount(0);
});

test("cancel a late workflow response without selecting its revised package", async ({
	page,
}) => {
	const { raw, packageValue } = await packageFixture(page);
	await page
		.getByLabel("Continue to correction when declared tests differ")
		.check();
	let release: () => void = () => {};
	let ready: () => void = () => {};
	const held = new Promise<void>((resolve) => {
		release = resolve;
	});
	const responseReady = new Promise<void>((resolve) => {
		ready = resolve;
	});
	await page.route("**/api/agent/v1/portable", async (route) => {
		const response = await route.fetch();
		ready();
		await held;
		await route.fulfill({ response }).catch(() => {});
	});
	await page
		.getByRole("button", { name: "Propose and verify correction", exact: true })
		.click();
	await responseReady;
	await page
		.getByRole("button", { name: "Cancel portable workflow", exact: true })
		.click();
	release();
	await expect(
		page.getByRole("status").filter({ hasText: "Cancelled locally" }),
	).toBeVisible();
	await expect(
		page.getByRole("heading", { name: "Bounded agent workflow", exact: true }),
	).toBeFocused();
	await expect(
		page.getByRole("button", {
			name: "Download verified revision",
			exact: true,
		}),
	).toHaveCount(0);
	expect(
		await page.evaluate(() =>
			JSON.parse(sessionStorage.getItem("flip-project") || "null"),
		),
	).toEqual(raw);
	expect(
		await page.evaluate(() =>
			JSON.parse(sessionStorage.getItem("flip-portable") || "null"),
		),
	).toEqual(packageValue);
});
