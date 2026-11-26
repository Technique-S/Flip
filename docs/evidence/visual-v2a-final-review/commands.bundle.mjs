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
  if (sources.some((source) => !name(source.alias)))
    fail("invalid source alias");
  const aliases = new Map(sources.map((s) => [s.alias, s]));
  if (aliases.size !== sources.length) fail("duplicate source alias");
  const nodes = [];
  const edges = [];
  const widths = /* @__PURE__ */ new Map();
  const levels = /* @__PURE__ */ new Map();
  const rows = /* @__PURE__ */ new Map();
  let allocatedPorts = 0;
  const ports = (n, prefix, locator, mappings, derived = false) => {
    if (allocatedPorts + n > 4096)
      fail("visible pin budget exceeded before allocation");
    allocatedPorts += n;
    return Array.from({ length: n }, (_, index) => ({
      id: `${prefix}:${index}`,
      index,
      locator: derived ? `${locator}#${prefix}:${index}` : `${locator}[${index}]`,
      ...mappings ? { mapping: { ...mappings[index] } } : {}
    }));
  };
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
    if (edges.length + mappings.length > 1e3)
      fail("connection budget exceeded before allocation");
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
      if (!name(c.sourceAlias ?? "")) fail("invalid REF source alias");
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

// apps/web/src/visual/commands.ts
var name2 = (v) => typeof v === "string" && /^[A-Za-z][A-Za-z0-9_-]{0,63}$/.test(v);
var requestKey = (r) => JSON.stringify(r);
var size = (s) => new TextEncoder().encode(s).length;
function checkInteractiveBudget(r) {
  const d = r.project.candidate;
  const pins = d.components.reduce(
    (n, c) => n + c.inputs.length,
    d.outputs.length
  );
  const width = d.components.reduce(
    (n, c) => n + (r.project.sources.find((s) => s.alias === c.sourceAlias)?.nOut ?? 1),
    d.nIn
  );
  if (pins * width > 65e3 || d.nIn > 255 || d.outputs.length > 255)
    throw Error(
      "This project exceeds the interactive pin table budget. Use the CLI for larger designs."
    );
  if (size(requestKey(r)) > 1048576)
    throw Error("Project exceeds the 1 MiB interactive request limit.");
}
function availablePins(r) {
  const d = r.project.candidate;
  const pins = Array.from({ length: d.nIn }, (_, pin) => ({
    component: null,
    pin
  }));
  for (const c of d.components) {
    const n = c.kind === "NAND" ? 1 : r.project.sources.find((s) => s.alias === c.sourceAlias)?.nOut ?? 0;
    for (let pin = 0; pin < n; pin++)
      pins.push({ component: c.instanceId, pin });
  }
  return pins;
}
function removalProblem(r, id) {
  const c = r.project.candidate.components.find((c2) => c2.instanceId === id);
  if (c?.kind !== "NAND")
    return "Select an existing NAND component. REF removal is unavailable here.";
  const refs = [];
  r.project.candidate.components.forEach((c2, i) => {
    c2.inputs.forEach((p, j) => {
      if (p.component === id)
        refs.push(`project.candidate.components[${i}].inputs[${j}]`);
    });
  });
  r.project.candidate.outputs.forEach((p, i) => {
    if (p.component === id) refs.push(`project.candidate.outputs[${i}]`);
  });
  return refs.length ? `Cannot remove ${id}: referenced by ${refs.slice(0, 8).join(", ")}${refs.length > 8 ? ` and ${refs.length - 8} more` : ""}. Change those mappings explicitly in Advanced first.` : null;
}
function proposeNand(r, value) {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw Error("Invalid edit command.");
  const c = value;
  if (!name2(c.instanceId))
    throw Error(
      "Component ID must start with a letter and contain at most 64 letters, digits, underscores or hyphens."
    );
  if (c.type !== "AddNand" && c.type !== "RemoveNand")
    throw Error("Unsupported edit command.");
  const keys = c.type === "AddNand" ? ["type", "instanceId", "inputs"] : ["type", "instanceId"];
  if (Object.keys(c).length !== keys.length || Object.keys(c).some((k) => !keys.includes(k)))
    throw Error("Unexpected edit command fields.");
  const next = structuredClone(r);
  if (c.type === "AddNand") {
    if (next.project.candidate.components.some(
      (x) => x.instanceId === c.instanceId
    ))
      throw Error("Component ID already exists.");
    if (!Array.isArray(c.inputs) || c.inputs.length !== 2)
      throw Error("Choose exactly two explicit NAND input sources.");
    const available = availablePins(r);
    const inputs = c.inputs.map((p) => {
      if (!p || typeof p !== "object" || Array.isArray(p))
        throw Error("Invalid input binding.");
      const v = p;
      if (Object.keys(v).length !== 2 || !("component" in v) || !("pin" in v) || v.component !== null && !name2(v.component) || typeof v.pin !== "number" || !Number.isInteger(v.pin) || !available.some((a) => a.component === v.component && a.pin === v.pin))
        throw Error(
          "Input must identify an existing external or preceding output pin."
        );
      return { component: v.component, pin: v.pin };
    });
    next.project.candidate.components.push({
      kind: "NAND",
      instanceId: c.instanceId,
      inputs
    });
  } else {
    const issue = removalProblem(r, c.instanceId);
    if (issue) throw Error(issue);
    next.project.candidate.components = next.project.candidate.components.filter(
      (x) => x.instanceId !== c.instanceId
    );
  }
  checkInteractiveBudget(next);
  projectExecution(next);
  return next;
}
var openHistory = (r) => ({
  present: structuredClone(r),
  past: [],
  future: [],
  saved: requestKey(r),
  evicted: 0
});
function bounded(h) {
  let bytes = [h.present, ...h.past, ...h.future].reduce(
    (n, r) => n + size(requestKey(r)),
    size(h.saved)
  );
  while (h.past.length + h.future.length > 100 || bytes > 4 * 1048576) {
    const removed = h.past.length ? h.past.shift() : h.future.pop();
    if (!removed) break;
    bytes -= size(requestKey(removed));
    h.evicted++;
  }
  return h;
}
function commitHistory(h, next) {
  return bounded({
    ...h,
    present: structuredClone(next),
    past: [...h.past, h.present],
    future: []
  });
}
function moveHistory(h, direction) {
  if (direction === "Undo") {
    const target2 = h.past.at(-1);
    if (!target2) throw Error("Nothing to undo.");
    return bounded({
      ...h,
      present: structuredClone(target2),
      past: h.past.slice(0, -1),
      future: [h.present, ...h.future]
    });
  }
  const target = h.future[0];
  if (!target) throw Error("Nothing to redo.");
  return bounded({
    ...h,
    present: structuredClone(target),
    past: [...h.past, h.present],
    future: h.future.slice(1)
  });
}
export {
  availablePins,
  checkInteractiveBudget,
  commitHistory,
  moveHistory,
  openHistory,
  proposeNand,
  removalProblem,
  requestKey
};
