// Release-only checks. Never starts a server or imports production runtime.
import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import { resolve, relative, dirname, join, extname } from "node:path";
import { loadRecording, sha } from "../apps/showcase/lib.mjs";
import { execFileSync } from "node:child_process";
const root = resolve("apps/showcase/dist");
async function walk(dir) {
	const names = [];
	for (const e of await readdir(dir, { withFileTypes: true })) {
		assert(!e.isSymbolicLink(), "No distribution symlinks");
		if (e.isDirectory()) names.push(...(await walk(join(dir, e.name))));
		else names.push(relative(root, join(dir, e.name)).replaceAll("\\", "/"));
	}
	return names;
}
await loadRecording(new URL("../apps/showcase/recordings/", import.meta.url));
const files = await walk(root);
const sums = JSON.parse(await readFile(join(root, "CHECKSUMS.json"), "utf8"));
assert.deepEqual([...Object.keys(sums), "CHECKSUMS.json"].sort(), files.sort());
let links = 0;
for (const name of files) {
	assert(
		[".html", ".css", ".json", ".txt"].includes(extname(name)),
		`Unexpected executable/distribution type: ${name}`,
	);
	const bytes = await readFile(join(root, name));
	if (name !== "CHECKSUMS.json") {
		assert.equal(sha(bytes), sums[name].sha256);
		assert.equal(bytes.length, sums[name].bytes);
	}
	const source = bytes.toString("utf8");
	if (name.endsWith(".css"))
		assert(
			!/url\s*\(|@import/i.test(source),
			"No remote/imported CSS resources",
		);
	if (!name.endsWith(".html")) continue;
	assert(
		!/<(?:script|form|input|button|iframe|object|embed|video|audio|img|svg|base)\b|\son\w+\s*=|\bsrc\s*=/i.test(
			source,
		),
		"No executable, interactive input or external resource elements",
	);
	assert(
		source.includes("script-src 'none'; connect-src 'none'"),
		"Script and connections denied",
	);
	assert(source.includes("RECORDED · HISTORICAL"), "Required historical label");
	for (const match of source.matchAll(/\b(?:href)="([^"]+)"/g)) {
		const [path, fragment] = match[1].split("#");
		assert(
			!/^[a-z][\w+.-]*:|^\/|\\|%/i.test(path),
			`Non-local link: ${match[1]}`,
		);
		const target = resolve(root, dirname(name), path || name.split("/").at(-1));
		assert(!relative(root, target).startsWith(".."), "Link escapes package");
		const targetText = await readFile(target, "utf8");
		if (fragment)
			assert(targetText.includes(`id="${fragment}"`), "Broken fragment");
		links++;
	}
}
const build = JSON.parse(await readFile(join(root, "BUILD.json"), "utf8"));
assert(Object.values(build.capabilities).every((value) => value === false));
// Documentation-relative local links; external status/access compliance is not inferred.
for (const name of [
	"README.md",
	"apps/showcase/README.md",
	...(await readdir("docs/release"))
		.filter((n) => n.startsWith("M45_R3_") && n.endsWith(".md"))
		.map((n) => `docs/release/${n}`),
]) {
	const source = await readFile(name, "utf8");
	for (const match of source.matchAll(/(?<!!)\[[^\]]+\]\(([^)]+)\)/g)) {
		const path = match[1].split("#")[0];
		if (!path || /^https?:/.test(path)) continue;
		assert(!/^[a-z]+:/i.test(path), "Unsupported documentation URI");
		await readFile(resolve(dirname(name), path));
		links++;
	}
}
const inventory = JSON.parse(
	await readFile("docs/release/M45_R3_ASSET_INVENTORY.json", "utf8"),
);
assert.deepEqual(
	sums,
	inventory.staticChecksums,
	"Static output differs from release inventory",
);
assert.equal(
	sha(await readFile(join(root, "CHECKSUMS.json"))),
	inventory.staticChecksumManifest.sha256,
);
// R3 is a historical static release. These three files also serve the evolving
// workbench/checker, so their R3 provenance is checked at the immutable R3 merge.
// All other release sources and the actual generated output remain current checks.
const releaseSourceRef = "7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f";
const historicalSourcePaths = new Set([
	"apps/web/package.json",
	"apps/web/package-lock.json",
	"scripts/check_m45_release_package.mjs",
]);
execFileSync("git", ["merge-base", "--is-ancestor", releaseSourceRef, "HEAD"]);
const historicalFile = (name) => execFileSync("git", ["show", `${releaseSourceRef}:${name}`], { encoding: "utf8" });
const originalInventory = JSON.parse(historicalFile("docs/release/M45_R3_ASSET_INVENTORY.json"));
assert.deepEqual(inventory.sourceHashes, originalInventory.sourceHashes, "Historical R3 source inventory changed");
for (const [name, record] of Object.entries(inventory.sourceHashes)) {
	const bytes = Buffer.from(
		(historicalSourcePaths.has(name) ? historicalFile(name) : await readFile(name, "utf8")).replaceAll("\r\n", "\n"),
	);
	assert.equal(sha(bytes), record.sha256, `Release source drift: ${name}`);
	assert.equal(bytes.length, record.bytes);
}
console.log(`R3 historical source provenance at ${releaseSourceRef}: ${[...historicalSourcePaths].join(", ")}. All other source pins and static artifacts checked in current checkout; this does not validate current workbench dependencies.`);
console.log(
	`PASS: ${files.length} checksummed inert files, ${links} local links; no scripts, server, imports, native binaries, RPC, wallet or publication surface.`,
);
