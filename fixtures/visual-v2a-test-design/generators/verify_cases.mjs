// Bounded consistency verifier for the prospective V2-A fixture set.
import { readFile, readdir } from "node:fs/promises";

const manifest = JSON.parse((await readFile("fixtures/visual-v2a-test-design/MANIFEST.json", "utf8")).toString());
const errors = [];
const cases = [];
for (const entry of manifest.files.filter((f) => f.path.includes("/cases/"))) {
	const raw = await readFile(entry.path);
	const c = JSON.parse(raw.toString("utf8"));
	cases.push(c);
	if (c.status !== "PROSPECTIVE_ACCEPTANCE") errors.push(`${c.id}: wrong status`);
	if (!["ACCEPT", "REJECT"].includes(c.expectedOutcome)) errors.push(`${c.id}: bad outcome`);
	if (!Array.isArray(c.editSequence)) errors.push(`${c.id}: no editSequence`);
	if (c.expectedOutcome === "REJECT" && !c.rejectionReason) errors.push(`${c.id}: reject without reason`);
	if (c.expectedOutcome === "ACCEPT" && c.expectedCanonicalState?.mode !== "CANDIDATE" && c.expectedCanonicalState?.mode !== "UNCHANGED") errors.push(`${c.id}: accept without expected state`);
	if (!c.regressionTest?.startsWith("tests/visual-edit.spec.ts::")) errors.push(`${c.id}: no regression pointer`);
	if (c.input?.base !== "docs/schema/m3/examples/half-adder.request.json") errors.push(`${c.id}: non-genuine base`);
	for (const b of c.semanticBlockers) if (!/^SB-\d+$/.test(b)) errors.push(`${c.id}: bad blocker ${b}`);
}
const ids = cases.map((c) => c.id);
if (new Set(ids).size !== ids.length) errors.push("duplicate case IDs");
const index = JSON.parse((await readFile("docs/evidence/visual-v2a-test-design/cases-index.json", "utf8")).toString());
if (index.totalCases !== cases.length) errors.push("index count mismatch");
if (index.focusAreas.length !== 15) errors.push(`focus area count ${index.focusAreas.length} != 15`);
for (const area of index.focusAreas) if (!cases.some((c) => c.focus === area)) errors.push(`no case for ${area}`);
for (const b of Object.keys(index.blockers)) if (!cases.some((c) => c.semanticBlockers.includes(b))) errors.push(`unused blocker ${b}`);
const files = (await readdir("fixtures/visual-v2a-test-design/cases")).filter((n) => n.endsWith(".json"));
if (files.length !== cases.length) errors.push("case file count mismatch");
console.log(JSON.stringify({ cases: cases.length, focusAreas: index.focusAreas.length, accept: cases.filter((c) => c.expectedOutcome === "ACCEPT").length, reject: cases.filter((c) => c.expectedOutcome === "REJECT").length, errors }, null, 2));
if (errors.length) process.exitCode = 1;
