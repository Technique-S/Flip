import { expect, test } from "@playwright/test";

const storageKey = "flip-library-m45-v1";

test("F-01 exact malformed-favorites restore retains bytes and recovers seeds", async ({
	page,
}) => {
	await library(page);
	await expect(page.locator(".library-list button")).toHaveCount(2);
	const corrupted = await page.evaluate((key) => {
		const saved = JSON.parse(localStorage.getItem(key) ?? "{}");
		saved.schemaVersion = "m45-library-1.0.0";
		saved.overlay.favorites = [{ label: "corrupt favorite" }];
		const raw = JSON.stringify(saved);
		localStorage.setItem(key, raw);
		return raw;
	}, storageKey);
	await page.reload();
	await page
		.getByRole("button", { name: "Circuit Library", exact: true })
		.click();
	await expect(page.locator(".library-list button")).toHaveCount(2);
	await expect(page.getByText(/Saved library.*invalid/)).toBeVisible();
	await expect(
		page.getByText("Loading known addresses…", { exact: true }),
	).toHaveCount(0);
	expect(
		await page.evaluate((key) => localStorage.getItem(key), storageKey),
	).toBe(corrupted);
	await expect(page.locator(".library-list")).toContainText("UNKNOWN");
	await expect(page.locator(".library-list")).not.toContainText("CURRENT");
});

test("F-02 favorite-only metadata is USER_SUPPLIED in UI and legacy storage migration", async ({
	page,
}) => {
	const response = await page.request.post("/api/library/v1/execute", {
		data: {
			schemaVersion: "m45-library-1.0.0",
			operation: "favorite",
			identity: { processor: `0x${"77".repeat(20)}`, circuitId: "77" },
		},
	});
	const result = await response.json();
	expect(result.errorCode).toBe("UNSUPPORTED_SCHEMA_VERSION");
	const saved = JSON.stringify(result.catalog);
	await page.addInitScript(({ key, raw }) => localStorage.setItem(key, raw), {
		key: storageKey,
		raw: saved,
	});
	await library(page);
	await page
		.getByRole("combobox", { name: "Collection", exact: true })
		.selectOption("favorites");
	await page.locator(".library-list button").click();
	const inspector = page.getByRole("region", { name: "Selected metadata" });
	await expect(inspector).toContainText("USER_SUPPLIED");
	await expect(inspector).toContainText("No onchain metadata observed");
	await expect(inspector).toContainText("No chain observation");
	await expect(inspector).not.toContainText("ONCHAIN_DISPLAY_ONLY");
	expect(
		await page.evaluate((key) => localStorage.getItem(key), storageKey),
	).toBe(saved);
	await page.getByLabel("Local display alias").fill("migrated local pointer");
	await page.getByRole("button", { name: "Save alias", exact: true }).click();
	await expect(page.locator(".library-list")).toContainText(
		"migrated local pointer",
	);
	const storage = await page.evaluate(
		(key) => ({
			current: JSON.parse(localStorage.getItem(key) ?? "{}"),
			backup: localStorage.getItem(`${key}-1.0.0-backup`),
		}),
		storageKey,
	);
	expect(storage.current.schemaVersion).toBe("m45-library-1.1.0");
	expect(storage.backup).toBe(saved);
});

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
