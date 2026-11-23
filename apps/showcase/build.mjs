import assert from "node:assert/strict";
import { readFile, writeFile, mkdir, readdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join, relative } from "node:path";
import { loadRecording, sha, text, code, table } from "./lib.mjs";

const root = new URL("./", import.meta.url);
const out = fileURLToPath(new URL("dist/", root));
const recording = await loadRecording(new URL("recordings/", root));
const { manifest, receipt, logs, project, evidence, data } = recording;
const compare = logs.get("compare").output;
const diagnostic = logs.get("inspect").output;
const witness = compare.report.verification.witness;
const composition = data.get("composition.json");
const steps = [
	["index.html", "Sample", "Open the recorded sample"],
	["composition.html", "Composition", "Inspect the recorded composition"],
	["difference.html", "DIFFERENT", "Read the reproduced difference"],
	["connections.html", "Connections", "Follow the relevant connections"],
	["correction.html", "Correction", "Inspect the verified correction"],
	["revision.html", "Portable revision", "Inspect the portable revision"],
	["evidence.html", "Evidence", "Take the evidence to a local verifier"],
];
const result = (heading, body) =>
	`<section class="result" aria-label="Recorded result"><h2>${text(heading)}</h2>${body}</section>`;
const details = (title, body) =>
	`<details><summary>${text(title)}</summary>${body}</details>`;
const pretty = (value) => `<pre>${text(JSON.stringify(value, null, 2))}</pre>`;
const download = (name, label) =>
	`<a href="artifacts/${name}">${text(label)}</a>`;
const inputRows = project.tests[0].vectors.map((v) => [
	v.inputs.bits,
	v.outputs.bits,
]);
const compositionRows = ["reference", "candidate"].map((side) => {
	const c = composition[side];
	return [
		side === "reference"
			? "Declared half-adder reference"
			: "Recorded different candidate",
		(c.netlist.length - 2) / 2,
		c.manifest.expandedGates,
		c.manifest.freshness,
	];
});
const correction = logs.get("verify").output;
const before = receipt.originalExecutionRequest.project.candidate.outputs;
const after = project.executionRequest.project.candidate.outputs;
const contents = [
	`<p class="lead">One half-adder reference, a wiring change, and a separately verified revision. Explore selected snapshots from an actual bounded workflow.</p>
   <p><strong>This is a curated recording, not a video or a live workbench.</strong> Opening a step only displays saved information. Nothing is imported from a network or computed in this browser.</p>
   ${result("Recorded half-adder reference", `<p>The declared reference uses archived TapeOut circuit snapshots on X Layer, chain 196. Its corrected composition is 81 bytes with 8 expanded gates.</p>`)}
   ${table(
			"Source identities in the recorded execution",
			["Source", "Processor", "Circuit ID"],
			receipt.originalExecutionRequest.imports.map((i) => [
				i.alias ?? i.identity?.circuitId ?? "Pinned dependency",
				i.manifest.root.identity.processor,
				i.manifest.root.identity.circuitId,
			]),
		)}
   <p>The next step places the reference beside the actual recorded candidate. This example has different wiring and 12 candidate gates; it is not presented as a simple output swap.</p>
   ${details("Where these snapshots came from", `<p>${text(manifest.source)}</p><p>Runtime ${code(manifest.acceptedRuntimeSha)}. Audit ${code(manifest.r2AuditSha)}.</p><p>${text(manifest.storyNote)}</p>`)}`,
	`<p class="lead">These are saved compiler outputs for the exact reference and candidate requests in the recording. This page does not compile a circuit.</p>
   ${table("Recorded composition", ["Design", "TAP-02 bytes", "Expanded gates", "Freshness"], compositionRows)}
   ${table("Declared half-adder vectors — pin 0 first", ["Input bits", "Expected output bits"], inputRows)}
   <p>Four declared vectors illustrate the interface; they are not a universal equivalence proof. The next step shows the actual trusted comparison and its replayed counterexample.</p>
   ${details("Reference and candidate netlist identities", `<p>Reference ${code(composition.reference.candidateIdentity.netlistHash)}</p><p>Candidate ${code(composition.candidate.candidateIdentity.netlistHash)}</p>`)}
   ${details("Recorded candidate TAP-02 bytes", `<pre>${text(composition.candidate.netlist)}</pre>`)}`,
	`<p class="lead">A completed behavioral difference, preserved from the native verifier. This is not a live proof response.</p>
   ${result("Recorded verdict: DIFFERENT", `<p>${text(witness.replay)}. The trusted evaluator reproduced different outputs for this input.</p><p>Input bits, pin 0 first: ${code(witness.inputs.bits)}. Scope: ${text(compare.coverage)}; HISTORICAL.</p>`)}
   ${table(
			"Recorded counterexample",
			["Mapped output pin", "Reference", "Candidate", "Observation"],
			Array.from(witness.referenceOutputs.bits, (v, i) => [
				i,
				v,
				witness.candidateOutputs.bits[i],
				v === witness.candidateOutputs.bits[i]
					? "Same output"
					: "Different output",
			]),
		)}
   <p>DIFFERENT is a result, not an instruction to retry. A live timeout would be UNKNOWN. No such computation occurs in this showcase.</p>
   ${details("Recorded comparison context", pretty({ recordedAt: compare.verifiedAt, solver: compare.report.verification.solverBackend, outcome: compare.report.verification.solverOutcome, engineHash: compare.engineHash, requestHash: compare.requestHash }))}`,
	`<p class="lead">Trace the saved witness to numeric connections. Relevance explains influence; it does not prove which wire is uniquely defective.</p>
   ${result("Recorded diagnostic: VERIFIED_DIFFERENCE", `<p>${text(diagnostic.attribution)}. Unique fault claim: ${text(diagnostic.uniqueFaultClaim)}.</p>`)}
   <p class="relevant">Showing ${Math.min(8, diagnostic.connections.filter((c) => c.classification === "RELEVANT_CONNECTION" && c.side === "candidate").length)} recorded candidate connections. The complete receipt contains ${diagnostic.connections.length} indexed connections.</p>
   ${table(
			"Relevant connections from the recorded diagnostic",
			["Connection", "Source signal", "Destination", "Component"],
			diagnostic.connections
				.filter(
					(c) =>
						c.classification === "RELEVANT_CONNECTION" &&
						c.side === "candidate",
				)
				.slice(0, 8)
				.map((c) => [
					c.connectionRef,
					c.sourceSignal,
					c.destination,
					c.instanceId ?? "Nested or generated",
				]),
		)}
   <p>The local workbench can inspect these paths. This display has no debugger backend and cannot diagnose a new project.</p>`,
	`<p class="lead">The recorded controller proposed a separate candidate, verified it against the declared local reference, then applied it locally. No original project was overwritten.</p>
   ${result("Recorded classification: VERIFIED_CORRECTION", `<p>Trusted comparison: ${text(correction.comparison.report.verification.verdict)} / ${text(correction.comparison.report.verification.solverOutcome)}. It is historical and reference-relative, not a claim of intended correctness.</p>`)}
   ${table(
			"Recorded workflow order",
			["Step", "Operation", "Recorded status"],
			receipt.logs.map((l) => [l.step, l.op, l.status]),
		)}
   ${details("Candidate output mappings before and after", pretty({ before, after }))}
   <p>The mismatch continuation was explicit. The correction passed separate verify and apply operations plus post-tests and a fresh export. This page cannot propose or apply edits.</p>`,
	`<p class="lead">The new Portable Project 1.1 revision links its parent and retains named tests. The original remains available in the recording.</p>
   ${table(
			"Recorded package",
			["Field", "Value"],
			[
				["Schema", project.schemaVersion],
				["Project", project.revision.projectId],
				["Revision", project.revision.sequence],
				["Parent", project.revision.parentHash],
				["Revision hash", project.revision.revisionHash],
				["Named test sets", project.tests.length],
				["Evidence references", project.evidenceRefs.length],
			],
		)}
   ${details("Ordered edit record", pretty(project.revision.editLog))}
   <p>Revision hashes establish local integrity, not authorship, current chain state or signing permission. This viewer does not select or modify a project.</p>
   <ul class="downloads"><li>${download("project.json", "Open the recorded Portable 1.1 revision (JSON)")}</li></ul>`,
	`<p class="lead">Inspect the saved evidence or save the exact files for a compatible local verifier. JSON links open local files; use your browser’s Save as command to retain a copy. Opening them does not run commands.</p>
   ${result("Recorded exported verdict: EQUIVALENT", `<p>HISTORICAL · ${text(evidence.comparison.coverage)}. Recorded at ${text(evidence.comparison.verifiedAt)}.</p><p>This page displays the saved result. It does not independently replay or certify it.</p>`)}
   <ul class="downloads">${[
			["evidence.json", "Recorded FLIP_EVIDENCE"],
			["receipt.json", "Complete recorded workflow receipt"],
			["project.json", "Recorded Portable 1.1 revision"],
			["replay.request.json", "Recorded package replay request"],
			["corrected.execution.json", "Corrected execution request"],
			["candidate.execution.json", "Original candidate execution request"],
			["composition.json", "Recorded compiler outputs"],
			["manifest.json", "Recording provenance and file checksums"],
		]
			.map(([name, label]) => `<li>${download(name, `${label} (JSON)`)}</li>`)
			.join("")}</ul>
   <p>For fresh local verification, use the supported source checkout and the downloaded corrected request/evidence with ${code("flip verify-bundle --project corrected.execution.json --bundle evidence.json")}. A different native engine can reject old evidence; preserve it and create new local evidence instead of overriding identity checks.</p>
   <p>${text(evidence.limitations)}</p>
   ${details("Integrity is not proof authority", `<p>File checksums detect byte changes relative to this bundle, not authorship or truth. The recorded artifacts were rechecked by the accepted native consumer during curation. This static build verifies only pinned input integrity.</p><p>Native content hash ${code(evidence.contentHash)}</p><p>Recording manifest SHA-256 ${code(sha(recording.manifestBytes))}</p><p><a href="CHECKSUMS.json">Open static package checksums (JSON)</a></p>`)}
   <h2>Publication is outside this showcase</h2><p>There is no publication control here. In the local workbench, publication intent terminates at STOP_AUTHORIZATION. This package contains no wallet, signer, RPC client, transaction path or permission grant.</p>`,
];
const CSP =
	"default-src 'none'; script-src 'none'; connect-src 'none'; style-src 'self'; img-src 'none'; font-src 'none'; object-src 'none'; frame-src 'none'; worker-src 'none'; media-src 'none'; base-uri 'none'; form-action 'none'";
const outputs = new Map();
for (let i = 0; i < steps.length; i++) {
	const [file, label, heading] = steps[i];
	const nav = steps
		.map(
			([name, title], j) =>
				`<li><a href="${name}"${j === i ? ' aria-current="page"' : ""}><span aria-hidden="true">${j + 1}</span>${text(title)}</a></li>`,
		)
		.join("");
	const prev = i
		? `<a class="action" href="${steps[i - 1][0]}">Previous: ${text(steps[i - 1][1])}</a>`
		: "<span></span>";
	const next =
		i < steps.length - 1
			? `<a class="action primary" href="${steps[i + 1][0]}">Next recorded step: ${text(steps[i + 1][1])}</a>`
			: '<a class="action" href="index.html">Start the recorded walkthrough again</a>';
	outputs.set(
		file,
		Buffer.from(`<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="${CSP}"><meta name="referrer" content="no-referrer"><title>${text(label)} — Flip recorded showcase</title><link rel="stylesheet" href="style.css"></head><body>
<a class="skip" href="#main">Skip to the recorded step</a>
<header class="mast"><a class="brand" href="index.html" aria-label="Flip recorded showcase start"><i aria-hidden="true"></i>Flip</a><p>Circuit workbench · static showcase</p><p class="network">Archived X Layer · chain 196</p></header>
<p class="scope"><strong>RECORDED · HISTORICAL</strong> — saved results, not live computation. No backend, native solver, wallet or RPC connection.</p>
<div class="layout"><nav aria-label="Recorded workflow"><p>Recorded walkthrough</p><ol>${nav}</ol></nav><main id="main" tabindex="-1"><h1>${text(heading)}</h1>${contents[i]}<div class="actions">${prev}${next}</div><section class="context" aria-label="Recording context"><p>Selected snapshots from an R2 regression recording, not a continuous screen recording. Native runtime: ${code(manifest.acceptedRuntimeSha)}.</p><p>Recorded comparisons: ${text(manifest.recordedDifferenceAt)} → ${text(manifest.recordedEquivalentAt)}. No current-chain or authorship claim.</p></section></main></div>
<footer>This showcase cannot run proofs or publish circuits. Open the supported local workbench for fresh computation. Rights and judge-access approval remain owner decisions.</footer>
</body></html>
`),
	);
}
outputs.set("style.css", await readFile(new URL("style.css", root)));
for (const [name, bytes] of recording.raw)
	outputs.set(`artifacts/${name}`, bytes);
outputs.set("artifacts/manifest.json", recording.manifestBytes);
const sources = {};
for (const name of ["build.mjs", "lib.mjs", "style.css"])
	sources[name] = sha(await readFile(new URL(name, root)));
outputs.set(
	"BUILD.json",
	Buffer.from(`${JSON.stringify({ format: "flip-static-build-1.0.0", recordingManifestSha256: sha(recording.manifestBytes), acceptedRuntimeSha: manifest.acceptedRuntimeSha, sourceHashes: sources, capabilities: { backend: false, nativeSolver: false, clientJavaScript: false, rpc: false, wallet: false, publication: false } }, null, 2)}
`),
);
outputs.set(
	"README.txt",
	Buffer.from(`Flip recorded static showcase. Open index.html; no server or network is required. HTML/CSS/JSON only. Recorded historical results, not live proof. No wallet/RPC/publication. No source license selected or native binary redistributed. Owner rights and hosting approval are still required before publication. CHECKSUMS.json covers every other distribution file.
`),
);
const checksums = Object.fromEntries(
	[...outputs]
		.sort(([a], [b]) => a.localeCompare(b))
		.map(([name, bytes]) => [
			name,
			{ bytes: bytes.length, sha256: sha(bytes) },
		]),
);
outputs.set(
	"CHECKSUMS.json",
	Buffer.from(`${JSON.stringify(checksums, null, 2)}
`),
);
async function files(dir) {
	let result = [];
	try {
		for (const entry of await readdir(dir, { withFileTypes: true })) {
			assert(!entry.isSymbolicLink(), "Symlinks are not distribution files");
			result = result.concat(
				entry.isDirectory()
					? await files(join(dir, entry.name))
					: [join(dir, entry.name)],
			);
		}
	} catch (e) {
		if (e.code !== "ENOENT") throw e;
	}
	return result;
}
for (const file of await files(out))
	assert(
		outputs.has(relative(out, file).replaceAll("\\", "/")),
		`Unexpected output file; choose a clean distribution directory: ${file}`,
	);
for (const [name, bytes] of outputs) {
	const target = join(out, name);
	if (process.argv.includes("--check"))
		assert.deepEqual(
			await readFile(target),
			bytes,
			`Static build drift: ${name}`,
		);
	else {
		await mkdir(join(target, ".."), { recursive: true });
		await writeFile(target, bytes);
	}
}
console.log(
	`${process.argv.includes("--check") ? "Checked" : "Built"} ${outputs.size} deterministic static files; no client JavaScript, backend, native proof or network.`,
);
