import { useRef, useState } from "react";
import { Comparison, Verdict } from "./Comparison";
import { Composer } from "./Composer";
import {
	api,
	type Built,
	type Bundle,
	download,
	type Execution,
	type Imported,
	type Preflight,
	type Proof,
	productBody,
	readFile,
	source,
} from "./model";

const pages = ["Sources", "Composition", "Wiring Canary", "Evidence"] as const;
const copy = [
	"Import and inspect circuit sources.",
	"Connect pins and build a TAP-02 netlist.",
	"Compare a candidate against its reference.",
	"Export a run or replay evidence against the open project.",
];
function FileInput({
	label,
	open,
}: {
	label: string;
	open: (file: File) => void;
}) {
	return (
		<label className="file">
			{label}
			<input
				type="file"
				accept=".json,application/json"
				onChange={(e) => {
					const f = e.target.files?.[0];
					e.target.value = "";
					if (f) open(f);
				}}
			/>
		</label>
	);
}
function Schematic() {
	return (
		<div
			className="schematic"
			role="img"
			aria-label="Half-adder outputs. XOR produces sum. NAND followed by an inverter produces carry."
		>
			<div className="wires">
				<code>A, B</code>
				<i />
				<b>XOR</b>
				<i />
				<code>sum</code>
			</div>
			<div className="wires">
				<code>A, B</code>
				<i />
				<b>NAND</b>
				<i />
				<b>INV</b>
				<i />
				<code>carry</code>
			</div>
		</div>
	);
}
function SourceCard({ item, alias }: { item: Imported; alias: string }) {
	const m = item.manifest,
		r = m.root;
	return (
		<details className="source">
			<summary>
				<strong>
					{alias} <code>#{r.identity.circuitId}</code>
				</strong>
				<span>
					{r.nIn} in / {r.nOut} out · {r.expandedGates} gates
				</span>
			</summary>
			<dl>
				<dt>Processor</dt>
				<dd>{r.identity.processor}</dd>
				<dt>Manifest</dt>
				<dd>{item.manifestHash}</dd>
				<dt>Block</dt>
				<dd>{m.block.number}</dd>
				<dt>State pins</dt>
				<dd>{r.nState}</dd>
				<dt>REF dependencies</dt>
				<dd>{m.dependencies.length}</dd>
			</dl>
			<pre>{JSON.stringify(m.dependencies, null, 2)}</pre>
		</details>
	);
}
export default function App() {
	const [page, go] = useState(0),
		[req, setReq] = useState<Execution | null>(null),
		[origin, setOrigin] = useState("");
	const [built, setBuilt] = useState<Built | null>(null),
		[proof, setProof] = useState<Proof | null>(null);
	const [busy, setBusy] = useState(""),
		lock = useRef(false),
		[error, setError] = useState(""),
		[note, setNote] = useState("");
	const [proc, setProc] = useState(""),
		[cid, setCid] = useState("1"),
		[addMode, setAddMode] = useState(false);
	const [inspected, setInspected] = useState<Imported | null>(null),
		[obs, setObs] = useState<Preflight | null>(null),
		[observe, setObserve] = useState(false);
	const [chainNote, setChainNote] = useState(""),
		[replayed, setReplayed] = useState(false);
	const [table, setTable] = useState<{
		verdict: string;
		rows: number;
		mismatches: { inputs: { bits: string }; actual: { bits: string } }[];
	} | null>(null);
	const sampleRows = [
		["00", "00"],
		["01", "01"],
		["10", "01"],
		["11", "10"],
	];
	function checkTable() {
		if (!req) return;
		void work("Evaluating truth table", async () => {
			const bits = (value: string) => ({
				bits: value,
				width: 2,
				encoding: "tap02-lsb0-v1",
			});
			const vectors = sampleRows.map(([input, output]) => ({
				inputs: bits(input),
				outputs: bits(output),
			}));
			setTable(
				await api<NonNullable<typeof table>>("vectors", { ...req, vectors }),
			);
		});
	}
	async function work(label: string, fn: () => Promise<void>) {
		if (lock.current) return;
		lock.current = true;
		setBusy(label);
		setError("");
		setNote("");
		try {
			await fn();
		} catch (e) {
			setError(e instanceof Error ? e.message : "Operation failed.");
		} finally {
			lock.current = false;
			setBusy("");
		}
	}
	function replace(r: Execution) {
		const design = r.project.candidate;
		const pins = design.components.reduce(
			(n, c) => n + c.inputs.length,
			design.outputs.length,
		);
		const width = design.components.reduce(
			(n, c) =>
				n +
				(r.project.sources.find((s) => s.alias === c.sourceAlias)?.nOut ?? 1),
			design.nIn,
		);
		if (pins * width > 65000 || design.nIn > 255 || design.outputs.length > 255)
			throw Error(
				"This project exceeds the interactive pin table budget. Use the CLI for larger designs.",
			);
		setTable(null);
		setReq(r);
		setBuilt(null);
		setProof(null);
		setObs(null);
		setReplayed(false);
		setNote("");
		setError("");
		setChainNote("");
	}
	function change(fn: (r: Execution) => void) {
		if (!req) return;
		const r = structuredClone(req);
		try {
			fn(r);
			replace(r);
		} catch (e) {
			setError(String(e));
		}
	}
	function navigate(n: number) {
		go(n);
		setError("");
		setNote("");
	}
	function sample() {
		void work("Opening historical sample", async () => {
			replace(await api<Execution>("sample/half-adder"));
			setOrigin("Historical sample");
			setInspected(null);
			go(1);
		});
	}
	function live() {
		void work("Reading X Layer", async () => {
			if (!/^0x[0-9a-f]{40}$/i.test(proc) || !/^(0|[1-9][0-9]*)$/.test(cid))
				throw Error(
					"Enter a 20-byte processor address and a decimal circuit ID.",
				);
			const append = addMode && req;
			const route = `import${append ? `?blockNumber=${req.imports[0].manifest.block.number}` : ""}`;
			const item = await api<Imported>(route, {
				schemaVersion: "1.0.0",
				chainId: 196,
				processor: proc,
				circuitId: cid,
			});
			setInspected(item);
			if (item.manifest.root.nState)
				throw Error(
					"Stateful circuit inspected. Flip supports stateless composition only.",
				);
			if (append) {
				if (req.imports.some((i) => i.manifestHash === item.manifestHash))
					throw Error("This source is already in the project.");
				const updated = structuredClone(req);
				let n = updated.project.sources.length + 1;
				while (updated.project.sources.some((s) => s.alias === `source${n}`))
					n++;
				updated.imports.push(item);
				updated.project.sources.push(source(item, `source${n}`));
				await api("compose", updated);
				replace(updated);
			} else {
				const r = await api<Execution>("new-project", {
					schemaVersion: "m4-1.0.0",
					kind: "PRODUCT_REQUEST",
					source: item,
				});
				replace(r);
				setOrigin("Live import snapshot");
			}
			setNote(`Imported and pinned at block ${item.manifest.block.number}.`);
		});
	}
	const title =
		req?.project.projectId === "historicalHalfAdder"
			? "Half-adder"
			: req?.project.projectId;
	async function openProject(f: File) {
		await work("Validating project", async () => {
			const raw = await readFile(f);
			await api("compose", raw);
			replace(JSON.parse(raw) as Execution);
			setInspected(null);
			setOrigin("Local project snapshot");
			go(1);
		});
	}
	function compile() {
		if (req)
			void work("Building netlist", async () => {
				setBuilt(await api<Built>("compose", req));
			});
	}
	function compare() {
		if (req)
			void work("Running local solver", async () => {
				setProof(null);
				setReplayed(false);
				try {
					setProof(await api<Proof>("compare", req));
				} catch (e) {
					throw Error(
						`Comparison UNKNOWN · ${e instanceof Error ? e.message : String(e)}`,
					);
				}
			});
	}
	function revalidate() {
		if (req)
			void work("Revalidating sources", async () => {
				const statuses: string[] = [];
				const r = structuredClone(req);
				for (const item of r.imports) {
					const v = await api<{
						integrity: { freshness: string; checkedBlock: { number: string } };
						changes: string[];
					}>("revalidate", item.manifest);
					statuses.push(
						`#${item.manifest.root.identity.circuitId} ${v.integrity.freshness} at ${v.integrity.checkedBlock.number} ${v.changes.join(", ")}`,
					);
					if (v.integrity.freshness === "STALE") {
						item.integrity = { ...item.integrity, freshness: "STALE" };
						replace(structuredClone(r));
					}
				}
				setChainNote(statuses.join(" · "));
			});
	}
	const stale = req?.imports.some((i) => i.integrity.freshness === "STALE");
	return (
		<>
			<a className="skip" href="#workspace">
				Skip to workspace
			</a>
			<header className="mast">
				<div className="brand">
					<i aria-hidden="true" />
					Flip
				</div>
				<span>Circuit workbench</span>
				<span className="network">
					X Layer <code>196</code>
				</span>
			</header>
			<div className="shell">
				<aside>
					<div className="kicker">Workspace</div>
					<strong>{title ?? "New project"}</strong>
					<nav aria-label="Workflow">
						{pages.map((name, i) => (
							<button
								type="button"
								key={name}
								disabled={!!busy || (!req && i > 0)}
								onClick={() => navigate(i)}
								aria-current={page === i ? "page" : undefined}
							>
								{name}
								<span aria-hidden="true">↗</span>
							</button>
						))}
					</nav>
					<div className="local">
						<b>Local session</b>
						<br />
						Project data goes to this device’s API. Live reads use its
						configured RPC.
					</div>
				</aside>
				<main id="workspace" tabIndex={-1}>
					<div className="trail">
						Workbench <span>/</span> {pages[page]}
					</div>
					<fieldset disabled={!!busy} className="workspace">
						<legend className="sr">Circuit workflow</legend>
						<div className="heading">
							<h1>{pages[page]}</h1>
							{origin && <small>{origin}</small>}
						</div>
						<p className="intro">{copy[page]}</p>
						{page === 0 && (
							<>
								{!req && (
									<article className="sample">
										<div>
											<span className="kicker">Historical sample</span>
											<h2>Half-adder</h2>
											<p>
												Trace two inputs through an 81-byte circuit. Swap its
												outputs to see the first wiring difference.
											</p>
											<button
												type="button"
												className="primary"
												onClick={sample}
											>
												Open sample →
											</button>
										</div>
										<Schematic />
									</article>
								)}
								<section>
									<h2>Import from X Layer</h2>
									<p>
										Read a registered processor and its dependencies on chain
										196.
									</p>
									<div className="fields address">
										<label>
											Processor address
											<input
												placeholder="0x…"
												value={proc}
												onChange={(e) => setProc(e.target.value)}
												spellCheck={false}
											/>
										</label>
										<label>
											Circuit ID
											<input
												value={cid}
												onChange={(e) => setCid(e.target.value)}
												inputMode="numeric"
											/>
										</label>
									</div>
									{req && (
										<label className="check">
											<input
												type="checkbox"
												checked={addMode}
												onChange={(e) => setAddMode(e.target.checked)}
											/>
											Add to project at pinned block{" "}
											{req.imports[0].manifest.block.number}
										</label>
									)}
									<div className="actions">
										<button type="button" onClick={live}>
											{req && !addMode
												? "Import as new project"
												: "Import circuit"}
										</button>
										<FileInput label="Open project file" open={openProject} />
									</div>
								</section>
								{inspected && (
									<SourceCard alias="Last inspected" item={inspected} />
								)}
								{req && (
									<section>
										<h2>Pinned sources</h2>
										<p>
											{stale ? "STALE" : "Snapshot"} · {origin} · block{" "}
											{req.imports[0].manifest.block.number}
										</p>
										{req.imports.map((i) => (
											<SourceCard
												key={i.manifestHash}
												item={i}
												alias={
													req.project.sources.find(
														(s) => s.manifestHash === i.manifestHash,
													)?.alias ?? "Source"
												}
											/>
										))}
										<div className="actions">
											<button type="button" onClick={revalidate}>
												Revalidate on chain
											</button>
											<button type="button" onClick={() => navigate(1)}>
												Open composition →
											</button>
										</div>
										{chainNote && <p>{chainNote}</p>}
									</section>
								)}
							</>
						)}
						{page === 1 && req && (
							<>
								{origin === "Historical sample" && (
									<div className="guide">
										<div>
											<b>Half-adder wiring fault</b>
											<p>
												Compare the original design, swap the two outputs, then
												verify the repair.
											</p>
										</div>
										<button
											type="button"
											onClick={() =>
												change((r) => {
													r.project.candidate.outputs.reverse();
												})
											}
										>
											Swap outputs
										</button>
										<button
											type="button"
											onClick={() =>
												change((r) => {
													const ref = r.project.referenceCandidate;
													if (ref) r.project.candidate = structuredClone(ref);
												})
											}
											disabled={!req.project.referenceCandidate}
										>
											Restore original
										</button>
									</div>
								)}
								{origin === "Historical sample" && (
									<details>
										<summary>Half-adder truth table</summary>
										<p>
											Inputs [A, B] and outputs [carry, sum] start at pin 0.
										</p>
										<button type="button" onClick={checkTable}>
											Evaluate four inputs
										</button>
										{table && (
											<>
												<p>
													{table.verdict} · {table.rows} rows evaluated
												</p>
												<table>
													<thead>
														<tr>
															<th>Input</th>
															<th>Expected</th>
															<th>Observed</th>
														</tr>
													</thead>
													<tbody>
														{sampleRows.map(([input, expected]) => (
															<tr key={input}>
																<th>{input}</th>
																<td>{expected}</td>
																<td>
																	{table.mismatches.find(
																		(m) => m.inputs.bits === input,
																	)?.actual.bits ?? expected}
																</td>
															</tr>
														))}
													</tbody>
												</table>
											</>
										)}
									</details>
								)}
								<Composer
									request={req}
									change={change}
									build={compile}
									built={built}
									next={() => navigate(2)}
								/>
							</>
						)}
						{page === 2 && req && (
							<Comparison
								r={req}
								change={change}
								run={compare}
								result={proof}
								next={() => navigate(3)}
							/>
						)}
						{page === 3 && req && (
							<>
								<section>
									<h2>Verification evidence</h2>
									<p>
										{proof
											? `Latest run · ${proof.report.verification.verdict} · ${proof.report.integrity.freshness}`
											: "Run a comparison or replay evidence for this project."}
									</p>
									<label className="check">
										<input
											type="checkbox"
											checked={observe}
											onChange={(e) => setObserve(e.target.checked)}
										/>
										Attach a fresh structural check from X Layer
									</label>
									<div className="actions">
										<button
											type="button"
											className="primary"
											disabled={!proof}
											onClick={() =>
												work("Re-running and exporting", async () => {
													const b = await api<Bundle>("export", {
														...productBody(req),
														observeChain: observe,
													});
													download("evidence.json", b);
													setProof(b.comparison);
													setObs(b.chainObservation);
													setNote(
														`Exported a new ${b.comparison.report.verification.verdict} run.`,
													);
												})
											}
										>
											Run and export evidence
										</button>
										<button
											type="button"
											onClick={() => download("project.json", req)}
										>
											Save project
										</button>
									</div>
								</section>
								<section>
									<h2>Replay a bundle</h2>
									<p>
										Flip uses the open project as the expected reference and
										recomputes the proof locally. Choose a project you trust
										independently.
									</p>
									<FileInput
										label="Replay evidence file"
										open={(f) =>
											work("Replaying evidence", async () => {
												setReplayed(false);
												setProof(null);
												const result = await api<Proof>("verify-bundle", {
													...productBody(req),
													bundleText: await readFile(f),
												});
												setProof(result);
												setReplayed(true);
											})
										}
									/>
									{replayed && proof && (
										<>
											<h3>Replay verified</h3>
											<Verdict value={proof} />
										</>
									)}
								</section>
								<section>
									<h2>Structural pre-flight</h2>
									<p>
										Read the current fee, check every pinned dependency, and
										probe the first source processor with a read-only call.
									</p>
									<button
										type="button"
										onClick={() =>
											work("Checking current chain", async () => {
												setObs(null);
												setObs(
													await api<Preflight>("preflight", productBody(req)),
												);
											})
										}
									>
										Run read-only pre-flight
									</button>
									{obs && (
										<div className="result">
											<h3>{obs.status.replaceAll("_", " ")}</h3>
											<p>
												{obs.reasonCode ?? "Observed the validated burn stage."}{" "}
												· {obs.integrity.freshness}
											</p>
											{obs.observation && (
												<p>
													Block {obs.observation.block.number} ·{" "}
													{obs.observation.feeWei} wei
												</p>
											)}
										</div>
									)}
								</section>
							</>
						)}
					</fieldset>
					<div role="status" aria-live="polite">
						{busy || note}
					</div>
					{error && (
						<div role="alert">
							<b>Operation incomplete</b>
							<p>{error}</p>
						</div>
					)}
				</main>
			</div>
		</>
	);
}
