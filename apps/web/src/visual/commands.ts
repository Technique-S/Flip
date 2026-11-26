import type { Execution, Pin } from "../model";
import { projectExecution } from "./projection";

export type NandCommand =
	| { type: "AddNand"; instanceId: string; inputs: [Pin, Pin] }
	| { type: "RemoveNand"; instanceId: string };
const name = (v: unknown): v is string =>
	typeof v === "string" && /^[A-Za-z][A-Za-z0-9_-]{0,63}$/.test(v);
export const requestKey = (r: Execution) => JSON.stringify(r); // Exact UI snapshot, NOT a canonical hash.
const size = (s: string) => new TextEncoder().encode(s).length;
export function checkInteractiveBudget(r: Execution) {
	const d = r.project.candidate;
	const pins = d.components.reduce(
		(n, c) => n + c.inputs.length,
		d.outputs.length,
	);
	const width = d.components.reduce(
		(n, c) =>
			n + (r.project.sources.find((s) => s.alias === c.sourceAlias)?.nOut ?? 1),
		d.nIn,
	);
	if (pins * width > 65000 || d.nIn > 255 || d.outputs.length > 255)
		throw Error(
			"This project exceeds the interactive pin table budget. Use the CLI for larger designs.",
		);
	if (size(requestKey(r)) > 1048576)
		throw Error("Project exceeds the 1 MiB interactive request limit.");
}
export function availablePins(r: Execution): Pin[] {
	const d = r.project.candidate;
	const pins: Pin[] = Array.from({ length: d.nIn }, (_, pin) => ({
		component: null,
		pin,
	}));
	for (const c of d.components) {
		const n =
			c.kind === "NAND"
				? 1
				: (r.project.sources.find((s) => s.alias === c.sourceAlias)?.nOut ?? 0);
		for (let pin = 0; pin < n; pin++)
			pins.push({ component: c.instanceId, pin });
	}
	return pins;
}
export function removalProblem(r: Execution, id: string): string | null {
	const c = r.project.candidate.components.find((c) => c.instanceId === id);
	if (c?.kind !== "NAND")
		return "Select an existing NAND component. REF removal is unavailable here.";
	const refs: string[] = [];
	r.project.candidate.components.forEach((c, i) => {
		c.inputs.forEach((p, j) => {
			if (p.component === id)
				refs.push(`project.candidate.components[${i}].inputs[${j}]`);
		});
	});
	r.project.candidate.outputs.forEach((p, i) => {
		if (p.component === id) refs.push(`project.candidate.outputs[${i}]`);
	});
	return refs.length
		? `Cannot remove ${id}: referenced by ${refs.slice(0, 8).join(", ")}${refs.length > 8 ? ` and ${refs.length - 8} more` : ""}. Change those mappings explicitly in Advanced first.`
		: null;
}
export function proposeNand(r: Execution, value: unknown): Execution {
	if (!value || typeof value !== "object" || Array.isArray(value))
		throw Error("Invalid edit command.");
	const c = value as Record<string, unknown>;
	if (!name(c.instanceId))
		throw Error(
			"Component ID must start with a letter and contain at most 64 letters, digits, underscores or hyphens.",
		);
	if (c.type !== "AddNand" && c.type !== "RemoveNand")
		throw Error("Unsupported edit command.");
	const keys =
		c.type === "AddNand"
			? ["type", "instanceId", "inputs"]
			: ["type", "instanceId"];
	if (
		Object.keys(c).length !== keys.length ||
		Object.keys(c).some((k) => !keys.includes(k))
	)
		throw Error("Unexpected edit command fields.");
	const next = structuredClone(r);
	if (c.type === "AddNand") {
		if (
			next.project.candidate.components.some(
				(x) => x.instanceId === c.instanceId,
			)
		)
			throw Error("Component ID already exists.");
		if (!Array.isArray(c.inputs) || c.inputs.length !== 2)
			throw Error("Choose exactly two explicit NAND input sources.");
		const available = availablePins(r);
		const inputs = c.inputs.map((p: unknown) => {
			if (!p || typeof p !== "object" || Array.isArray(p))
				throw Error("Invalid input binding.");
			const v = p as Record<string, unknown>;
			if (
				Object.keys(v).length !== 2 ||
				!("component" in v) ||
				!("pin" in v) ||
				(v.component !== null && !name(v.component)) ||
				typeof v.pin !== "number" ||
				!Number.isInteger(v.pin) ||
				!available.some((a) => a.component === v.component && a.pin === v.pin)
			)
				throw Error(
					"Input must identify an existing external or preceding output pin.",
				);
			return { component: v.component as string | null, pin: v.pin };
		});
		next.project.candidate.components.push({
			kind: "NAND",
			instanceId: c.instanceId,
			inputs,
		});
	} else {
		const issue = removalProblem(r, c.instanceId);
		if (issue) throw Error(issue);
		next.project.candidate.components =
			next.project.candidate.components.filter(
				(x) => x.instanceId !== c.instanceId,
			);
	}
	checkInteractiveBudget(next);
	projectExecution(next); // Reuse bounded display checks; Python compose still decides acceptance.
	return next;
}
export type History = {
	present: Execution;
	past: Execution[];
	future: Execution[];
	saved: string;
	evicted: number;
};
export const openHistory = (r: Execution): History => ({
	present: structuredClone(r),
	past: [],
	future: [],
	saved: requestKey(r),
	evicted: 0,
});
function bounded(h: History): History {
	let bytes = [h.present, ...h.past, ...h.future].reduce(
		(n, r) => n + size(requestKey(r)),
		size(h.saved),
	);
	while (h.past.length + h.future.length > 100 || bytes > 4 * 1048576) {
		const removed = h.past.length ? h.past.shift() : h.future.pop();
		if (!removed) break;
		bytes -= size(requestKey(removed));
		h.evicted++;
	}

	return h;
}
export function commitHistory(h: History, next: Execution): History {
	return bounded({
		...h,
		present: structuredClone(next),
		past: [...h.past, h.present],
		future: [],
	});
}
export function moveHistory(h: History, direction: "Undo" | "Redo"): History {
	if (direction === "Undo") {
		const target = h.past.at(-1);
		if (!target) throw Error("Nothing to undo.");
		return bounded({
			...h,
			present: structuredClone(target),
			past: h.past.slice(0, -1),
			future: [h.present, ...h.future],
		});
	}
	const target = h.future[0];
	if (!target) throw Error("Nothing to redo.");
	return bounded({
		...h,
		present: structuredClone(target),
		past: [...h.past, h.present],
		future: h.future.slice(1),
	});
}
