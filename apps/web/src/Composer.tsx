import { useState } from "react";
import {
	type Built,
	type Component,
	type Execution,
	external,
	indices,
	type Pin,
} from "./model";

type Props = {
	request: Execution;
	change: (fn: (d: Execution) => void) => void;
	build: () => void;
	built: Built | null;
	next: () => void;
};
const pinName = (p: Pin) => `${p.component ?? "external"} [${p.pin}]`;
export function Composer({ request, change, build, built, next }: Props) {
	const [selected, select] = useState("");
	const [kind, setKind] = useState("NAND");
	const { candidate: d, sources } = request.project;
	function choices(before: number) {
		const pins = indices(d.nIn).map(external);
		for (const c of d.components.slice(0, before)) {
			const n =
				c.kind === "NAND"
					? 1
					: (sources.find((s) => s.alias === c.sourceAlias)?.nOut ?? 0);
			pins.push(...indices(n).map((pin) => ({ component: c.instanceId, pin })));
		}
		return pins;
	}
	function row(
		target: string,
		p: Pin,
		available: Pin[],
		apply: (r: Execution, p: Pin) => void,
	) {
		return (
			<tr key={target} className={target === selected ? "selected" : ""}>
				<th scope="row">{target}</th>
				<td>
					<select
						aria-label={`Source for ${target}`}
						value={JSON.stringify([p.component, p.pin])}
						onFocus={() => select(target)}
						onChange={(e) => {
							const [component, pin] = JSON.parse(e.target.value);
							change((r) => apply(r, { component, pin }));
						}}
					>
						{!available.some(
							(pin) => pin.component === p.component && pin.pin === p.pin,
						) && (
							<option disabled value={JSON.stringify([p.component, p.pin])}>
								Disconnected · {pinName(p)}
							</option>
						)}
						{available.map((pin) => (
							<option
								key={pinName(pin)}
								value={JSON.stringify([pin.component, pin.pin])}
							>
								{pinName(pin)}
							</option>
						))}
					</select>
				</td>
			</tr>
		);
	}
	function add() {
		change((r) => {
			const design = r.project.candidate;
			const src = sources.find((s) => s.alias === kind);
			let i = design.components.length + 1;
			while (design.components.some((c) => c.instanceId === `part${i}`)) i++;
			const first = choices(d.components.length)[0];
			const c: Component = {
				kind: src ? "REF" : "NAND",
				instanceId: `part${i}`,
				inputs: indices(src?.nIn ?? 2).map(() => first),
			};
			if (src) c.sourceAlias = src.alias;
			design.components.push(c);
		});
	}
	return (
		<>
			<div className="bar">
				<h2>Candidate wiring</h2>
				<button type="button" onClick={build}>
					Build netlist
				</button>
			</div>
			<p>
				Each input connects to an external pin or an earlier component output.
			</p>
			<label>
				External inputs
				<input
					type="number"
					min="0"
					max="255"
					value={d.nIn}
					onChange={(e) => {
						const n = Number(e.target.value);
						if (Number.isInteger(n) && n >= 0 && n <= 255)
							change((r) => {
								r.project.candidate.nIn = n;
								r.project.comparison.inputMap = indices(n);
							});
					}}
				/>
			</label>
			<div className="parts">
				{d.components.map((c, i) => (
					<section className="part" key={c.instanceId}>
						<header>
							<h3>{c.instanceId}</h3>
							<code>
								{c.kind}
								{c.sourceAlias ? ` / ${c.sourceAlias}` : ""}
							</code>
						</header>
						<table>
							<caption className="sr">Connections for {c.instanceId}</caption>
							<thead>
								<tr>
									<th>Destination</th>
									<th>Source output</th>
								</tr>
							</thead>
							<tbody>
								{c.inputs.map((p, j) =>
									row(`${c.instanceId} [${j}]`, p, choices(i), (r, p) => {
										r.project.candidate.components[i].inputs[j] = p;
									}),
								)}
							</tbody>
						</table>
					</section>
				))}
			</div>
			<div className="actions">
				<label>
					Component
					<select value={kind} onChange={(e) => setKind(e.target.value)}>
						<option value="NAND">NAND glue</option>
						{sources
							.filter((s) => !s.nState && s.nIn <= 255 && s.nOut <= 255)
							.map((s) => (
								<option key={s.alias} value={s.alias}>
									{s.alias} · REF
								</option>
							))}
					</select>
				</label>
				<button
					type="button"
					disabled={
						!choices(d.components.length).length &&
						(sources.find((s) => s.alias === kind)?.nIn ?? 2) > 0
					}
					onClick={add}
				>
					Add component
				</button>
				{d.components.length > 0 && (
					<button
						type="button"
						onClick={() =>
							change((r) => {
								r.project.candidate.components.pop();
							})
						}
					>
						Remove last component
					</button>
				)}
			</div>
			<h2>Final outputs</h2>
			<table>
				<thead>
					<tr>
						<th>Destination</th>
						<th>Source output</th>
					</tr>
				</thead>
				<tbody>
					{d.outputs.map((p, j) =>
						row(`output [${j}]`, p, choices(d.components.length), (r, p) => {
							r.project.candidate.outputs[j] = p;
						}),
					)}
				</tbody>
			</table>
			<div className="actions">
				<button
					type="button"
					disabled={!choices(d.components.length).length}
					onClick={() =>
						change((r) => {
							r.project.candidate.outputs.push(choices(d.components.length)[0]);
							r.project.comparison.outputMap = indices(
								r.project.candidate.outputs.length,
							);
						})
					}
				>
					Add output
				</button>
				<button
					type="button"
					disabled={d.outputs.length <= 1}
					onClick={() =>
						change((r) => {
							r.project.candidate.outputs.pop();
							r.project.comparison.outputMap = indices(
								r.project.candidate.outputs.length,
							);
						})
					}
				>
					Remove last output
				</button>
			</div>
			{request.project.referenceCandidate && (
				<details>
					<summary>Local reference design</summary>
					<pre>
						{JSON.stringify(request.project.referenceCandidate, null, 2)}
					</pre>
					<button
						type="button"
						onClick={() =>
							change((r) => {
								r.project.referenceCandidate = structuredClone(
									r.project.candidate,
								);
							})
						}
					>
						Use current wiring as reference
					</button>
				</details>
			)}
			{built && (
				<div className="result">
					<h3>Netlist built</h3>
					<p>
						{(built.netlist.length - 2) / 2} bytes ·{" "}
						{built.manifest.expandedGates} expanded gates ·{" "}
						{built.manifest.dependencies.length} dependencies
					</p>
					<details>
						<summary>TAP-02 bytes and manifest</summary>
						<pre>{JSON.stringify(built, null, 2)}</pre>
					</details>
					<button type="button" className="primary" onClick={next}>
						Compare circuits →
					</button>
				</div>
			)}
		</>
	);
}
