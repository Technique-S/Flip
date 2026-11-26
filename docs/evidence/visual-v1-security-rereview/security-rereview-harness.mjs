// Independent P7-V1 security re-review harness. Writes only to temporary scratch copies.
// Run from repository root: node docs/evidence/visual-v1-security-rereview/security-rereview-harness.mjs
import { cp, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { execFileSync, spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { resolve, dirname, basename, join, relative } from "node:path";
import { sha } from "../../../apps/showcase/lib.mjs";

const repository = process.cwd();
const inventoryPath = "docs/release/M45_R3_ASSET_INVENTORY.json";
const trustPath = "docs/release/V1_RELEASE_TRUST.json";
const inventory = JSON.parse(await readFile(inventoryPath, "utf8"));
const gitDir = execFileSync("git", ["rev-parse", "--absolute-git-dir"], { encoding: "utf8" }).trim();
const workflow = await readFile(".github/workflows/m1-contracts.yml", "utf8");
const bootstrapCode = workflow.match(/node --input-type=module <<'JS'\n([\s\S]*?)\n          JS/)[1].replace(/^          /gm, "");
let currentBootstrapCode = bootstrapCode;
const results = [];

async function isolated(mode, mutate) {
	const root = await mkdtemp(join(resolve(tmpdir()), "flip-v1-rereview-"));
	try {
		await writeFile(join(root, ".git"), `gitdir: ${gitDir}\n`);
		for (const name of [...Object.keys(inventory.sourceHashes), "README.md", "apps/showcase/README.md"]) {
			await mkdir(dirname(join(root, name)), { recursive: true });
			await cp(join(repository, name), join(root, name));
		}
		await cp(join(repository, "docs/release"), join(root, "docs/release"), { recursive: true });
		await cp(join(repository, "apps/showcase/dist"), join(root, "apps/showcase/dist"), { recursive: true });
		await cp(join(repository, "apps/showcase/recordings"), join(root, "apps/showcase/recordings"), { recursive: true });
		// Preserve all documentation link targets so failures must come from integrity checks.
		const docs = ["README.md", "apps/showcase/README.md", ...(await readdir("docs/release")).filter((n) => n.startsWith("M45_R3_") && n.endsWith(".md")).map((n) => `docs/release/${n}`)];
		for (const name of docs) {
			for (const m of (await readFile(name, "utf8")).matchAll(/(?<!!)\[[^\]]+\]\(([^)]+)\)/g)) {
				const p = m[1].split("#")[0];
				if (!p || /^https?:/.test(p)) continue;
				const local = relative(repository, resolve(repository, dirname(name), p));
				if (local.startsWith("..")) continue;
				await mkdir(dirname(join(root, local)), { recursive: true });
				await cp(join(repository, local), join(root, local)).catch(() => {});
			}
		}
		if (mutate) await mutate(root);
		if (mode === "checker")
			return spawnSync(process.execPath, [join(root, "scripts/check_m45_release_package.mjs")], { cwd: root, encoding: "utf8" });
		return spawnSync(process.execPath, ["--input-type=module", "-e", currentBootstrapCode], { cwd: root, encoding: "utf8" });
	} finally {
		if (dirname(resolve(root)) !== resolve(tmpdir()) || !basename(root).startsWith("flip-v1-rereview-")) throw Error("unsafe scratch cleanup");
		await rm(root, { recursive: true, force: true });
	}
}

function record(id, mode, expected, diagnostic, mutate) {
	return isolated(mode, mutate).then((r) => {
		const passed = r.status === 0;
		const text = `${r.stdout ?? ""}\n${r.stderr ?? ""}`;
		const diagnosticOk = !diagnostic || diagnostic.test(text);
		const ok = (expected === "PASS" ? passed : !passed) && diagnosticOk;
		results.push({
			id,
			mode,
			expected,
			observed: passed ? "PASS" : "REJECT",
			status: ok ? "OK" : "FAIL",
			exitCode: r.status,
			diagnosticMatched: diagnostic ? diagnostic.test(text) : null,
			diagnostic: text.split("\n").map((l) => l.trim()).filter((l) => /AssertionError|Error:|mismatch|changed|scope|drift|integrity|ENOENT|PASS:/i.test(l)).slice(0, 3).join(" | "),
		});
	});
}

// --- Phase B: six original attacks against corrected checker -----------------
await record("B0-pristine-checker", "checker", "PASS", /PASS:/);
await record("B1-checker-self-tamper", "checker", "REJECT", /Current checker integrity mismatch/, async (root) => {
	const p = join(root, "scripts/check_m45_release_package.mjs");
	await writeFile(p, (await readFile(p, "utf8")) + "\n// self-tampered\n");
});
await record("B1b-checker-exemption-expansion", "checker", "REJECT", /Current checker scope changed/, async (root) => {
	const p = join(root, "scripts/check_m45_release_package.mjs");
	const src = (await readFile(p, "utf8")).replace('"scripts/check_m45_release_package.mjs",', '"scripts/check_m45_release_package.mjs", "apps/showcase/style.css",');
	if (!src.includes('"apps/showcase/style.css"')) throw Error("edit not applied");
	await writeFile(p, src);
});
await record("B2-historical-commit-retarget-checker", "checker", "REJECT", /Current checker integrity mismatch/, async (root) => {
	const p = join(root, "scripts/check_m45_release_package.mjs");
	const src = (await readFile(p, "utf8")).replace("7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f", "39322e49f9fb1aa83a726fe3bbe81921c7e0f21e");
	if (src.includes("7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f")) throw Error("retarget not applied");
	await writeFile(p, src);
});
await record("B2b-historical-commit-retarget-metadata", "checker", "REJECT", /Authorized historical commit mismatch/, async (root) => {
	const p = join(root, trustPath);
	const t = JSON.parse(await readFile(p, "utf8"));
	t.commit = "39322e49f9fb1aa83a726fe3bbe81921c7e0f21e";
	await writeFile(p, JSON.stringify(t));
});
await record("B3-exemption-expansion-plus-current-source-tamper", "checker", "REJECT", /Current checker scope changed/, async (root) => {
	const p = join(root, "scripts/check_m45_release_package.mjs");
	const src = (await readFile(p, "utf8")).replace('"scripts/check_m45_release_package.mjs",', '"scripts/check_m45_release_package.mjs", "apps/showcase/style.css",');
	await writeFile(p, src);
	await writeFile(join(root, "apps/showcase/style.css"), "/* tampered current source */\n");
});
await record("B4-coordinated-artifact-and-inventory-tamper", "checker", "REJECT", /Historical static integrity mismatch: staticChecksums/, async (root) => {
	const html = join(root, "apps/showcase/dist/index.html");
	await writeFile(html, (await readFile(html, "utf8")) + "\n<!-- tampered -->\n");
	const cpPath = join(root, "apps/showcase/dist/CHECKSUMS.json");
	const sums = JSON.parse(await readFile(cpPath, "utf8"));
	const bytes = await readFile(html);
	sums["index.html"] = { sha256: sha(bytes), bytes: bytes.length };
	await writeFile(cpPath, JSON.stringify(sums));
	const ip = join(root, inventoryPath);
	const inv2 = JSON.parse(await readFile(ip, "utf8"));
	inv2.staticChecksums = sums;
	inv2.staticChecksumManifest.sha256 = sha(await readFile(cpPath));
	await writeFile(ip, JSON.stringify(inv2));
});
await record("B5-source-hash-tamper", "checker", "REJECT", /Historical R3 source inventory changed/, async (root) => {
	const p = join(root, inventoryPath);
	const i = JSON.parse(await readFile(p, "utf8"));
	i.sourceHashes["pyproject.toml"].sha256 = "1".repeat(64);
	await writeFile(p, JSON.stringify(i));
});

// --- Phase D: exact CI bootstrap challenges ----------------------------------
await record("D0-pristine-bootstrap", "bootstrap", "PASS");
await record("D1-changed-checker-unchanged-metadata", "bootstrap", "REJECT", /CI checker integrity mismatch/, async (root) => {
	const p = join(root, "scripts/check_m45_release_package.mjs");
	await writeFile(p, (await readFile(p, "utf8")) + "\n// changed\n");
});
await record("D2-changed-metadata-unchanged-workflow-digest", "bootstrap", "REJECT", /CI release trust metadata mismatch/, async (root) => {
	const p = join(root, trustPath);
	const t = JSON.parse(await readFile(p, "utf8"));
	t.currentSourceHashes["scripts/check_m45_release_package.mjs"] = "0".repeat(64);
	await writeFile(p, JSON.stringify(t));
});
await record("D3-changed-imported-showcase-library", "bootstrap", "REJECT", /CI checker integrity mismatch/, async (root) => {
	const p = join(root, "apps/showcase/lib.mjs");
	await writeFile(p, (await readFile(p, "utf8")) + "\n// changed\n");
});
await record("D4-missing-trust-metadata", "bootstrap", "REJECT", /ENOENT/, async (root) => {
	await rm(join(root, trustPath));
});
await record("D5-invalid-checksum-formatting", "bootstrap", "REJECT", /CI release trust metadata mismatch|CI checker integrity mismatch/, async (root) => {
	const p = join(root, trustPath);
	let raw = await readFile(p, "utf8");
	raw = raw.replace('"visual-v1-release-trust-1"', '"visual-v1-release-trust-1 "');
	await writeFile(p, raw);
});
await record("D6-combined-checker-metadata-workflow-evasion", "bootstrap", "REJECT", /CI release trust metadata mismatch/, async (root) => {
	const cp = join(root, "scripts/check_m45_release_package.mjs");
	await writeFile(cp, (await readFile(cp, "utf8")) + "\n// changed\n");
	const tp = join(root, trustPath);
	const t = JSON.parse(await readFile(tp, "utf8"));
	t.currentSourceHashes["scripts/check_m45_release_package.mjs"] = sha((await readFile(cp, "utf8")).replaceAll("\r\n", "\n"));
	await writeFile(tp, JSON.stringify(t));
});
await record("D7-unauthorized-historical-identity", "checker", "REJECT", /Authorized historical commit mismatch|Historical tree mismatch|Historical blob mismatch/, async (root) => {
	const tp = join(root, trustPath);
	const t = JSON.parse(await readFile(tp, "utf8"));
	t.tree = "0".repeat(40);
	await writeFile(tp, JSON.stringify(t));
});

// Residual trust: a PR that can edit checker + metadata + workflow digest is self-consistent.
await record("D8-coordinated-checker-metadata-workflow", "bootstrap", "PASS", null, async (root) => {
	const cp = join(root, "scripts/check_m45_release_package.mjs");
	await writeFile(cp, (await readFile(cp, "utf8")) + "\n// coordinated change\n");
	const tp = join(root, trustPath);
	const t = JSON.parse(await readFile(tp, "utf8"));
	t.currentSourceHashes["scripts/check_m45_release_package.mjs"] = sha((await readFile(cp, "utf8")).replaceAll("\r\n", "\n"));
	await writeFile(tp, JSON.stringify(t));
	// Use a workflow whose inline digest was updated in the same PR (tracked variable `code` is re-derived here).
	const newDigest = sha(await readFile(tp));
	currentBootstrapCode = bootstrapCode.replace("c7f129581342c63887ec0d90c5e62bf3daa17f79468d63cbc0ba4f387901c1f0", newDigest);
});
currentBootstrapCode = bootstrapCode;
// CRLF in the current checker is normalized before hashing.
await record("D9-crlf-checker-normalized", "checker", "PASS", /PASS:/, async (root) => {
	const p = join(root, "scripts/check_m45_release_package.mjs");
	await writeFile(p, (await readFile(p, "utf8")).replaceAll("\n", "\r\n"));
});
// CRLF in raw trust metadata fails the raw-byte workflow digest (gitattributes enforces LF checkout).
await record("D10-crlf-metadata-rejected", "bootstrap", "REJECT", /CI release trust metadata mismatch/, async (root) => {
	const p = join(root, trustPath);
	await writeFile(p, (await readFile(p, "utf8")).replaceAll("\n", "\r\n"));
});

await mkdir(".test-tmp/visual-v1-security-rereview", { recursive: true });
await writeFile(
	"docs/evidence/visual-v1-security-rereview/security-rereview-results.json",
	JSON.stringify({ generatedAt: new Date().toISOString(), prHead: "53a7f1cdd729188c7bfd593d37049836b6ed6a12", results }, null, 2) + "\n",
);
console.log(`cases=${results.length} failures=${results.filter((r) => r.status === "FAIL").length}`);
for (const r of results) console.log(`${r.status} ${r.id}: expected=${r.expected} observed=${r.observed} exit=${r.exitCode} :: ${r.diagnostic}`);
