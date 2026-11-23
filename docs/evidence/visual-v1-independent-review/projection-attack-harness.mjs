// Independent adversarial projection harness. Read-only: mutates in-memory copies only.
// Run from repository root:
//   node -e "const e=require('./apps/web/node_modules/esbuild');e.buildSync({entryPoints:['apps/web/src/visual/projection.ts'],bundle:true,platform:'node',format:'esm',outfile:'docs/evidence/visual-v1-independent-review/projection.bundle.mjs'})"
//   node docs/evidence/visual-v1-independent-review/projection-attack-harness.mjs
import { readFile, writeFile } from "node:fs/promises";
import { projectExecution } from "./projection.bundle.mjs";

const sample = JSON.parse(
	await readFile("docs/schema/m3/examples/half-adder.request.json", "utf8"),
);
const clone = (value) => structuredClone(value);
const results = [];
let failures = 0;

function record(id, expectation, mutation, extra) {
	let input = clone(sample);
	if (mutation) {
		const replaced = mutation(input);
		if (replaced !== undefined) input = replaced;
	}
	const before = JSON.stringify(input);
	let outcome = "ACCEPT";
	let detail = "";
	try {
		const graph = projectExecution(input);
		detail = `${graph.nodes.length} nodes / ${graph.edges.length} edges`;
		if (extra) {
			try {
				extra(graph, input);
			} catch (error) {
				outcome = "ASSERTION_FAILED";
				detail = String(error?.message ?? error);
			}
		}
	} catch (error) {
		outcome = "REJECT";
		detail = String(error?.message ?? error);
	}
	const immutable = JSON.stringify(input) === before;
	const ok =
		(expectation === "ACCEPT" && outcome === "ACCEPT") ||
		(expectation === "REJECT" && outcome === "REJECT" && detail.includes("Visual view unavailable")) ||
		(expectation === "ASSERTION_FAILED" && outcome === "ASSERTION_FAILED");
	if (!ok || !immutable) failures++;
	results.push({
		id,
		expectation,
		outcome,
		detail,
		inputUnchanged: immutable,
		status: ok && immutable ? "OK" : "FAIL",
	});
}

const d = (r) => r.project.candidate;

// --- Structural / canonical identity cases ---------------------------------
record("baseline-real-sample", "ACCEPT", undefined, (g, r) => {
	if (g.nodes.length !== d(r).components.length + 2)
		throw Error("node count mismatch");
	if (g.edges.length !== d(r).components.flatMap((c) => c.inputs).length + d(r).outputs.length)
		throw Error("edge count mismatch");
	const ids = g.edges.map((e) => e.id);
	if (new Set(ids).size !== ids.length) throw Error("edge ID alias");
	for (const e of g.edges) {
		if (!g.nodes.some((n) => n.id === e.source && n.outputs.some((p) => p.id === e.sourceHandle)))
			throw Error(`dangling source ${e.id}`);
		if (!g.nodes.some((n) => n.id === e.target && n.inputs.some((p) => p.id === e.targetHandle)))
			throw Error(`dangling target ${e.id}`);
	}
	if (g.version !== "flip-visual-adapter-1.0.0") throw Error("adapter version");
});
record("empty-components-no-outputs", "REJECT", (r) => {
	d(r).components = [];
	d(r).outputs = [];
});
record("empty-components-with-external-output", "ACCEPT", (r) => {
	d(r).components = [];
	d(r).outputs = [{ component: null, pin: 0 }];
});
record("zero-inputs", "ACCEPT", (r) => {
	d(r).nIn = 0;
	d(r).components = [
		{ kind: "REF", instanceId: "zeroIn", sourceAlias: r.project.sources[0].alias, inputs: [] },
	];
	r.project.sources[0].nIn = 0;
	const imp = r.imports.find((x) => x.manifestHash === r.project.sources[0].manifestHash);
	Object.assign(imp.manifest.root, { nIn: 0, identity: structuredClone(r.project.sources[0].identity) });
	d(r).outputs = [{ component: "zeroIn", pin: 0 }];
});
record("duplicate-component-id", "REJECT", (r) => {
	d(r).components[1].instanceId = d(r).components[0].instanceId;
});
record("instance-id-with-slash", "REJECT", (r) => {
	d(r).components[0].instanceId = "a/b";
});
record("instance-id-65-chars", "REJECT", (r) => {
	d(r).components[0].instanceId = "a".repeat(65);
});
record("instance-id-leading-digit", "REJECT", (r) => {
	d(r).components[0].instanceId = "1bad";
});
record("nand-one-input", "REJECT", (r) => {
	d(r).components[0].inputs = [{ component: null, pin: 0 }];
});
record("nand-three-inputs", "REJECT", (r) => {
	d(r).components[0].inputs.push({ component: null, pin: 0 });
});
record("pin-out-of-range", "REJECT", (r) => {
	d(r).outputs[0].pin = 99;
});
record("pin-negative", "REJECT", (r) => {
	d(r).components[0].inputs[0].pin = -1;
});
record("pin-fractional", "REJECT", (r) => {
	d(r).components[0].inputs[0].pin = 0.5;
});
record("pin-string-zero", "REJECT", (r) => {
	d(r).components[0].inputs[0].pin = "0";
});
record("pin-nan", "REJECT", (r) => {
	d(r).components[0].inputs[0].pin = Number.NaN;
});
record("pin-infinity", "REJECT", (r) => {
	d(r).components[0].inputs[0].pin = Number.POSITIVE_INFINITY;
});
record("missing-input-pin", "REJECT", (r) => {
	d(r).components[0].inputs[0] = {};
});
record("forward-reference", "REJECT", (r) => {
	d(r).components[0].inputs[0] = { component: d(r).components[2].instanceId, pin: 0 };
});
record("self-reference", "REJECT", (r) => {
	d(r).components[1].inputs[0] = { component: d(r).components[1].instanceId, pin: 0 };
});
record("unknown-component-reference", "REJECT", (r) => {
	d(r).outputs[0].component = "notReal";
});
record("unsupported-kind-LATCH", "REJECT", (r) => {
	d(r).components[0].kind = "LATCH";
});
record("unsupported-kind-lowercase", "REJECT", (r) => {
	d(r).components[0].kind = "nand";
});
record("nIn-above-512", "REJECT", (r) => {
	d(r).nIn = 513;
});
record("nIn-negative", "REJECT", (r) => {
	d(r).nIn = -1;
});
record("nIn-fractional", "REJECT", (r) => {
	d(r).nIn = 2.5;
});
record("components-over-500", "REJECT", (r) => {
	const proto = d(r).components[0];
	d(r).components = Array.from({ length: 501 }, (_, i) => ({
		kind: "NAND",
		instanceId: `c${i}`,
		inputs: [{ component: null, pin: 0 }, { component: null, pin: 0 }],
	}));
	void proto;
});

// --- Source / import identity cases -----------------------------------------
record("stateful-source-nState-1", "REJECT", (r) => {
	r.project.sources[0].nState = 1;
});
record("stateful-manifest-root", "REJECT", (r) => {
	const imp = r.imports.find((x) => x.manifestHash === r.project.sources[0].manifestHash);
	imp.manifest.root.nState = 1;
});
record("wrong-chain", "REJECT", (r) => {
	r.project.chainId = 1;
});
record("source-chain-mismatch", "REJECT", (r) => {
	r.project.sources[0].identity.chainId = 1;
});
record("source-schema-mismatch", "REJECT", (r) => {
	r.project.sources[0].identity.schemaVersion = "2.0.0";
});
record("processor-uppercase-valid", "ACCEPT", (r) => {
	const s = r.project.sources[0];
	s.identity.processor = s.identity.processor.toUpperCase().replace("0X", "0x");
	const imp = r.imports.find((x) => x.manifestHash === s.manifestHash);
	imp.manifest.root.identity.processor = s.identity.processor;
});
record("processor-malformed", "REJECT", (r) => {
	r.project.sources[0].identity.processor = "0x1234";
});
record("circuit-id-leading-zero", "REJECT", (r) => {
	r.project.sources[0].identity.circuitId = "0001";
});
record("circuit-id-hex", "REJECT", (r) => {
	r.project.sources[0].identity.circuitId = "0x1";
});
record("circuit-id-2^64", "REJECT", (r) => {
	const s = r.project.sources[0];
	s.identity.circuitId = "18446744073709551616";
	const imp = r.imports.find((x) => x.manifestHash === s.manifestHash);
	imp.manifest.root.identity.circuitId = s.identity.circuitId;
});
record("circuit-id-2^64-minus-1", "ACCEPT", (r) => {
	const s = r.project.sources[0];
	s.identity.circuitId = "18446744073709551615";
	const imp = r.imports.find((x) => x.manifestHash === s.manifestHash);
	imp.manifest.root.identity.circuitId = s.identity.circuitId;
});
record("circuit-id-21-digits", "REJECT", (r) => {
	const s = r.project.sources[0];
	s.identity.circuitId = "1".repeat(21);
	const imp = r.imports.find((x) => x.manifestHash === s.manifestHash);
	imp.manifest.root.identity.circuitId = s.identity.circuitId;
});
record("uint53-plus-one-preserved", "ACCEPT", (r) => {
	const s = r.project.sources[0];
	s.identity.circuitId = "9007199254740993";
	const imp = r.imports.find((x) => x.manifestHash === s.manifestHash);
	imp.manifest.root.identity.circuitId = s.identity.circuitId;
}, (g) => {
	const displayed = g.nodes
		.map((n) => n.source)
		.filter(Boolean)
		.map((s) => s.identity.circuitId);
	if (!displayed.includes("9007199254740993")) throw Error("decimal precision lost");
});
record("manifest-root-mismatch", "REJECT", (r) => {
	const imp = r.imports.find((x) => x.manifestHash === r.project.sources[0].manifestHash);
	imp.manifest.root.identity.circuitId = "99";
});
record("manifest-nIn-mismatch", "REJECT", (r) => {
	const imp = r.imports.find((x) => x.manifestHash === r.project.sources[0].manifestHash);
	imp.manifest.root.nIn = 99;
});
record("duplicate-source-alias", "REJECT", (r) => {
	r.project.sources.push(structuredClone(r.project.sources[0]));
});
record("missing-source-alias", "REJECT", (r) => {
	d(r).components.find((c) => c.kind === "REF").sourceAlias = "absent";
});
record("empty-source-alias-malformed", "ACCEPT", (r) => {
	const s = r.project.sources[0];
	s.alias = "";
	for (const c of d(r).components) if (c.kind === "REF") c.sourceAlias = "";
}, (g, r) => {
	if (!g.nodes.some((n) => n.source?.alias === ""))
		throw Error("empty alias not displayed");
});
record("numeric-source-alias", "REJECT", (r) => {
	r.project.sources[0].alias = 42;
});
record("imports-not-array", "REJECT", (r) => {
	r.imports = null;
});
record("sources-not-array", "REJECT", (r) => {
	r.project.sources = null;
});
record("null-top-level", "REJECT", () => null);
// The replacement form above is used only for the explicit null case.


// --- Display-string / escaping cases ----------------------------------------
record("html-instance-id-rejected", "REJECT", (r) => {
	d(r).components[0].instanceId = "<img src=x onerror=alert(1)>";
});
record("unicode-instance-id-rejected", "REJECT", (r) => {
	d(r).components[0].instanceId = "café";
});
record("xss-alias-displayed-as-text", "ACCEPT", (r) => {
	r.project.sources[0].alias = "<script>alert(1)</script>";
	for (const c of d(r).components) if (c.kind === "REF") c.sourceAlias = r.project.sources[0].alias;
}, (g, r) => {
	if (typeof g.nodes.find((n) => n.source)?.source?.alias !== "string")
		throw Error("alias not string");
});

// --- Aliasing / detachment ---------------------------------------------------
record("source-and-identity-are-detached-copies", "ACCEPT", undefined, (g, input) => {
	const displayed = g.nodes.find((n) => n.source).source;
	const original = input.project.sources.find((s) => s.alias === displayed.alias);
	if (displayed === original) throw Error("displayed source aliases canonical source");
	if (displayed.identity === original.identity)
		throw Error("displayed identity aliases canonical identity");
	const before = JSON.stringify(input);
	displayed.alias = "tampered";
	displayed.identity.circuitId = "0";
	if (JSON.stringify(input) !== before) throw Error("projection mutation changed request");
});

record("derived-locators-resolve-existing-fields", "ACCEPT", undefined, (g, r) => {
	for (const n of g.nodes) {
		for (const p of [...n.inputs, ...n.outputs]) {
			const base = p.locator.split("#")[0];
			const parts = base.replace(/\[(\d+)\]/g, ".$1").split(".");
			let value = r;
			for (const part of parts) value = value?.[part];
			if (value === undefined) throw Error(`unresolvable locator ${p.locator}`);
		}
	}
});

record("pin-mappings-are-copies", "ACCEPT", undefined, (g, r) => {
	const node = g.nodes.find((n) => n.kind === "OUTPUTS");
	const projected = node.inputs[0].mapping;
	const canonical = r.project.candidate.outputs[0];
	if (projected === canonical) throw Error("pin mapping aliases canonical object");
});

const out = {
	generatedAt: new Date().toISOString(),
	prHead: "006050d7b8349dca3c263da2e3f1112617706541",
	adapterVersion: "flip-visual-adapter-1.0.0",
	total: results.length,
	failures,
	results,
};
await writeFile(
	"docs/evidence/visual-v1-independent-review/projection-attack-results.json",
	JSON.stringify(out, null, 2) + "\n",
);
console.log(`cases=${results.length} failures=${failures}`);
for (const r of results)
	if (r.status === "FAIL") console.log(`FAIL ${r.id}: expected=${r.expectation} got=${r.outcome} :: ${r.detail}`);
console.log(
	results.filter((r) => r.expectation === "ACCEPT").map((r) => `${r.id}=${r.outcome}`).join("\n"),
);
