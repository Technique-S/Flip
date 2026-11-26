import type { Execution, Pin } from "../model";
import { projectExecution } from "./projection";

export type NandCommand =
	| { type: "AddNand"; instanceId: string; inputs: [Pin, Pin] }
	| { type: "RemoveNand"; instanceId: string };
export const isComponentName = (v: unknown): v is string =>
	typeof v === "string" && /^[A-Za-z][A-Za-z0-9_-]{0,63}$/.test(v);
export const requestKey = (r: Execution) => JSON.stringify(r); // Exact UI snapshot, NOT a canonical hash.
const size = (s: string) => new TextEncoder().encode(s).length;

/** Conservative UI table cost, not native gate/solver cost. Lookup/fallback is unchanged. */
export function interactiveCapacity(r: Execution) {
	const d = r.project.candidate;
	const destinationPins = d.components.reduce(
		(n, c) => n + c.inputs.length,
		d.outputs.length,
	);
	const sourcePins = d.components.reduce(
		(n, c) =>
			n + (r.project.sources.find((s) => s.alias === c.sourceAlias)?.nOut ?? 1),
		d.nIn,
	);
	return {
		destinationPins,
		sourcePins,
		score: destinationPins * sourcePins,
		externalInputs: d.nIn,
		outputs: d.outputs.length,
		requestBytes: size(requestKey(r)),
	};
}
export function checkInteractiveBudget(r: Execution) {
	const c = interactiveCapacity(r);
	const n = (v: number) => v.toLocaleString("en-US");
	const preserved =
		" Your accepted wiring is unchanged. UI limits are independent of native compiler and solver limits.";
	if (c.score > 65000)
		throw Error(
			`Edit not applied. Interactive capacity score ${n(c.score)} exceeds the limit of 65,000 (${n(c.destinationPins)} destination pins × ${n(c.sourcePins)} source pins; interactive pin table budget).${preserved}`,
		);
	if (c.externalInputs > 255)
		throw Error(
			`Edit not applied. External input count ${n(c.externalInputs)} exceeds the interactive limit of 255.${preserved}`,
		);
	if (c.outputs > 255)
		throw Error(
			`Edit not applied. Output count ${n(c.outputs)} exceeds the interactive limit of 255.${preserved}`,
		);
	if (c.requestBytes > 1048576)
		throw Error(
			`Edit not applied. Full Execution UTF-8 size ${n(c.requestBytes)} bytes exceeds the 1 MiB interactive request limit (1,048,576 bytes).${preserved}`,
		);
}

function dataFields(
	value: unknown,
	expected: readonly string[],
	array = false,
): Record<string, unknown> {
	try {
		if (!value || typeof value !== "object" || Array.isArray(value) !== array)
			throw Error();
		const keys = Reflect.ownKeys(value);
		if (
			keys.length !== expected.length ||
			keys.some((k) => typeof k !== "string" || !expected.includes(k))
		)
			throw Error();
		const result = Object.create(null) as Record<string, unknown>;
		for (const key of expected) {
			const d = Object.getOwnPropertyDescriptor(value, key);
			if (
				!d ||
				!Object.hasOwn(d, "value") ||
				d.enumerable !== !(array && key === "length")
			)
				throw Error();
			result[key] = d.value;
		}
		return result;
	} catch {
		// Reflection may invoke proxy traps; do not invoke accessors or expose trap errors.
		throw Error(
			"Invalid command record: exact enumerable own data fields are required.",
		);
	}
}
export const ownFields = (value: unknown, expected: readonly string[]) =>
	dataFields(value, expected);
export function ownDiscriminant(value: unknown, key: string): unknown {
	try {
		if (!value || typeof value !== "object" || Array.isArray(value))
			throw Error();
		const d = Object.getOwnPropertyDescriptor(value, key);
		if (!d || !Object.hasOwn(d, "value") || !d.enumerable) throw Error();
		return d.value;
	} catch {
		throw Error("Invalid edit command type: an own data field is required.");
	}
}
export function normalizeName(value: unknown): string {
	if (!isComponentName(value))
		throw Error(
			"Component ID must start with a letter and contain at most 64 letters, digits, underscores or hyphens.",
		);
	return value;
}
export function normalizePin(value: unknown): Pin {
	const p = ownFields(value, ["component", "pin"]);
	if (p.component !== null) normalizeName(p.component);
	if (typeof p.pin !== "number" || !Number.isSafeInteger(p.pin) || p.pin < 0)
		throw Error("Pin index must be an explicit safe nonnegative integer.");
	return { component: p.component as string | null, pin: p.pin };
}
function normalizeNand(value: unknown): NandCommand {
	const type = ownDiscriminant(value, "type");
	if (type !== "AddNand" && type !== "RemoveNand")
		throw Error("Unsupported edit command.");
	const c = ownFields(
		value,
		type === "AddNand"
			? ["type", "instanceId", "inputs"]
			: ["type", "instanceId"],
	);
	const instanceId = normalizeName(c.instanceId);
	if (type === "RemoveNand") return { type, instanceId };
	const inputs = dataFields(c.inputs, ["0", "1", "length"], true);
	if (inputs.length !== 2)
		throw Error("Choose exactly two explicit NAND input sources.");
	return {
		type,
		instanceId,
		inputs: [normalizePin(inputs["0"]), normalizePin(inputs["1"])],
	};
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
	const c = normalizeNand(value);
	const next = structuredClone(r);
	if (c.type === "AddNand") {
		if (
			next.project.candidate.components.some(
				(x) => x.instanceId === c.instanceId,
			)
		)
			throw Error("Component ID already exists.");
		const available = availablePins(r);
		if (
			c.inputs.some(
				(p) =>
					!available.some(
						(a) => a.component === p.component && a.pin === p.pin,
					),
			)
		)
			throw Error(
				"Input must identify an existing external or preceding output pin.",
			);
		next.project.candidate.components.push({
			kind: "NAND",
			instanceId: c.instanceId,
			inputs: c.inputs,
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
	projectExecution(next); // Display checks only; Python compose still decides acceptance.
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
