import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { expect, type Page, test } from "@playwright/test";

const example = resolve(
	"../../docs/schema/m45-debugging/examples/swapped-prior.execution.json",
);
const debuggerRegion = (page: Page) =>
	page.getByRole("region", { name: "Connection debugger", exact: true });

async function openDifferentProject(page: Page) {
	await page.goto("/");
	await page.getByLabel("Open project file").setInputFiles(example);
	await page.getByRole("button", { name: "Wiring Canary" }).click();
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "DIFFERENT", exact: true }),
	).toBeVisible();
}

async function propose(page: Page) {
	const debug = debuggerRegion(page);
	await debug.getByRole("button", { name: "Inspect connection paths" }).click();
	await expect(
		debug.getByRole("heading", { name: "Candidate correction", exact: true }),
	).toBeVisible();
	await debug
		.getByRole("radio", { name: "Test the declared reference mappings" })
		.check();
}

test("acceptance: changing the project invalidates an already selected proposal before apply", async ({
	page,
}) => {
	const original = JSON.parse(await readFile(example, "utf8"));
	await openDifferentProject(page);
	await propose(page);
	const debug = debuggerRegion(page);
	await expect(
		debug.getByRole("button", { name: "Apply candidate locally" }),
	).toBeEnabled();
	await page.getByRole("button", { name: /Pin mapping ·/ }).click();
	await page.getByLabel("outputMap 0", { exact: true }).selectOption("1");
	await expect(
		debug.getByRole("button", { name: "Apply candidate locally" }),
	).toHaveCount(0);
	await expect(
		debug.getByRole("button", { name: "Revert candidate correction" }),
	).toHaveCount(0);
	await expect(debug.locator(".debug-relevant")).toHaveCount(0);
	const saved = await page.evaluate(() =>
		JSON.parse(sessionStorage.getItem("flip-project") || "null"),
	);
	expect(saved.project.candidate).toEqual(original.project.candidate);
	expect(saved.project.comparison.outputMap).toEqual([1, 0]);
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toBeVisible();
	await debug.getByRole("button", { name: "Inspect connection paths" }).click();
	await expect(
		debug.getByText("NO_FAULT_ATTRIBUTION · NO_FAULT_ATTRIBUTION", {
			exact: true,
		}),
	).toBeVisible();
	await expect(
		debug.getByRole("button", { name: "Apply candidate locally" }),
	).toHaveCount(0);
});

test("acceptance: repeated correction checks are fresh and refresh restores data without undo or proof authority", async ({
	page,
}) => {
	const originalBytes = await readFile(example, "utf8");
	let verificationRequests = 0;
	page.on("request", (request) => {
		if (
			request.url().endsWith("/api/v1/debug") &&
			request.method() === "POST" &&
			request.postDataJSON().operation === "verify-correction"
		)
			verificationRequests += 1;
	});
	await openDifferentProject(page);
	const debug = debuggerRegion(page);
	for (let round = 0; round < 2; round += 1) {
		await propose(page);
		await expect(
			debug.getByText(/VERIFIED_CORRECTION · EXACT_STATELESS/),
		).toHaveCount(0);
		// Wait for the bounded verification operation, then measure UI rendering.
		// The 5s locator expectation must not double as a solver deadline.
		const verifiedResponse = page.waitForResponse(
			(response) =>
				response.url().endsWith("/api/v1/debug") &&
				response.request().method() === "POST" &&
				response.request().postDataJSON().operation === "verify-correction",
		);
		await debug
			.getByRole("button", { name: "Verify proposed revision" })
			.click();
		const verified = await verifiedResponse;
		expect(verified.ok()).toBeTruthy();
		const verifiedBody = await verified.json();
		expect(verifiedBody.correction.classification).toBe("VERIFIED_CORRECTION");
		expect(verifiedBody.correction.comparison.report.verification.verdict).toBe(
			"EQUIVALENT",
		);
		await expect(
			debug.getByText(/VERIFIED_CORRECTION · EXACT_STATELESS/),
		).toBeVisible();
		await debug
			.getByRole("button", { name: "Apply candidate locally" })
			.click();
		await debug
			.getByRole("button", { name: "Compare applied revision" })
			.click();
		await expect(
			page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
		).toBeVisible();
		if (round === 0) {
			await debug
				.getByRole("button", { name: "Revert candidate correction" })
				.click();
			await page.getByRole("button", { name: "Run comparison" }).click();
			await expect(
				page.getByRole("heading", { name: "DIFFERENT", exact: true }),
			).toBeVisible();
		}
	}
	expect(verificationRequests).toBe(2);
	await expect(
		debug.getByRole("button", { name: "Revert candidate correction" }),
	).toBeVisible();
	const applied = await page.evaluate(() =>
		JSON.parse(sessionStorage.getItem("flip-project") || "null"),
	);
	await page.reload();
	await expect(
		page.getByText("Project restored from this browser session.", {
			exact: true,
		}),
	).toBeVisible();
	await page.getByRole("button", { name: "Wiring Canary" }).click();
	await expect(
		debug.getByRole("button", { name: "Revert candidate correction" }),
	).toHaveCount(0);
	await expect(
		debug.getByText(/VERIFIED_CORRECTION · EXACT_STATELESS/),
	).toHaveCount(0);
	await expect(
		debug.getByRole("button", { name: "Inspect connection paths" }),
	).toBeDisabled();
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toHaveCount(0);
	const restored = await page.evaluate(() =>
		JSON.parse(sessionStorage.getItem("flip-project") || "null"),
	);
	expect(restored).toEqual(applied);
	expect(await readFile(example, "utf8")).toBe(originalBytes);
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toBeVisible();
});
