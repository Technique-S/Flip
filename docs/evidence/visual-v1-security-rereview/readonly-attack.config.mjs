import { resolve } from "node:path";
import { defineConfig } from "../../../apps/web/node_modules/@playwright/test/index.mjs";

const root = process.cwd();
const appPort = 18771;
const rpcPort = 18772;
const py = resolve(root, ".venv/Scripts/python.exe");
const launch = (command) => ({
	command: `"${py}" ${command}`,
	reuseExistingServer: false,
	timeout: 30000,
});
export default defineConfig({
	testDir: ".",
	testMatch: "readonly-attack.spec.mjs",
	reporter: [["list"], ["json", { outputFile: resolve(root, ".test-tmp/visual-v1-security-rereview/readonly-attack.json") }]],
	timeout: 60000,
	workers: 1,
	outputDir: resolve(root, ".test-tmp/visual-v1-security-rereview/browser"),
	use: { baseURL: `http://127.0.0.1:${appPort}`, viewport: { width: 1280, height: 860 } },
	webServer: [
		{ ...launch(resolve(root, "apps/web/tests/rpc_fixture.py")), port: rpcPort, env: { FLIP_TEST_RPC_PORT: String(rpcPort) } },
		{
			...launch(`-m flip_api.local --port ${appPort}`),
			url: `http://127.0.0.1:${appPort}/healthz`,
			env: { FLIP_LOCAL_SOLVER: "1", FLIP_RPC_URL: `http://127.0.0.1:${rpcPort}`, FLIP_RPC_RETRIES: "0" },
		},
	],
});
