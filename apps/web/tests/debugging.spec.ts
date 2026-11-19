import { spawnSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const example = resolve(
	"../../docs/schema/m45-debugging/examples/swapped-prior.execution.json",
);
const request = resolve(
	"../../docs/schema/m45-debugging/examples/swapped-prior.request.json",
);
const python = resolve(
	process.platform === "win32"
		? "../../.venv/Scripts/python.exe"
		: "../../.venv/bin/python",
);

test("debugger replays paths, verifies a separate correction, applies and reverts with CLI parity", async ({
	page,
}, info) => {
	await page.goto("/");
	await page.getByLabel("Open project file").setInputFiles(example);
	await page.getByRole("button", { name: "Wiring Canary" }).click();
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "DIFFERENT", exact: true }),
	).toBeVisible();
	const debug = page.getByRole("region", {
		name: "Connection debugger",
		exact: true,
	});
	await debug.getByRole("button", { name: "Inspect connection paths" }).focus();
	await page.keyboard.press("Enter");
	await expect(
		debug.getByText("VERIFIED_DIFFERENCE · AMBIGUOUS_MULTIPLE_CAUSES", {
			exact: true,
		}),
	).toBeVisible();
	await expect(
		debug.getByText("Witness bound to these paths", { exact: true }),
	).toBeVisible();
	await expect(debug.locator(".debug-relevant").first()).toBeVisible();
	const audit = await new AxeBuilder({ page })
		.include(".debugger")
		.withTags(["wcag2a", "wcag2aa", "wcag21aa"])
		.analyze();
	expect(audit.violations).toEqual([]);
	await expect(debug.locator(".debug-witness .different")).toHaveCount(2);
	const pending = page.waitForEvent("download");
	await debug.getByRole("button", { name: "Download diagnostic JSON" }).click();
	const output = info.outputPath("diagnostic.json");
	await (await pending).saveAs(output);
	const cli = spawnSync(
		python,
		["-m", "flip_cli", "debug", "--request", request],
		{ encoding: "utf8" },
	);
	expect(cli.status, cli.stderr).toBe(1);
	expect(JSON.parse(await readFile(output, "utf8"))).toEqual(
		JSON.parse(cli.stdout),
	);
	await debug.screenshot({ path: info.outputPath("debugger-desktop.png") });
	await debug
		.getByRole("radio", { name: "Test the declared reference mappings" })
		.check();
	await debug.getByRole("button", { name: "Verify proposed revision" }).click();
	await expect(
		debug.getByText(/VERIFIED_CORRECTION · EXACT_STATELESS/),
	).toBeVisible();
	// A proposal check does not modify the workspace's original comparison.
	await expect(
		page.getByRole("heading", { name: "DIFFERENT", exact: true }),
	).toBeVisible();
	await debug.getByRole("button", { name: "Apply candidate locally" }).click();
	await debug.getByRole("button", { name: "Compare applied revision" }).click();
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toBeVisible();
	await page
		.getByRole("navigation")
		.getByRole("button", { name: "Evidence", exact: true })
		.click();
	await page
		.getByRole("navigation")
		.getByRole("button", { name: "Wiring Canary", exact: true })
		.click();
	await debug.getByRole("button", { name: "Inspect connection paths" }).click();
	await expect(
		debug.getByText("NO_FAULT_ATTRIBUTION · NO_FAULT_ATTRIBUTION", {
			exact: true,
		}),
	).toBeVisible();
	await expect(debug.locator(".debug-relevant")).toHaveCount(0);
	await debug
		.getByRole("button", { name: "Revert candidate correction" })
		.click();
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "DIFFERENT", exact: true }),
	).toBeVisible();
});

test("debugger narrow viewport, reduced motion and production resource UNKNOWN", async ({
	page,
}, info) => {
	await page.setViewportSize({ width: 390, height: 844 });
	await page.emulateMedia({ reducedMotion: "reduce" });
	await page.goto("/");
	await page.getByLabel("Open project file").setInputFiles(example);
	await page.getByRole("button", { name: "Wiring Canary" }).click();
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "DIFFERENT", exact: true }),
	).toBeVisible();
	const debug = page.getByRole("region", {
		name: "Connection debugger",
		exact: true,
	});
	await debug.getByRole("button", { name: "Inspect connection paths" }).click();
	await expect(debug.locator(".debug-relevant").first()).toBeVisible();
	expect(
		await page.evaluate(
			() => document.documentElement.scrollWidth <= window.innerWidth,
		),
	).toBe(true);
	await debug.screenshot({ path: info.outputPath("debugger-mobile.png") });
	await page.route("**/api/v1/debug", async (route) => {
		const body = route.request().postDataJSON();
		body.budget = { maxNodes: 1 };
		await route.continue({ postData: JSON.stringify(body) });
	});
	await debug.getByRole("button", { name: "Inspect connection paths" }).click();
	await expect(
		debug.getByText("UNKNOWN · UNKNOWN_NO_ATTRIBUTION", { exact: true }),
	).toBeVisible();
	await expect(
		debug.getByText("RESOURCE_LIMIT", { exact: true }),
	).toBeVisible();
	await expect(debug.locator(".debug-relevant")).toHaveCount(0);
	await expect(
		debug.getByRole("button", { name: "Apply candidate locally" }),
	).toHaveCount(0);
});

test("debugger discards an in-flight result when the project mapping changes", async ({
	page,
}) => {
	await page.goto("/");
	await page.getByLabel("Open project file").setInputFiles(example);
	await page.getByRole("button", { name: "Wiring Canary" }).click();
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "DIFFERENT", exact: true }),
	).toBeVisible();
	let release: () => void = () => {};
	const wait = new Promise<void>((resolve) => {
		release = resolve;
	});
	let finished: () => void = () => {};
	const done = new Promise<void>((resolve) => {
		finished = resolve;
	});
	await page.route("**/api/v1/debug", async (route) => {
		const response = await route.fetch();
		await wait;
		await route.fulfill({ response });
		finished();
	});
	const debug = page.getByRole("region", {
		name: "Connection debugger",
		exact: true,
	});
	await debug.getByRole("button", { name: "Inspect connection paths" }).click();
	await page.getByRole("button", { name: /Pin mapping ·/ }).click();
	await page.getByLabel("outputMap 0", { exact: true }).selectOption("1");
	release();
	await done;
	await expect(
		debug.getByRole("button", { name: "Inspect connection paths" }),
	).toBeDisabled();
	await expect(
		debug.getByRole("button", { name: "Apply candidate locally" }),
	).toHaveCount(0);
	await expect(debug.locator(".debug-relevant")).toHaveCount(0);
});
