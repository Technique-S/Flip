import { test, expect } from "../../web/node_modules/@playwright/test/index.mjs";
import { cp, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { execFileSync, spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { resolve, dirname, basename, join, relative } from "node:path";

const repository = process.cwd();
const checker = resolve("scripts/check_m45_release_package.mjs");
const inventoryPath = "docs/release/M45_R3_ASSET_INVENTORY.json";
const inventory = JSON.parse(await readFile(inventoryPath, "utf8"));
const gitDir = execFileSync("git", ["rev-parse", "--absolute-git-dir"], { encoding: "utf8" }).trim();

async function isolated(operation) {
	const parent = resolve(tmpdir());
	const root = await mkdtemp(join(parent, "flip-v1-guard-"));
	try {
		// Read-only Git history access; no clone, source edits, network or real fixture rewrite.
		await writeFile(join(root, ".git"), `gitdir: ${gitDir}\n`);
		for (const name of [...Object.keys(inventory.sourceHashes), "README.md", "apps/showcase/README.md"]) {
			await mkdir(dirname(join(root, name)), { recursive: true });
			await cp(join(repository, name), join(root, name));
		}
		await cp(join(repository, "docs/release"), join(root, "docs/release"), { recursive: true });
		await cp(join(repository, "apps/showcase/dist"), join(root, "apps/showcase/dist"), { recursive: true });
		// Preserve the checker's documentation-link checks in the isolated workspace.
		const documents = ["README.md", "apps/showcase/README.md", ...(await readdir("docs/release")).filter((n) => n.startsWith("M45_R3_") && n.endsWith(".md")).map((n) => `docs/release/${n}`)];
		for (const name of documents) {
			const source = await readFile(name, "utf8");
			for (const match of source.matchAll(/(?<!!)\[[^\]]+\]\(([^)]+)\)/g)) {
				const path = match[1].split("#")[0];
				if (!path || /^https?:/.test(path)) continue;
				const target = resolve(repository, dirname(name), path);
				const local = relative(repository, target);
				if (local.startsWith("..")) throw Error("Documentation target escaped repository");
				await mkdir(dirname(join(root, local)), { recursive: true });
				await cp(target, join(root, local));
			}
		}
		return await operation(root);
	} finally {
		if (dirname(resolve(root)) !== parent || !basename(root).startsWith("flip-v1-guard-")) throw Error("Unsafe scratch cleanup path");
		await rm(root, { recursive: true, force: true });
	}
}
function run(root) {
	return spawnSync(process.execPath, [checker], { cwd: root, encoding: "utf8" });
}
for (const attack of ["none", "current-source", "static-output", "inventory", "unknown-path", "missing-history", "wrong-history"]) {
	test(`R3 source scope preserves fail-closed checks: ${attack}`, async () => {
		await isolated(async (root) => {
			if (attack === "current-source") await writeFile(join(root, "apps/showcase/style.css"), "/* tampered */");
			if (attack === "static-output") await writeFile(join(root, "apps/showcase/dist/index.html"), "<script>tampered</script>");
			if (["inventory", "unknown-path"].includes(attack)) {
				const copy = structuredClone(inventory);
				if (attack === "inventory") copy.sourceHashes["apps/web/package.json"].sha256 = "0".repeat(64);
				else copy.sourceHashes["unreviewed/fallback.json"] = { sha256: "0".repeat(64), bytes: 0 };
				await writeFile(join(root, inventoryPath), JSON.stringify(copy));
			}
			if (["missing-history", "wrong-history"].includes(attack)) {
				await rm(join(root, ".git"));
				if (attack === "wrong-history") execFileSync("git", ["init", "--quiet", root]);
			}
			const result = run(root);
			if (attack === "none") {
				expect(result.status, result.stderr).toBe(0);
				expect(result.stdout).toContain("R3 historical source provenance at 7ecfb9b");
				expect(result.stdout).toContain("All other source pins and static artifacts checked in current checkout");
			} else {
				expect(result.status, result.stdout).not.toBe(0);
				if (attack === "current-source") expect(result.stderr).toContain("Release source drift: apps/showcase/style.css");
				if (["inventory", "unknown-path"].includes(attack)) expect(result.stderr).toContain("Historical R3 source inventory changed");
				if (attack === "missing-history") expect(result.stderr).toContain("not a git repository");
				if (attack === "wrong-history") expect(result.stderr).toMatch(/not a valid|Not a valid|bad revision/);
				expect(result.stdout).not.toContain("PASS:");
			}
		});
	});
}
test("independent original attacks reject at the intended integrity boundaries", async () => {
 const result = spawnSync(process.execPath, [resolve("docs/ux/visual-v1/results/run-attack-harness.mjs")], {cwd:repository, encoding:"utf8"});
 expect(result.status,result.stderr).toBe(0);
 const report=JSON.parse(await readFile(".test-tmp/rg-replay/results.json","utf8"));
 expect(report.results).toHaveLength(6);
 for(const row of report.results) {
  expect(row.status,row.id).toBe("OK"); expect(row.observed,row.id).toBe("REJECT");
  expect(row.diagnostic,row.id).toMatch(row.id.startsWith("coordinated") ? /Historical static integrity mismatch/ : row.id.startsWith("single") ? /Historical R3 source inventory changed/ : /Current checker (scope changed|integrity mismatch)/);
 }
});

test("coordinated checker and metadata tamper is rejected by the actual CI trust anchor", async () => {
 await isolated(async root=>{
  const path=join(root,"scripts/check_m45_release_package.mjs");
  await writeFile(path,(await readFile(path,"utf8"))+"\n// changed\n");
  const {createHash}=await import("node:crypto");
  const tp=join(root,"docs/release/V1_RELEASE_TRUST.json"); const trust=JSON.parse(await readFile(tp,"utf8"));
  trust.currentSourceHashes["scripts/check_m45_release_package.mjs"]=createHash("sha256").update((await readFile(path,"utf8")).replaceAll("\r\n","\n")).digest("hex");
  await writeFile(tp,JSON.stringify(trust));
  const workflow=await readFile(".github/workflows/m1-contracts.yml","utf8");
  const code=workflow.match(/node --input-type=module <<'JS'\n([\s\S]*?)\n          JS/)[1].replace(/^          /gm,"");
  const run=spawnSync(process.execPath,["--input-type=module","-e",code],{cwd:root,encoding:"utf8"});
  expect(run.status).not.toBe(0); expect(run.stderr).toContain("CI release trust metadata mismatch");
 });
});
