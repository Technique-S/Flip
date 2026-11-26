// Independent boundary cases for the V1 security remediation alias/budget guards.
import { readFile, writeFile } from "node:fs/promises";
import { projectExecution } from "./projection-rereview.bundle.mjs";

const sample = JSON.parse(await readFile("docs/schema/m3/examples/half-adder.request.json", "utf8"));
const results = [];
function run(id, expectation, mutate, match) {
	const r = structuredClone(sample);
	if (mutate) mutate(r);
	const before = JSON.stringify(r);
	let observed = "ACCEPT";
	let detail = "";
	try {
		const g = projectExecution(r);
		detail = `${g.nodes.length} nodes / ${g.edges.length} edges`;
	} catch (error) {
		observed = "REJECT";
		detail = String(error?.message ?? error);
	}
	const unchanged = JSON.stringify(r) === before;
	const expectedMatch = !match || match.test(detail);
	const ok = (expectation === "ACCEPT" ? observed === "ACCEPT" : observed === "REJECT" && expectedMatch) && unchanged;
	results.push({ id, expectation, observed, detail, inputUnchanged: unchanged, status: ok ? "OK" : "FAIL" });
}
const d = (r) => r.project.candidate;

for (const [id, alias, expectation] of [
	["alias-1-char", "a", "ACCEPT"],
	["alias-64-chars", "a".repeat(64), "ACCEPT"],
	["alias-65-chars", "a".repeat(65), "REJECT"],
	["alias-hyphen-underscore-digits", "a_b-c9", "ACCEPT"],
	["alias-leading-digit", "0abc", "REJECT"],
	["alias-dot", "a.b", "REJECT"],
	["alias-space", "a b", "REJECT"],
	["alias-empty", "", "REJECT"],
	["alias-xss", "<script>alert(1)</script>", "REJECT"],
]) {
	run(id, expectation, (r) => {
		const old = r.project.sources[0].alias;
		r.project.sources[0].alias = alias;
		for (const c of d(r).components) if (c.sourceAlias === old) c.sourceAlias = alias;
	}, /invalid source alias/);
}
run("ref-used-alias-malformed", "REJECT", (r) => {
	for (const c of d(r).components) if (c.kind === "REF") c.sourceAlias = "bad.alias";
}, /invalid REF source alias/);

run("edges-exactly-1000", "ACCEPT", (r) => {
	d(r).components = Array.from({ length: 499 }, (_, i) => ({
		kind: "NAND", instanceId: `part${i}`,
		inputs: [{ component: null, pin: 0 }, { component: null, pin: 1 }],
	}));
	d(r).outputs = [
		{ component: "part0", pin: 0 },
		{ component: "part1", pin: 0 },
	];
});
run("edges-1001-rejected-early", "REJECT", (r) => {
	d(r).components = Array.from({ length: 500 }, (_, i) => ({
		kind: "NAND", instanceId: `part${i}`,
		inputs: [{ component: null, pin: 0 }, { component: null, pin: 1 }],
	}));
}, /connection budget exceeded before allocation/);
run("pins-over-4096-rejected-early", "REJECT", (r) => {
	const s = r.project.sources[0];
	s.nIn = 0;
	s.nOut = 255;
	const imp = r.imports.find((x) => x.manifestHash === s.manifestHash);
	Object.assign(imp.manifest.root, { nIn: 0, nOut: 255, identity: structuredClone(s.identity) });
	d(r).nIn = 0;
	d(r).components = Array.from({ length: 17 }, (_, i) => ({
		kind: "REF", instanceId: `wide${i}`, sourceAlias: s.alias, inputs: [],
	}));
	d(r).outputs = [{ component: "wide0", pin: 0 }];
}, /visible pin budget exceeded before allocation/);

await writeFile(
	"docs/evidence/visual-v1-security-rereview/projection-boundary-results.json",
	JSON.stringify({ generatedAt: new Date().toISOString(), results }, null, 2) + "\n",
);
console.log(`cases=${results.length} failures=${results.filter((r) => r.status === "FAIL").length}`);
for (const r of results) console.log(`${r.status} ${r.id}: expected=${r.expectation} observed=${r.observed} :: ${r.detail}`);
