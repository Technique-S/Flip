import { expect, test } from "@playwright/test";

const storageKey = "flip-library-m45-v1";

async function library(page) {
	await page.goto("/");
	await page
		.getByRole("button", { name: "Circuit Library", exact: true })
		.click();
}

test("LC01 invalid saved catalog recovers known addresses without overwriting saved bytes", async ({
	page,
}) => {
	const saved = JSON.stringify({
		schemaVersion: "m45-library-99.0.0",
		records: [],
	});
	await page.addInitScript(
		({ key, value }) => localStorage.setItem(key, value),
		{ key: storageKey, value: saved },
	);
	await library(page);
	await expect(page.locator(".library-list button")).toHaveCount(2);
	await expect(
		page.getByText(/Saved library.*invalid|Saved library.*unsupported/),
	).toBeVisible();
	expect(
		await page.evaluate((key) => localStorage.getItem(key), storageKey),
	).toBe(saved);
	await page.locator(".library-list button").first().click();
	await page.getByRole("button", { name: "Add favorite", exact: true }).click();
	await expect(
		page.getByRole("button", { name: "Remove favorite", exact: true }),
	).toBeVisible();
	expect(
		await page.evaluate(
			(key) => localStorage.getItem(`${key}-recovery`),
			storageKey,
		),
	).toBe(saved);
});

test("LC02 recent imports display most recent first after browser restore", async ({
	page,
}) => {
	let catalog: unknown;
	for (const circuitId of ["1", "2"]) {
		const response = await page.request.post("/api/library/v1/execute", {
			data: {
				operation: "import",
				...(catalog ? { catalog } : {}),
				identity: {
					processor: "0x839bdd6fa7a66416a609a735e11de5411b98574e",
					circuitId,
				},
			},
		});
		const result = await response.json();
		expect(result.status).toBe("COMPLETE");
		catalog = result.catalog;
	}
	await page.addInitScript(
		({ key, value }) => localStorage.setItem(key, JSON.stringify(value)),
		{ key: storageKey, value: catalog },
	);
	await library(page);
	await page
		.getByRole("combobox", { name: "Collection", exact: true })
		.selectOption("recents");
	await expect(page.locator(".library-list button")).toHaveCount(2);
	await expect(page.locator(".library-list button").first()).toContainText(
		"Circuit #2",
	);
});
