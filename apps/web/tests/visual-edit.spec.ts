import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import type { Execution, Pin } from "../src/model";
import {
	checkInteractiveBudget,
	commitHistory,
	moveHistory,
	openHistory,
	proposeNand,
} from "../src/visual/commands";
const sample = async (): Promise<Execution> =>
	JSON.parse(
		await readFile(
			resolve("../../docs/schema/m3/examples/half-adder.request.json"),
			"utf8",
		),
	);
const pin = (component: string | null, n: number): Pin => ({
	component,
	pin: n,
});
const command = (id: string, inputs: Pin[] = [pin(null, 0), pin(null, 1)]) => ({
	type: "AddNand",
	instanceId: id,
	inputs,
});
const snapshot = async (page: Page) =>
	page.evaluate(() =>
		JSON.parse(sessionStorage.getItem("flip-project") ?? "null"),
	) as Promise<Execution>;
async function open(page: Page) {
	await page.goto("/");
	await page.getByRole("button", { name: /^Open sample/ }).click();
	await page.getByRole("button", { name: "Visual", exact: true }).click();
	await expect(page.locator(".react-flow__node")).toHaveCount(5);
}
async function form(
	page: Page,
	id: string,
	inputs = [pin(null, 0), pin(null, 1)],
) {
	await page.getByRole("button", { name: "Add NAND", exact: true }).click();
	await expect(page.getByLabel("NAND input 0 source")).toHaveValue("");
	await expect(page.getByLabel("NAND input 1 source")).toHaveValue("");
	await page.getByLabel("New NAND ID").fill(id);
	await page
		.getByLabel("NAND input 0 source")
		.selectOption(JSON.stringify(inputs[0]));
	await page
		.getByLabel("NAND input 1 source")
		.selectOption(JSON.stringify(inputs[1]));
}
async function add(page: Page, id: string, inputs?: Pin[]) {
	await form(page, id, inputs);
	await page.getByRole("button", { name: "Validate and add NAND" }).click();
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).toContainText(`Add NAND ${id} committed`);
}

test("V2-A pure proposals compile with the real canonical engine and preserve REF/output bindings", async ({
	request,
}) => {
	const r = await sample(),
		before = structuredClone(r);
	const a = proposeNand(r, command("spare"));
	expect(r).toEqual(before);
	expect(a.project.candidate.components.slice(0, -1)).toEqual(
		r.project.candidate.components,
	);
	expect(a.imports).toEqual(r.imports);
	expect(a.project.sources).toEqual(r.project.sources);
	expect(a.project.comparison).toEqual(r.project.comparison);
	expect(a.project.candidate.outputs).toEqual(r.project.candidate.outputs);
	const compile = async (data: Execution) => {
		const res = await request.post("/api/v1/compose", { data });
		expect(res.ok()).toBeTruthy();
		return res.json();
	};
	const b = await compile(r),
		c = await compile(a);
	expect(c.projectHash).not.toBe(b.projectHash);
	expect(c.manifest.dependencies).toEqual(b.manifest.dependencies);
	expect(proposeNand(r, command("spare"))).toEqual(a);
	const chain = proposeNand(
		a,
		command("tail", [pin("carry", 0), pin("sum", 0)]),
	);
	const removed = proposeNand(chain, {
		type: "RemoveNand",
		instanceId: "spare",
	});
	expect(removed.project.candidate.components.at(-1)).toEqual(
		chain.project.candidate.components.at(-1),
	);
	await compile(removed);
	const restored = proposeNand(a, { type: "RemoveNand", instanceId: "spare" });
	expect(restored).toEqual(r);
	expect(await compile(restored)).toEqual(b);
	const invalid = structuredClone(r);
	invalid.project.candidate.components.push({
		kind: "NAND",
		instanceId: "missing",
		inputs: [],
	});
	expect(
		(await request.post("/api/v1/compose", { data: invalid })).ok(),
	).toBeFalsy();
});

test("V2-A removal refuses both final-output and preceding-input references, including REF targets", async () => {
	const r = await sample();
	expect(() =>
		proposeNand(r, { type: "RemoveNand", instanceId: "carry" }),
	).toThrow(/candidate.outputs/);
	expect(() =>
		proposeNand(r, { type: "RemoveNand", instanceId: "nand0" }),
	).toThrow(/REF removal/);
	const a = proposeNand(
		proposeNand(r, command("spare")),
		command("consumer", [pin("spare", 0), pin(null, 0)]),
	);
	expect(() =>
		proposeNand(a, { type: "RemoveNand", instanceId: "spare" }),
	).toThrow(/components\[4\].inputs\[0\]/);
});
for (const [label, value] of Object.entries({
	null: null,
	kind: { ...command("new1"), type: "AddRef" },
	duplicate: command("carry"),
	badId: command("bad/name"),
	missingInput: command("new1", [pin(null, 0)]),
	nullInput: command("new1", [null as unknown as Pin, pin(null, 0)]),
	boolPin: command("new1", [
		pin(null, true as unknown as number),
		pin(null, 1),
	]),
	negative: command("new1", [pin(null, -1), pin(null, 1)]),
	forward: command("new1", [pin("new1", 0), pin(null, 1)]),
	extra: { ...command("new1"), outputs: [] },
	pinExtra: command("new1", [
		{ ...pin(null, 0), label: "fake" } as Pin,
		pin(null, 1),
	]),
}))
	test(`V2-A malformed command: ${label}`, async () => {
		const r = await sample(),
			before = structuredClone(r);
		expect(() => proposeNand(r, value)).toThrow();
		expect(r).toEqual(before);
	});

test("V2-A interactive boundary rejects the first over-budget edit while the native compiler accepts the baseline", async ({
	request,
}) => {
	const r = await sample();
	r.project.candidate.components = Array.from({ length: 178 }, (_, i) => ({
		kind: "NAND" as const,
		instanceId: `part${i}`,
		inputs: [pin(null, 0), pin(null, 1)],
	}));
	r.project.candidate.outputs = [pin("part176", 0), pin("part177", 0)];
	checkInteractiveBudget(r);
	expect(
		(await request.post("/api/v1/compose", { data: r })).ok(),
	).toBeTruthy();
	expect(() => proposeNand(r, command("overflow"))).toThrow(
		/interactive pin table budget/,
	);
});

test("V2-A bounded history restores exact full requests, diverges safely, and never mutates previous history", async () => {
	const r = await sample();
	let h = openHistory(r);
	const initial = structuredClone(h);
	const first = proposeNand(r, command("first"));
	h = commitHistory(h, first);
	const second = proposeNand(first, command("second"));
	h = commitHistory(h, second);
	expect(moveHistory(moveHistory(h, "Undo"), "Undo").present).toEqual(r);
	expect(
		moveHistory(moveHistory(moveHistory(h, "Undo"), "Undo"), "Redo").present,
	).toEqual(first);
	const divergent = commitHistory(
		moveHistory(h, "Undo"),
		proposeNand(first, command("different")),
	);
	expect(divergent.future).toEqual([]);
	expect(h.present).toEqual(second);
	expect(initial).toEqual(openHistory(r));
	for (let i = 0; i < 110; i++) {
		const next =
			i % 2
				? proposeNand(h.present, {
						type: "RemoveNand",
						instanceId: `temp${i - 1}`,
					})
				: proposeNand(h.present, command(`temp${i}`));
		h = commitHistory(h, next);
	}
	expect(h.past.length + h.future.length).toBeLessThanOrEqual(100);
	expect(h.evicted).toBeGreaterThan(0);
	expect(
		[h.present, ...h.past, ...h.future].reduce(
			(n, r) => n + new TextEncoder().encode(JSON.stringify(r)).length,
			new TextEncoder().encode(h.saved).length,
		),
	).toBeLessThanOrEqual(4 * 1048576);
	expect(h.present.imports).toEqual(r.imports);
	expect(h.present.project.comparison).toEqual(r.project.comparison);
});

test("V2-A explicit creation, inspector, Advanced parity, and only existing compose network calls", async ({
	page,
}, info) => {
	await open(page);
	const before = await snapshot(page);
	const calls: { method: string; url: string }[] = [];
	page.on("request", (r) => calls.push({ method: r.method(), url: r.url() }));
	await form(page, "editA");
	await page.screenshot({
		path: info.outputPath("v2a-explicit-input-form.png"),
		fullPage: true,
	});
	await page.getByRole("button", { name: "Validate and add NAND" }).click();
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).toContainText("Add NAND editA committed");
	await expect(page.locator(".react-flow__node")).toHaveCount(6);
	await expect(page.getByLabel("Inspect component")).toHaveValue(
		"candidate/component/editA",
	);
	await expect(page.getByLabel("Inspect component")).toBeFocused();
	const after = await snapshot(page);
	expect(after.imports).toEqual(before.imports);
	expect(after.project.sources).toEqual(before.project.sources);
	expect(after.project.candidate.outputs).toEqual(
		before.project.candidate.outputs,
	);
	await page.getByRole("button", { name: "Advanced", exact: true }).click();
	await expect(
		page.getByLabel("Source for editA [0]", { exact: true }),
	).toHaveValue("[null,0]");
	expect(await snapshot(page)).toEqual(after);
	await page.getByRole("button", { name: "Visual", exact: true }).click();
	expect(await snapshot(page)).toEqual(after);
	expect(calls.length).toBeGreaterThan(0);
	expect(
		calls.every(
			(c) =>
				c.method === "POST" && new URL(c.url).pathname === "/api/v1/compose",
		),
	).toBeTruthy();
	await page.screenshot({
		path: info.outputPath("v2a-desktop.png"),
		fullPage: true,
	});
	await page.setViewportSize({ width: 390, height: 844 });
	await page.getByRole("button", { name: "Fit circuit", exact: true }).click();
	expect(
		await page.evaluate(
			() => document.documentElement.scrollWidth <= innerWidth,
		),
	).toBeTruthy();
	await expect(
		page.getByRole("button", { name: "Add NAND", exact: true }),
	).toBeVisible();
	const axe = await new AxeBuilder({ page }).analyze();
	expect(axe.violations).toEqual([]);
	await page.screenshot({
		path: info.outputPath("v2a-narrow.png"),
		fullPage: true,
	});
});

test("V2-A multiple undo/redo and a divergent edit restore ordering and invalidate redo", async ({
	page,
}) => {
	await open(page);
	const before = await snapshot(page);
	await add(page, "first");
	const first = await snapshot(page);
	await add(page, "second", [pin("first", 0), pin(null, 1)]);
	const second = await snapshot(page);
	await page.getByRole("button", { name: "Undo edit" }).click();
	await expect.poll(() => snapshot(page)).toEqual(first);
	await page.getByRole("button", { name: "Undo edit" }).click();
	await expect.poll(() => snapshot(page)).toEqual(before);
	await page.getByRole("button", { name: "Redo edit" }).click();
	await expect.poll(() => snapshot(page)).toEqual(first);
	await page.getByRole("button", { name: "Redo edit" }).click();
	await expect.poll(() => snapshot(page)).toEqual(second);
	await page.getByRole("button", { name: "Undo edit" }).click();
	await expect.poll(() => snapshot(page)).toEqual(first);
	await add(page, "different");
	await expect(page.getByRole("button", { name: "Redo edit" })).toBeDisabled();
	expect(
		(await snapshot(page)).project.candidate.components.at(-1)?.instanceId,
	).toBe("different");
});

test("V2-A safe removal confirms an unused NAND and blocks a referenced output", async ({
	page,
}, info) => {
	await open(page);
	const before = await snapshot(page);
	await add(page, "unused");
	await page.getByRole("button", { name: "Remove this NAND" }).click();
	await expect(
		page.getByRole("heading", { name: "Remove unused?" }),
	).toBeFocused();
	await page.getByRole("button", { name: "Confirm remove NAND" }).click();
	await expect.poll(() => snapshot(page)).toEqual(before);
	await page
		.getByLabel("Inspect component")
		.selectOption("candidate/component/carry");
	await page.getByRole("button", { name: "Remove this NAND" }).click();
	await expect(
		page.getByRole("button", { name: "Confirm remove NAND" }),
	).toBeDisabled();
	await expect(page.getByRole("alert")).toContainText("candidate.outputs");
	expect(await snapshot(page)).toEqual(before);
	await page.screenshot({
		path: info.outputPath("v2a-blocked-removal.png"),
		fullPage: true,
	});
	await page.getByRole("button", { name: "Discard draft" }).click();
});

test("V2-A invalid local drafts never change or submit the accepted candidate", async ({
	page,
}) => {
	await open(page);
	const before = await snapshot(page);
	const calls: string[] = [];
	page.on("request", (r) => calls.push(r.url()));
	await page.getByRole("button", { name: "Add NAND", exact: true }).click();
	await page.getByRole("button", { name: "Validate and add NAND" }).click();
	await expect(page.getByLabel("New NAND ID")).toBeFocused();
	expect(await snapshot(page)).toEqual(before);
	await page.getByLabel("New NAND ID").fill("carry");
	await page
		.getByLabel("NAND input 0 source")
		.selectOption(JSON.stringify(pin(null, 0)));
	await page.getByRole("button", { name: "Validate and add NAND" }).click();
	await expect(page.getByRole("alert")).toContainText("both NAND input");
	await page
		.getByLabel("NAND input 1 source")
		.selectOption(JSON.stringify(pin(null, 1)));
	await page.getByRole("button", { name: "Validate and add NAND" }).click();
	await expect(page.getByRole("alert")).toContainText("already exists");
	expect(calls).toEqual([]);
	expect(await snapshot(page)).toEqual(before);
	await page.getByRole("button", { name: "Cancel NAND draft" }).click();
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).not.toContainText("Unsaved changes");
});

test("V2-A cancellation ignores a late real compiler response and rapid repeated submit is one transaction", async ({
	page,
}) => {
	await open(page);
	const before = await snapshot(page);
	let release = () => {};
	const barrier = new Promise<void>((r) => {
		release = r;
	});
	let finished = () => {};
	const done = new Promise<void>((r) => {
		finished = r;
	});
	await page.route("**/api/v1/compose", async (route) => {
		const response = await route.fetch();
		await barrier;
		try {
			await route.fulfill({ response });
		} catch {
		} finally {
			finished();
		}
	});
	await form(page, "cancelled");
	await page.getByRole("button", { name: "Validate and add NAND" }).click();
	await expect(
		page.getByRole("button", { name: "Cancel pending edit" }),
	).toBeVisible();
	expect(await snapshot(page)).toEqual(before);
	await page.getByRole("button", { name: "Cancel pending edit" }).click();
	release();
	await done;
	await page.unroute("**/api/v1/compose");
	expect(await snapshot(page)).toEqual(before);
	await form(page, "rapid");
	let posts = 0;
	page.on("request", (r) => {
		if (r.url().endsWith("/api/v1/compose")) posts++;
	});
	await page.evaluate(() => {
		const b = Array.from(document.querySelectorAll("button")).find(
			(b) => b.textContent === "Validate and add NAND",
		);
		b?.click();
		b?.click();
	});
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).toContainText("Add NAND rapid committed");
	expect(posts).toBe(1);
	expect(
		(await snapshot(page)).project.candidate.components.filter(
			(c) => c.instanceId === "rapid",
		),
	).toHaveLength(1);
	expect(
		(await snapshot(page)).project.candidate.components.some(
			(c) => c.instanceId === "cancelled",
		),
	).toBeFalsy();
});

test("V2-A old proof stays historical after undo, while export checkpoints determine dirty state", async ({
	page,
}) => {
	await open(page);
	await page.getByRole("button", { name: "Advanced", exact: true }).click();
	await page
		.getByRole("button", { name: "Wiring Canary", exact: true })
		.click();
	await page.getByRole("button", { name: "Run comparison" }).click();
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toBeVisible();
	await page.getByRole("button", { name: "Composition", exact: true }).click();
	await page.getByRole("button", { name: "Visual", exact: true }).click();
	await add(page, "historyGate");
	await page.getByRole("button", { name: "Undo edit" }).click();
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).toContainText("Undo committed");
	await page.getByRole("button", { name: "Evidence", exact: true }).click();
	await expect(page.getByText(/Historical comparisons \(1\)/)).toBeVisible();
	await expect(
		page.getByRole("button", { name: "Run and export evidence" }),
	).toBeDisabled();
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toHaveCount(0);
	await page.getByRole("button", { name: "Composition", exact: true }).click();
	await page.getByRole("button", { name: "Redo edit" }).click();
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).toContainText("Unsaved changes");
	await page.getByRole("button", { name: "Evidence", exact: true }).click();
	const download = page.waitForEvent("download");
	await page.getByRole("button", { name: "Save project", exact: true }).click();
	await download;
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).not.toContainText("Unsaved changes");
	await page.getByRole("button", { name: "Composition", exact: true }).click();
	await page.getByRole("button", { name: "Undo edit" }).click();
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).toContainText("Unsaved changes");
	await page.getByRole("button", { name: "Redo edit" }).click();
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).not.toContainText("Unsaved changes");
});

test("V2-A invalid Advanced candidate remains a draft and both modes retain the accepted request", async ({
	page,
}) => {
	await open(page);
	const before = await snapshot(page);
	await page.getByRole("button", { name: "Advanced", exact: true }).click();
	await page.getByLabel("External inputs", { exact: true }).fill("0");
	await expect(page.getByRole("alert")).toContainText("INVALID_INPUT");
	expect(await snapshot(page)).toEqual(before);
	await page.getByRole("button", { name: "Visual", exact: true }).click();
	await expect(
		page.getByRole("alert").filter({ hasText: "Visual view unavailable" }),
	).toBeVisible();
	await expect(
		page.getByRole("button", { name: "Add NAND", exact: true }),
	).toBeDisabled();
	await page.getByRole("button", { name: "Advanced", exact: true }).click();
	await page.getByLabel("External inputs", { exact: true }).fill("2");
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).not.toContainText("Local draft");
	expect(await snapshot(page)).toEqual(before);
});

test("V2-A keyboard-only add, selection and confirmed remove keep focus usable", async ({
	page,
}) => {
	await page.goto("/");
	await page.getByRole("button", { name: /^Open sample/ }).focus();
	await page.keyboard.press("Enter");
	await page.getByRole("button", { name: "Visual", exact: true }).focus();
	await page.keyboard.press("Enter");
	await page.getByRole("button", { name: "Add NAND", exact: true }).focus();
	await page.keyboard.press("Enter");
	await expect(page.getByLabel("New NAND ID")).toBeFocused();
	await page.keyboard.type("keyboardGate");
	await page.keyboard.press("Tab");
	await page.keyboard.press("ArrowDown");
	await expect(page.getByLabel("NAND input 0 source")).toHaveValue(
		JSON.stringify(pin(null, 0)),
	);
	await page.keyboard.press("Tab");
	await page.keyboard.press("ArrowDown");
	await page.keyboard.press("ArrowDown");
	await expect(page.getByLabel("NAND input 1 source")).toHaveValue(
		JSON.stringify(pin(null, 1)),
	);
	await page.keyboard.press("Tab");
	await expect(
		page.getByRole("button", { name: "Validate and add NAND" }),
	).toBeFocused();
	await page.keyboard.press("Enter");
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).toContainText("Add NAND keyboardGate committed");
	await expect(page.getByLabel("Inspect component")).toBeFocused();
	await page.keyboard.press("Tab");
	await expect(
		page.getByRole("button", { name: "Remove this NAND" }),
	).toBeFocused();
	await page.keyboard.press("Enter");
	await expect(
		page.getByRole("heading", { name: "Remove keyboardGate?" }),
	).toBeFocused();
	await page.keyboard.press("Tab");
	await page.keyboard.press("Enter");
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).toContainText("Remove NAND keyboardGate committed");
	await expect(page.locator(".react-flow__node")).toHaveCount(5);
});

test("V2-A failed native validation preserves the accepted candidate and the complete draft", async ({
	page,
}) => {
	await open(page);
	await page
		.getByRole("button", { name: "Wiring Canary", exact: true })
		.click();
	await page.getByLabel("Gate budget", { exact: true }).fill("8");
	await page.getByRole("button", { name: "Composition", exact: true }).click();
	await page.getByRole("button", { name: "Visual", exact: true }).click();
	const before = await snapshot(page);
	await form(page, "limited");
	await page.getByRole("button", { name: "Validate and add NAND" }).click();
	await expect(page.getByRole("alert")).toContainText("RESOURCE_LIMIT");
	expect(await snapshot(page)).toEqual(before);
	await expect(page.getByLabel("New NAND ID")).toHaveValue("limited");
	await page.getByRole("button", { name: "Cancel NAND draft" }).click();
	expect(await snapshot(page)).toEqual(before);
});

test("V2-A interrupted complete edit is recovered only after real authoritative revalidation", async ({
	page,
}) => {
	await open(page);
	let release = () => {};
	const barrier = new Promise<void>((r) => {
		release = r;
	});
	let fetched = () => {};
	const started = new Promise<void>((r) => {
		fetched = r;
	});
	let finished = () => {};
	const done = new Promise<void>((r) => {
		finished = r;
	});
	let first = true;
	await page.route("**/api/v1/compose", async (route) => {
		if (!first) {
			await route.continue();
			return;
		}
		first = false;
		try {
			const response = await route.fetch();
			fetched();
			await barrier;
			await route.fulfill({ response });
		} catch {
		} finally {
			finished();
		}
	});
	await form(page, "recoveredGate");
	await page.getByRole("button", { name: "Validate and add NAND" }).click();
	await started;
	const original = await snapshot(page);
	expect(
		original.project.candidate.components.some(
			(c) => c.instanceId === "recoveredGate",
		),
	).toBeFalsy();
	await page.reload();
	release();
	await done;
	await expect(
		page.getByText("Project restored from this browser session.", {
			exact: true,
		}),
	).toBeVisible();
	await expect
		.poll(
			async () =>
				(await snapshot(page)).project.candidate.components.filter(
					(c) => c.instanceId === "recoveredGate",
				).length,
		)
		.toBe(1);
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).toContainText("Unsaved changes");
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).toContainText("Recovered edit committed");
	await page.reload();
	await expect(
		page.getByText("Project restored from this browser session.", {
			exact: true,
		}),
	).toBeVisible();
	await expect(
		page.getByRole("status", { name: "Editing status" }),
	).toContainText("Unsaved changes");
});

test("V2-A explicit workspace reset clears private edit recovery and export checkpoint data", async ({
	page,
}) => {
	await open(page);
	await add(page, "resetGate");
	expect(
		await page.evaluate(() => sessionStorage.getItem("flip-edit-checkpoint")),
	).not.toBeNull();
	await page
		.getByRole("button", { name: "Reset workspace", exact: true })
		.click();
	await page
		.getByRole("button", { name: "Confirm reset", exact: true })
		.click();
	await expect(
		page.getByRole("button", { name: /^Open sample/ }),
	).toBeVisible();
	expect(
		await page.evaluate(() =>
			[
				"flip-project",
				"flip-edit-draft",
				"flip-edit-checkpoint",
				"flip-portable",
			].map((k) => sessionStorage.getItem(k)),
		),
	).toEqual([null, null, null, null]);
	await page.getByRole("button", { name: /^Open sample/ }).click();
	await page.getByRole("button", { name: "Evidence", exact: true }).click();
	await expect(page.getByText(/Historical comparisons \(/)).toHaveCount(0);
});
