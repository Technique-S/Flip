import { useEffect, useRef, useState } from "react";
import { api, download, type Execution } from "./model";
import type { Portable } from "./Portable";

type Result = {
	status: string;
	revisionCreated: boolean;
	revisedPackage: Portable | null;
	receipt: {
		logs: {
			step: string;
			op: string;
			status: string;
			output: unknown;
			entryHash: string;
		}[];
	} | null;
	evidenceArtifacts: Record<string, unknown>;
	error: { message: string } | null;
};
export function AgentPortable({
	request,
	value,
	openRevision,
	work,
}: {
	request: Execution;
	value: Portable;
	openRevision: (p: Portable) => void;
	work: (label: string, fn: () => Promise<void>) => Promise<void>;
}) {
	const [result, setResult] = useState<Result | null>(null);
	const [cancelNote, setCancelNote] = useState("");
	const [continueMismatch, setContinueMismatch] = useState(false);
	const [running, setRunning] = useState(false);
	const pending = useRef<AbortController | null>(null);
	useEffect(() => {
		const cancel = () => {
			pending.current?.abort();
			setCancelNote("Cancelled locally. The original project remains open.");
		};
		window.addEventListener("flip-cancel-portable", cancel);
		return () => window.removeEventListener("flip-cancel-portable", cancel);
	}, []);
	// biome-ignore lint/correctness/useExhaustiveDependencies: Selection changes invalidate pending receipts.
	useEffect(() => {
		setResult(null);
		return () => pending.current?.abort();
	}, [value, request]);
	async function run(action: string) {
		await work("Running bounded portable workflow", async () => {
			setResult(null);
			setCancelNote("");
			setRunning(true);
			const controller = new AbortController();
			pending.current = controller;
			try {
				const prepared = await api<{ request: unknown }>(
					"agent-portable/prepare",
					{
						schemaVersion: "m45-agent-portable-1.0.0",
						kind: "AGENT_PORTABLE_PREPARATION",
						package: value,
						action,
						continueOnTestMismatch: continueMismatch,
						...(action === "verify-edit"
							? { draftExecutionRequest: request }
							: {}),
					},
				);
				if (controller.signal.aborted) return;
				const response = await fetch("/api/agent/v1/portable", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify(prepared.request),
					signal: controller.signal,
				});
				const body = await response.json();
				if (!response.ok)
					throw Error(
						body.error?.message ?? `Workflow returned HTTP ${response.status}`,
					);
				if (!controller.signal.aborted) setResult(body);
			} catch (error) {
				if (!controller.signal.aborted) throw error;
			} finally {
				if (pending.current === controller) {
					pending.current = null;
					setRunning(false);
				}
			}
		});
	}
	return (
		<section aria-labelledby="portable-agent-heading">
			<h3 id="portable-agent-heading" tabIndex={-1}>
				Bounded agent workflow
			</h3>
			<p>
				Compare the saved revision, inspect a mismatch, or verify an explicit
				local edit against its declared reference. A prepared revision stays
				separate until you choose to open it.
			</p>
			<label className="check">
				<input
					type="checkbox"
					checked={continueMismatch}
					onChange={(e) => setContinueMismatch(e.target.checked)}
				/>
				Continue to correction when declared tests differ
			</label>
			<div className="actions">
				<button type="button" onClick={() => void run("inspect")}>
					Inspect saved revision
				</button>
				<button type="button" onClick={() => void run("correct")}>
					Propose and verify correction
				</button>
				<button type="button" onClick={() => void run("verify-edit")}>
					Verify current edit and prepare revision
				</button>
				<button type="button" onClick={() => void run("publish")}>
					Request publication handoff
				</button>
			</div>
			{cancelNote && <p role="status">{cancelNote}</p>}
			{running && (
				<p role="status">Workflow running. Cancel discards a late result.</p>
			)}
			{result && (
				<>
					<p role="status">
						Workflow: {result.status}.{" "}
						{result.revisionCreated
							? "New revision prepared; the original remains open."
							: "No new revision created."}
					</p>
					{result.error && <p>{result.error.message}</p>}
					{result.status === "STOP_AUTHORIZATION" && (
						<p>
							Publication stopped. No approval, transaction, signer or wallet is
							created. Later queued operations did not run.
						</p>
					)}
					{result.receipt && (
						<>
							<table className="agent-workflow-table">
								<caption>Workflow operations</caption>
								<thead>
									<tr>
										<th>Step</th>
										<th>Operation</th>
										<th>Status</th>
									</tr>
								</thead>
								<tbody>
									{result.receipt.logs.map((e) => (
										<tr key={e.entryHash}>
											<th>{e.step}</th>
											<td>{e.op}</td>
											<td>{e.status}</td>
										</tr>
									))}
								</tbody>
							</table>
							<details>
								<summary>Workflow diagnostics and proof context</summary>
								<pre>{JSON.stringify(result.receipt, null, 2)}</pre>
							</details>
							<button
								type="button"
								onClick={() =>
									download("workflow-receipt.json", result.receipt)
								}
							>
								Download workflow receipt
							</button>
						</>
					)}
					{result.revisedPackage && (
						<div className="actions">
							<button
								type="button"
								onClick={() => {
									const p = result.revisedPackage;
									if (p)
										download(
											`project-r${p.revision.sequence}-${p.revision.revisionHash.slice(2, 10)}.json`,
											p,
										);
								}}
							>
								Download verified revision
							</button>
							<button
								type="button"
								onClick={() => {
									if (result.revisedPackage)
										openRevision(result.revisedPackage);
								}}
							>
								Open verified revision
							</button>
						</div>
					)}
					{Object.entries(result.evidenceArtifacts).map(
						([digest, artifact]) => (
							<button
								type="button"
								key={digest}
								onClick={() =>
									download(`evidence-${digest.slice(2, 10)}.json`, artifact)
								}
							>
								Download evidence {digest.slice(2, 10)}
							</button>
						),
					)}
					<p>
						Vector matches cover declared inputs. Revision hashes establish
						local integrity, not authorship or permission.
					</p>
				</>
			)}
		</section>
	);
}
