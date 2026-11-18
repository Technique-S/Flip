export type Pin = { component: string | null; pin: number };
export type Component = {
	instanceId: string;
	kind: "REF" | "NAND";
	sourceAlias?: string;
	inputs: Pin[];
};
export type Design = { nIn: number; components: Component[]; outputs: Pin[] };
type Identity = {
	schemaVersion: "1.0.0";
	processor: string;
	circuitId: string;
	chainId: 196;
};
type Snapshot = {
	identity: Identity;
	nIn: number;
	nOut: number;
	nState: number;
	expandedGates: number;
	netlistHash: string;
};
export type Imported = {
	manifestHash: string;
	manifest: {
		root: Snapshot;
		dependencies: Snapshot[];
		block: { number: string; hash: string };
	};
	integrity: { freshness: string };
};
type Source = Pick<Snapshot, "identity" | "nIn" | "nOut" | "nState"> & {
	alias: string;
	manifestHash: string;
};
export type Execution = {
	schemaVersion: "m3-1.0.0";
	kind: "M3_EXECUTION";
	relation: "BEHAVIORAL" | "PREVIOUS_VERSION" | "REFERENCE";
	imports: Imported[];
	project: {
		schemaVersion: "m3-1.0.0" | "1.0.0";
		projectId: string;
		toolVersion: "0.1.0";
		chainId: 196;
		sources: Source[];
		candidate: Design;
		referenceCandidate?: Design;
		comparison: {
			kind: "PAIRWISE_EQUIVALENCE";
			referenceAlias: string | null;
			intent: "UNDECLARED" | "TRUSTED_REFERENCE";
			trustAssertion: string | null;
			inputMap: number[];
			outputMap: number[];
		};
		limits: {
			gateCap: number;
			solverTimeoutMs: number;
			refDepthCap: number;
			solverMemoryMiB: number;
		};
	};
};
export type Built = {
	projectHash: string;
	manifestHash: string;
	netlist: string;
	manifest: {
		expandedGates: number;
		dependencies: Snapshot[];
		netlistHash: string;
	};
};
export type Proof = {
	report: {
		projectHash: string;
		candidateManifestHash: string;
		referenceManifestHash: string;
		integrity: { freshness: string };
		verification: {
			verdict: string;
			solverOutcome: string;
			reasonCode: string | null;
			witness: null | {
				inputs: { bits: string };
				referenceOutputs: { bits: string };
				candidateOutputs: { bits: string };
			};
		};
	};
	coverage: string;
	referenceIdentity: unknown;
	candidateIdentity: unknown;
	resources: { totalMs: number };
	engineHash: string;
};
export type Preflight = {
	status: string;
	reasonCode: string | null;
	integrity: { freshness: string };
	observation: null | {
		block: { number: string };
		feeWei: string;
		classification: string;
	};
};
export type Bundle = {
	schemaVersion: string;
	contentHash: string;
	comparison: Proof;
	chainObservation: Preflight | null;
};
export const indices = (n: number) => Array.from({ length: n }, (_, i) => i);
export const external = (pin: number): Pin => ({ component: null, pin });
export function source(item: Imported, alias: string): Source {
	const { identity, nIn, nOut, nState } = item.manifest.root;
	return {
		alias,
		identity,
		nIn,
		nOut,
		nState,
		manifestHash: item.manifestHash,
	};
}
export const productBody = (executionRequest: Execution) => ({
	schemaVersion: "m4-1.0.0",
	kind: "PRODUCT_REQUEST",
	executionRequest,
});
export async function api<T>(path: string, body?: unknown): Promise<T> {
	const r = await fetch(
		`/api/v1/${path}`,
		body === undefined
			? {}
			: {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: typeof body === "string" ? body : JSON.stringify(body),
				},
	);
	if (!r.ok) {
		const detail = await r.json().catch(() => null);
		if (r.status === 501)
			throw Error(
				"Local solver disabled. Set FLIP_LOCAL_SOLVER=1 and restart Flip.",
			);
		throw Error(
			detail?.error
				? `${detail.error.code} · ${detail.error.message}`
				: `Local API returned HTTP ${r.status}`,
		);
	}
	return r.json();
}
export async function readFile(file: File) {
	if (file.size > 1048576) throw Error("File exceeds the 1 MiB input limit.");
	return file.text();
}
export function download(name: string, value: unknown) {
	const url = URL.createObjectURL(
		new Blob([JSON.stringify(value)], { type: "application/json" }),
	);
	const link = document.createElement("a");
	link.href = url;
	link.download = name;
	link.click();
	setTimeout(() => URL.revokeObjectURL(url), 1000);
}
