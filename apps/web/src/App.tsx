import { useEffect, useRef, useState } from "react";
import { Comparison, Verdict } from "./Comparison";
import { Composer } from "./Composer";
import type { DebugEdit } from "./Debugger";
import { Library } from "./Library";
import { PortablePanel, portableBody, type Portable } from "./Portable";
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

import { useCandidateEditor } from "./visual/useCandidateEditor";
import { checkInteractiveBudget } from "./visual/commands";

const pages = [
	"Sources",
	"Composition",
	"Wiring Canary",
	"Evidence",
	"Circuit Library",
] as const;
const copy = [
	"Import and inspect circuit sources.",
	"Connect pins and build a TAP-02 netlist.",
	"Compare a candidate against its reference.",
	"Export a run or replay evidence against the open project.",
	"Find processors, inspect circuit interfaces and reuse verified imports.",
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
	const cancelPortableFocus = useRef(false);

	const [portable, setPortableState] = useState<Portable | null>(null);
	function setPortable(value: Portable | null) {
		setPortableState(value);
		if (!value) {
			try {
				sessionStorage.removeItem("flip-portable");
			} catch {
				/* Existing storage notice covers unavailable storage. */
			}
		}
	}
	const [debugEdit, setDebugEdit] = useState<DebugEdit | null>(null);
	const [page, go] = useState(0),
		[req, setReq] = useState<Execution | null>(null),
		[origin, setOrigin] = useState("");
	const [built, setBuilt] = useState<Built | null>(null),
		[proof, setProof] = useState<Proof | null>(null);
	const [busy, setBusy] = useState(""),
		lock = useRef(false),
		[error, setError] = useState(""),
		[note, setNote] = useState("");
	useEffect(() => {
		if (!busy && cancelPortableFocus.current) {
			document.getElementById("portable-agent-heading")?.focus();
			cancelPortableFocus.current = false;
		}
	}, [busy]);
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
	const [storageMessage, setStorageMessage] = useState("");
	const [resetting, setResetting] = useState(false);
	const [pastEvidence, setPastEvidence] = useState<{
		runs: { request: Execution; proof: Proof; revision: number }[];
		evicted: boolean;
	}>({ runs: [], evicted: false });
	const historicalRuns = pastEvidence.runs,
		evictedRuns = pastEvidence.evicted;
	const editor = useCandidateEditor({
		commit: (r) => replace(r, true),
		invalidate,
		busy: () => lock.current,
	});
	function invalidate() {
		if (proof && req)
			setPastEvidence((previousState) => {
				const previous = previousState.runs;
				const entry = {
					request: structuredClone(req),
					proof: structuredClone(proof),
					revision: editor.revision,
				};
				if (previous.some((p) => JSON.stringify(p) === JSON.stringify(entry)))
					return previousState;
				const next = [...previous, entry];
				let evicted = previousState.evicted;
				while (
					next.length > 10 ||
					new TextEncoder().encode(JSON.stringify(next)).length > 4 * 1048576
				) {
					next.shift();
					evicted = true;
				}
				return { runs: next, evicted };
			});
		setTable(null);
		setBuilt(null);
		setProof(null);
		setObs(null);
		setReplayed(false);
		setChainNote("");
	}

	// biome-ignore lint/correctness/useExhaustiveDependencies: Restore once on mount.
	useEffect(() => {
		let saved: string | null = null;
		try {
			saved = sessionStorage.getItem("flip-project");
		} catch {
			setStorageMessage(
				"Browser storage unavailable. Save a project file before refreshing.",
			);
		}
		if (saved)
			void work("Restoring project", async () => {
				await api("compose", saved);
				const restored = JSON.parse(saved) as Execution;
				const editRecovery = sessionStorage.getItem("flip-edit-draft");
				const exportCheckpoint = sessionStorage.getItem("flip-edit-checkpoint");
				const savedPackage = sessionStorage.getItem("flip-portable");
				replace(restored);
				editor.restoreSaved(exportCheckpoint);
				if (savedPackage) {
					const checked = await api<Portable>(
						"portable",
						portableBody("validate", { package: JSON.parse(savedPackage) }),
					);
					if (
						checked.executionRequest.project.projectId ===
						restored.project.projectId
					)
						setPortable(checked);
				}
				await editor.restore(editRecovery);
				setOrigin("Restored snapshot");
				setStorageMessage("Project restored from this browser session.");
			});
	}, []);
	useEffect(() => {
		if (error) document.getElementById("operation-error")?.focus();
	}, [error]);
	useEffect(() => {
		if (req) {
			try {
				sessionStorage.setItem("flip-project", JSON.stringify(req));
			} catch {
				setStorageMessage(
					"Browser storage is full or unavailable. Save the project file before refreshing.",
				);
			}
		}
	}, [req]);
	useEffect(() => {
		try {
			if (portable)
				sessionStorage.setItem("flip-portable", JSON.stringify(portable));
		} catch {
			setStorageMessage(
				"Portable history could not be saved in this browser. Download the complete project before refreshing.",
			);
		}
	}, [portable]);
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
	const original = useRef<Execution["project"]["candidate"] | null>(null);
	function rememberObservation(observation: Preflight | null) {
		if (req && observation?.integrity.freshness === "STALE") {
			const updated = structuredClone(req);
			for (const item of updated.imports) item.integrity.freshness = "STALE";
			replace(updated);
		}
		setObs(observation);
	}
	async function work(label: string, fn: () => Promise<void>) {
		if (lock.current) return;
		if (editor.blocked()) {
			setError(
				"Complete or discard the local edit draft before executing or exporting this project.",
			);
			return;
		}
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
	function replace(r: Execution, editing = false) {
		checkInteractiveBudget(r);
		invalidate();
		if (!editing) editor.open(r);
		try {
			sessionStorage.setItem("flip-project", JSON.stringify(r));
		} catch {
			setStorageMessage(
				"Browser storage is full or unavailable. Save the project file before refreshing.",
			);
		}
		setReq(r);
		if (req && r.project.projectId !== req.project.projectId) setPortable(null);
		setNote("");
		setError("");
	}
	function change(fn: (r: Execution) => void) {
		if (!req) return;
		if (!editor.matches(req)) {
			setError("Project changed. Repeat the edit on the current revision.");
			return;
		}
		try {
			const next = structuredClone(editor.advanced ?? req);
			fn(next);
			if (JSON.stringify(next) === JSON.stringify(req)) {
				if (editor.advanced) editor.cancel();
				return;
			}
			if (
				JSON.stringify(next.project.candidate) ===
				JSON.stringify(req.project.candidate)
			)
				editor.configure(next);
			else editor.change(fn);
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
			const historical = await api<Execution>("sample/half-adder");
			original.current = structuredClone(historical.project.candidate);
			setPortable(null);
			replace(historical);
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
			const parsed = JSON.parse(raw);
			if (parsed.kind === "PORTABLE_PROJECT") {
				const opened = await api<{
					executionRequest: Execution;
					package: Portable;
				}>("portable", portableBody("open", { package: parsed }));
				replace(opened.executionRequest);
				setPortable(opened.package);
			} else {
				await api("compose", raw);
				replace(parsed as Execution);
				setPortable(null);
			}
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
								disabled={!!busy || editor.pending || (!req && i > 0 && i < 4)}
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
					{storageMessage && <p role="status">{storageMessage}</p>}
					{req && (
						<div className="actions">
							<button
								type="button"
								disabled={!!busy}
								onClick={() => setResetting(true)}
							>
								Reset workspace
							</button>
							{resetting && (
								<>
									<span>Discard this session’s project?</span>
									<button
										type="button"
										onClick={() => {
											try {
												sessionStorage.removeItem("flip-project");
											} catch {}
											editor.open(null);
											setReq(null);
											setPortable(null);
											setDebugEdit(null);
											setProof(null);
											setBuilt(null);
											setObs(null);
											setOrigin("");
											go(0);
											setResetting(false);
											setStorageMessage("Workspace reset.");
										}}
									>
										Confirm reset
									</button>
									<button type="button" onClick={() => setResetting(false)}>
										Keep project
									</button>
								</>
							)}
						</div>
					)}
					<div className="trail">
						Workbench <span>/</span> {pages[page]}
					</div>
					{req && (
						<div className="edit-status">
							<p role="status" aria-label="Editing status">
								Revision {editor.revision} ·{" "}
								{editor.dirty
									? "Unsaved changes"
									: "No committed changes since opening or export request"}
								{editor.blocked()
									? " · Local draft — unsaved; execution and export blocked"
									: ""}
								. {editor.message} {editor.storageIssue}
							</p>
							{editor.blocked() && (
								<button type="button" onClick={editor.cancel}>
									{editor.pending ? "Cancel pending edit" : "Discard draft"}
								</button>
							)}
							{editor.dirty && (
								<small>
									Export before opening another project; a new project clears
									this edit history. Browser session storage is separate from
									exported files.
								</small>
							)}
						</div>
					)}
					<fieldset disabled={!!busy || editor.pending} className="workspace">
						<legend className="sr">Circuit workflow</legend>
						<div className="heading">
							<h1>{pages[page]}</h1>
							{origin && <small>{origin}</small>}
						</div>
						<p className="intro">{copy[page]}</p>
						{page === 4 && (
							<Library
								onImport={async (item) => {
									if (item.manifest.root.nState)
										throw Error(
											"Stateful circuit inspected. Stateless composition is unavailable.",
										);
									const project = await api<Execution>("new-project", {
										schemaVersion: "m4-1.0.0",
										kind: "PRODUCT_REQUEST",
										source: item,
									});
									replace(project);
									setInspected(item);
									setOrigin("Library import snapshot");
									go(1);
								}}
							/>
						)}
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
													const ref = original.current;
													if (ref) r.project.candidate = structuredClone(ref);
												})
											}
											disabled={!original.current}
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
									editor={editor}
									request={editor.advanced ?? req}
									change={change}
									build={compile}
									built={built}
									next={() => navigate(2)}
								/>
							</>
						)}
						{page === 2 && req && (
							<Comparison
								blocked={editor.blocked()}
								debugEdit={debugEdit}
								setDebugEdit={setDebugEdit}
								r={editor.advanced ?? req}
								change={change}
								run={compare}
								result={proof}
								next={() => navigate(3)}
							/>
						)}
						{page === 3 && req && (
							<>
								<fieldset
									className="execution-guard"
									disabled={editor.blocked()}
								>
									<legend className="sr">Portable project actions</legend>
									<PortablePanel
										onExport={editor.markExported}
										request={req}
										value={portable}
										update={setPortable}
										openRevision={(p) => {
											replace(p.executionRequest);
											setPortable(p);
										}}
										work={work}
									/>
								</fieldset>
								<section>
									<h2>Verification evidence</h2>
									{historicalRuns.length > 0 && (
										<details>
											<summary>
												Historical comparisons ({historicalRuns.length}) — not
												current verification
											</summary>
											<p>
												These are original comparison records bound to the
												request and revision shown. Undo does not reverify them.
												Keep exported evidence separately.
											</p>
											{historicalRuns.map((run) => (
												<details key={JSON.stringify(run)}>
													<summary>
														{run.request.project.projectId} · revision{" "}
														{run.revision} · historical{" "}
														{run.proof.report.verification.verdict}
													</summary>
													<pre>{JSON.stringify(run, null, 2)}</pre>
												</details>
											))}
										</details>
									)}
									{evictedRuns && (
										<p>
											Earlier local comparisons exceeded the in-memory history
											limit. Retain exported evidence files.
										</p>
									)}

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
											disabled={!proof || editor.blocked()}
											onClick={() =>
												work("Re-running and exporting", async () => {
													const b = await api<Bundle>("export", {
														...productBody(req),
														observeChain: observe,
													});
													download("evidence.json", b);
													rememberObservation(b.chainObservation);
													setProof(b.comparison);
													setNote(
														`Exported a new ${b.comparison.report.verification.verdict} run.`,
													);
												})
											}
										>
											Run and export evidence (JSON)
										</button>
										<button
											type="button"
											disabled={editor.blocked()}
											onClick={() => {
												if (!editor.blocked()) {
													download("project.json", req);
													editor.markExported(req);
												}
											}}
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
										probe the first source processor with a read-only call. No
										transaction broadcast.
									</p>
									<button
										type="button"
										onClick={() =>
											work("Checking current chain", async () => {
												setObs(null);
												rememberObservation(
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
					{busy === "Running bounded portable workflow" && (
						<button
							type="button"
							onClick={() => {
								cancelPortableFocus.current = true;
								window.dispatchEvent(new Event("flip-cancel-portable"));
							}}
						>
							Cancel portable workflow
						</button>
					)}
					<div role="status" aria-live="polite">
						{busy ||
							note ||
							(proof
								? "Result: " +
									proof.report.verification.verdict +
									". Freshness: " +
									proof.report.integrity.freshness +
									". Intent: " +
									req?.project.comparison.intent +
									(proof.report.verification.witness
										? ". Counterexample available."
										: "")
								: "")}
					</div>
					{error && (
						<div role="alert" id="operation-error" tabIndex={-1}>
							<b>Operation incomplete</b>
							<p>{error}</p>
						</div>
					)}
				</main>
			</div>
		</>
	);
}
