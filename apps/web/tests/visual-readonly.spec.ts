import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import type { Execution } from "../src/model";
import { projectExecution } from "../src/visual/projection";

const samplePath = resolve(
	"../../docs/schema/m3/examples/half-adder.request.json",
);
const sample = async (): Promise<Execution> =>
	JSON.parse(await readFile(samplePath, "utf8"));

test("projection preserves exact recipe, every scalar mapping, order and stable destination identity", async () => {
	const r = await sample();
	const before = JSON.stringify(r);
	const graph = projectExecution(r);
	expect(graph).toEqual(projectExecution(JSON.parse(before)));
	expect(graph.nodes.map((n) => n.id)).toEqual([
		"candidate/external",
		...r.project.candidate.components.map(
			(c) => `candidate/component/${c.instanceId}`,
		),
		"candidate/outputs",
	]);
	const widths = new Map<string | null, number>([
		[null, r.project.candidate.nIn],
	]);
	for (const c of r.project.candidate.components)
		widths.set(
			c.instanceId,
			c.kind === "NAND"
				? 1
				: (r.project.sources.find((s) => s.alias === c.sourceAlias)?.nOut ?? 0),
		);
	for (const n of graph.nodes) {
		expect(n.locator).toMatch(/^project.candidate/);
		expect(n.inputs.map((p) => p.id)).toEqual(
			n.inputs.map((_, i) => `in:${i}`),
		);
		expect(n.outputs.map((p) => p.id)).toEqual(
			n.outputs.map((_, i) => `out:${i}`),
		);
		for (const p of [...n.inputs, ...n.outputs]) {
			const path = p.locator.split("#")[0];
			const parts = path.replace(/\[(\d+)\]/g, ".$1").split(".");
			let value: unknown = r;
			for (const part of parts)
				value = (value as Record<string, unknown>)[part];
			expect(value, p.locator).not.toBeUndefined();
		}
	}
	const expected = [
		...r.project.candidate.components.map((c, i) => ({
			target: `candidate/component/${c.instanceId}`,
			pins: c.inputs,
			locator: `project.candidate.components[${i}].inputs`,
		})),
		{
			target: "candidate/outputs",
			pins: r.project.candidate.outputs,
			locator: "project.candidate.outputs",
		},
	].flatMap(({ target, pins, locator }) =>
		pins.map((p, i) => ({
			id: `${target}/in/${i}`,
			source:
				p.component === null
					? "candidate/external"
					: `candidate/component/${p.component}`,
			sourceHandle: `out:${p.pin}`,
			target,
			targetHandle: `in:${i}`,
			locator: `${locator}[${i}]`,
		})),
	);
	expect(graph.edges).toEqual(expected);
	expect(JSON.stringify(r)).toBe(before);
});

test("projection handles zero-input multioutput REF and uint64 decimal IDs without precision loss", async () => {
	const r = await sample();
	const s = r.project.sources[0];
	s.nIn = 0;
	s.nOut = 2;
	s.identity.circuitId = "9007199254740993";
	const imported = r.imports.find((x) => x.manifestHash === s.manifestHash);
	if (!imported) throw Error("missing sample source");
	Object.assign(imported.manifest.root, {
		nIn: 0,
		nOut: 2,
		identity: structuredClone(s.identity),
	});
	r.project.candidate = {
		nIn: 0,
		components: [
			{
				kind: "REF",
				instanceId: "constantPair",
				sourceAlias: s.alias,
				inputs: [],
			},
		],
		outputs: [
			{ component: "constantPair", pin: 1 },
			{ component: "constantPair", pin: 0 },
		],
	};
	const g = projectExecution(r);
	expect(g.nodes[0].outputs).toEqual([]);
	expect(g.nodes[1].outputs.map((p) => p.index)).toEqual([0, 1]);
	expect(g.nodes[1].source?.identity.circuitId).toBe("9007199254740993");
	expect(g.edges.map((e) => e.sourceHandle)).toEqual(["out:1", "out:0"]);
});

for (const attack of [
	"null",
	"kind",
	"forward",
	"negative",
	"arity",
	"stateful",
	"binding",
	"duplicate",
	"huge",
	"missing",
]) {
	test(`projection refuses ${attack} input without mutating it`, async () => {
		const r = await sample();
		const c = r.project.candidate.components[0];
		if (attack === "kind") Object.assign(c, { kind: "LATCH" });
		if (attack === "forward")
			c.inputs[0] = {
				component: r.project.candidate.components[2].instanceId,
				pin: 0,
			};
		if (attack === "negative") c.inputs[0].pin = -1;
		if (attack === "arity") c.inputs = [];
		if (attack === "stateful")
			r.project.sources.forEach((s) => {
				s.nState = 1;
			});
		if (attack === "binding")
			r.imports[0].manifest.root.identity.circuitId = "99";
		if (attack === "duplicate")
			r.project.candidate.components[1].instanceId = c.instanceId;
		if (attack === "huge") r.project.candidate.nIn = 1e10;
		if (attack === "missing") Object.assign(r.project, { sources: null });
		const input = attack === "null" ? null : r;
		const before = JSON.stringify(input);
		expect(() => projectExecution(input)).toThrow(/Visual view unavailable/);
		expect(JSON.stringify(input)).toBe(before);
	});
}

test("real sample visual/advanced parity, all rendered connections, disabled mutation and zero additional network", async ({
	page,
}, info) => {
	const errors: string[] = [];
	page.on("pageerror", (e) => errors.push(e.message));
	await page.goto("/");
	await page.getByRole("button", { name: /^Open sample/ }).click();
	const compiledResponse = page.waitForResponse(
		(r) =>
			r.url().endsWith("/api/v1/compose") && r.request().method() === "POST",
	);
	await page
		.getByRole("button", { name: "Build netlist", exact: true })
		.click();
	await expect(page.getByText(/81 bytes · 8 expanded gates/)).toBeVisible();
	const compiledBefore = await (await compiledResponse).json();
	const before = await page.evaluate(() =>
		sessionStorage.getItem("flip-project"),
	);
	if (!before) throw Error("sample not stored");
	const expected = projectExecution(JSON.parse(before));
	const calls: string[] = [];
	page.on("request", (r) => calls.push(`${r.method()} ${r.url()}`));
	await page.getByRole("button", { name: "Visual", exact: true }).click();
	await expect(page.locator(".react-flow__node")).toHaveCount(
		expected.nodes.length,
	);
	await expect(page.locator(".react-flow__edge")).toHaveCount(
		expected.edges.length,
	);
	await page
		.locator("summary")
		.filter({ hasText: /^Exact connection mappings/ })
		.click();
	for (const e of expected.edges) {
		const row = page.locator(`[data-edge-id="${e.id}"]`);
		await expect(row).toContainText(`${e.source} / ${e.sourceHandle}`);
		await expect(row).toContainText(`${e.target} / ${e.targetHandle}`);
		await expect(row).toContainText(e.locator);
		await expect(
			page.locator(`.react-flow__edge[data-id="${e.id}"]`),
		).toHaveAttribute(
			"aria-label",
			`${e.source} ${e.sourceHandle} to ${e.target} ${e.targetHandle}, read-only`,
		);
	}
	await expect(
		page.getByRole("heading", { name: "EQUIVALENT", exact: true }),
	).toHaveCount(0);
	const handles = page.locator(".react-flow__handle");
	await expect(handles.first()).toHaveCSS("pointer-events", "none");
	await expect(page.locator(".react-flow__node.draggable")).toHaveCount(0);
	const node = page.locator(".react-flow__node").first();
	await node.focus();
	await page.keyboard.press("Delete");
	await page.keyboard.press("Backspace");
	await page.locator(".react-flow__edge").first().focus();
	await page.keyboard.press("Delete");
	await expect(page.locator(".react-flow__node")).toHaveCount(
		expected.nodes.length,
	);
	await expect(page.locator(".react-flow__edge")).toHaveCount(
		expected.edges.length,
	);
	await page.getByRole("button", { name: "Advanced", exact: true }).click();
	await expect(page.getByText(/81 bytes · 8 expanded gates/)).toBeVisible();
	await expect(
		page.getByLabel("Source for nand0 [0]", { exact: true }),
	).toHaveValue(JSON.stringify([null, 0]));
	await page.getByRole("button", { name: "Visual", exact: true }).click();
	await expect(page.locator(".react-flow__node")).toHaveCount(
		expected.nodes.length,
	);
	expect(
		await page.evaluate(() => sessionStorage.getItem("flip-project")),
	).toBe(before);
	expect(calls).toEqual([]);
	expect(errors).toEqual([]);
	const compiledAfterResponse = await page.request.post("/api/v1/compose", {
		data: JSON.parse(before),
	});
	expect(compiledAfterResponse.ok()).toBeTruthy();
	const compiledAfter = await compiledAfterResponse.json();
	expect(compiledAfter).toEqual(compiledBefore);
	await page.screenshot({
		path: info.outputPath("visual-desktop.png"),
		fullPage: true,
	});
	await info.attach("canonical-before-after", {
		body: JSON.stringify({
			before: JSON.parse(before),
			after: JSON.parse(
				(await page.evaluate(() => sessionStorage.getItem("flip-project"))) ??
					"null",
			),
			projection: expected,
			compiledBefore,
			compiledAfter,
		}),
		contentType: "application/json",
	});
});

test("keyboard pin inspector, zoom/pan/fit, responsive axe and StrictMode renderer", async ({
	page,
}, info) => {
	await page.goto("/");
	await page.getByRole("button", { name: /^Open sample/ }).click();
	await page.getByRole("button", { name: "Visual", exact: true }).click();
	const component = page.getByLabel("Inspect component", { exact: true });
	await component.focus();
	await page.keyboard.press("s");
	await page.keyboard.press("Enter");
	await component.selectOption("candidate/component/sum");
	await page.getByLabel("Inspect pin", { exact: true }).selectOption("in:1");
	await expect(
		page.getByRole("status").filter({ hasText: "Input pin 1" }),
	).toContainText("Source: external [1]");
	const pinButton = page.getByRole("button", {
		name: "sum input 0, width 1",
		exact: true,
	});
	await pinButton.focus();
	await page.keyboard.press("Enter");
	await expect(
		page.getByRole("status").filter({ hasText: "Input pin 0" }),
	).toBeVisible();
	const zoom = page.getByLabel("Canvas zoom", { exact: true });
	const initial = await zoom.textContent();
	await page.getByRole("button", { name: "Zoom in", exact: true }).click();
	await expect(zoom).not.toHaveText(initial ?? "");
	await page.getByRole("button", { name: "Zoom out", exact: true }).click();
	const viewport = page.locator(".react-flow__viewport");
	const transform = await viewport.getAttribute("style");
	const canvas = await page.getByTestId("visual-canvas").boundingBox();
	if (!canvas) throw Error("canvas missing");
	await page.mouse.move(canvas.x + 30, canvas.y + 30);
	await page.mouse.down();
	await page.mouse.move(canvas.x + 90, canvas.y + 70);
	await page.mouse.up();
	await expect(viewport).not.toHaveAttribute("style", transform ?? "");
	await page.getByRole("button", { name: "Fit circuit", exact: true }).click();
	expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
	for (const width of [390, 320]) {
		await page.setViewportSize({ width, height: 844 });
		expect(
			await page.evaluate(
				() => document.documentElement.scrollWidth <= innerWidth,
			),
		).toBeTruthy();
		await page.screenshot({
			path: info.outputPath(`visual-${width}.png`),
			fullPage: true,
		});
	}
	await page.emulateMedia({ reducedMotion: "reduce" });
	await expect(
		page.getByRole("button", { name: "Advanced", exact: true }),
	).toBeVisible();
});

test("unsupported visual recipe fails visibly while Advanced remains available", async ({
	page,
}) => {
	await page.route("**/api/v1/sample/half-adder", async (route) => {
		const response = await route.fetch();
		const r = await response.json();
		r.project.candidate.components[0].kind = "LATCH";
		await route.fulfill({ response, json: r });
	});
	await page.goto("/");
	await page.getByRole("button", { name: /^Open sample/ }).click();
	await page.getByRole("button", { name: "Visual", exact: true }).click();
	await expect(page.getByRole("alert")).toContainText(
		"unsupported component kind",
	);
	await expect(page.locator(".react-flow__node")).toHaveCount(0);
	await page.getByRole("button", { name: "Advanced", exact: true }).click();
	await expect(
		page.getByRole("button", { name: "Build netlist", exact: true }),
	).toBeVisible();
});
