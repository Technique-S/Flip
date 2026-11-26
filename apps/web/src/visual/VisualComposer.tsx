import {
	Background,
	Handle,
	type Node,
	type NodeProps,
	Position,
	ReactFlow,
	ReactFlowProvider,
	useReactFlow,
	useViewport,
} from "@xyflow/react";
import { StrictMode, useEffect, useMemo, useState } from "react";
import type { Execution } from "../model";
import { rendererNotices } from "./notices";
import { projectExecution, type VisualNode } from "./projection";
import "@xyflow/react/dist/style.css";
import "./visual.css";

type CircuitNode = Node<
	{ semantic: VisualNode; inspect: (node: VisualNode, port?: string) => void },
	"circuit"
>;
function RecipeNode({ data }: NodeProps<CircuitNode>) {
	const n = data.semantic;
	return (
		<div
			className={`visual-node visual-${n.kind.toLowerCase()}`}
			data-locator={n.locator}
		>
			<div className="visual-node-heading">
				<strong>{n.title}</strong>
				<span>
					{n.kind === "INPUTS"
						? "Input bank"
						: n.kind === "OUTPUTS"
							? "Output bank"
							: n.kind}
				</span>
			</div>
			<div className="visual-ports">
				<div>
					{n.inputs.map((p) => (
						<div className="visual-port visual-in" key={p.id}>
							<Handle
								type="target"
								position={Position.Left}
								id={p.id}
								isConnectable={false}
								style={{ top: 17 }}
							/>
							<button
								type="button"
								aria-label={`${n.title} input ${p.index}, width 1`}
								data-locator={p.locator}
								onClick={(event) => {
									event.stopPropagation();
									data.inspect(n, p.id);
								}}
							>
								input {p.index}
							</button>
						</div>
					))}
				</div>
				<div>
					{n.outputs.map((p) => (
						<div className="visual-port visual-out" key={p.id}>
							<Handle
								type="source"
								position={Position.Right}
								id={p.id}
								isConnectable={false}
								style={{ top: 17 }}
							/>
							<button
								type="button"
								aria-label={`${n.title} output ${p.index}, width 1`}
								data-locator={p.locator}
								onClick={(event) => {
									event.stopPropagation();
									data.inspect(n, p.id);
								}}
							>
								output {p.index}
							</button>
						</div>
					))}
				</div>
			</div>
			{!n.inputs.length && !n.outputs.length && <p>No pins</p>}
		</div>
	);
}
const nodeTypes = { circuit: RecipeNode };
function ViewControls() {
	const { zoomIn, zoomOut, fitView } = useReactFlow();
	const { zoom } = useViewport();
	return (
		<nav className="visual-controls" aria-label="Canvas navigation">
			<button type="button" onClick={() => zoomOut()}>
				Zoom out
			</button>
			<output aria-label="Canvas zoom">{Math.round(zoom * 100)}%</output>
			<button type="button" onClick={() => zoomIn()}>
				Zoom in
			</button>
			<button type="button" onClick={() => fitView({ padding: 0.15 })}>
				Fit circuit
			</button>
		</nav>
	);
}
type EditProps = {
	request: Execution;
	inspectId?: string;
	onInspect?: (id: string) => void;
	onRemove?: (id: string) => void;
};
function Canvas({ request, inspectId, onInspect, onRemove }: EditProps) {
	const projection = useMemo(() => {
		try {
			return { graph: projectExecution(request) };
		} catch (error) {
			return { error: String(error) };
		}
	}, [request]);
	const [selection, setSelection] = useState<{
		id: string;
		port?: string;
	} | null>(null);
	const graph = projection.graph;
	useEffect(() => {
		if (inspectId && graph?.nodes.some((n) => n.id === inspectId))
			setSelection({ id: inspectId });
	}, [inspectId, graph]);
	const nodes = useMemo<CircuitNode[]>(
		() =>
			graph?.nodes.map((semantic) => ({
				id: semantic.id,
				position: semantic.position,
				type: "circuit",
				data: {
					semantic,
					inspect: (node, port) => {
						setSelection({ id: node.id, port });
						if (node.kind === "NAND") onInspect?.(node.title);
					},
				},
				ariaLabel: `${semantic.title}, ${semantic.kind}, read-only`,
				selected: selection?.id === semantic.id,
				draggable: false,
				connectable: false,
			})) ?? [],
		[graph, selection?.id, onInspect],
	);
	const edges = useMemo(
		() =>
			graph?.edges.map((e) => ({
				...e,
				type: "step",
				ariaLabel: `${e.source} ${e.sourceHandle} to ${e.target} ${e.targetHandle}, read-only`,
				reconnectable: false,
				deletable: false,
				data: { locator: e.locator },
			})) ?? [],
		[graph],
	);
	if (!graph)
		return (
			<div role="alert" className="visual-error">
				{projection.error}
			</div>
		);
	const selected = graph.nodes.find((n) => n.id === selection?.id);
	const port =
		selected &&
		[...selected.inputs, ...selected.outputs].find(
			(p) => p.id === selection?.port,
		);
	return (
		<section className="visual-composer" aria-label="Visual circuit">
			<h2>Candidate circuit</h2>
			<p>
				Connections are read-only. Select a component or pin to inspect its
				exact mapping. Drag empty space to pan.
			</p>
			<ViewControls />
			<div className="visual-workspace">
				<div className="visual-canvas" data-testid="visual-canvas">
					<ReactFlow<CircuitNode>
						nodes={nodes}
						edges={edges}
						nodeTypes={nodeTypes}
						nodesDraggable={false}
						nodesConnectable={false}
						edgesReconnectable={false}
						deleteKeyCode={null}
						disableKeyboardA11y={true}
						nodesFocusable={true}
						edgesFocusable={true}
						onNodeClick={(_, node) => {
							setSelection({ id: node.id });
							if (node.data.semantic.kind === "NAND")
								onInspect?.(node.data.semantic.title);
						}}
						onSelectionChange={({ nodes: picked }) => {
							if (picked[0])
								setSelection((previous) =>
									previous?.id === picked[0].id
										? previous
										: { id: picked[0].id },
								);
						}}
						fitView
						minZoom={0.1}
						maxZoom={2}
						preventScrolling={false}
						ariaLabelConfig={{
							"node.a11yDescription.default":
								"Connections are read-only. Use pin buttons or the component list to inspect, and NAND controls for explicit component commands.",
							"node.a11yDescription.keyboardDisabled":
								"Connections are read-only. Use pin buttons or the component list to inspect, and NAND controls for explicit component commands.",
							"edge.a11yDescription.default":
								"Read-only connection. Its endpoints are listed in Exact connection mappings. No reconnect or deletion is available.",
						}}
					>
						<Background color="#d6d8dc" gap={24} />
					</ReactFlow>
				</div>
				<aside className="visual-inspector" aria-label="Circuit inspector">
					<h3>Inspect recipe</h3>
					<label>
						Component
						<select
							id="visual-inspect-component"
							aria-label="Inspect component"
							value={selected?.id ?? ""}
							onChange={(e) => {
								setSelection({ id: e.target.value });
								const node = graph.nodes.find((n) => n.id === e.target.value);
								if (node?.kind === "NAND") onInspect?.(node.title);
							}}
						>
							<option value="">Choose a component</option>
							{graph.nodes.map((n) => (
								<option key={n.id} value={n.id}>
									{n.title} · {n.kind}
								</option>
							))}
						</select>
					</label>
					{selected && (
						<>
							<p>
								<strong>{selected.title}</strong> · {selected.kind}
							</p>
							<code>{selected.locator}</code>
							{selected.kind === "NAND" && onRemove && (
								<button type="button" onClick={() => onRemove(selected.title)}>
									Remove this NAND
								</button>
							)}
							<label>
								Pin
								<select
									aria-label="Inspect pin"
									value={port?.id ?? ""}
									onChange={(e) =>
										setSelection({ id: selected.id, port: e.target.value })
									}
								>
									<option value="">Choose a pin</option>
									{[...selected.inputs, ...selected.outputs].map((p) => (
										<option key={p.id} value={p.id}>
											{p.id} · width 1
										</option>
									))}
								</select>
							</label>
							{port && (
								<div role="status">
									<p>
										{port.id.startsWith("in:") ? "Input" : "Output"} pin{" "}
										{port.index} · width 1
									</p>
									<code>{port.locator}</code>
									{port.mapping && (
										<p>
											Source: {port.mapping.component ?? "external"} [
											{port.mapping.pin}]
										</p>
									)}
									<p>
										{
											graph.edges.filter(
												(e) =>
													(e.target === selected.id &&
														e.targetHandle === port.id) ||
													(e.source === selected.id &&
														e.sourceHandle === port.id),
											).length
										}{" "}
										connection(s)
									</p>
								</div>
							)}
							{selected.source && (
								<dl>
									<dt>Source alias</dt>
									<dd>{selected.source.alias}</dd>
									<dt>Processor</dt>
									<dd>{selected.source.identity.processor}</dd>
									<dt>Circuit ID (decimal)</dt>
									<dd>{selected.source.identity.circuitId}</dd>
									<dt>Manifest binding</dt>
									<dd>{selected.source.manifestHash}</dd>
								</dl>
							)}
						</>
					)}
					<p>
						REF internals and decoded LATCH structures are unavailable in this
						view. This view does not simulate or verify circuits. Use Advanced
						to edit wiring.
					</p>
				</aside>
			</div>
			<details>
				<summary>Exact connection mappings ({graph.edges.length})</summary>
				<div className="visual-mapping-table">
					<table>
						<thead>
							<tr>
								<th>Source / output</th>
								<th>Target / input</th>
								<th>Canonical locator</th>
							</tr>
						</thead>
						<tbody>
							{graph.edges.map((e) => (
								<tr key={e.id} data-edge-id={e.id}>
									<td>
										{e.source} / {e.sourceHandle}
									</td>
									<td>
										{e.target} / {e.targetHandle}
									</td>
									<td>{e.locator}</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</details>
		</section>
	);
}

export function VisualComposer(props: EditProps) {
	// Exercise the renderer under StrictMode without changing the surrounding application.
	return (
		<StrictMode>
			<ReactFlowProvider>
				<Canvas {...props} />
			</ReactFlowProvider>
			<details className="visual-notices">
				<summary>Renderer and dependency licenses</summary>
				<pre>{rendererNotices}</pre>
			</details>
		</StrictMode>
	);
}
