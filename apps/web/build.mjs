import { copyFile, mkdir } from "node:fs/promises";
import { build } from "esbuild";

await mkdir("dist", { recursive: true });
await build({
	entryPoints: ["src/main.tsx"],
	bundle: true,
	minify: true,
	format: "esm",
	target: "es2022",
	outfile: "dist/flip.js",
	define: { "process.env.NODE_ENV": '"production"' },
});
await copyFile("index.html", "dist/index.html");
