import {
	test,
	expect,
} from "../../web/node_modules/@playwright/test/index.mjs";
import AxeBuilder from "../../web/node_modules/@axe-core/playwright/dist/index.mjs";
import { readFile, writeFile, mkdir, cp } from "node:fs/promises";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";
import { spawnSync } from "node:child_process";
import { text, table, sha } from "../lib.mjs";

const dist = resolve("apps/showcase/dist");
const pages = [
	"index.html",
	"composition.html",
	"difference.html",
	"connections.html",
	"correction.html",
	"revision.html",
	"evidence.html",
];
const file = (name) => pathToFileURL(join(dist, name)).href;

test("offline file walkthrough has no backend, network or sensitive capability calls", async ({
	context,
	page,
}) => {
	await context.setOffline(true);
	await context.addInitScript(() => {
		window.__showcaseCalls = [];
		const blocked = (name) => () => {
			window.__showcaseCalls.push(name);
			throw new Error(`Unexpected ${name}`);
		};
		window.fetch = blocked("fetch");
		window.XMLHttpRequest = blocked("XHR");
		window.WebSocket = blocked("WebSocket");
		window.EventSource = blocked("EventSource");
		navigator.sendBeacon = blocked("sendBeacon");
		window.ethereum = { request: blocked("wallet") };
		window.solana = { connect: blocked("wallet") };
	});
	const requests = [];
	const errors = [];
	page.on("request", (r) => requests.push(r.url()));
	page.on("pageerror", (e) => errors.push(e.message));
	await page.goto(file("index.html"));
	for (let i = 0; i < pages.length; i++) {
		await expect(page).toHaveURL(file(pages[i]));
		await expect(page.locator(".scope")).toContainText("RECORDED · HISTORICAL");
		await expect(page.locator("h1")).toHaveCount(1);
		await expect(
			page
				.getByRole("navigation", { name: "Recorded workflow" })
				.locator('[aria-current="page"]'),
		).toHaveCount(1);
		expect(
			await page
				.locator("script,form,input,iframe,object,embed,video,audio")
				.count(),
		).toBe(0);
		expect(await page.evaluate(() => window.__showcaseCalls)).toEqual([]);
		expect(
			await page
				.locator('meta[http-equiv="Content-Security-Policy"]')
				.getAttribute("content"),
		).toContain("script-src 'none'; connect-src 'none'");
		if (i < pages.length - 1)
			await page.getByRole("link", { name: /Next recorded step:/ }).click();
	}
	expect(errors).toEqual([]);
	expect(requests.length).toBeGreaterThan(0);
	expect(
		requests.every((url) => url.startsWith(pathToFileURL(dist).href + "/")),
	).toBe(true);
	expect(
		await page
			.locator('a[href^="http"],a[href^="javascript:"],a[href^="data:"]')
			.count(),
	).toBe(0);
});

test("recorded witness, non-unique paths, correction and revision match source artifacts", async ({
	page,
}) => {
	const receipt = JSON.parse(
		await readFile(join(dist, "artifacts/receipt.json"), "utf8"),
	);
	const project = JSON.parse(
		await readFile(join(dist, "artifacts/project.json"), "utf8"),
	);
	await page.goto(file("difference.html"));
	await expect(
		page.getByRole("heading", {
			name: "Recorded verdict: DIFFERENT",
			exact: true,
		}),
	).toBeVisible();
	await expect(page.getByRole("table")).toContainText("Different output");
	await expect(page.locator(".result")).toContainText("REF_BEAT_REPRODUCED");
	await page.goto(file("connections.html"));
	await expect(page.locator(".result")).toContainText(
		"AMBIGUOUS_MULTIPLE_CAUSES",
	);
	await expect(page.locator(".result")).toContainText("false");
	await page.goto(file("correction.html"));
	await expect(page.locator(".result")).toContainText("VERIFIED_CORRECTION");
	await expect(page.locator(".result")).toContainText("EQUIVALENT / UNSAT");
	await expect(page.getByRole("table")).toContainText(receipt.logs.at(-1).step);
	await page.goto(file("revision.html"));
	await expect(page.getByRole("table")).toContainText(
		project.revision.parentHash,
	);
	await expect(page.getByRole("table")).toContainText(
		project.revision.revisionHash,
	);
	await page.goto(file("composition.html"));
	await expect(
		page.getByRole("table", { name: "Recorded composition" }),
	).toContainText("109");
	await expect(
		page.getByRole("table", { name: "Recorded composition" }),
	).toContainText("81");
});

test("all seven file pages pass axe at desktop and 390px with reduced motion", async ({
	context,
	page,
}, info) => {
	await context.setOffline(true);
	await page.emulateMedia({ reducedMotion: "reduce" });
	for (const width of [1280, 390]) {
		await page.setViewportSize({ width, height: 900 });
		for (const name of pages) {
			await page.goto(file(name));
			expect(
				await page.evaluate(
					() => document.documentElement.scrollWidth <= innerWidth,
				),
			).toBe(true);
			expect(
				await page
					.locator("body")
					.evaluate((e) => getComputedStyle(e).fontFamily),
			).toContain("Segoe UI");
			expect(
				(
					await new AxeBuilder({ page })
						.withTags(["wcag2a", "wcag2aa", "wcag21aa"])
						.analyze()
				).violations,
			).toEqual([]);
			expect(
				await page
					.locator("main")
					.evaluate((e) => getComputedStyle(e).animationName),
			).toBe("none");
			if (name === "difference.html" || name === "revision.html")
				await page.screenshot({
					path: info.outputPath(`${name}-${width}.png`),
					fullPage: true,
				});
		}
	}
	await page.setViewportSize({ width: 320, height: 844 });
	await page.goto(file("evidence.html"));
	expect(
		await page.evaluate(
			() => document.documentElement.scrollWidth <= innerWidth,
		),
	).toBe(true);
});

test("keyboard skip, step links and native disclosure work with JavaScript disabled", async ({
	browser,
}) => {
	const context = await browser.newContext({
		javaScriptEnabled: false,
		offline: true,
	});
	const page = await context.newPage();
	await page.goto(file("index.html"));
	await page.keyboard.press("Tab");
	await expect(
		page.getByRole("link", { name: "Skip to the recorded step" }),
	).toBeFocused();
	await page.keyboard.press("Enter");
	await expect(page.locator("main")).toBeFocused();
	await page.locator("summary").focus();
	await page.keyboard.press("Enter");
	await expect(page.locator("details")).toHaveAttribute("open", "");
	const next = page.getByRole("link", { name: /Next recorded step:/ });
	await next.focus();
	await page.keyboard.press("Enter");
	await expect(page).toHaveURL(file("composition.html"));
	await context.close();
});

test("recorded project link opens the exact packaged JSON offline", async ({
	context,
	page,
}) => {
	await context.setOffline(true);
	await page.goto(file("revision.html"));
	const link = page.getByRole("link", {
		name: "Open the recorded Portable 1.1 revision (JSON)",
	});
	expect(await link.getAttribute("href")).toBe("artifacts/project.json");
	await link.click();
	await expect(page).toHaveURL(file("artifacts/project.json"));
	const displayed = JSON.parse(await page.locator("body").innerText());
	expect(displayed).toEqual(
		JSON.parse(await readFile(join(dist, "artifacts/project.json"), "utf8")),
	);
});

test("build integrity rejects tampering and escaping treats artifact strings only as text", async ({}, info) => {
	expect(text('<img src=x onerror="attack()">')).toBe(
		"&lt;img src=x onerror=&quot;attack()&quot;&gt;",
	);
	expect(
		table("<script>", ["<img>"], [["<svg onload=attack()>"]]),
	).not.toContain("<script>");
	const temp = info.outputPath("tampered-builder");
	await mkdir(temp, { recursive: true });
	for (const name of ["build.mjs", "lib.mjs", "style.css"])
		await cp(resolve("apps/showcase", name), join(temp, name));
	await cp(resolve("apps/showcase/recordings"), join(temp, "recordings"), {
		recursive: true,
	});
	await writeFile(
		join(temp, "recordings/project.json"),
		'{"forged":"<script>attack()</script>"}',
	);
	const rejected = spawnSync(process.execPath, [join(temp, "build.mjs")], {
		encoding: "utf8",
	});
	expect(rejected.status).not.toBe(0);
	expect(rejected.stderr).toMatch(/Wrong byte length|Wrong recording checksum/);
});
