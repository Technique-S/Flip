import { expect, test } from "@playwright/test";

test("F-02 computed mapping and disclosure markers; F-03 timeout and accessible retry", async ({
	page,
}) => {
	await page.goto("/");
	await page.getByRole("button", { name: "Open sample" }).click();
	const pin = page.getByLabel("Source for nand0 [0]", { exact: true });
	await pin.focus();
	const row = page.locator("tr.selected th");
	await expect(row).toContainText("nand0 [0]");
	expect(
		await row.evaluate((e) => getComputedStyle(e, "::before").content),
	).toBe('"→ "');
	await page.getByRole("button", { name: "Sources", exact: true }).click();
	const disclosure = page.locator("details.source").first();
	const summary = disclosure.locator("summary");
	expect(
		await summary.evaluate((e) => getComputedStyle(e, "::before").content),
	).toBe('"▸"');
	await summary.click();
	expect(
		await summary.evaluate((e) => getComputedStyle(e, "::before").content),
	).toBe('"▾"');
	await page.getByRole("button", { name: "Wiring Canary" }).click();
	await page.getByLabel("Timeout (ms)").fill("1");
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "UNKNOWN", exact: true }),
	).toBeVisible();
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toHaveCount(0);
	await expect(page.getByText(/SOLVER_TIMEOUT/)).toContainText(
		"Retry with a higher timeout",
	);
	await expect(page.getByRole("status").last()).toContainText(
		"Result: UNKNOWN. Freshness: HISTORICAL",
	);
	await page.getByLabel("Timeout (ms)").fill("5000");
	await page.getByRole("button", { name: "Run comparison" }).focus();
	await page.keyboard.press("Enter");
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toBeVisible();
});
