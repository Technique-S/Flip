import { defineConfig } from "../web/node_modules/@playwright/test/index.mjs";
export default defineConfig({
	testDir: "tests",
	workers: 1,
	timeout: 30000,
	reporter: [
		["list"],
		["json", { outputFile: "../../.test-tmp/r3/showcase-results.json" }],
	],
	outputDir: "../../.test-tmp/r3/showcase-browser",
	use: { viewport: { width: 1280, height: 900 }, serviceWorkers: "block" },
});
