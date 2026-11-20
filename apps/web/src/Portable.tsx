import { useState } from "react";
import { api, download, type Execution, readFile } from "./model";

export type Portable = {
	schemaVersion: "flip-portable-project-1.1.0";
	kind: "PORTABLE_PROJECT";
	executionRequest: Execution;
	executionRequestHash: string;
	tests: {
		name: string;
		declaredIntent: string;
		expectedCoverage: string;
		vectors: unknown[];
	}[];
	noDeclaredTests: boolean;
	evidenceRefs: {
		digest: string;
		engineHash: string;
		reproduce: string;
		executionRequestHash: string;
		kind: "FLIP_EVIDENCE";
	}[];
	ancestors: Revision[];
	revision: Revision;
};
type Revision = {
	sequence: number;
	revisionHash: string;
	parentHash: string | null;
	editLog: {
		description: string;
		beforeHash: string | null;
		afterHash: string;
	}[];
};
export const portableBody = (
	operation: string,
	fields: Record<string, unknown>,
) => ({
	schemaVersion: "flip-portable-project-1.1.0",
	kind: "PORTABLE_REQUEST",
	operation,
	...fields,
});

export function PortablePanel({
	request,
	value,
	update,
	work,
}: {
	request: Execution;
	value: Portable | null;
	update: (value: Portable) => void;
	work: (label: string, fn: () => Promise<void>) => Promise<void>;
}) {
	const [result, setResult] = useState<unknown>(null);
	const [lossy, setLossy] = useState(false);
	const [detach, setDetach] = useState(false);
	async function save(extra: Record<string, unknown> = {}) {
		const next = await api<Portable>(
			"portable",
			portableBody("wrap", {
				executionRequest: request,
				...(value
					? {
							previous: value,
							expectedRevisionHash: value.revision.revisionHash,
						}
					: {}),
				...(detach ? { evidenceRefs: [] } : {}),
				...extra,
			}),
		);
		update(next);
		setResult(null);
		return next;
	}
	return (
		<section className="portable" aria-labelledby="portable-heading">
			<h2 id="portable-heading">Portable project</h2>
			<p>
				Save tests, evidence references and revision history together. Opening a
				package checks local integrity; evidence requires a separate replay.
			</p>
			<div className="actions">
				<button
					type="button"
					onClick={() =>
						void work("Saving portable revision", async () => {
							const next = await save();
							download(
								`project-r${next.revision.sequence}-${next.revision.revisionHash.slice(2, 10)}.json`,
								next,
							);
						})
					}
				>
					Save complete portable project
				</button>
				<label className="file">
					Import named test sets
					<input
						type="file"
						accept=".json,application/json"
						onChange={(e) => {
							const file = e.target.files?.[0];
							e.target.value = "";
							if (file)
								void work("Importing named tests", async () => {
									await save({
										tests: JSON.parse(await readFile(file)),
										description: "Import named test sets",
									});
								});
						}}
					/>
				</label>
				<label className="file">
					Import evidence references
					<input
						type="file"
						accept=".json,application/json"
						onChange={(e) => {
							const file = e.target.files?.[0];
							e.target.value = "";
							if (file)
								void work("Importing evidence references", async () => {
									await save({
										evidenceRefs: JSON.parse(await readFile(file)),
										description: "Import evidence references",
									});
								});
						}}
					/>
				</label>
			</div>
			{value && (
				<>
					<p>
						Saved revision {value.revision.sequence} ·{" "}
						{value.noDeclaredTests
							? "No declared tests"
							: `${value.tests.length} named test sets`}{" "}
						· {value.evidenceRefs.length} evidence references
					</p>
					<p>
						Edits create another revision when saved. Keep the previous file to
						retain its complete test and evidence metadata.
					</p>
					<details>
						<summary>Named tests</summary>
						{value.noDeclaredTests ? (
							<p>No declared tests. No expected behavior has been supplied.</p>
						) : (
							value.tests.map((t) => (
								<article key={t.name}>
									<h3>{t.name}</h3>
									<p>
										{t.declaredIntent} · {t.expectedCoverage} ·{" "}
										{t.vectors.length} rows
									</p>
									<pre>{JSON.stringify(t.vectors, null, 2)}</pre>
								</article>
							))
						)}
						<button
							type="button"
							onClick={() =>
								void work("Evaluating named tests", async () => {
									const current = await save();
									setResult(
										await api(
											"portable",
											portableBody("test", { package: current }),
										),
									);
								})
							}
						>
							Run named tests
						</button>
						<p>
							Vector matches describe declared inputs. Universal equivalence
							requires Wiring Canary.
						</p>
					</details>
					<details>
						<summary>Revision history</summary>
						<ol>
							{[...value.ancestors, value.revision].map((r) => (
								<li key={r.revisionHash}>
									<p>
										Revision {r.sequence}:{" "}
										{r.editLog.map((e) => e.description).join("; ")}
									</p>
									<code>{r.revisionHash}</code>
								</li>
							))}
						</ol>
						<p>
							Revision hashes establish local integrity. They do not
							authenticate authors.
						</p>
					</details>
					<details>
						<summary>Evidence references</summary>
						<p>
							Replays check saved revision {value.revision.sequence}. Save
							current edits before checking evidence for the current draft.
						</p>
						{value.evidenceRefs.length ? (
							<pre>{JSON.stringify(value.evidenceRefs, null, 2)}</pre>
						) : (
							<p>No evidence references.</p>
						)}
						<label className="check">
							<input
								type="checkbox"
								checked={detach}
								onChange={(e) => setDetach(e.target.checked)}
							/>
							Remove previous evidence references in the next revision
						</label>
						<p>
							References bind an exact execution request. After editing it,
							remove or replace references before saving.
						</p>
						<label className="file">
							Replay referenced evidence files
							<input
								type="file"
								multiple
								accept=".json,application/json"
								onChange={(e) => {
									const files = [...(e.target.files ?? [])];
									e.target.value = "";
									void work("Replaying referenced evidence", async () => {
										const artifacts: Record<string, unknown> = {};
										for (const file of files) {
											const artifact = JSON.parse(await readFile(file));
											artifacts[artifact.contentHash] = artifact;
										}
										setResult(
											await api(
												"portable",
												portableBody("replay-evidence", {
													package: value,
													artifacts,
												}),
											),
										);
									});
								}}
							/>
						</label>
						<button
							type="button"
							onClick={() =>
								void work("Checking evidence availability", async () => {
									setResult(
										await api(
											"portable",
											portableBody("replay-evidence", { package: value }),
										),
									);
								})
							}
						>
							Check missing evidence
						</button>
					</details>
				</>
			)}
			<details>
				<summary>Convert to legacy project</summary>
				<p>
					Legacy files discard named tests, evidence references, revision
					history, provenance and agent task references.
				</p>
				<label className="check">
					<input
						type="checkbox"
						checked={lossy}
						onChange={(e) => setLossy(e.target.checked)}
					/>
					I acknowledge the loss of portable metadata
				</label>
				<button
					type="button"
					disabled={!lossy}
					onClick={() =>
						void work("Converting to legacy", async () => {
							const current = await save();
							const converted = await api<{
								executionRequest: Execution;
								warning: string;
								discardedFields: string[];
							}>(
								"portable",
								portableBody("downgrade", {
									package: current,
									allowLossy: true,
								}),
							);
							download("legacy-project.json", converted.executionRequest);
							setResult(
								`${converted.warning} ${converted.discardedFields.join(", ")}`,
							);
						})
					}
				>
					Export legacy project
				</button>
			</details>
			{result !== null && (
				<pre role="status">{JSON.stringify(result, null, 2)}</pre>
			)}
		</section>
	);
}
