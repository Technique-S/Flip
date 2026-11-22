import { spawnSync } from "node:child_process";
const result = spawnSync(
	process.execPath,
	[
		"apps/web/node_modules/@playwright/test/cli.js",
		"test",
		"--config=apps/showcase/playwright.config.mjs",
	],
	{ stdio: "inherit" },
);
if (result.error) throw result.error;
process.exitCode = result.status ?? 1;
