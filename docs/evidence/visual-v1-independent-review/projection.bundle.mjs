// apps/web/src/visual/projection.ts
var ADAPTER_VERSION = "flip-visual-adapter-1.0.0";
var fail = (reason) => {
  throw new Error(
    `Visual view unavailable: ${reason}. Use Advanced to inspect the original project.`
  );
};
var count = (n, max) => Number.isInteger(n) && n >= 0 && n <= max;
var name = (s) => typeof s === "string" && /^[A-Za-z][A-Za-z0-9_-]{0,63}$/.test(s);
var componentId = (id) => `candidate/component/${id}`;
function projectExecution(value) {
  try {
    return project(value);
  } catch (error) {
    if (error instanceof Error && error.message.startsWith("Visual view unavailable:"))
      throw error;
    return fail("malformed recipe or missing source metadata");
  }
}
function project(r) {
  if (r.schemaVersion !== "m3-1.0.0" || r.kind !== "M3_EXECUTION" || r.project.chainId !== 196)
    fail("unsupported execution format or chain");
  const { candidate: d, sources } = r.project;
  if (!count(d.nIn, 512) || !Array.isArray(d.components) || d.components.length > 500 || !Array.isArray(d.outputs) || !d.outputs.length || d.outputs.length > 512 || !Array.isArray(sources))
    fail("recipe exceeds the bounded visual profile");
  const aliases = new Map(sources.map((s) => [s.alias, s]));
  if (aliases.size !== sources.length) fail("duplicate source alias");
  const nodes = [];
  const edges = [];
  const widths = /* @__PURE__ */ new Map();
  const levels = /* @__PURE__ */ new Map();
  const rows = /* @__PURE__ */ new Map();
  const ports = (n, prefix, locator, mappings, derived = false) => Array.from({ length: n }, (_, index) => ({
    id: `${prefix}:${index}`,
    index,
    locator: derived ? `${locator}#${prefix}:${index}` : `${locator}[${index}]`,
    ...mappings ? { mapping: { ...mappings[index] } } : {}
  }));
  function addNode(n, level) {
    const y = rows.get(level) ?? 0;
    nodes.push({ ...n, position: { x: level * 330, y } });
    rows.set(
      level,
      y + 110 + 34 * Math.max(n.inputs.length, n.outputs.length, 1)
    );
  }
  addNode(
    {
      id: "candidate/external",
      title: "External inputs",
      kind: "INPUTS",
      locator: "project.candidate.nIn",
      inputs: [],
      outputs: ports(d.nIn, "out", "project.candidate.nIn", void 0, true)
    },
    0
  );
  function pin(p) {
    const width = p.component === null ? d.nIn : widths.get(p.component);
    if (width === void 0 || !count(p.pin, 65535) || p.pin >= width)
      fail("unbound, forward or out-of-range pin");
    return {
      id: p.component === null ? "candidate/external" : componentId(p.component),
      level: p.component === null ? 0 : levels.get(p.component) ?? 0
    };
  }
  function connections(target, mappings, locator) {
    mappings.forEach((p, i) => {
      const from = pin(p);
      edges.push({
        id: `${target}/in/${i}`,
        source: from.id,
        sourceHandle: `out:${p.pin}`,
        target,
        targetHandle: `in:${i}`,
        locator: `${locator}[${i}]`
      });
    });
  }
  for (const [index, c] of d.components.entries()) {
    if (!name(c.instanceId) || widths.has(c.instanceId) || !Array.isArray(c.inputs) || c.inputs.length > 512)
      fail("invalid or duplicate component identity");
    const locator = `project.candidate.components[${index}]`;
    let width = 1;
    let source;
    if (c.kind === "NAND") {
      if (c.inputs.length !== 2) fail("NAND requires two scalar inputs");
    } else if (c.kind === "REF") {
      source = aliases.get(c.sourceAlias ?? "");
      if (source?.nState !== 0 || !count(source.nIn, 255) || !count(source.nOut, 255) || !source.nOut || c.inputs.length !== source.nIn)
        fail("unresolved or stateful REF interface");
      const s = source;
      if (s.identity.chainId !== 196 || s.identity.schemaVersion !== "1.0.0" || typeof s.identity.circuitId !== "string" || !/^0x[0-9a-f]{40}$/i.test(s.identity.processor) || !/^(0|[1-9][0-9]*)$/.test(s.identity.circuitId) || s.identity.circuitId.length > 20 || BigInt(s.identity.circuitId) >= 2n ** 64n)
        fail("invalid REF identity");
      const imported = r.imports.find(
        (entry) => entry.manifestHash === s.manifestHash
      );
      const root = imported?.manifest.root;
      if (!root || root.identity.processor !== s.identity.processor || root.identity.circuitId !== s.identity.circuitId || root.identity.chainId !== s.identity.chainId || root.nIn !== s.nIn || root.nOut !== s.nOut || root.nState !== 0)
        fail("REF source and manifest interface differ");
      width = s.nOut;
    } else fail("unsupported component kind (LATCH authoring is unavailable)");
    const level = 1 + Math.max(0, ...c.inputs.map((p) => pin(p).level));
    const id = componentId(c.instanceId);
    connections(id, c.inputs, `${locator}.inputs`);
    widths.set(c.instanceId, width);
    levels.set(c.instanceId, level);
    addNode(
      {
        id,
        title: c.instanceId,
        kind: c.kind,
        locator,
        inputs: ports(c.inputs.length, "in", `${locator}.inputs`, c.inputs),
        outputs: ports(
          width,
          "out",
          source ? `project.sources[${sources.indexOf(source)}].nOut` : `${locator}.kind`,
          void 0,
          true
        ),
        ...source ? { source: { ...source, identity: { ...source.identity } } } : {}
      },
      level
    );
  }
  connections("candidate/outputs", d.outputs, "project.candidate.outputs");
  addNode(
    {
      id: "candidate/outputs",
      title: "Final outputs",
      kind: "OUTPUTS",
      locator: "project.candidate.outputs",
      inputs: ports(
        d.outputs.length,
        "in",
        "project.candidate.outputs",
        d.outputs
      ),
      outputs: []
    },
    1 + Math.max(0, ...levels.values())
  );
  if (edges.length > 1e3 || nodes.reduce((sum, n) => sum + n.inputs.length + n.outputs.length, 0) > 4096)
    fail("connection or visible pin budget exceeded");
  return { version: ADAPTER_VERSION, nodes, edges };
}
export {
  ADAPTER_VERSION,
  projectExecution
};
