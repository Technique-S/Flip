import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

async function openLibrary(page) {
	await page.goto("/");
	await page
		.getByRole("button", { name: "Circuit Library", exact: true })
		.click();
	await expect(
		page.getByRole("heading", { name: "Circuit Library", exact: true }),
	).toBeVisible();
	await expect(
		page.getByRole("status").filter({ hasText: "COMPLETE" }),
	).toBeVisible();
}

test("L01 discovery, sparse IDs, metadata, alias, favorite, import and recent persistence", async ({
	page,
}) => {
	await openLibrary(page);
	await page
		.getByRole("button", { name: "Discover processors", exact: true })
		.click();
	await expect(
		page.getByRole("status").filter({ hasText: "COMPLETE" }),
	).toBeVisible();
	await page
		.locator(".library-list button")
		.filter({ hasText: "Processor 0" })
		.click();
	await expect(
		page.getByRole("region", { name: "Selected metadata" }),
	).toContainText("Processor <display only>");
	await page
		.getByRole("button", { name: "Browse circuits", exact: true })
		.click();
	await expect(page.locator(".library-list button")).toHaveCount(3);
	await expect(
		page.getByRole("status").filter({ hasText: "COMPLETE_WITH_GAPS" }),
	).toBeVisible();
	await page
		.locator(".library-list button")
		.filter({ hasText: "Circuit #1" })
		.click();
	await page.getByRole("button", { name: "Add favorite", exact: true }).click();
	await expect(
		page.getByRole("button", { name: "Remove favorite" }),
	).toBeVisible();
	await page
		.getByLabel("Local display alias")
		.fill("<img src=x onerror=alert(1)>\u202eXOR");
	await page.getByRole("button", { name: "Save alias" }).click();
	await expect(page.locator(".library-list")).toContainText(
		"<img src=x onerror=alert(1)>XOR (local alias)",
	);
	await expect(page.locator(".library img")).toHaveCount(0);
	await page.getByLabel("Search library").fill("XOR");
	await expect(page.locator(".library-list button")).toHaveCount(1);
	await page
		.getByRole("button", { name: "Revalidate circuit", exact: true })
		.click();
	await expect(
		page.getByRole("status").filter({ hasText: "COMPLETE" }),
	).toBeVisible();
	await expect(
		page.getByRole("region", { name: "Selected metadata" }),
	).toContainText("Netlist hash");
	await page.screenshot({
		path: "../../.test-tmp/library-desktop.png",
		fullPage: true,
	});
	expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
	await page
		.getByRole("button", { name: "Import into composition", exact: true })
		.click();
	await expect(
		page.getByRole("heading", { name: "Composition", exact: true }),
	).toBeVisible();
	await expect(page.getByText("Library import snapshot")).toBeVisible();
	await page.reload();
	await page
		.getByRole("button", { name: "Circuit Library", exact: true })
		.click();
	await page
		.getByRole("combobox", { name: "Collection", exact: true })
		.selectOption("recents");
	await expect(page.locator(".library-list button")).toHaveCount(1);
	await page
		.getByRole("combobox", { name: "Collection", exact: true })
		.selectOption("favorites");
	await expect(page.locator(".library-list button")).toHaveCount(1);
});

test("L02 known-address fallback, stale favorites, bounded pagination and mobile", async ({
	page,
}) => {
	await page.setViewportSize({ width: 390, height: 844 });
	await openLibrary(page);
	await page.locator(".library-list button").first().click();
	await page.getByRole("button", { name: "Add favorite", exact: true }).click();
	await expect(
		page.getByRole("button", { name: "Remove favorite" }),
	).toBeVisible();
	await page.route("**/api/library/v1/execute", async (route) => {
		const body = route.request().postDataJSON();
		if (body.operation === "discover") {
			const response = await route.fetch();
			const result = await response.json();
			result.status = "UNKNOWN";
			result.errorCode = "RPC_UNAVAILABLE";
			for (const record of result.catalog.records) record.freshness = "STALE";
			await route.fulfill({ json: result });
		} else await route.continue();
	});
	await page
		.getByRole("button", { name: "Discover processors", exact: true })
		.click();
	await expect(page.getByText(/Enumeration unavailable/)).toBeVisible();
	await page
		.getByRole("combobox", { name: "Collection", exact: true })
		.selectOption("favorites");
	await expect(page.locator(".library-list button")).toHaveCount(1);
	await expect(page.locator(".library-list button")).toContainText("STALE");
	await page.locator(".library-list button").click();
	await page.screenshot({
		path: "../../.test-tmp/library-mobile.png",
		fullPage: true,
	});
	expect(
		await page.evaluate(
			() => document.documentElement.scrollWidth <= window.innerWidth,
		),
	).toBe(true);
	expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});

test("L03 resumes a pinned circuit page and skips missing IDs", async ({
	page,
}) => {
	await page.route("**/api/library/v1/execute", async (route) => {
		const body = route.request().postDataJSON();
		if (body.operation === "circuits") {
			const response = await route.fetch({
				postData: JSON.stringify({ ...body, limit: 2 }),
			});
			await route.fulfill({ response });
		} else await route.continue();
	});
	await openLibrary(page);
	await page.locator(".library-list button").first().click();
	await page
		.getByRole("button", { name: "Browse circuits", exact: true })
		.click();
	await expect(
		page.getByRole("status").filter({ hasText: "PARTIAL_BOUNDED" }),
	).toBeVisible();
	await expect(page.locator(".library-list button")).toHaveCount(2);
	await page
		.getByRole("button", { name: "Next discovery page", exact: true })
		.click();
	await expect(
		page.getByRole("status").filter({ hasText: "COMPLETE_WITH_GAPS" }),
	).toBeVisible();
	await expect(page.locator(".library-list button")).toHaveCount(3);
	await page
		.locator(".library-list button")
		.filter({ hasText: "Circuit #4" })
		.click();
	await expect(
		page.getByRole("button", { name: "Import into composition" }),
	).toBeDisabled();
});
