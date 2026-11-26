import { execFileSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { expect, test, type APIRequestContext } from "@playwright/test";
import type { Execution, Pin } from "../src/model";
import {
	checkInteractiveBudget,
	commitHistory,
	interactiveCapacity,
	moveHistory,
	openHistory,
	proposeNand,
	requestKey,
} from "../src/visual/commands";
import { projectExecution } from "../src/visual/projection";
import { proposeReplaceBinding } from "../src/visual/wiring";

const sample = async (): Promise<Execution> =>
	JSON.parse(
		await readFile(
			resolve("../../docs/schema/m3/examples/half-adder.request.json"),
			"utf8",
		),
	);
const pin = (component: string | null, n = 0): Pin => ({ component, pin: n });
const input = (instanceId: string, n = 0) => ({
	kind: "component-input",
	instanceId,
	pin: n,
});
const output = (n = 0) => ({ kind: "output", pin: n });
const replace = (target: unknown, source: unknown = pin(null)) => ({
	type: "ReplaceBinding",
	target,
	source,
});
const add = (p: unknown = pin(null)) => ({
	type: "AddNand",
	instanceId: "new1",
	inputs: [p, pin(null, 1)],
});
async function compile(request: APIRequestContext, r: Execution) {
	const res = await request.post("/api/v1/compose", { data: r });
	expect(res.ok(), await res.text()).toBeTruthy();
	return res.json();
}

test("B0 F1 preserves the exact source lookup, REF weighting and nullish fallback", async () => {
	const r = await sample();
	expect(interactiveCapacity(r)).toMatchObject({
		destinationPins: 8,
		sourcePins: 5,
		score: 40,
	});
	const before = requestKey(r);
	r.project.sources[0].nOut = 7;
	expect(interactiveCapacity(r).sourcePins).toBe(11);
	// Deliberately noncanonical metric-only metadata: preserve ?? rather than ||,
	// including the historical lookup even on a NAND with a sourceAlias.
	r.project.sources[0].nOut = 0;
	expect(interactiveCapacity(r).sourcePins).toBe(4);
	r.project.candidate.components[1].sourceAlias = "xor";
	expect(interactiveCapacity(r).sourcePins).toBe(3);
	r.project.candidate.components[2].sourceAlias = "missing";
	expect(interactiveCapacity(r).sourcePins).toBe(4);
	expect(requestKey(await sample())).toBe(before);
});

test("B0 F1 exact score and interface boundaries have cause-specific measured diagnostics", async () => {
	// Metric-only synthetic envelopes isolate arithmetic; these are not native fixtures.
	const r = await sample();
	r.project.candidate.nIn = 1;
	r.project.candidate.components = [
		{ kind: "REF", instanceId: "metric", sourceAlias: "xor", inputs: [] },
	];
	r.project.sources[0].nOut = 259;
	r.project.candidate.outputs = Array.from({ length: 250 }, () => pin(null));
	expect(interactiveCapacity(r).score).toBe(65000);
	checkInteractiveBudget(r);
	r.project.sources[0].nOut = 460;
	r.project.candidate.outputs = Array.from({ length: 141 }, () => pin(null));
	expect(interactiveCapacity(r).score).toBe(65001);
	expect(() => checkInteractiveBudget(r)).toThrow(
		/65,001.*65,000.*141 destination pins × 461 source pins/,
	);
	const boundary = await sample();
	boundary.project.candidate.components = [];
	boundary.project.candidate.outputs = [pin(null)];
	boundary.project.candidate.nIn = 255;
	checkInteractiveBudget(boundary);
	boundary.project.candidate.nIn = 256;
	expect(() => checkInteractiveBudget(boundary)).toThrow(
		/External input count 256.*255/,
	);
	const oversized = structuredClone(boundary);
	let serialized = 0;
	Object.defineProperty(oversized, "toJSON", {
		value() {
			serialized++;
			throw Error("Serialization must follow the table guards");
		},
	});
	expect(() => checkInteractiveBudget(oversized)).toThrow(
		/External input count 256.*255/,
	);
	expect(serialized).toBe(0);
	boundary.project.candidate.nIn = 1;
	boundary.project.candidate.outputs = Array.from({ length: 255 }, () =>
		pin(null),
	);
	checkInteractiveBudget(boundary);
	boundary.project.candidate.outputs.push(pin(null));
	expect(() => checkInteractiveBudget(boundary)).toThrow(
		/Output count 256.*255/,
	);
	const nativeBoundary = await sample();
	nativeBoundary.project.candidate.components = Array.from(
		{ length: 179 },
		(_, i) => ({
			kind: "NAND",
			instanceId: `part${i}`,
			inputs: [pin(null), pin(null, 1)],
		}),
	);
	expect(() => checkInteractiveBudget(nativeBoundary)).toThrow(
		/65,160.*360 destination pins × 181 source pins/,
	);
});

test("B0 F1 measures full UTF-8 bytes at one MiB and one byte over", async () => {
	const r = await sample();
	// Padding is explicitly a metric-only unknown field, never sent to native compose.
	const envelope = r as unknown as Record<string, unknown>;
	envelope.padding = "é";
	const remaining = 1048576 - interactiveCapacity(r).requestBytes;
	envelope.padding = `é${"x".repeat(remaining)}`;
	expect(interactiveCapacity(r).requestBytes).toBe(1048576);
	checkInteractiveBudget(r);
	envelope.padding = `${envelope.padding}x`;
	expect(() => checkInteractiveBudget(r)).toThrow(
		/1,048,577 bytes.*1,048,576 bytes/,
	);
	expect(() => checkInteractiveBudget(r)).toThrow(
		/accepted wiring is unchanged.*independent of native/,
	);
});

test("B0 F1 display allocation and history budgets remain independent", async () => {
	// UI-only synthetic interfaces, not claims of validated imported netlist bytes.
	const r = await sample();
	for (let i = 0; i < 2; i++) {
		r.project.sources[i].nIn = 0;
		r.imports[i].manifest.root.nIn = 0;
	}
	r.project.sources[0].nOut = 255;
	r.imports[0].manifest.root.nOut = 255;
	r.project.candidate.nIn = 1;
	r.project.candidate.components = Array.from({ length: 16 }, (_, i) => ({
		kind: "REF",
		instanceId: `block${i}`,
		sourceAlias: "xor",
		inputs: [],
	}));
	r.project.candidate.outputs = Array.from({ length: 15 }, () => pin(null));
	checkInteractiveBudget(r);
	expect(
		projectExecution(r).nodes.flatMap((n) => [...n.inputs, ...n.outputs]),
	).toHaveLength(4096);
	r.project.candidate.components.push({
		kind: "REF",
		instanceId: "extra",
		sourceAlias: "nand",
		inputs: [],
	});
	checkInteractiveBudget(r);
	expect(() => projectExecution(r)).toThrow(/visible pin budget/);
	const small = await sample();
	const h = openHistory(small),
		before = structuredClone(h);
	interactiveCapacity(small);
	checkInteractiveBudget(small);
	expect(h).toEqual(before);
	const many = await sample();
	many.project.candidate.outputs = [pin(null), pin(null, 1)];
	many.project.candidate.components = Array.from({ length: 499 }, (_, i) => ({
		kind: "NAND",
		instanceId: `part${i}`,
		inputs: [pin(null), pin(null)],
	}));
	expect(projectExecution(many).edges).toHaveLength(1000);
	many.project.candidate.outputs.push(pin(null));
	expect(() => projectExecution(many)).toThrow(/connection budget/);
	many.project.candidate.components.push(
		...many.project.candidate.components.slice(0, 2),
	);
	expect(() => projectExecution(many)).toThrow(/bounded visual profile/);
});

test("B0 F2 rejects hostile top-level records without invoking accessors", async () => {
	const r = await sample();
	let invoked = 0;
	const getter = () => {
		invoked++;
		throw Error("accessor must not execute");
	};
	const fields = ["type", "instanceId", "inputs"];
	const hostile: unknown[] = [
		null,
		[],
		"command",
		1,
		JSON.parse(
			'{"type":"AddNand","instanceId":"new1","inputs":[{"component":null,"pin":0},{"component":null,"pin":1}],"__proto__":{}}',
		),
		Object.assign(Object.create({ type: "AddNand" }), {
			instanceId: "new1",
			inputs: [pin(null), pin(null)],
		}),
	];
	for (const key of fields) {
		const c = add();
		Object.defineProperty(c, key, { get: getter, enumerable: true });
		hostile.push(c);
	}
	for (const extra of [
		"extra",
		"__proto__",
		"constructor",
		"prototype",
		Symbol("hidden"),
	]) {
		const c = add();
		Object.defineProperty(c, extra, { value: true, enumerable: false });
		hostile.push(c);
	}
	const hidden = add();
	Object.defineProperty(hidden, "instanceId", {
		value: "new1",
		enumerable: false,
	});
	hostile.push(
		hidden,
		new Proxy(add(), {
			ownKeys() {
				throw Error("trap");
			},
		}),
	);
	const revoked = Proxy.revocable(add(), {});
	revoked.revoke();
	hostile.push(revoked.proxy);
	for (const c of hostile) expect(() => proposeNand(r, c)).toThrow();
	const badRemove = { type: "RemoveNand", instanceId: "carry" };
	Object.defineProperty(badRemove, "instanceId", { get: getter });
	expect(() => proposeNand(r, badRemove)).toThrow();
	const badReplace = replace(output());
	Object.defineProperty(badReplace, "source", { get: getter });
	expect(() => proposeReplaceBinding(r, badReplace)).toThrow();
	expect(invoked).toBe(0);
	expect(r).toEqual(await sample());
});

test("B0 F2 nested pins reject inherited decoys, own extras, symbols and unsafe scalars", async () => {
	const r = await sample();
	let invoked = 0;
	const bad: unknown[] = [
		null,
		[],
		{},
		{ component: null },
		Object.assign(Object.create({ component: null, pin: 0 }), { a: 1, b: 2 }),
		JSON.parse('{"component":null,"pin":0,"__proto__":{}}'),
	];
	for (const value of [
		-1,
		true,
		"0",
		undefined,
		null,
		NaN,
		Infinity,
		-Infinity,
		Number.MAX_SAFE_INTEGER + 1,
		0n,
	])
		bad.push({ component: null, pin: value });
	for (const key of ["component", "pin"]) {
		const p = pin(null);
		Object.defineProperty(p, key, {
			get() {
				invoked++;
				throw Error("getter");
			},
			enumerable: true,
		});
		bad.push(p);
		const hidden = pin(null);
		Object.defineProperty(hidden, key, {
			value: key === "pin" ? 0 : null,
			enumerable: false,
		});
		bad.push(hidden);
		const setter = pin(null);
		Object.defineProperty(setter, key, {
			set() {
				invoked++;
			},
			enumerable: true,
		});
		bad.push(setter);
	}
	for (const key of [Symbol("extra"), "unknown", "__proto__"]) {
		const p = pin(null);
		Object.defineProperty(p, key, { value: 1 });
		bad.push(p);
	}
	for (const p of bad) {
		expect(() => proposeNand(r, add(p))).toThrow();
		expect(() =>
			proposeReplaceBinding(r, replace(input("carry"), p)),
		).toThrow();
	}
	expect(invoked).toBe(0);
});

test("B0 F2 dense NAND tuples and replacement destinations require own data fields", async () => {
	const r = await sample();
	let invoked = 0;
	const sparse = new Array(2);
	sparse[1] = pin(null);
	const accessor = [pin(null), pin(null)];
	Object.defineProperty(accessor, "0", {
		get() {
			invoked++;
			throw Error("getter");
		},
	});
	const extra = [pin(null), pin(null)];
	Object.defineProperty(extra, Symbol("extra"), { value: true });
	for (const inputs of [
		sparse,
		accessor,
		extra,
		[pin(null)],
		[pin(null), pin(null), pin(null)],
	])
		expect(() =>
			proposeNand(r, { type: "AddNand", instanceId: "new1", inputs }),
		).toThrow();
	const targetGetter = input("carry");
	Object.defineProperty(targetGetter, "kind", {
		get() {
			invoked++;
			throw Error("getter");
		},
	});
	for (const key of ["instanceId", "pin"]) {
		const target = input("carry");
		Object.defineProperty(target, key, {
			get() {
				invoked++;
				throw Error("getter");
			},
			enumerable: true,
		});
		expect(() => proposeReplaceBinding(r, replace(target))).toThrow();
	}
	for (const n of [
		-1,
		"0",
		undefined,
		null,
		NaN,
		Infinity,
		Number.MAX_SAFE_INTEGER + 1,
	])
		expect(() =>
			proposeReplaceBinding(r, replace({ ...output(), pin: n })),
		).toThrow();
	for (const t of [
		null,
		[],
		{ kind: "input", pin: 0 },
		Object.assign(Object.create({ kind: "output", pin: 0 }), { a: 1, b: 2 }),
		{ ...output(), instanceId: "extra" },
		targetGetter,
		{ ...input("carry"), pin: true },
		{ ...input("carry"), pin: 2 },
		input("missing"),
	])
		expect(() => proposeReplaceBinding(r, replace(t))).toThrow();
	expect(invoked).toBe(0);
});

test("B0 F2 valid own fields normalize prototypes and preserve canonical JavaScript-like names", async ({
	request,
}) => {
	let r = await sample();
	for (const instanceId of ["constructor", "prototype"]) {
		const p = {
			component: null,
			pin: 0,
			__proto__: { ignored: "prototype field" },
		};
		const c = Object.assign(Object.create(null), {
			type: "AddNand",
			instanceId,
			inputs: [p, Object.assign(Object.create(null), pin(null, 1))],
		});
		r = proposeNand(r, c);
		await compile(request, r);
	}
	const next = proposeReplaceBinding(r, {
		type: "ReplaceBinding",
		target: Object.assign(Object.create(null), output()),
		source: { component: "constructor", pin: 0, __proto__: null },
	});
	expect(next.project.candidate.outputs[0]).toEqual(pin("constructor"));
	await compile(request, next);
	expect(({} as Record<string, unknown>).ignored).toBeUndefined();
});

test("B0 native NAND, REF and output replacement changes exactly one slot", async ({
	request,
}, info) => {
	const r = await sample(),
		before = structuredClone(r),
		built = await compile(request, r);
	const observations = [];
	for (const [target, source] of [
		[input("carry"), pin(null)],
		[input("sum", 1), pin("carry")],
		[output(), pin(null)],
		[output(), pin("sum")],
	] as const) {
		const expected = structuredClone(r);
		if (target.kind === "output")
			expected.project.candidate.outputs[target.pin] = source;
		else {
			const component = expected.project.candidate.components.find(
				(c) => c.instanceId === target.instanceId,
			);
			if (!component) throw Error("Synthetic test destination missing");
			component.inputs[target.pin] = source;
		}
		const next = proposeReplaceBinding(r, replace(target, source));
		expect(next).not.toBe(r);
		expect(next).toEqual(expected);
		expect(r).toEqual(before);
		const result = await compile(request, next);
		expect(result.projectHash).not.toBe(built.projectHash);
		expect(result.manifest.dependencies).toEqual(built.manifest.dependencies);
		observations.push({
			target,
			source,
			projectHash: result.projectHash,
			netlistHash: result.manifest.netlistHash,
			expandedGates: result.manifest.expandedGates,
		});
	}
	await info.attach("b0-native-one-slot", {
		body: JSON.stringify(observations),
		contentType: "application/json",
	});
	// Native JSON acceptance does not remove aliases from the caller's in-memory
	// object. Both design sharing and input/output sharing must remain harmless.
	const shared = await sample();
	shared.project.candidate.outputs =
		shared.project.candidate.components[0].inputs;
	shared.project.referenceCandidate = shared.project.candidate;
	await compile(request, shared);
	const original = requestKey(shared);
	for (const [target, source] of [
		[input("nand0"), pin(null, 1)],
		[output(), pin("carry")],
	] as const) {
		const expected: Execution = JSON.parse(original);
		if (target.kind === "output")
			expected.project.candidate.outputs[0] = source;
		else expected.project.candidate.components[0].inputs[0] = source;
		const next = proposeReplaceBinding(shared, replace(target, source));
		expect(next).toEqual(expected);
		expect(next.project.referenceCandidate).toEqual(
			shared.project.referenceCandidate,
		);
		expect(requestKey(shared)).toBe(original);
		await compile(request, next);
	}
});

test("B0 real multi-output REF permits fan-out and rejects pin equal to width", async ({
	request,
}) => {
	const root = resolve("../..");
	const py = resolve(
		root,
		process.platform === "win32"
			? ".venv/Scripts/python.exe"
			: ".venv/bin/python",
	);
	// Reuse the existing synthetic FakeChain fixture generator in memory only.
	const code =
		"import sys;from pathlib import Path;sys.path.insert(0,str(Path.cwd()/'packages/flip-core/tests'));from test_m3_engine import half_adder;print(half_adder.__wrapped__().model_dump_json())";
	const r: Execution = JSON.parse(
		execFileSync(py, ["-c", code], { cwd: root, encoding: "utf8" }),
	);
	r.project.candidate.components = [
		{
			kind: "REF",
			instanceId: "pair",
			sourceAlias: "baseline",
			inputs: [pin(null), pin(null, 1)],
		},
		{ kind: "NAND", instanceId: "tail", inputs: [pin("pair"), pin("pair", 1)] },
	];
	r.project.candidate.outputs = [pin("pair"), pin("tail")];
	await compile(request, r);
	const next = proposeReplaceBinding(r, replace(input("tail"), pin("pair", 1)));
	await compile(request, next);
	expect(next.project.candidate.components[1].inputs).toEqual([
		pin("pair", 1),
		pin("pair", 1),
	]);
	const corrupt = structuredClone(r);
	expect(corrupt.imports[0].manifest.dependencies.length).toBeGreaterThan(0);
	corrupt.imports[0].manifest.dependencies[0].netlistHash = `0x${"00".repeat(32)}`;
	expect(
		(await request.post("/api/v1/compose", { data: corrupt })).ok(),
	).toBeFalsy();
	expect(() =>
		proposeReplaceBinding(r, replace(input("tail"), pin("pair", 2))),
	).toThrow(/out of range/);
	const bad = structuredClone(r);
	bad.project.candidate.components[1].inputs[0] = pin("pair", 2);
	expect(
		(await request.post("/api/v1/compose", { data: bad })).ok(),
	).toBeFalsy();
});

test("B0 invalid source direction, self/forward order and range fail closed locally and natively", async ({
	request,
}) => {
	const r = await sample(),
		before = requestKey(r);
	for (const source of [
		pin("carry"),
		pin("sum"),
		pin("missing"),
		pin("nand0", 1),
		pin(null, 2),
	]) {
		expect(() =>
			proposeReplaceBinding(r, replace(input("carry"), source)),
		).toThrow();
		const bad = structuredClone(r);
		bad.project.candidate.components[1].inputs[0] = source;
		expect(
			(await request.post("/api/v1/compose", { data: bad })).ok(),
		).toBeFalsy();
	}
	for (const c of [
		replace(output(), { kind: "input", component: null, pin: 0 }),
		replace({ kind: "external", pin: 0 }),
		replace(input("nand0"), pin("carry")),
		replace(output(2)),
	])
		expect(() => proposeReplaceBinding(r, c)).toThrow();
	expect(requestKey(r)).toBe(before);
});

test("B0 invalid identities, unsupported state and corrupted dependencies cannot establish a native-accepted base", async ({
	request,
}) => {
	const r = await sample();
	const cases: Execution[] = [];
	for (const mode of [
		"identity",
		"missing",
		"state",
		"latch",
		"bytes",
		"environment",
	]) {
		const bad = structuredClone(r);
		if (mode === "identity") bad.project.sources[0].identity.circuitId = "999";
		if (mode === "missing") bad.imports = [];
		if (mode === "state") bad.project.sources[0].nState = 1;
		if (mode === "latch")
			(
				bad.project.candidate.components[1] as unknown as Record<
					string,
					unknown
				>
			).kind = "LATCH";
		if (mode === "bytes")
			(
				bad.imports[0] as unknown as { circuits: { netlist: string }[] }
			).circuits[0].netlist = "0x00";
		if (mode === "environment")
			bad.imports[0].manifest.root.netlistHash = `0x${"00".repeat(32)}`;
		cases.push(bad);
	}
	for (const bad of cases) {
		const res = await request.post("/api/v1/compose", { data: bad });
		expect(res.ok()).toBeFalsy(); // No accepted base: do not call the pure proposal.
	}
	for (const bad of cases.slice(0, 4))
		expect(() => proposeReplaceBinding(bad, replace(output()))).toThrow();
	expect(r).toEqual(await sample());
});

test("B0 same binding is exact identity and leaves history, saved checkpoint and proof untouched", async ({
	request,
}) => {
	const r = await sample();
	await compile(request, r);
	const h = openHistory(r),
		before = structuredClone(h);
	const proofResponse = await request.post("/api/v1/compare", { data: r });
	expect(proofResponse.ok()).toBeTruthy();
	const proof = await proofResponse.json(),
		proofBefore = structuredClone(proof);
	expect(proof.report.verification.verdict).toBe("EQUIVALENT");
	for (const command of [
		replace(input("carry"), pin("nand0")),
		replace(output(1), pin("sum")),
	]) {
		const proposed = proposeReplaceBinding(h.present, command);
		expect(proposed).toBe(h.present); // Caller must skip POST/commit/invalidation.
		expect(h).toEqual(before);
		expect(proof).toEqual(proofBefore);
	}
});

test("B0 repeated proposals interoperate with native-validated complete-request history", async ({
	request,
}) => {
	const r = await sample();
	await compile(request, r);
	let h = openHistory(r);
	const first = proposeReplaceBinding(
		h.present,
		replace(input("carry"), pin(null)),
	);
	expect(
		proposeReplaceBinding(h.present, replace(input("carry"), pin(null))),
	).toEqual(first);
	await compile(request, first);
	h = commitHistory(h, first);
	const second = proposeReplaceBinding(h.present, replace(output(), pin(null)));
	await compile(request, second);
	h = commitHistory(h, second);
	h = moveHistory(h, "Undo");
	await compile(request, h.present);
	expect(h.present).toEqual(first);
	h = moveHistory(h, "Undo");
	await compile(request, h.present);
	expect(h.present).toEqual(r);
	h = moveHistory(h, "Redo");
	await compile(request, h.present);
	expect(h.present).toEqual(first);
	const divergent = proposeReplaceBinding(
		h.present,
		replace(output(1), pin(null, 1)),
	);
	await compile(request, divergent);
	h = commitHistory(h, divergent);
	expect(h.future).toEqual([]);
	expect(h.saved).toBe(requestKey(r));
});

test("B0 UI capacity does not substitute for native output-copy gate limits", async ({
	request,
}) => {
	const r = await sample();
	r.project.limits.gateCap = 8;
	await compile(request, r);
	const h = openHistory(r),
		before = structuredClone(h);
	const next = proposeReplaceBinding(r, replace(output(), pin(null)));
	expect(interactiveCapacity(next).score).toBe(interactiveCapacity(r).score);
	const rejected = await request.post("/api/v1/compose", { data: next });
	expect(rejected.ok()).toBeFalsy();
	expect((await rejected.json()).error.code).toBe("RESOURCE_LIMIT");
	expect(h).toEqual(before);
	expect(r).toEqual(before.present);
});

test("B0 pure commands initiate no fetch, and the live canvas remains read-only", async ({
	page,
}) => {
	const r = await sample(),
		saved = globalThis.fetch;
	let calls = 0;
	globalThis.fetch = async () => {
		calls++;
		throw Error("unexpected network");
	};
	try {
		interactiveCapacity(r);
		proposeNand(r, add());
		proposeReplaceBinding(r, replace(output(), pin(null)));
	} finally {
		globalThis.fetch = saved;
	}
	expect(calls).toBe(0);
	await page.goto("/");
	await page.getByRole("button", { name: /^Open sample/ }).click();
	await expect
		.poll(() => page.evaluate(() => sessionStorage.getItem("flip-project")))
		.not.toBeNull();
	const before = await page.evaluate(() =>
		sessionStorage.getItem("flip-project"),
	);
	const apiCalls: string[] = [];
	page.on("request", (req) => {
		if (req.url().includes("/api/")) apiCalls.push(req.url());
	});
	await page.getByRole("button", { name: "Visual", exact: true }).click();
	await expect(page.locator(".react-flow__handle").first()).toHaveCSS(
		"pointer-events",
		"none",
	);
	await expect(
		page.getByRole("button", {
			name: /Edit connections|Use as source|Apply connection/,
		}),
	).toHaveCount(0);
	await page.getByRole("button", { name: "Advanced", exact: true }).click();
	expect(
		await page.evaluate(() => sessionStorage.getItem("flip-project")),
	).toBe(before);
	expect(apiCalls).toEqual([]);
});

test("B0 unchanged accepted canonical project, netlist and manifest identities", async ({
	request,
}, info) => {
	const r = await sample(),
		before = requestKey(r),
		built = await compile(request, r);
	expect(built.projectHash).toBe(
		"0xff70814e174ae2dc841eef4a9e6367bb5318bccd069307c3afdce1adaa329959",
	);
	expect(built.manifest.netlistHash).toBe(
		"0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce",
	);
	expect(built.manifestHash).toBe(
		"0x10a2616767a30352158c32aae8cdb85b44cd7f5f04b168c462f41a8789b6f299",
	);
	proposeReplaceBinding(r, replace(output(), pin(null)));
	expect(requestKey(r)).toBe(before);
	expect(await compile(request, r)).toEqual(built);
	await info.attach("b0-canonical-identities", {
		body: JSON.stringify(built),
		contentType: "application/json",
	});
});
