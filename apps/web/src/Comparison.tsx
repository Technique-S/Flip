import { useState } from "react";
import { type DebugEdit, Debugger } from "./Debugger";
import { type Execution, indices, type Proof } from "./model";

type Props = {
	debugEdit: DebugEdit | null;
	setDebugEdit: (value: DebugEdit | null) => void;
	r: Execution;
	change: (fn: (r: Execution) => void) => void;
	run: () => void;
	result: Proof | null;
	next: () => void;
};
export function Verdict({ value }: { value: Proof }) {
	const v = value.report.verification,
		w = v.witness;
	return (
		<section className="result" aria-label="Verification result">
			<span className="kicker">Solver result</span>
			<h2>{v.verdict}</h2>
			<p>
				{v.verdict === "DIFFERENT"
					? "The evaluator reproduced different outputs for this input."
					: v.verdict === "EQUIVALENT"
						? "Every mapped output agrees for every input in this stateless comparison."
						: `The solver could not establish a conclusion. ${v.reasonCode === "SOLVER_TIMEOUT" ? "The solver timed out (SOLVER_TIMEOUT). Retry with a higher timeout." : (v.reasonCode ?? "")}`}
			</p>
			<p className="mono">
				{v.solverOutcome} · {value.resources.totalMs} ms ·{" "}
				{value.report.integrity.freshness}
			</p>
			{w && (
				<>
					<h3>Replayed counterexample</h3>
					<p>
						Input pins, starting at pin 0 <code>{w.inputs.bits || "∅"}</code>
					</p>
					<table>
						<thead>
							<tr>
								<th>Mapped pin</th>
								<th>Reference</th>
								<th>Candidate</th>
								<th>Behavior</th>
							</tr>
						</thead>
						<tbody>
							{indices(w.referenceOutputs.bits.length).map((i) => {
								const a = w.referenceOutputs.bits[i],
									b = w.candidateOutputs.bits[i],
									diff = a !== b;
								return (
									<tr key={`pin${i}`} className={diff ? "different" : ""}>
										<th>[{i}]</th>
										<td>{a}</td>
										<td>{b}</td>
										<td>{diff ? "≠ Different" : "= Same"}</td>
									</tr>
								);
							})}
						</tbody>
					</table>
				</>
			)}
			<details>
				<summary>Identities and proof context</summary>
				<pre>
					{JSON.stringify(
						{
							reference: value.referenceIdentity,
							candidate: value.candidateIdentity,
							scope: value.coverage,
							referenceManifest: value.report.referenceManifestHash,
							candidateManifest: value.report.candidateManifestHash,
							engine: value.engineHash,
						},
						null,
						2,
					)}
				</pre>
			</details>
		</section>
	);
}
export function Comparison({
	r,
	change,
	run,
	result,
	next,
	debugEdit,
	setDebugEdit,
}: Props) {
	const [maps, setMaps] = useState(false);
	const p = r.project,
		plan = p.comparison;
	function mapping(key: "inputMap" | "outputMap") {
		return (
			<div>
				<h3>
					{key === "inputMap"
						? "Reference input → candidate input"
						: "Reference output → candidate output"}
				</h3>
				{indices(plan[key].length).map((i) => (
					<label key={`pin${i}`}>
						Pin {i}
						<select
							aria-label={`${key} ${i}`}
							value={plan[key][i]}
							onChange={(e) => {
								const n = Number(e.target.value);
								change((r) => {
									const m = r.project.comparison[key],
										j = m.indexOf(n);
									m[j] = m[i];
									m[i] = n;
								});
							}}
						>
							{indices(plan[key].length).map((x) => (
								<option key={x}>{x}</option>
							))}
						</select>
					</label>
				))}
			</div>
		);
	}
	return (
		<>
			<h2>Comparison setup</h2>
			<p>
				Verify all inputs of two stateless circuits using explicit pin mappings.
			</p>
			<div className="fields">
				<label>
					Reference
					<select
						value={plan.referenceAlias ?? "local"}
						onChange={(e) =>
							change((d) => {
								const id = e.target.value;
								if (id === "local") {
									d.project.schemaVersion = "m3-1.0.0";
									d.project.referenceCandidate = structuredClone(
										d.project.candidate,
									);
									d.project.comparison.referenceAlias = null;
								} else {
									d.project.schemaVersion = "1.0.0";
									delete d.project.referenceCandidate;
									d.project.comparison.referenceAlias = id;
								}
							})
						}
					>
						<option value="local">
							{p.referenceCandidate
								? "Local reference design"
								: "Snapshot current candidate"}
						</option>
						{p.sources
							.filter((s) => !s.nState)
							.map((s) => (
								<option key={s.alias} value={s.alias}>
									{s.alias} · #{s.identity.circuitId}
								</option>
							))}
					</select>
				</label>
				<label>
					Intent
					<select
						value={r.relation}
						onChange={(e) =>
							change((d) => {
								d.relation = e.target.value as Execution["relation"];
								d.project.comparison.intent =
									d.relation === "BEHAVIORAL"
										? "UNDECLARED"
										: "TRUSTED_REFERENCE";
								d.project.comparison.trustAssertion =
									d.relation === "BEHAVIORAL" ? null : "";
							})
						}
					>
						<option value="BEHAVIORAL">Behavior only</option>
						<option value="REFERENCE">Trusted reference</option>
						<option value="PREVIOUS_VERSION">Previous version</option>
					</select>
				</label>
			</div>
			{r.relation !== "BEHAVIORAL" ? (
				<label>
					Why do you trust this reference?
					<input
						value={plan.trustAssertion ?? ""}
						maxLength={1000}
						onChange={(e) =>
							change((d) => {
								d.project.comparison.trustAssertion = e.target.value;
							})
						}
					/>
				</label>
			) : (
				<p>
					Intent is undeclared. A difference identifies behavior. Choosing the
					intended wiring requires a reference you trust.
				</p>
			)}
			<button type="button" onClick={() => setMaps(!maps)} aria-expanded={maps}>
				Pin mapping · {plan.inputMap.length} in / {plan.outputMap.length} out
			</button>
			{maps && (
				<div className="fields">
					{mapping("inputMap")}
					{mapping("outputMap")}
				</div>
			)}
			<h3>Execution limits</h3>
			<div className="fields">
				{(["gateCap", "solverTimeoutMs"] as const).map((k) => (
					<label key={k}>
						{k === "gateCap" ? "Gate budget" : "Timeout (ms)"}
						<input
							type="number"
							min="1"
							max="5000"
							value={p.limits[k]}
							onChange={(e) =>
								change((d) => {
									d.project.limits[k] = Number(e.target.value);
								})
							}
						/>
					</label>
				))}
			</div>
			<p>
				{p.limits.refDepthCap} REF levels · {p.limits.solverMemoryMiB} MiB
				worker limit
			</p>
			<button type="button" className="primary" onClick={run}>
				Run comparison →
			</button>
			{result && (
				<>
					<Verdict value={result} />
					<button type="button" onClick={next}>
						Open evidence →
					</button>
				</>
			)}
			<Debugger
				r={r}
				available={result !== null}
				change={change}
				run={run}
				undo={debugEdit}
				setUndo={setDebugEdit}
			/>
		</>
	);
}
