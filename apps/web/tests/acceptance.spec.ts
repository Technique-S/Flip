import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

async function keyboard(page: Page, name: string) {
	const button = page.getByRole("button", { name, exact: false });
	for (let i = 0; i < 100; i++) {
		if (await button.evaluate((e) => e === document.activeElement)) {
			await page.keyboard.press("Enter");
			return;
		}
		await page.keyboard.press("Tab");
	}
	throw Error(`Keyboard target unreachable: ${name}`);
}
async function sample(page: Page) {
	await page.goto("/");
	await page.getByRole("button", { name: "Open sample" }).click();
}
test("B01 keyboard-only complete export journey", async ({ page }) => {
	await page.goto("/");
	await keyboard(page, "Open sample");
	await keyboard(page, "Build netlist");
	await expect(page.getByText(/81 bytes/)).toBeVisible();
	await keyboard(page, "Compare circuits");
	await keyboard(page, "Run comparison");
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toBeVisible();
	await keyboard(page, "Open evidence");
	const download = page.waitForEvent("download");
	await keyboard(page, "Run and export evidence");
	expect((await download).suggestedFilename()).toBe("evidence.json");
});
test("B02 focus recovery and B06 error state", async ({ page }) => {
	await page.goto("/");
	await page.getByRole("button", { name: "Import circuit" }).click();
	await expect(page.getByRole("alert")).toBeFocused();
	await expect(page.getByRole("alert")).toContainText("20-byte");
	expect(
		await page
			.getByRole("alert")
			.evaluate((e) => getComputedStyle(e).outlineStyle),
	).not.toBe("none");
	await page
		.getByLabel("Processor address")
		.fill("0x839bdd6fa7a66416a609a735e11de5411b98574e");
	await page.route("**/api/v1/import", (r) =>
		r.fulfill({
			status: 503,
			json: {
				error: {
					code: "RPC_UNAVAILABLE",
					message: "Network reader unavailable. Retry the import.",
				},
			},
		}),
	);
	await page.getByRole("button", { name: "Import circuit" }).click();
	await expect(page.getByRole("alert")).toContainText("RPC_UNAVAILABLE");
	await expect(page.getByRole("alert")).toBeFocused();
	await page.unroute("**/api/v1/import");
	await page.getByRole("button", { name: "Import circuit" }).click();
	await expect(
		page.getByRole("heading", { name: "Pinned sources" }),
	).toBeVisible();
});
test("B03 accessible labels and B05 responsive axe audit", async ({
	page,
}, info) => {
	await sample(page);
	for (const width of [320, 768, 1280]) {
		await page.setViewportSize({ width, height: 900 });
		for (const screen of [
			"Sources",
			"Composition",
			"Wiring Canary",
			"Evidence",
		]) {
			await page
				.getByRole("navigation")
				.getByRole("button", { name: screen })
				.click();
			expect(
				await page.evaluate(() => document.documentElement.scrollWidth),
			).toBeLessThanOrEqual(width);
			const audit = await new AxeBuilder({ page })
				.withTags(["wcag2a", "wcag2aa", "wcag21aa"])
				.analyze();
			expect(
				audit.violations.map((v) => ({
					id: v.id,
					nodes: v.nodes.map((n) => n.target),
				})),
			).toEqual([]);
		}
	}
	await page.screenshot({
		path: info.outputPath("evidence.png"),
		fullPage: true,
	});
});
test("B04 result announcement, mappings, and semantic differences", async ({
	page,
}) => {
	await sample(page);
	await page.getByRole("button", { name: "Swap outputs" }).click();
	await page.getByRole("button", { name: "Wiring Canary" }).click();
	await page.getByRole("button", { name: "Pin mapping" }).click();
	await page.getByLabel("inputMap 0").selectOption("1");
	await expect(page.getByLabel("inputMap 1")).toHaveValue("0");
	await page.getByLabel("inputMap 0").selectOption("0");
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(page.getByRole("status").last()).toContainText(
		"Result: DIFFERENT. Freshness: HISTORICAL",
	);
	await expect(page.getByText("≠ Different", { exact: true })).toHaveCount(2);
	await page.getByLabel("outputMap 0").selectOption("1");
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toBeVisible();
});
test("B07 timeout recovery and B08 repeated runs", async ({ page }) => {
	await sample(page);
	await page.getByRole("button", { name: "Wiring Canary" }).click();
	await page.getByLabel("Timeout (ms)").fill("1");
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "UNKNOWN", exact: true }),
	).toBeVisible();
	await page.getByLabel("Timeout (ms)").fill("5000");
	for (let i = 0; i < 5; i++) {
		await page.getByRole("button", { name: "Run comparison" }).click();
		await expect(
			page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
		).toHaveCount(1);
	}
	await page.emulateMedia({ reducedMotion: "reduce" });
	await expect
		.poll(() =>
			page
				.getByRole("button", { name: "Run comparison" })
				.evaluate((e) => getComputedStyle(e).transitionDuration),
		)
		.toBe("0s");
});
test("B09 refresh recovery, confirmed reset and storage failure", async ({
	page,
}) => {
	await sample(page);
	await page.getByRole("button", { name: "Swap outputs" }).click();
	await page.reload();
	await expect(
		page.getByText("Project restored from this browser session."),
	).toBeVisible();
	await page.getByRole("button", { name: "Wiring Canary" }).click();
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "DIFFERENT", exact: true }),
	).toBeVisible();
	await page.getByRole("button", { name: "Reset workspace" }).click();
	await page.getByRole("button", { name: "Keep project" }).click();
	await page.getByRole("button", { name: "Reset workspace" }).click();
	await page.getByRole("button", { name: "Confirm reset" }).click();
	await expect(page.getByRole("button", { name: "Open sample" })).toBeVisible();
	await page.evaluate(() => {
		Storage.prototype.setItem = () => {
			throw new DOMException("Quota", "QuotaExceededError");
		};
	});
	await page.getByRole("button", { name: "Open sample" }).click();
	await expect(page.getByText(/Browser storage is full/)).toBeVisible();
});
test("B10 download name and replay is covered by workflow suite", async ({
	page,
}) => {
	await sample(page);
	await page.getByRole("button", { name: "Evidence", exact: true }).click();
	await expect(
		page.getByRole("button", { name: "Run and export evidence (JSON)" }),
	).toBeVisible();
	await expect(page.getByLabel("Replay evidence file")).toBeAttached();
});
test("B11 preflight separates three structural outcomes", async ({ page }) => {
	await sample(page);
	await page.getByRole("button", { name: "Evidence", exact: true }).click();
	for (const status of ["STRUCTURALLY_ACCEPTED", "REJECTED", "UNKNOWN"]) {
		await page.route("**/api/v1/preflight", (r) =>
			r.fulfill({
				json: {
					status,
					reasonCode:
						status === "STRUCTURALLY_ACCEPTED" ? null : "UNRECOGNIZED_REVERT",
					integrity: { freshness: "HISTORICAL" },
					observation: null,
				},
			}),
		);
		await page
			.getByRole("button", { name: "Run read-only pre-flight" })
			.click();
		await expect(
			page.getByRole("heading", {
				name: status.replaceAll("_", " "),
				exact: true,
			}),
		).toBeVisible();
		await expect(page.getByText(/No transaction broadcast/)).toBeVisible();
		await page.unroute("**/api/v1/preflight");
	}
});
