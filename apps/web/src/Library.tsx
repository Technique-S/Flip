import { useEffect, useRef, useState } from "react";
import type { Imported } from "./model";

type Identity = {
	chainId: 196;
	factory: string;
	processor: string;
	circuitId: string | null;
};
type Record = {
	identity: Identity;
	sources: string[];
	freshness: string;
	block: { number: string; hash: string } | null;
	nIn: number | null;
	nOut: number | null;
	nState: number | null;
	gateCount: number | null;
	onchainName: string;
	onchainSymbol: string;
	processorNumber: string | null;
	environmentDigest: string | null;
	manifestHash: string | null;
	netlistHash: string | null;
	dependencyHashes: string[];
};
type Favorite = {
	identity: Identity;
	label: string;
	description: string;
	tags: string[];
};
type Catalog = {
	schemaVersion: string;
	kind: string;
	records: Record[];
	overlay: {
		favorites: Favorite[];
		aliases: Favorite[];
		recents: { identity: Identity; manifestHash: string }[];
	};
};
type Result = {
	status: string;
	errorCode: string | null;
	catalog: Catalog;
	results: Record[];
	cursor: unknown;
	total: string | null;
	block: { number: string } | null;
	rpcCallsUsed: number;
	rpcCallBudget: number;
	imported: Imported | null;
};
const storageKey = "flip-library-m45-v1";
const same = (a: Identity, b: Identity) =>
	a.processor === b.processor && a.circuitId === b.circuitId;

export function Library({
	onImport,
}: {
	onImport: (item: Imported) => Promise<void>;
}) {
	const [catalog, setCatalog] = useState<Catalog | null>(null);
	const [query, setQuery] = useState("");
	const [scope, setScope] = useState("all");
	const [processor, setProcessor] = useState<Identity | null>(null);
	const [selected, setSelected] = useState<Record | null>(null);
	const [cursor, setCursor] = useState<unknown>(null);
	const [nextId, setNextId] = useState<string | null>(null);
	const [report, setReport] = useState<Result | null>(null);
	const [label, setLabel] = useState("");
	const [busy, setBusy] = useState("");
	const [error, setError] = useState("");
	const [storageNote, setStorageNote] = useState("");
	const [shown, setShown] = useState(12);
	const current = useRef<Catalog | null>(null);
	const controller = useRef<AbortController | null>(null);

	async function operate(
		operation: string,
		extra: object = {},
		initial?: Catalog,
	) {
		if (controller.current) return;
		const abort = new AbortController();
		controller.current = abort;
		setBusy(operation);
		setError("");
		try {
			const response = await fetch("/api/library/v1/execute", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				signal: abort.signal,
				body: JSON.stringify({
					schemaVersion: "m45-library-1.0.0",
					kind: "LIBRARY_REQUEST",
					operation,
					...((initial ?? current.current)
						? { catalog: initial ?? current.current }
						: {}),
					limit: 12,
					...extra,
				}),
			});
			const value = await response.json();
			if (!response.ok)
				throw Error(value.error?.message ?? "Library request failed.");
			const result = value as Result;
			current.current = result.catalog;
			setCatalog(result.catalog);
			setReport(result);
			if (operation === "discover" || operation === "circuits")
				setCursor(result.cursor);
			if (operation === "circuits") setNextId(result.total);
			if (selected && operation !== "discover" && operation !== "circuits")
				setSelected(
					result.catalog.records.find((r) =>
						same(r.identity, selected.identity),
					) ?? selected,
				);
			try {
				localStorage.setItem(storageKey, JSON.stringify(result.catalog));
			} catch {
				setStorageNote(
					"Browser storage unavailable. This library lasts until the page closes.",
				);
			}
			if (
				operation === "import" &&
				result.status === "COMPLETE" &&
				result.imported
			) {
				await onImport(result.imported);
			}
		} catch (e) {
			setError(
				abort.signal.aborted
					? "Discovery stopped. Previous catalog retained."
					: e instanceof Error
						? e.message
						: "Library unavailable. Retry the operation.",
			);
		} finally {
			controller.current = null;
			setBusy("");
		}
	}
	// biome-ignore lint/correctness/useExhaustiveDependencies: Restore and validate once per mount.
	useEffect(() => {
		let saved: Catalog | undefined;
		try {
			const raw = localStorage.getItem(storageKey);
			if (raw) saved = JSON.parse(raw);
		} catch {
			setStorageNote(
				"Saved library could not be read. Known addresses are available.",
			);
		}
		void operate("search", {}, saved);
		return () => controller.current?.abort();
	}, []);

	function pick(record: Record) {
		setSelected(record);
		setLabel(
			catalog?.overlay.aliases.find((a) => same(a.identity, record.identity))
				?.label ?? "",
		);
	}
	function browse(identity: Identity) {
		const proc = { ...identity, circuitId: null };
		setProcessor(proc);
		setCursor(null);
		setSelected(null);
		setShown(12);
		void operate("circuits", { identity: proc });
	}
	const pointers = catalog?.overlay;
	const rows = [...(catalog?.records ?? [])];
	for (const f of [
		...(pointers?.favorites ?? []),
		...(pointers?.recents ?? []),
	]) {
		if (!rows.some((r) => same(r.identity, f.identity)))
			rows.push({
				identity: f.identity,
				sources: ["USER_FAVORITE_ONLY"],
				freshness: "UNKNOWN",
				block: null,
				nIn: null,
				nOut: null,
				nState: null,
				gateCount: null,
				onchainName: "",
				onchainSymbol: "",
				processorNumber: null,
				environmentDigest: null,
				manifestHash: null,
				netlistHash: null,
				dependencyHashes: [],
			});
	}
	const alias = (r: Record) =>
		pointers?.aliases.find((a) => same(a.identity, r.identity))?.label ?? "";
	const filtered = rows.filter((r) => {
		if (
			scope === "favorites" &&
			!pointers?.favorites.some((f) => same(f.identity, r.identity))
		)
			return false;
		if (
			scope === "recents" &&
			!pointers?.recents.some((f) => same(f.identity, r.identity))
		)
			return false;
		if (
			scope === "all" &&
			(processor
				? r.identity.processor !== processor.processor || !r.identity.circuitId
				: r.identity.circuitId)
		)
			return false;
		const text =
			`${r.identity.processor} ${r.identity.circuitId ?? ""} ${r.processorNumber ?? ""} ${r.onchainName} ${r.onchainSymbol} ${alias(r)} ${pointers?.favorites.find((f) => same(f.identity, r.identity))?.label ?? ""}`.toLocaleLowerCase();
		return query
			.toLocaleLowerCase()
			.split(/\s+/)
			.every((token) => text.includes(token));
	});
	return (
		<section className="library" aria-label="Circuit Library">
			<p>
				Browse X Layer processors and numbered circuit interfaces. Discovery is
				a single-provider observation; import checks the complete circuit and
				REF dependencies again.
			</p>
			<div className="actions">
				<button
					type="button"
					disabled={!!busy}
					onClick={() => {
						setProcessor(null);
						setScope("all");
						setCursor(null);
						setShown(12);
						void operate("discover");
					}}
				>
					Discover processors
				</button>
				<button
					type="button"
					disabled={!!busy}
					onClick={() => {
						setProcessor(null);
						setScope("all");
						setSelected(null);
						setCursor(null);
						setShown(12);
					}}
				>
					Browse saved processors
				</button>
				{busy && (
					<button type="button" onClick={() => controller.current?.abort()}>
						Stop discovery
					</button>
				)}
			</div>
			<div className="library-filters">
				<label>
					Search library
					<input
						type="search"
						value={query}
						maxLength={256}
						onChange={(e) => {
							setQuery(e.target.value);
							setShown(12);
						}}
						placeholder="Address, circuit ID or local alias"
					/>
				</label>
				<label>
					Collection
					<select
						value={scope}
						onChange={(e) => {
							setScope(e.target.value);
							setShown(12);
						}}
					>
						<option value="all">All records</option>
						<option value="favorites">Favorites</option>
						<option value="recents">Recent imports</option>
					</select>
				</label>
			</div>
			{storageNote && <p role="status">{storageNote}</p>}
			{error && <p role="alert">{error}</p>}
			<p role="status">
				{busy
					? `Reading ${busy}…`
					: report
						? `${report.status}${report.errorCode ? ` · ${report.errorCode}` : ""} · ${report.rpcCallsUsed}/${report.rpcCallBudget} RPC reads`
						: "Loading known addresses…"}
			</p>
			{report?.status === "UNKNOWN" && (
				<p>
					Enumeration unavailable. Known-address hints and saved favorites
					remain selectable. Retry discovery or revalidate a circuit.
				</p>
			)}
			{processor && (
				<p>
					Processor <code>{processor.processor}</code> · Circuit IDs below the
					exclusive nextId bound {nextId ?? "unknown"}.
				</p>
			)}
			<div className="library-layout">
				<div>
					{!filtered.length && (
						<p>
							No matching records. Try another search, discover processors, or
							open Favorites.
						</p>
					)}
					<ul className="library-list">
						{filtered.slice(0, shown).map((r) => (
							<li key={`${r.identity.processor}:${r.identity.circuitId}`}>
								<button
									type="button"
									aria-pressed={
										selected ? same(r.identity, selected.identity) : false
									}
									onClick={() => pick(r)}
								>
									<strong>
										{r.identity.circuitId
											? `Circuit #${r.identity.circuitId}`
											: `Processor ${r.processorNumber ?? "address"}`}
										{alias(r) && ` · ${alias(r)} (local alias)`}
									</strong>
									<code>{r.identity.processor}</code>
									<span>
										{r.freshness} · {r.sources.join(", ")}
										{r.nIn !== null &&
											` · ${r.nIn} in / ${r.nOut} out · ${r.nState ? "Stateful" : "Stateless"}`}
									</span>
								</button>
							</li>
						))}
					</ul>
					<div className="actions">
						{filtered.length > shown && (
							<button type="button" onClick={() => setShown((n) => n + 12)}>
								Show more saved records
							</button>
						)}
						{cursor !== null && scope === "all" && (
							<button
								type="button"
								disabled={!!busy}
								onClick={() => {
									setShown((n) => n + 12);
									void operate(processor ? "circuits" : "discover", {
										cursor,
										...(processor ? { identity: processor } : {}),
									});
								}}
							>
								Next discovery page
							</button>
						)}
					</div>
				</div>
				{selected && (
					<section className="library-inspector" aria-label="Selected metadata">
						<h2>
							{selected.identity.circuitId
								? `Circuit #${selected.identity.circuitId}`
								: "Processor details"}
						</h2>
						<dl>
							<dt>Processor</dt>
							<dd>{selected.identity.processor}</dd>
							<dt>Freshness</dt>
							<dd>{selected.freshness} · Revalidation required for use</dd>
							<dt>Observation block / hash</dt>
							<dd>
								{selected.block
									? `${selected.block.number} / ${selected.block.hash}`
									: "No chain observation"}
							</dd>
							<dt>Onchain display only</dt>
							<dd>
								{selected.onchainName || "No name available"}{" "}
								{selected.onchainSymbol}
							</dd>
							<dt>Numeric interface</dt>
							<dd>
								{selected.nIn === null
									? "Import to inspect"
									: `${selected.nIn} input pins / ${selected.nOut} output pins / ${selected.nState} state pins / ${selected.gateCount} gates`}
							</dd>
							<dt>Environment digest</dt>
							<dd>{selected.environmentDigest ?? "Unverified seed hint"}</dd>
							<dt>Netlist hash</dt>
							<dd>{selected.netlistHash ?? "Not imported"}</dd>
							<dt>Dependency hashes</dt>
							<dd>{selected.dependencyHashes.join(", ") || "None observed"}</dd>
						</dl>
						<div className="actions">
							<button
								type="button"
								disabled={!!busy}
								onClick={() =>
									void operate(
										pointers?.favorites.some((f) =>
											same(f.identity, selected.identity),
										)
											? "unfavorite"
											: "favorite",
										{ identity: selected.identity },
									)
								}
							>
								{pointers?.favorites.some((f) =>
									same(f.identity, selected.identity),
								)
									? "Remove favorite"
									: "Add favorite"}
							</button>
							<button
								type="button"
								disabled={!!busy}
								onClick={() => browse(selected.identity)}
							>
								Browse circuits
							</button>
						</div>
						<label>
							Local display alias
							<input
								value={label}
								maxLength={256}
								onChange={(e) => setLabel(e.target.value)}
							/>
						</label>
						<button
							type="button"
							disabled={!!busy}
							onClick={() =>
								void operate("alias", {
									identity: selected.identity,
									metadata: {
										identity: selected.identity,
										label,
										description: "",
										tags: [],
									},
								})
							}
						>
							Save alias
						</button>
						{selected.identity.circuitId && (
							<div className="actions">
								<button
									type="button"
									disabled={!!busy}
									onClick={() =>
										void operate("revalidate", { identity: selected.identity })
									}
								>
									Revalidate circuit
								</button>
								<button
									className="primary"
									type="button"
									disabled={!!busy || !!selected.nState}
									onClick={() =>
										void operate("import", { identity: selected.identity })
									}
								>
									Import into composition
								</button>
								{!!selected.nState && (
									<p>Stateful circuit. Stateless composition is unavailable.</p>
								)}
							</div>
						)}
					</section>
				)}
			</div>
		</section>
	);
}
