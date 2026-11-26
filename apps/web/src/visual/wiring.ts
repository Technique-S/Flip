import type { Execution, Pin } from "../model";
import {
	checkInteractiveBudget,
	normalizeName,
	normalizePin,
	ownDiscriminant,
	ownFields,
} from "./commands";
import { projectExecution } from "./projection";

export type BindingTarget =
	| { kind: "component-input"; instanceId: string; pin: number }
	| { kind: "output"; pin: number };
export type ReplaceBinding = {
	type: "ReplaceBinding";
	target: BindingTarget;
	source: Pin;
};

function normalizeTarget(value: unknown): BindingTarget {
	const kind = ownDiscriminant(value, "kind");
	if (kind !== "component-input" && kind !== "output")
		throw Error("Unsupported binding destination direction or kind.");
	const t = ownFields(
		value,
		kind === "output" ? ["kind", "pin"] : ["kind", "instanceId", "pin"],
	);
	if (typeof t.pin !== "number" || !Number.isSafeInteger(t.pin) || t.pin < 0)
		throw Error(
			"Destination pin must be an explicit safe nonnegative integer.",
		);
	return kind === "output"
		? { kind, pin: t.pin }
		: { kind, instanceId: normalizeName(t.instanceId), pin: t.pin };
}

/** Normalize UI-local data only; this is not a new canonical/API schema. */
export function normalizeReplaceBinding(value: unknown): ReplaceBinding {
	const c = ownFields(value, ["type", "target", "source"]);
	if (c.type !== "ReplaceBinding") throw Error("Unsupported wiring command.");
	return {
		type: "ReplaceBinding",
		target: normalizeTarget(c.target),
		source: normalizePin(c.source),
	};
}

/**
 * Pure proposal on an already native-accepted Execution. No network, state or proof
 * authority. Native compose must validate the complete result before any commit;
 * display metadata checks do not validate imported bytes/closure/environment.
 * Identical binding returns the exact input object: callers must not commit it.
 */
export function proposeReplaceBinding(r: Execution, value: unknown): Execution {
	const c = normalizeReplaceBinding(value);
	checkInteractiveBudget(r);
	projectExecution(r); // Reuse bounded display/REF interface guards, not an engine.
	const d = r.project.candidate;
	const target = c.target;
	const index =
		target.kind === "output"
			? d.components.length
			: d.components.findIndex((part) => part.instanceId === target.instanceId);
	if (index < 0) throw Error("Binding destination component does not exist.");
	const slots =
		c.target.kind === "output" ? d.outputs : d.components[index].inputs;
	if (c.target.pin >= slots.length)
		throw Error("Binding destination pin is out of range.");
	if (c.source.component === null) {
		if (c.source.pin >= d.nIn)
			throw Error("External source pin is out of range.");
	} else {
		const sourceIndex = d.components.findIndex(
			(part) => part.instanceId === c.source.component,
		);
		if (sourceIndex < 0)
			throw Error("Binding source component does not exist.");
		if (sourceIndex >= index)
			throw Error(
				"Source must precede the destination; self/forward wiring is unavailable.",
			);
		const source = d.components[sourceIndex];
		const width =
			source.kind === "NAND"
				? 1
				: (r.project.sources.find((s) => s.alias === source.sourceAlias)
						?.nOut ?? 0);
		if (c.source.pin >= width)
			throw Error("Component source pin is out of range.");
	}
	const previous = slots[c.target.pin];
	if (
		previous.component === c.source.component &&
		previous.pin === c.source.pin
	)
		return r;
	const next = structuredClone(r);
	const nextSlots =
		c.target.kind === "output"
			? next.project.candidate.outputs
			: next.project.candidate.components[index].inputs;
	nextSlots[c.target.pin] = {
		component: c.source.component,
		pin: c.source.pin,
	};
	checkInteractiveBudget(next);
	projectExecution(next);
	return next;
}
