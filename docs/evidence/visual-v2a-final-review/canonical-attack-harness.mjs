// Independent adversarial probes of the real V2-A command layer at PR head.
import { readFile, writeFile } from "node:fs/promises";
import { proposeNand, checkInteractiveBudget, removalProblem, openHistory, commitHistory, moveHistory, requestKey } from "./commands.bundle.mjs";

const sample = JSON.parse(await readFile("docs/schema/m3/examples/half-adder.request.json", "utf8"));
const results = [];
const probe = (id, fn) => {
	try { results.push({ id, outcome: "ACCEPT", detail: fn() ?? "" }); }
	catch (e) { results.push({ id, outcome: "REJECT", detail: String(e?.message ?? e) }); }
};
const add = (r, instanceId, inputs) => proposeNand(r, { type: "AddNand", instanceId, inputs });
const ex = (n) => ({ component: null, pin: n });
const ref = (c, p) => ({ component: c, pin: p });

probe("duplicate-instance-id", () => add(sample, "carry", [ex(0), ex(1)]));
probe("unsupported-kind-LATCH", () => proposeNand(sample, { type: "AddNand", instanceId: "l1", inputs: [ex(0), ex(1)], kind: "LATCH" }));
probe("missing-second-input", () => add(sample, "g1", [ex(0)]));
probe("boolean-pin", () => add(sample, "g1", [ex(true), ex(1)]));
probe("negative-pin", () => add(sample, "g1", [ex(-1), ex(1)]));
probe("fractional-pin", () => add(sample, "g1", [ex(0.5), ex(1)]));
probe("out-of-range-pin-65536", () => add(sample, "g1", [ex(65536), ex(1)]));
probe("true-forward-reference", () => add(sample, "g1", [ref("future", 0), ex(1)]));
probe("invalid-source-component", () => add(sample, "g1", [ref("notReal", 0), ex(1)]));
probe("json-proto-extra-field", () => proposeNand(sample, JSON.parse('{"type":"AddNand","instanceId":"g1","inputs":[{"component":null,"pin":0},{"component":null,"pin":1}],"__proto__":{"polluted":true}}')));
probe("url-extra-field", () => proposeNand(sample, { type: "AddNand", instanceId: "g1", inputs: [ex(0), ex(1)], url: "https://attacker.invalid" }));
probe("bad-name-leading-digit", () => add(sample, "1bad", [ex(0), ex(1)]));
probe("bad-name-65-chars", () => add(sample, "a".repeat(65), [ex(0), ex(1)]));
probe("issue-insert-order", () => proposeNand(sample, { type: "InsertComponent", instanceId: "g1", index: 0, inputs: [ex(0), ex(1)] }));
probe("issue-output-remap", () => proposeNand(sample, { type: "SetOutput", index: 0, value: ex(1) }));
probe("issue-ref-add", () => proposeNand(sample, { type: "AddRef", instanceId: "r1", sourceAlias: "xor", inputs: [ex(0), ex(1)] }));
probe("remove-ref-component", () => proposeNand(sample, { type: "RemoveNand", instanceId: "nand0" }));
probe("remove-output-referenced-nand", () => proposeNand(sample, { type: "RemoveNand", instanceId: "carry" }));
probe("remove-unreferenced-nand", () => {
	const a = add(sample, "unused", [ex(0), ex(1)]);
	const b = proposeNand(a, { type: "RemoveNand", instanceId: "unused" });
	return requestKey(b) === requestKey(sample) ? "exact original restored" : "STATE MISMATCH";
});
probe("remove-downstream-referenced-nand", () => {
	const a = add(sample, "chain", [ref("carry", 0), ex(1)]);
	const b = add(a, "leaf", [ref("chain", 0), ex(1)]);
	const problem = removalProblem(b, "chain");
	if (!problem) return "REFERENCED REMOVAL ALLOWED";
	throw Error(problem);
});
probe("history-two-add-two-undo", () => {
	let h = openHistory(sample);
	const a = add(sample, "a1", [ex(0), ex(1)]); h = commitHistory(h, a);
	const b = add(a, "a2", [ex(0), ex(1)]); h = commitHistory(h, b);
	h = moveHistory(h, "Undo"); h = moveHistory(h, "Undo");
	if (requestKey(h.present) !== requestKey(sample)) return "STATE MISMATCH";
	h = moveHistory(h, "Redo"); h = moveHistory(h, "Redo");
	return requestKey(h.present) === requestKey(b) ? "exact snapshots restored" : "REDO MISMATCH";
});
probe("history-divergent-redo-invalidated", () => {
	let h = openHistory(sample);
	const a = add(sample, "d1", [ex(0), ex(1)]); h = commitHistory(h, a);
	h = moveHistory(h, "Undo");
	const c = add(h.present, "d2", [ex(1), ex(0)]); h = commitHistory(h, c);
	try { moveHistory(h, "Redo"); return "STALE REDO APPLIED"; }
	catch (e) { return `redo rejected: ${e.message}`; }
});
for (const n of [178, 179, 499]) {
	probe(`interactive-budget-${n}-nands`, () => {
		const r = structuredClone(sample);
		r.project.candidate.components = Array.from({ length: n }, (_, i) => ({ kind: "NAND", instanceId: `c${i}`, inputs: [ex(0), ex(1)] }));
		return checkInteractiveBudget(r), `budget accepted at ${n}`;
	});
}
probe("request-1MiB-limit", () => {
	const r = structuredClone(sample);
	r.imports[0].manifest.root.environment.beacon.address = "0x" + "a".repeat(40);
	r.project.projectId = "p".repeat(1048576);
	return checkInteractiveBudget(r), "size accepted";
});

await writeFile("docs/evidence/visual-v2a-final-review/canonical-attack-results.json", JSON.stringify({ generatedAt: new Date().toISOString(), prHead: "036c7a99f26d87dd4366762c8c3c059ac8e3d65d", results }, null, 2) + "\n");
console.log(`probes=${results.length}`);
for (const r of results) console.log(`${r.id}: ${r.outcome} :: ${r.detail}`);
