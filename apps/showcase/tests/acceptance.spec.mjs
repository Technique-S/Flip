import {
	test,
	expect,
} from "../../web/node_modules/@playwright/test/index.mjs";
import { readFile, writeFile, mkdir, cp } from "node:fs/promises";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";
import { execFileSync, spawnSync } from "node:child_process";
import { sha } from "../lib.mjs";

const researchSha = "82e25deef9ae3498f837e188a7faed0ed61cd7ff";
const fixturePath =
	"docs/evidence/m45-release-acceptance/original-fixtures/claim-negative-cases.json";
const fixtureBytes = await readFile(fixturePath);
expect(sha(fixtureBytes)).toBe(
	"c50aa3012f228ecbfc09c56f2415f38cb3adaa5b739adc3f4b799f21bbce988f",
);
const fixture = JSON.parse(fixtureBytes);
expect(fixture.cases).toHaveLength(12);

test("OpenCode research retains every original Git blob and conclusion", async () => {
	const files = execFileSync(
		"git",
		[
			"ls-tree",
			"-r",
			"--name-only",
			researchSha,
			"docs/evidence/m45-release-acceptance",
			"fixtures/m45-release-acceptance",
		],
		{ encoding: "utf8" },
	)
		.trim()
		.split("\n");
	expect(files).toHaveLength(9);
	for (const name of files) {
		const archivedPath = name.replace(
			/^fixtures\/m45-release-acceptance\//,
			"docs/evidence/m45-release-acceptance/original-fixtures/",
		);
		expect(await readFile(archivedPath)).toEqual(
			execFileSync("git", ["show", `${researchSha}:${name}`]),
		);
	}
});

// The showcase accepts only pinned recordings. This exercises that boundary, not
// a semantic classifier: each invented claim is placed in a displayed source alias.
for (const negative of fixture.cases) {
	test(`${negative.id}: rejects unapproved recording claim (${negative.category})`, async ({
		context,
		page,
	}, info) => {
		const temp = info.outputPath("claim-builder");
		await mkdir(temp, { recursive: true });
		for (const name of ["build.mjs", "lib.mjs", "style.css"])
			await cp(resolve("apps/showcase", name), join(temp, name));
		await cp(resolve("apps/showcase/recordings"), join(temp, "recordings"), {
			recursive: true,
		});
		const receiptPath = join(temp, "recordings/receipt.json");
		const receipt = JSON.parse(await readFile(receiptPath, "utf8"));
		receipt.originalExecutionRequest.imports[0].alias = negative.syntheticClaim;
		const bytes = Buffer.from(JSON.stringify(receipt));
		await writeFile(receiptPath, bytes);
		const run = () =>
			spawnSync(process.execPath, [join(temp, "build.mjs")], {
				encoding: "utf8",
			});
		const rejected = run();
		expect(rejected.error).toBeUndefined();
		expect(rejected.status).not.toBe(0);
		expect(rejected.stderr).toMatch(
			/Wrong byte length|Wrong recording checksum/,
		);
		// Updating a checksum inventory cannot grant authority to the forged claim.
		const manifestPath = join(temp, "recordings/manifest.json");
		const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
		Object.assign(
			manifest.files.find((f) => f.name === "receipt.json"),
			{ bytes: bytes.length, sha256: sha(bytes) },
		);
		await writeFile(manifestPath, JSON.stringify(manifest));
		const repinned = run();
		expect(repinned.error).toBeUndefined();
		expect(repinned.status).not.toBe(0);
		expect(repinned.stderr).toContain(
			"Recording manifest differs from the reviewed build input",
		);
		await expect(readFile(join(temp, "dist/index.html"))).rejects.toThrow(
			/ENOENT/,
		);
		await context.setOffline(true);
		const observations = [];
		for (const name of [
			"index",
			"composition",
			"difference",
			"connections",
			"correction",
			"revision",
			"evidence",
		]) {
			await page.goto(
				pathToFileURL(resolve(`apps/showcase/dist/${name}.html`)).href,
			);
			await expect(page.locator(".scope")).toContainText(
				"RECORDED · HISTORICAL",
			);
			await expect(page.locator("body")).not.toContainText(
				negative.syntheticClaim,
			);
			observations.push({
				page: name,
				scope: await page.locator(".scope").innerText(),
				misleadingClaimPresent: false,
			});
		}
		await info.attach(`${negative.id}-observations`, {
			contentType: "application/json",
			body: Buffer.from(
				JSON.stringify(
					{
						researchSha,
						fixtureSha256: sha(fixtureBytes),
						id: negative.id,
						syntheticClaim: negative.syntheticClaim,
						requiredAssertion: negative.requiredAssertion,
						classification: "REJECT",
						mechanism: "Pinned recording custody; no semantic classifier",
						tamperedSha256: sha(bytes),
						rejection: rejected.stderr,
						repinnedRejection: repinned.stderr,
						observations,
					},
					null,
					2,
				),
			),
		});
	});
}
