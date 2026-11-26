// Independent release-guard attack harness. All writes are to temporary scratch copies.
// Run from repository root: node docs/evidence/visual-v1-independent-review/release-guard-attack-harness.mjs
import { cp, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { execFileSync, spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { resolve, dirname, join, basename, relative } from "node:path";
import { sha } from "../../../apps/showcase/lib.mjs";

const repository = process.cwd();
const checker = resolve("scripts/check_m45_release_package.mjs");
const inventoryPath = "docs/release/M45_R3_ASSET_INVENTORY.json";
const originalInventory = JSON.parse(await readFile(inventoryPath, "utf8"));
const gitDir = execFileSync("git", ["rev-parse", "--absolute-git-dir"], { encoding: "utf8" }).trim();
const results = [];

async function isolated(attack, operation) {
	const parent = resolve(tmpdir());
	const root = await mkdtemp(join(parent, "flip-v1-rgattack-"));
	try {
		await writeFile(join(root, ".git"), `gitdir: ${gitDir}\n`);
		for (const name of [...Object.keys(originalInventory.sourceHashes), "README.md", "apps/showcase/README.md"]) {
			await mkdir(dirname(join(root, name)), { recursive: true });
			await cp(join(repository, name), join(root, name));
		}
		await cp(join(repository, "docs/release"), join(root, "docs/release"), { recursive: true });
		await cp(join(repository, "apps/showcase/dist"), join(root, "apps/showcase/dist"), { recursive: true });
		await cp(join(repository, "apps/showcase/recordings"), join(root, "apps/showcase/recordings"), { recursive: true });
		const documents = ["README.md", "apps/showcase/README.md", ...(await readdir("docs/release")).filter((n) => n.startsWith("M45_R3_") && n.endsWith(".md")).map((n) => `docs/release/${n}`)];
		for (const name of documents) {
			const source = await readFile(name, "utf8");
			for (const match of source.matchAll(/(?<!!)\[[^\]]+\]\(([^)]+)\)/g)) {
				const path = match[1].split("#")[0];
				if (!path || /^https?:/.test(path)) continue;
				const local = relative(repository, resolve(repository, dirname(name), path));
				if (local.startsWith("..")) continue;
				await mkdir(dirname(join(root, local)), { recursive: true });
				await cp(targetOrSkip(join(repository, local)), join(root, local)).catch(() => {});
			}
		}
		await attack(root);
		const r = spawnSync(process.execPath, [join(root, "scripts/check_m45_release_package.mjs")], { cwd: root, encoding: "utf8" });
		return operation(r);
	} finally {
		if (dirname(resolve(root)) !== parent || !basename(root).startsWith("flip-v1-rgattack-")) throw Error("unsafe cleanup path");
		await rm(root, { recursive: true, force: true });
	}
}
function targetOrSkip(p) { return p; }

function check(id, expected, attack, assertion) {
	return isolated(attack, (r) => {
		const passed = r.status === 0;
		const ok = expected === "PASS" ? passed : !passed;
		const stdout = r.stdout ?? "";
		const stderr = r.stderr ?? "";
		const extra = assertion ? assertion(r) : "";
		results.push({
			id,
			expected,
			observed: passed ? "PASS" : "REJECT",
			status: ok && (extra === "" || extra === true) ? "OK" : "FAIL",
			detail: (stderr || stdout).split("\n").filter(Boolean).slice(-3).join(" | "),
			assertion: extra === true ? "" : extra,
		});
	});
}

// 1. Coordinated tampering of static artifact + CHECKSUMS.json + inventory staticChecksums.
await check(
	"coordinated-static-artifact-and-inventory-tamper",
	"REJECT",
	async (root) => {
		const html = join(root, "apps/showcase/dist/index.html");
		await writeFile(html, (await readFile(html, "utf8")) + "\n<!-- tampered -->\n");
		const checksumsPath = join(root, "apps/showcase/dist/CHECKSUMS.json");
		const sums = JSON.parse(await readFile(checksumsPath, "utf8"));
		const bytes = await readFile(html);
		sums["index.html"] = { sha256: sha(bytes), bytes: bytes.length };
		await writeFile(checksumsPath, JSON.stringify(sums));
		const invPath = join(root, inventoryPath);
		const inv = JSON.parse(await readFile(invPath, "utf8"));
		inv.staticChecksums = sums;
		const manifestBytes = await readFile(checksumsPath);
		inv.staticChecksumManifest.sha256 = sha(manifestBytes);
		await writeFile(invPath, JSON.stringify(inv));
	},
);

// 2. Tamper one original source hash entry in the inventory while keeping files unchanged.
await check(
	"single-original-source-hash-tamper",
	"REJECT",
	async (root) => {
		const p = join(root, inventoryPath);
		const inv = JSON.parse(await readFile(p, "utf8"));
		inv.sourceHashes["pyproject.toml"].sha256 = "1".repeat(64);
		await writeFile(p, JSON.stringify(inv));
	},
);

// 3. Change the hardcoded historical commit identifier to another real commit.
await check(
	"pinned-commit-identifier-retarget",
	"REJECT",
	async (root) => {
		const p = join(root, "scripts/check_m45_release_package.mjs");
		const src = (await readFile(p, "utf8")).replace(
			"7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f",
			"39322e49f9fb1aa83a726fe3bbe81921c7e0f21e",
		);
		if (src.includes("7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f")) throw Error("retarget not applied");
		await writeFile(p, src);
	},
);

// 4. Add a non-allowlisted path to historicalSourcePaths (checker self-tamper).
await check(
	"checker-allowlist-expansion-self-tamper",
	"REJECT",
	async (root) => {
		const p = join(root, "scripts/check_m45_release_package.mjs");
		const src = (await readFile(p, "utf8")).replace(
			'"scripts/check_m45_release_package.mjs",',
			'"scripts/check_m45_release_package.mjs",\n\t"apps/showcase/style.css",',
		);
		if (!src.includes('"apps/showcase/style.css",')) throw Error("allowlist edit not applied");
		await writeFile(p, src);
	},
);

// 5. Widen historical exception to a current static output by checker self-tamper.
await check(
	"checker-bypass-of-current-static-check",
	"REJECT",
	async (root) => {
		const p = join(root, "scripts/check_m45_release_package.mjs");
		const src = (await readFile(p, "utf8")).replace(
			'assert.deepEqual(\n\tsums,\n\tinventory.staticChecksums,\n\t"Static output differs from release inventory",\n);',
			"// bypassed",
		);
		if (!src.includes("// bypassed")) throw Error("static assertion bypass not applied");
		await writeFile(p, src);
		await writeFile(join(root, "apps/showcase/dist/index.html"), "<script>tampered</script>");
	},
);

// 6. Self-tamper checker allowlist AND tamper the now-exempted current source file.
await check(
	"checker-allowlist-expansion-plus-current-source-tamper",
	"REJECT",
	async (root) => {
		const p = join(root, "scripts/check_m45_release_package.mjs");
		const src = (await readFile(p, "utf8")).replace(
			'"scripts/check_m45_release_package.mjs",',
			'"scripts/check_m45_release_package.mjs",\n\t"apps/showcase/style.css",',
		);
		if (!src.includes('"apps/showcase/style.css",')) throw Error("allowlist edit not applied");
		await writeFile(p, src);
		await writeFile(join(root, "apps/showcase/style.css"), "/* tampered current source */\n");
	},
);

await writeFile(
	"docs/evidence/visual-v1-independent-review/release-guard-attack-results.json",
	JSON.stringify({ generatedAt: new Date().toISOString(), results }, null, 2) + "\n",
);
console.log(`cases=${results.length} failures=${results.filter((r) => r.status === "FAIL").length}`);
for (const r of results) console.log(`${r.status} ${r.id}: expected=${r.expected} observed=${r.observed} :: ${r.detail}`);
