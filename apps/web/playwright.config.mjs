import { resolve } from "node:path";
import { defineConfig } from "@playwright/test";

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
	timeout: 60000,
	workers: 1,
	outputDir: "../../.test-tmp/browser",
	use: {
		baseURL: "http://127.0.0.1:18761",
		viewport: { width: 1280, height: 860 },
		trace: "retain-on-failure",
	},
	webServer: [
		{ ...launch("tests/rpc_fixture.py"), port: 18762 },
		{
			...launch("-m flip_api.local --port 18761"),
			url: "http://127.0.0.1:18761/healthz",
			env: {
				FLIP_LOCAL_SOLVER: "1",
				FLIP_RPC_URL: "http://127.0.0.1:18762",
				FLIP_RPC_RETRIES: "0",
			},
		},
	],
});
