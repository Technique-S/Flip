import { useEffect, useRef, useState } from "react";
import { api, type Execution } from "../model";
import {
	checkInteractiveBudget,
	commitHistory,
	type History,
	moveHistory,
	openHistory,
	proposeNand,
	removalProblem,
	requestKey,
} from "./commands";

type Draft = { instanceId: string; input0: string; input1: string };
type State = {
	history: History | null;
	advanced: Execution | null;
	nand: Draft | null;
	removeId: string | null;
	pending: boolean;
	recovery: boolean;
	storageIssue: string;
	issue: string;
	message: string;
	revision: number;
	selection: string;
	focus: number;
};
const initial = (): State => ({
	history: null,
	advanced: null,
	nand: null,
	removeId: null,
	pending: false,
	recovery: false,
	storageIssue: "",
	issue: "",
	message: "",
	revision: 0,
	selection: "",
	focus: 0,
});
export function useCandidateEditor(callbacks: {
	commit: (r: Execution) => void;
	invalidate: () => void;
	busy: () => boolean;
}) {
	const [state, setState] = useState<State>(initial);
	const current = useRef(state),
		cb = useRef(callbacks),
		generation = useRef(0),
		controller = useRef<AbortController | null>(null);
	cb.current = callbacks;
	const advancedFocus = useRef<HTMLElement | null>(null);
	useEffect(() => {
		if (state.pending || !advancedFocus.current) return;
		const target = advancedFocus.current;
		advancedFocus.current = null;
		if (
			document.activeElement === document.body &&
			target.isConnected &&
			!(target as HTMLInputElement).disabled
		)
			target.focus();
	}, [state.pending]);

	function publish(s: State) {
		if (s.history && s.history !== current.current.history) {
			try {
				sessionStorage.setItem(
					"flip-edit-checkpoint",
					JSON.stringify({
						current: requestKey(s.history.present),
						saved: s.history.saved,
					}),
				);
			} catch {
				s = {
					...s,
					storageIssue:
						"Edit recovery storage is unavailable. Export the project before leaving this page.",
				};
			}
		}
		current.current = s;
		setState(s);
	}
	function patch(p: Partial<State>) {
		publish({ ...current.current, ...p });
	}
	function clearRecovery() {
		try {
			sessionStorage.removeItem("flip-edit-draft");
		} catch {
			/* No recovery storage is available. */
		}
	}
	function cancel() {
		advancedFocus.current = null;
		clearRecovery();
		generation.current++;
		controller.current?.abort();
		controller.current = null;
		patch({
			advanced: null,
			nand: null,
			removeId: null,
			pending: false,
			recovery: false,
			issue: "",
			message: "Draft discarded. Accepted wiring is unchanged.",
			focus: current.current.focus + 1,
		});
	}
	function open(r: Execution | null) {
		advancedFocus.current = null;
		clearRecovery();
		if (!r) {
			try {
				sessionStorage.removeItem("flip-edit-checkpoint");
			} catch {
				/* Storage may be unavailable. */
			}
		}
		generation.current++;
		controller.current?.abort();
		controller.current = null;
		publish({ ...initial(), history: r ? openHistory(r) : null });
	}
	const blocked = () => {
		const s = current.current;
		return !!(s.pending || s.recovery || s.advanced || s.nand || s.removeId);
	};
	function idle() {
		return (
			!cb.current.busy() &&
			!current.current.pending &&
			state.history?.present === current.current.history?.present
		);
	}
	async function validate(
		next: Execution,
		history: History,
		selection: string,
		label: string,
		restoring = false,
	) {
		if (
			(!restoring && !idle()) ||
			current.current.pending ||
			!current.current.history
		)
			return false;
		const baseHistory = current.current.history;
		if (
			label === "Advanced edit" &&
			document.activeElement instanceof HTMLElement
		)
			advancedFocus.current = document.activeElement;
		const token = ++generation.current;
		const abort = new AbortController();
		controller.current = abort;
		cb.current.invalidate();
		patch({ pending: true, issue: "", message: `Validating ${label}…` });
		try {
			checkInteractiveBudget(next);
			try {
				sessionStorage.setItem(
					"flip-edit-draft",
					JSON.stringify({
						base: requestKey(baseHistory.present),
						request: next,
					}),
				);
			} catch {
				patch({
					storageIssue:
						"Edit recovery could not be stored. Keep this page open until validation finishes and export your project.",
				});
			}
			await api("compose", next, abort.signal);
			if (generation.current !== token) return false;
			cb.current.commit(next);
			clearRecovery();
			publish({
				...current.current,
				history,
				advanced: null,
				nand: null,
				removeId: null,
				pending: false,
				recovery: false,
				issue: "",
				message: `${label} committed. Prior comparisons remain historical; compare again for this revision.`,
				revision: current.current.revision + 1,
				selection,
				focus: current.current.focus + (label === "Advanced edit" ? 0 : 1),
			});
			return true;
		} catch (e) {
			if (generation.current === token)
				patch({
					pending: false,
					issue: e instanceof Error ? e.message : String(e),
					message:
						"Edit not committed. The last accepted candidate is preserved.",
				});
			return false;
		} finally {
			if (generation.current === token) controller.current = null;
		}
	}
	function startNand() {
		if (!idle() || blocked()) return;
		cb.current.invalidate();
		patch({
			nand: { instanceId: "", input0: "", input1: "" },
			issue: "",
			message:
				"Local NAND draft. Choose both inputs explicitly before committing.",
			focus: current.current.focus + 1,
		});
	}
	async function add() {
		const s = current.current;
		if (!s.history || !s.nand || !idle()) return false;
		try {
			if (!s.nand.input0 || !s.nand.input1)
				throw Error(
					"Choose both NAND input sources; no default connections are supplied.",
				);
			const inputs = [s.nand.input0, s.nand.input1].map((v) => JSON.parse(v));
			const next = proposeNand(s.history.present, {
				type: "AddNand",
				instanceId: s.nand.instanceId,
				inputs,
			});
			return await validate(
				next,
				commitHistory(s.history, next),
				s.nand.instanceId,
				`Add NAND ${s.nand.instanceId}`,
			);
		} catch (e) {
			patch({ issue: e instanceof Error ? e.message : String(e) });
			return false;
		}
	}
	function startRemove(id: string) {
		if (!idle() || blocked() || !current.current.history) return;
		patch({
			removeId: id,
			issue: removalProblem(current.current.history.present, id) ?? "",
			message: "Review the exact NAND removal before confirming.",
			focus: current.current.focus + 1,
		});
	}
	async function remove() {
		const s = current.current;
		if (!s.history || !s.removeId || !idle()) return false;
		try {
			const next = proposeNand(s.history.present, {
				type: "RemoveNand",
				instanceId: s.removeId,
			});
			return await validate(
				next,
				commitHistory(s.history, next),
				"",
				`Remove NAND ${s.removeId}`,
			);
		} catch (e) {
			patch({ issue: e instanceof Error ? e.message : String(e) });
			return false;
		}
	}
	async function move(direction: "Undo" | "Redo") {
		const s = current.current;
		if (!s.history || blocked() || !idle()) return;
		try {
			const history = moveHistory(s.history, direction);
			await validate(history.present, history, "", direction);
		} catch (e) {
			patch({ issue: e instanceof Error ? e.message : String(e) });
		}
	}
	function change(fn: (r: Execution) => void) {
		const s = current.current;
		if (!s.history || !idle()) return;
		if (s.nand || s.removeId) {
			patch({
				issue: "Complete or discard the NAND draft before another edit.",
			});
			return;
		}
		const next = structuredClone(s.advanced ?? s.history.present);
		try {
			fn(next);
		} catch (e) {
			patch({ issue: String(e) });
			return;
		}
		if (requestKey(next) === requestKey(s.history.present)) {
			cancel();
			return;
		}
		cb.current.invalidate();
		patch({ advanced: next });
		void validate(
			next,
			commitHistory(s.history, next),
			s.selection,
			"Advanced edit",
		);
	}
	async function restore(raw: string | null) {
		if (!raw || !current.current.history) return;
		patch({ recovery: true });
		try {
			sessionStorage.setItem("flip-edit-draft", raw);
		} catch {
			/* Existing storage warning applies. */
		}
		try {
			if (new TextEncoder().encode(raw).length > 3 * 1048576)
				throw Error("Stored edit draft exceeds recovery budget.");
			const value = JSON.parse(raw);
			if (value.base !== requestKey(current.current.history.present))
				throw Error(
					"Stored edit draft does not match the restored accepted project.",
				);
			checkInteractiveBudget(value.request);
			await validate(
				value.request,
				commitHistory(current.current.history, value.request),
				"",
				"Recovered edit",
				true,
			);
		} catch (e) {
			patch({
				issue: `Stored draft not applied: ${String(e)}. Discard the draft to use the preserved accepted project.`,
			});
		}
	}
	function configure(next: Execution) {
		const s = current.current;
		if (!s.history || s.nand || s.removeId || s.pending || cb.current.busy())
			return;
		if (
			JSON.stringify(next.project.candidate) !==
			JSON.stringify(s.history.present.project.candidate)
		)
			throw Error("Configuration cannot change the candidate recipe.");
		checkInteractiveBudget(next);
		cb.current.commit(next);
		publish({
			...initial(),
			history: { ...openHistory(next), saved: s.history.saved },
			revision: s.revision + 1,
			message:
				"Execution setup changed. Component edit history reset; operations validate these settings before producing evidence.",
		});
	}

	function restoreSaved(raw: string | null) {
		const h = current.current.history;
		if (!h || !raw) return;
		try {
			if (new TextEncoder().encode(raw).length > 3 * 1048576) return;
			const value = JSON.parse(raw);
			if (
				value.current === requestKey(h.present) &&
				typeof value.saved === "string" &&
				new TextEncoder().encode(value.saved).length <= 1048576
			)
				patch({ history: { ...h, saved: value.saved } });
		} catch {
			patch({
				storageIssue:
					"Export checkpoint could not be restored. Keep your existing project exports.",
			});
		}
	}

	function markExported(r: Execution) {
		const h = current.current.history;
		if (h && !blocked() && requestKey(r) === requestKey(h.present))
			patch({
				history: { ...h, saved: requestKey(r) },
				message:
					"Project export requested. Keep the downloaded file; browser storage is separate.",
			});
	}
	return {
		...state,
		dirty:
			!!state.history &&
			requestKey(state.history.present) !== state.history.saved,
		blocked,
		matches: (r: Execution) =>
			!!current.current.history &&
			requestKey(current.current.history.present) === requestKey(r),
		open,
		cancel,
		startNand,
		add,
		startRemove,
		remove,
		move,
		change,
		markExported,
		restore,
		restoreSaved,
		configure,
		updateNand: (v: Partial<Draft>) => {
			if (current.current.nand && !current.current.pending)
				patch({ nand: { ...current.current.nand, ...v }, issue: "" });
		},
		select: (selection: string) => patch({ selection }),
	};
}
export type CandidateEditor = ReturnType<typeof useCandidateEditor>;
