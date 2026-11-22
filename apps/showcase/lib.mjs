import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

export const manifestHash =
	"0d4161ac21ca4f94fefc2541979780bff0f365374662d41eb289d17147106029";
export const recordingNames = [
	"receipt.json",
	"project.json",
	"replay.request.json",
	"evidence.json",
	"candidate.execution.json",
	"corrected.execution.json",
	"composition.json",
];
export const sha = (data) => createHash("sha256").update(data).digest("hex");
export const text = (value) =>
	String(value ?? "Not recorded")
		.replaceAll("&", "&amp;")
		.replaceAll("<", "&lt;")
		.replaceAll(">", "&gt;")
		.replaceAll('"', "&quot;")
		.replaceAll("'", "&#39;");
export const code = (value) => `<code>${text(value)}</code>`;
export const table = (caption, headers, rows) =>
	`<div class="table-wrap"><table><caption>${text(caption)}</caption><thead><tr>${headers.map((h) => `<th scope="col">${text(h)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((v, i) => (i === 0 ? `<th scope="row">${text(v)}</th>` : `<td>${text(v)}</td>`)).join("")}</tr>`).join("")}</tbody></table></div>`;

export async function loadRecording(directory) {
	const manifestBytes = await readFile(new URL("manifest.json", directory));
	assert.equal(
		sha(manifestBytes),
		manifestHash,
		"Recording manifest differs from the reviewed build input",
	);
	const manifest = JSON.parse(manifestBytes);
	assert.equal(manifest.format, "flip-static-recording-1.0.0");
	assert.equal(
		manifest.acceptedRuntimeSha,
		"b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b",
	);
	assert.deepEqual(
		[...manifest.files.map((f) => f.name)].sort(),
		[...recordingNames].sort(),
	);
	const raw = new Map();
	const data = new Map();
	for (const f of manifest.files) {
		assert(recordingNames.includes(f.name));
		const bytes = await readFile(new URL(f.name, directory));
		assert.equal(bytes.length, f.bytes, `Wrong byte length: ${f.name}`);
		assert.equal(sha(bytes), f.sha256, `Wrong recording checksum: ${f.name}`);
		raw.set(f.name, bytes);
		data.set(f.name, JSON.parse(bytes));
	}
	const receipt = data.get("receipt.json");
	assert.equal(receipt.kind, "AGENT_WORKFLOW_RESULT");
	assert.equal(receipt.status, "COMPLETE");
	assert.deepEqual(
		receipt.logs.map((l) => l.step),
		[
			"pp_before0",
			"compare",
			"inspect",
			"propose",
			"verify",
			"apply",
			"pp_after0",
			"pp_export",
		],
	);
	const logs = new Map(receipt.logs.map((l) => [l.step, l]));
	assert.equal(
		logs.get("compare").output.report.verification.verdict,
		"DIFFERENT",
	);
	assert.equal(
		logs.get("compare").output.report.verification.witness.replay,
		"REF_BEAT_REPRODUCED",
	);
	assert.equal(logs.get("inspect").output.uniqueFaultClaim, false);
	for (const id of ["verify", "apply"])
		assert.equal(logs.get(id).output.classification, "VERIFIED_CORRECTION");
	const evidence = data.get("evidence.json");
	assert.equal(evidence.comparison.report.verification.verdict, "EQUIVALENT");
	assert.equal(evidence.comparison.report.integrity.freshness, "HISTORICAL");
	const project = data.get("project.json");
	assert.equal(project.schemaVersion, "flip-portable-project-1.1.0");
	assert.equal(
		project.revision.parentHash,
		project.ancestors.at(-1).revisionHash,
	);
	return {
		manifest,
		manifestBytes,
		raw,
		data,
		receipt,
		logs,
		project,
		evidence,
	};
}
