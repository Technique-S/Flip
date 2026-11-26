import { useEffect, useRef } from "react";
import type { Execution } from "../model";
import { availablePins, removalProblem } from "./commands";
import type { CandidateEditor } from "./useCandidateEditor";

export function NandControls({
	editor,
	request,
}: {
	editor: CandidateEditor;
	request: Execution;
}) {
	const focus = useRef(editor.focus);
	useEffect(() => {
		if (focus.current === editor.focus) return;
		focus.current = editor.focus;
		const id = editor.nand
			? "nand-id"
			: editor.removeId
				? "nand-removal-heading"
				: editor.selection
					? "visual-inspect-component"
					: "nand-selection";
		const target = document.getElementById(id);
		if (
			target?.getClientRects().length &&
			!(target as HTMLSelectElement).disabled
		)
			target.focus();
		else
			document
				.getElementById(editor.selection ? "nand-selection" : "add-nand")
				?.focus();
	}, [editor.focus, editor.nand, editor.removeId, editor.selection]);
	const pins = editor.nand
		? availablePins(editor.history?.present ?? request)
		: [];
	const nands = request.project.candidate.components.filter(
		(c) => c.kind === "NAND",
	);
	const problem = editor.removeId
		? removalProblem(editor.history?.present ?? request, editor.removeId)
		: null;
	return (
		<section className="nand-editor" aria-label="NAND component editing">
			<div className="actions">
				<button
					id="add-nand"
					type="button"
					disabled={editor.blocked()}
					onClick={editor.startNand}
				>
					Add NAND
				</button>
				<button
					type="button"
					disabled={editor.blocked() || !editor.history?.past.length}
					onClick={() => void editor.move("Undo")}
				>
					Undo edit
				</button>
				<button
					type="button"
					disabled={editor.blocked() || !editor.history?.future.length}
					onClick={() => void editor.move("Redo")}
				>
					Redo edit
				</button>
				<label>
					NAND component
					<select
						id="nand-selection"
						value={
							nands.some((c) => c.instanceId === editor.selection)
								? editor.selection
								: ""
						}
						disabled={editor.blocked() || !nands.length}
						onChange={(e) => editor.select(e.target.value)}
					>
						<option value="">Choose a NAND</option>
						{nands.map((c) => (
							<option key={c.instanceId} value={c.instanceId}>
								{c.instanceId}
							</option>
						))}
					</select>
				</label>
				<button
					type="button"
					disabled={
						editor.blocked() ||
						!nands.some((c) => c.instanceId === editor.selection)
					}
					onClick={() => editor.startRemove(editor.selection)}
				>
					Remove NAND
				</button>
			</div>
			{editor.history?.evicted ? (
				<p>
					History limit reached: {editor.history.evicted} earlier entries were
					evicted. Export important revisions.
				</p>
			) : null}
			{editor.nand && (
				<form
					noValidate
					onSubmit={async (e) => {
						e.preventDefault();
						if (!(await editor.add())) {
							const d = editor.nand;
							if (!d) return;
							document
								.getElementById(
									!d.instanceId
										? "nand-id"
										: !d.input0
											? "nand-input-0"
											: !d.input1
												? "nand-input-1"
												: "nand-id",
								)
								?.focus();
						}
					}}
				>
					<h3>Add NAND draft</h3>
					<p>
						Choose both inputs explicitly. No wiring is changed until the local
						compiler accepts the complete candidate.
					</p>
					<div className="fields">
						<label>
							New NAND ID
							<input
								id="nand-id"
								value={editor.nand.instanceId}
								maxLength={64}
								autoComplete="off"
								aria-describedby="nand-edit-issue"
								onChange={(e) =>
									editor.updateNand({ instanceId: e.target.value })
								}
							/>
						</label>
						{([0, 1] as const).map((i) => (
							<label key={i}>
								NAND input {i} source
								<select
									id={`nand-input-${i}`}
									value={i === 0 ? editor.nand?.input0 : editor.nand?.input1}
									aria-describedby="nand-edit-issue"
									onChange={(e) =>
										editor.updateNand(
											i === 0
												? { input0: e.target.value }
												: { input1: e.target.value },
										)
									}
								>
									<option value="">Choose a source output</option>
									{pins.map((p) => (
										<option key={JSON.stringify(p)} value={JSON.stringify(p)}>
											{p.component ?? "external"} [{p.pin}]
										</option>
									))}
								</select>
							</label>
						))}
					</div>
					{!pins.length && (
						<p>
							No existing output pins are available. This draft cannot be
							committed.
						</p>
					)}
					<button type="submit">Validate and add NAND</button>
					<button type="button" onClick={editor.cancel}>
						Cancel NAND draft
					</button>
				</form>
			)}
			{editor.removeId && (
				<div className="nand-confirm">
					<h3 id="nand-removal-heading" tabIndex={-1}>
						Remove {editor.removeId}?
					</h3>
					<p>
						{problem ??
							"Only this unreferenced NAND will be removed. Component IDs, other mappings and REF dependencies stay unchanged."}
					</p>
					<button
						type="button"
						disabled={!!problem}
						onClick={() => void editor.remove()}
					>
						Confirm remove NAND
					</button>
				</div>
			)}
			<p id="nand-edit-issue" role={editor.issue ? "alert" : undefined}>
				{editor.issue ||
					(editor.advanced
						? "Invalid or pending Advanced draft. Fix its mappings or discard it. Execution and export are blocked."
						: "")}
			</p>
		</section>
	);
}
