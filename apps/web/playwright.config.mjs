import { resolve } from "node:path";
import { defineConfig } from "@playwright/test";

const appPort = Number(process.env.FLIP_TEST_APP_PORT ?? 18761);
const rpcPort = Number(process.env.FLIP_TEST_RPC_PORT ?? 18762);

const py = resolve(
	process.platform === "win32"
		? "../../.venv/Scripts/python.exe"
		: "../../.venv/bin/python",
);
const launch = (command) => ({
	command: `"${py}" ${command}`,
	reuseExistingServer: false,
	timeout: 30000,
});
export default defineConfig({
	testDir: "tests",
	reporter: [
		["list"],
		["json", { outputFile: "../../.test-tmp/m4-browser.json" }],
	],
	timeout: 60000,
	workers: 1,
	outputDir: "../../.test-tmp/browser",
	use: {
		baseURL: `http://127.0.0.1:${appPort}`,
		viewport: { width: 1280, height: 860 },
		trace: "retain-on-failure",
	},
	webServer: [
		{
			...launch("tests/rpc_fixture.py"),
			port: rpcPort,
			env: { FLIP_TEST_RPC_PORT: String(rpcPort) },
		},
		{
			...launch(`-m flip_api.local --port ${appPort}`),
			url: `http://127.0.0.1:${appPort}/healthz`,
			env: {
				FLIP_LOCAL_SOLVER: "1",
				FLIP_RPC_URL: `http://127.0.0.1:${rpcPort}`,
				FLIP_RPC_RETRIES: "0",
			},
		},
	],
});
