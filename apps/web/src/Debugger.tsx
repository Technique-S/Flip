import { useEffect, useRef, useState } from "react";
import { api, type Execution, indices } from "./model";

type Action = {
	classification: "CANDIDATE_ACTION";
	actionId: string;
	title: string;
	reasoning: string;
	edits: {
		location: string;
		before: { component: string | null; pin: number };
		after: { component: string | null; pin: number };
	}[];
	proposedRevision: Execution;
};
type Diagnostic = {
	classification: string;
	attribution: string;
	reasoning: string;
	reasonCode: string | null;
	projectHash: string;
	executionHash: string;
	diagnosticEngineHash: string;
	semanticHash: string;
	differingOutputBits: number[];
	comparison: null | {
		report: {
			referenceManifestHash: string;
			candidateManifestHash: string;
			verification: {
				verdict: string;
				witness: null | {
					inputs: { bits: string };
					referenceOutputs: { bits: string };
					candidateOutputs: { bits: string };
				};
			};
		};
	};
	connections: {
		side: string;
		connectionRef: string;
		sourceSignal: number;
		destination: string;
		instanceId: string | null;
		inputPin: number | null;
		outputPin: number | null;
		netlistHash: string;
	}[];
	actions: Action[];
	correction: null | {
		classification: string;
		scope: string;
		revisedProjectHash: string;
	};
};
export type DebugEdit = { original: Execution; applied: Execution };
type Props = {
	undo: DebugEdit | null;
	setUndo: (value: DebugEdit | null) => void;
	r: Execution;
	available: boolean;
	change: (fn: (r: Execution) => void) => void;
	run: () => void;
};

export function Debugger({ r, available, change, run, undo, setUndo }: Props) {
	const [diagnostic, setDiagnostic] = useState<Diagnostic | null>(null);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState("");
	const [selected, setSelected] = useState(false);
	const [page, setPage] = useState(0);
	const signature = JSON.stringify(r);
	const live = useRef(signature);
	live.current = signature;
	useEffect(() => {
		if (signature) {
			setDiagnostic(null);
			setSelected(false);
			setPage(0);
			setError("");
			setBusy(false);
		}
	}, [signature]);
	useEffect(
		() => () => {
			live.current = "";
		},
		[],
	);
	async function inspect(actionId?: string) {
		const bound = signature;
		setBusy(true);
		setError("");
		try {
			const value = await api<Diagnostic>("debug", {
				schemaVersion: "m45-debugging-1.0.0",
				kind: "DEBUG_REQUEST",
				executionRequest: r,
				operation: actionId ? "verify-correction" : "diagnose",
				...(actionId ? { actionId } : {}),
			});
			if (live.current === bound) {
				setDiagnostic(value);
				setPage(0);
			}
		} catch (e) {
			if (live.current === bound)
				setError(
					`Diagnostics unavailable. ${e instanceof Error ? e.message : String(e)}`,
				);
		} finally {
			if (live.current === bound) setBusy(false);
		}
	}
	const action = diagnostic?.actions[0];
	const witness = diagnostic?.comparison?.report.verification.witness;
	const canUndo = undo !== null && signature === JSON.stringify(undo.applied);
	function apply() {
		if (!action || !selected) return;
		const applied = structuredClone(r);
		applied.project.candidate = structuredClone(
			action.proposedRevision.project.candidate,
		);
		setUndo({ original: structuredClone(r), applied });
		change((draft) => {
			draft.project.candidate = structuredClone(applied.project.candidate);
		});
	}
	return (
		<section
			className="debugger"
			aria-label="Connection debugger"
			aria-busy={busy}
		>
			<h2>Connection debugger</h2>
			<p>
				Trace a replayed output difference to numeric connections. Relevant
				paths show influencing computation; they do not prove which connection
				is defective.
			</p>
			<button
				type="button"
				disabled={!available || busy}
				onClick={() => void inspect()}
			>
				Inspect connection paths
			</button>
			{!available && !canUndo && (
				<p>Run a comparison to inspect its signal paths.</p>
			)}
			{busy && (
				<p role="status">
					Replaying the comparison and tracing bounded signal paths…
				</p>
			)}
			{error && <p role="alert">{error}</p>}
			{canUndo && (
				<div className="debug-edit">
					<p>
						Candidate revision applied locally. The original project is retained
						for reverting. Run a new comparison to check this workspace
						revision.
					</p>
					<button type="button" onClick={run}>
						Compare applied revision
					</button>
					<button
						type="button"
						onClick={() => {
							if (undo) {
								change((draft) => {
									draft.project.candidate = structuredClone(
										undo.original.project.candidate,
									);
								});
								setUndo(null);
							}
						}}
					>
						Revert candidate correction
					</button>
				</div>
			)}
			{diagnostic && (
				<>
					<p role="status" className="mono">
						{diagnostic.classification} · {diagnostic.attribution}
					</p>
					<p>
						{diagnostic.reasoning}{" "}
						{diagnostic.reasonCode && <code>{diagnostic.reasonCode}</code>}
					</p>
					{witness && (
						<div className="debug-witness">
							<h3>Witness bound to these paths</h3>
							<p>
								Input pins (pin 0 first):{" "}
								<code>{witness.inputs.bits || "∅"}</code>
							</p>
							<table>
								<thead>
									<tr>
										<th>Output pin</th>
										<th>Reference</th>
										<th>Candidate</th>
										<th>Observation</th>
									</tr>
								</thead>
								<tbody>
									{indices(witness.referenceOutputs.bits.length).map((i) => (
										<tr
											key={`debug-pin-${i}`}
											className={
												diagnostic.differingOutputBits.includes(i)
													? "different"
													: ""
											}
										>
											<th>[{i}]</th>
											<td>{witness.referenceOutputs.bits[i]}</td>
											<td>{witness.candidateOutputs.bits[i]}</td>
											<td>
												{diagnostic.differingOutputBits.includes(i)
													? "Different output"
													: "Same output"}
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					)}
					{diagnostic.connections.length > 0 && (
						<>
							<h3>Relevant connection paths</h3>
							<p>
								{diagnostic.connections.length} connections · showing{" "}
								{page * 50 + 1}–
								{Math.min((page + 1) * 50, diagnostic.connections.length)}. Each
								row is relevant computation, not a fault attribution.
							</p>
							<section
								className="debug-traces"
								aria-label="Relevant connection paths"
								// biome-ignore lint/a11y/noNoninteractiveTabindex: Keyboard users must scroll the bounded trace region.
								tabIndex={0}
							>
								<table>
									<thead>
										<tr>
											<th>Design / path</th>
											<th>Numeric connection</th>
											<th>Component pin</th>
										</tr>
									</thead>
									<tbody>
										{diagnostic.connections
											.slice(page * 50, (page + 1) * 50)
											.map((c) => (
												<tr
													key={`${c.side}:${c.connectionRef}`}
													className="debug-relevant"
												>
													<th>
														{c.side}
														<br />
														<code>{c.connectionRef}</code>
													</th>
													<td>
														Signal {c.sourceSignal} →{" "}
														<code>{c.destination}</code>
														<br />
														Relevant connection
													</td>
													<td>
														{c.instanceId ?? "Nested or generated"}
														<br />
														{c.inputPin !== null
															? `Input [${c.inputPin}]`
															: `Output [${c.outputPin}]`}
													</td>
												</tr>
											))}
									</tbody>
								</table>
							</section>
							{diagnostic.connections.length > 50 && (
								<div className="actions">
									<button
										type="button"
										disabled={page === 0}
										onClick={() => setPage(page - 1)}
									>
										Previous paths
									</button>
									<button
										type="button"
										disabled={(page + 1) * 50 >= diagnostic.connections.length}
										onClick={() => setPage(page + 1)}
									>
										Next paths
									</button>
								</div>
							)}
						</>
					)}
					{action && (
						<div className="debug-proposal">
							<h3>Candidate correction</h3>
							<p>{action.reasoning}</p>
							<label className="debug-choice">
								<input
									type="radio"
									name="debug-action"
									checked={selected}
									onChange={() => setSelected(true)}
								/>
								{action.title}
							</label>
							<table>
								<thead>
									<tr>
										<th>Mapping</th>
										<th>Original</th>
										<th>Proposed</th>
									</tr>
								</thead>
								<tbody>
									{action.edits.slice(0, 50).map((e) => (
										<tr key={e.location}>
											<th>
												<code>{e.location}</code>
											</th>
											<td>
												{e.before.component ?? "External input"} [{e.before.pin}
												]
											</td>
											<td>
												{e.after.component ?? "External input"} [{e.after.pin}]
											</td>
										</tr>
									))}
								</tbody>
							</table>
							{action.edits.length > 50 && (
								<p>
									Showing the first 50 of {action.edits.length} edits. Larger
									revisions require the downloaded diagnostic and a separate
									project file.
								</p>
							)}
							<button
								type="button"
								disabled={!selected || busy}
								onClick={() => void inspect(action.actionId)}
							>
								Verify proposed revision
							</button>
							{diagnostic.correction && (
								<p role="status">
									{diagnostic.correction.classification} ·{" "}
									{diagnostic.correction.scope}. This check is relative to the
									selected reference and historical snapshots.
								</p>
							)}
							<button
								type="button"
								disabled={!selected || busy || action.edits.length > 50}
								onClick={apply}
							>
								Apply candidate locally
							</button>
						</div>
					)}
					<details>
						<summary>Bound identities and manifests</summary>
						<pre>
							{JSON.stringify(
								{
									projectHash: diagnostic.projectHash,
									executionHash: diagnostic.executionHash,
									diagnosticEngineHash: diagnostic.diagnosticEngineHash,
									semanticHash: diagnostic.semanticHash,
									referenceManifestHash:
										diagnostic.comparison?.report.referenceManifestHash,
									candidateManifestHash:
										diagnostic.comparison?.report.candidateManifestHash,
									connectionNetlists: [
										...new Set(
											diagnostic.connections.map((c) => c.netlistHash),
										),
									],
									freshness:
										"Pinned historical snapshots; no live revalidation claimed",
								},
								null,
								2,
							)}
						</pre>
					</details>
					<button
						type="button"
						onClick={() => {
							const url = URL.createObjectURL(
								new Blob([JSON.stringify(diagnostic, null, 2)], {
									type: "application/json",
								}),
							);
							const a = document.createElement("a");
							a.href = url;
							a.download = "flip-diagnostics.json";
							a.click();
							URL.revokeObjectURL(url);
						}}
					>
						Download diagnostic JSON
					</button>
				</>
			)}
		</section>
	);
}
