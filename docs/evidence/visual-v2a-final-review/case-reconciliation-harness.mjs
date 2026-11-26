// Independent reconciliation of the 56 prospective cases against the actual V2-A command layer.
// Executes the real bundled proposeNand/history functions from the PR head. No production writes.
import { readFile, writeFile } from "node:fs/promises";
import { readdir } from "node:fs/promises";
import { proposeNand, openHistory, commitHistory, moveHistory, removalProblem } from "./commands.bundle.mjs";

const sample = JSON.parse(await readFile("docs/schema/m3/examples/half-adder.request.json", "utf8"));
const dir = process.env.CASE_DIR ?? "fixtures/visual-v2a-test-design/cases";
const files = (await readdir(dir)).filter((f) => f.endsWith(".json")).sort();
const key = (r) => JSON.stringify(r);
const pin = (p) => (p && typeof p === "object" && "component" in p && "pin" in p ? { component: p.component, pin: p.pin } : p);

function patchRequest(inputPatch) {
	const patch = inputPatch.length === 2 && Array.isArray(inputPatch[0])
		? [inputPatch]
		: inputPatch.length > 2
			? Array.from({ length: inputPatch.length / 2 }, (_, i) => [inputPatch[2 * i], inputPatch[2 * i + 1]])
			: [];
	const r = structuredClone(sample);
	for (const pair of patch) {
		const [path, value] = pair;
		if (!Array.isArray(path)) throw Error(`non-array patch path: ${JSON.stringify(path)}`);
		let node = r;
		for (const p of path.slice(0, -1)) node = node[p];
		node[path.at(-1)] = value;
	}
	return r;
}
const supported = new Set([
	"ADD_COMPONENT", "REMOVE_COMPONENT", "UNDO", "REDO", "CANCEL_DRAFT",
]);
const records = [];
for (const file of files) {
	const c = JSON.parse((await readFile(`${dir}/${file}`, "utf8")).toString());
	let present = patchRequest(c.input.patch);
	let history = openHistory(present);
	let rejected = null;
	let unsupportedOp = null;
	const applied = [];
	for (const op of c.editSequence) {
		if (rejected || unsupportedOp) break;
		try {
			if (op.op === "ADD_COMPONENT") {
				if (op.kind === "NAND") {
					const next = proposeNand(present, { type: "AddNand", instanceId: op.instanceId, inputs: op.inputs.map(pin) });
					history = commitHistory(history, next);
					present = next;
				} else {
					rejected = `unsupported component kind ${op.kind}`;
				}
			} else if (op.op === "REMOVE_COMPONENT") {
				const next = proposeNand(present, { type: "RemoveNand", instanceId: op.instanceId });
				history = commitHistory(history, next);
				present = next;
			} else if (op.op === "UNDO") {
				history = moveHistory(history, "Undo"); present = history.present;
			} else if (op.op === "REDO") {
				history = moveHistory(history, "Redo"); present = history.present;
			} else if (op.op === "CANCEL_DRAFT") {
				// Draft cancellation has no pure-layer representation; no canonical change.
			} else {
				unsupportedOp = op.op;
			}
			applied.push(op.op);
		} catch (e) {
			rejected = e instanceof Error ? e.message : String(e);
		}
	}
	const expected = c.expectedCanonicalState;
	let stateMatch = null;
	if (expected.mode === "UNCHANGED") stateMatch = key(present) === key(patchRequest(c.input.patch));
	else if (expected.mode === "CANDIDATE") stateMatch = key(present.project.candidate) === key(expected.candidate);
	let classification;
	let reason;
	if (unsupportedOp) {
		classification = c.expectedOutcome === "REJECT" ? "CONTRACT_MISMATCH" : "NOT_EXECUTED";
		reason = `op ${unsupportedOp} is not a V2-A command; governing source: handoff command table lines 17-23`;
	} else if (c.expectedOutcome === "REJECT") {
		classification = rejected ? "PASS" : "FAIL";
		reason = rejected ?? "expected rejection but command was accepted";
	} else {
		classification = rejected ? "FAIL" : stateMatch ? "PASS" : "FAIL";
		reason = rejected ?? (stateMatch ? "exact canonical state match" : "canonical state differs");
	}
	records.push({
		id: c.id,
		focus: c.focus,
		originalOutcome: c.expectedOutcome,
		originalReason: c.rejectionReason,
		actualOutcome: rejected ? "REJECT" : "ACCEPT",
		actualRejection: rejected,
		stateMatch,
		classification,
		reason,
		applied,
		blockers: c.semanticBlockers,
		governingSource: "P7_V2_A_HANDOFF.md:17-31 command contract; P7_V2_A_DESIGN_CHECKPOINT.md:40-51 proposed private layer; authorization explicit inputs",
	});
}
const summary = {};
for (const r of records) summary[r.classification] = (summary[r.classification] ?? 0) + 1;
const out = {
	generatedAt: new Date().toISOString(),
	prHead: "036c7a99f26d87dd4366762c8c3c059ac8e3d65d",
	implementationCommit: "b23d3dcf8f98e9b95cd0bc8ca8fbf612045e1daa",
	total: records.length,
	summary,
	records,
};
await writeFile("docs/evidence/visual-v2a-final-review/case-reconciliation.json", JSON.stringify(out, null, 2) + "\n");
console.log(JSON.stringify({ total: records.length, summary }, null, 2));
for (const r of records.filter((r) => r.classification === "FAIL")) console.log(`FAIL ${r.id}: ${r.reason}`);
