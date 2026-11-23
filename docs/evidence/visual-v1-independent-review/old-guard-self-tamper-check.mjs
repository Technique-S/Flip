// Compare pre-PR checker self-integrity behavior against the PR head checker.
// Uses temporary scratch copies only; no repository files are modified.
import { cp, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { execFileSync, spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { resolve, dirname, join, basename, relative } from "node:path";

const repository = process.cwd();
const inventoryPath = "docs/release/M45_R3_ASSET_INVENTORY.json";
const inv = JSON.parse(await readFile(inventoryPath, "utf8"));
const gitDir = execFileSync("git", ["rev-parse", "--absolute-git-dir"], { encoding: "utf8" }).trim();
const oldCheckerSource = execFileSync("git", ["show", `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f:scripts/check_m45_release_package.mjs`], { encoding: "utf8" });

const parent = resolve(tmpdir());
const root = await mkdtemp(join(parent, "flip-v1-oldguard-"));
try {
	await writeFile(join(root, ".git"), `gitdir: ${gitDir}\n`);
	for (const name of [...Object.keys(inv.sourceHashes), "README.md", "apps/showcase/README.md"]) {
		await mkdir(dirname(join(root, name)), { recursive: true });
		await cp(join(repository, name), join(root, name));
	}
	await cp(join(repository, "docs/release"), join(root, "docs/release"), { recursive: true });
	await cp(join(repository, "apps/showcase/dist"), join(root, "apps/showcase/dist"), { recursive: true });
	await cp(join(repository, "apps/showcase/recordings"), join(root, "apps/showcase/recordings"), { recursive: true });
	const docs = ["README.md", "apps/showcase/README.md", ...(await readdir("docs/release")).filter((n) => n.startsWith("M45_R3_") && n.endsWith(".md")).map((n) => `docs/release/${n}`)];
	for (const name of docs) {
		for (const match of (await readFile(name, "utf8")).matchAll(/(?<!!)\[[^\]]+\]\(([^)]+)\)/g)) {
			const p = match[1].split("#")[0];
			if (!p || /^https?:/.test(p)) continue;
			const local = relative(repository, resolve(repository, dirname(name), p));
			if (local.startsWith("..")) continue;
			await mkdir(dirname(join(root, local)), { recursive: true });
			await cp(join(repository, local), join(root, local)).catch(() => {});
		}
	}
	// Isolate the self-tamper check: restore the two dependency files the PR changed
	// to their accepted-main bytes so the old checker reaches its own hash entry.
	for (const name of ["apps/web/package.json", "apps/web/package-lock.json"]) {
		await writeFile(join(root, name), execFileSync("git", ["show", `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f:${name}`], { encoding: "utf8" }));
	}
	const checkerPath = join(root, "scripts/check_m45_release_package.mjs");
	await writeFile(checkerPath, oldCheckerSource + "\n// self-tampered\n");
	const r = spawnSync(process.execPath, [checkerPath], { cwd: root, encoding: "utf8" });
	console.log(JSON.stringify({
		checker: "pre-PR accepted-main version, self-tampered",
		status: r.status,
		driftFound: /Release source drift: scripts\/check_m45_release_package\.mjs/.test(r.stderr ?? ""),
		stderrLines: (r.stderr ?? "").split("\n").filter(Boolean).slice(0, 8),
	}, null, 2));
} finally {
	if (dirname(resolve(root)) !== parent || !basename(root).startsWith("flip-v1-oldguard-")) throw Error("unsafe cleanup");
	await rm(root, { recursive: true, force: true });
}
