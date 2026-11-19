"""Self-contained TAP-02 evaluator and connection-level signal-cone tracer.

Independent supporting-fixture code for M4.5-2D. Written from the TAP-02
encoding/evaluation rules and checked against the archived XOR#1 and NAND#2
truth vectors. No production Flip module, Codex branch or third-party package is
imported. Nothing here is a production diagnostic or a proof oracle.

The tracer records *relevant computation* only. It never decides that a
connection is faulty; fault claims require a declared intent oracle and a fresh
trusted comparison (see diagnostics/diagnostic-rules.json).
"""
from __future__ import annotations

from dataclasses import dataclass, field

NAND, LATCH, REF = 0x00, 0x01, 0x02
MAX_SIGNALS = 1 << 24
MAX_GATES = (1 << 32) - 1
CORE_VERSION = "debug-core-1.0.0"


class Malformed(ValueError):
    pass


class ResourceLimit(Malformed):
    pass


@dataclass
class Element:
    op: int
    ins: list[int]
    cpu: bytes = b""
    cid: int = 0
    n_out: int = 1
    first_out: int = 0


@dataclass
class Circuit:
    n_in: int
    n_out: int
    elements: list[Element]
    n_signals: int
    subs: dict = field(default_factory=dict)
    n_gates: int = 0


def nand(*ins: int) -> Element:
    return Element(NAND, list(ins))


def ref(cpu_hex: str, cid: int, ins: list[int], n_out: int = 1) -> Element:
    return Element(REF, list(ins), bytes.fromhex(cpu_hex), cid, n_out)


def encode(els: list[Element]) -> bytes:
    out = bytearray()
    for e in els:
        out.append(e.op)
        if e.op == REF:
            if len(e.cpu) != 20 or not 0 <= e.cid < 1 << 64:
                raise Malformed("invalid REF identity")
            out += e.cpu + e.cid.to_bytes(8, "big") + bytes([len(e.ins), e.n_out])
        for s in e.ins:
            if not 0 <= s < MAX_SIGNALS:
                raise Malformed("signal out of range")
            out += s.to_bytes(3, "big")
    return bytes(out)


def decode(data: bytes, n_in: int) -> list[Element]:
    if not isinstance(data, (bytes, bytearray)):
        raise Malformed("netlist must be bytes")
    p, nxt, els = 0, 2 + n_in, []

    def take(k: int) -> bytes:
        nonlocal p
        if p + k > len(data):
            raise Malformed("truncated record at byte %d" % p)
        chunk = data[p:p + k]
        p += k
        return chunk

    u24 = lambda: int.from_bytes(take(3), "big")
    while p < len(data):
        op = take(1)[0]
        if op == NAND:
            e = Element(NAND, [u24(), u24()])
        elif op == REF:
            cpu = take(20)
            cid = int.from_bytes(take(8), "big")
            ni, no = take(1)[0], take(1)[0]
            e = Element(REF, [u24() for _ in range(ni)], cpu, cid, no)
        else:
            raise Malformed("unsupported opcode 0x%02x at byte %d" % (op, p - 1))
        e.first_out = nxt
        nxt += e.n_out
        els.append(e)
    return els


def load(data: bytes, n_in: int, n_out: int, bank: dict,
         ref_depth_cap: int = 64, gate_cap: int = MAX_GATES,
         _stack: tuple = (), _memo: dict | None = None,
         _depth: int = 0) -> Circuit:
    """Decode, validate backward references and resolve REFs from ``bank``.

    ``bank`` maps (cpu_hex, cid) -> (nIn, nOut, netlist_bytes).
    """
    if not (0 <= n_in <= (1 << 16)) or not (1 <= n_out <= (1 << 16)):
        raise Malformed("interface width out of range")
    els = decode(data, n_in)
    n_sig = 2 + n_in + sum(e.n_out for e in els)
    if n_sig > MAX_SIGNALS or n_sig - 2 - n_in < n_out:
        raise Malformed("signal count invalid")
    memo = {} if _memo is None else _memo

    def resolve(key: tuple) -> Circuit:
        if key in _stack:
            raise Malformed("REF cycle at %s" % (key,))
        if _depth + 1 > ref_depth_cap:
            raise ResourceLimit("REF depth cap exceeded")
        if key in memo:
            return memo[key]
        entry = bank.get(key)
        if entry is None:
            raise Malformed("REF target is not a registered circuit")
        sni, sno, sdata = entry
        sub = load(sdata, sni, sno, bank, ref_depth_cap, gate_cap,
                   _stack + (key,), memo, _depth + 1)
        memo[key] = sub
        return sub

    c = Circuit(n_in, n_out, els, n_sig)
    for e in els:
        for s in e.ins:
            if s >= e.first_out:
                raise Malformed("signal %d at element %d is not available" % (s, e.first_out))
        if e.op == NAND:
            c.n_gates += 1
        else:
            sub = resolve((e.cpu.hex(), e.cid))
            if (sub.n_in, sub.n_out) != (len(e.ins), e.n_out):
                raise Malformed("REF arity mismatch")
            c.subs[(e.cpu.hex(), e.cid)] = sub
            c.n_gates += sub.n_gates
            if c.n_gates > gate_cap:
                raise ResourceLimit("expanded gate cap exceeded")
    return c


def evaluate_all(c: Circuit, inputs: list[int]) -> list[int]:
    """Return every signal value (0, 1, inputs, then each element output)."""
    if len(inputs) != c.n_in:
        raise ValueError("input width mismatch")
    vals = [0, 1] + list(inputs)

    def run(comp: Circuit, ins: list[int]) -> list[int]:
        local = [0, 1] + list(ins)
        for e in comp.elements:
            if e.op == NAND:
                local.append(1 - (local[e.ins[0]] & local[e.ins[1]]))
            else:
                sub = comp.subs[(e.cpu.hex(), e.cid)]
                outs = run(sub, [local[s] for s in e.ins])
                local.extend(outs[len(outs) - sub.n_out:])
        return local

    return run(c, inputs)


def mapped_outputs(c: Circuit, inputs: list[int], output_map: list[int]) -> list[int]:
    """Values selected by the declared output map (pin indices are signals)."""
    values = evaluate_all(c, inputs)
    if len(output_map) != c.n_out:
        raise Malformed("output map width mismatch")
    for s in output_map:
        if not 0 <= s < len(values):
            raise Malformed("output map selects a nonexistent signal")
    return [values[s] for s in output_map]


def eval_recursive(c: Circuit, inputs: list[int]) -> tuple[int, ...]:
    values = evaluate_all(c, inputs)
    return tuple(values[len(values) - c.n_out:])


def flatten(c: Circuit) -> tuple[list[tuple[int, int]], list[int]]:
    """Inline all REFs; return NAND pairs and the flat indices of emitted outputs."""
    gates: list[tuple[int, int]] = []

    def inline(comp: Circuit, input_sigs: list[int], next_sig: int) -> tuple[dict, int]:
        local = {0: 0, 1: 1}
        for i, s in enumerate(input_sigs):
            local[2 + i] = s
        for e in comp.elements:
            if e.op == NAND:
                gates.append((local[e.ins[0]], local[e.ins[1]]))
                local[e.first_out] = next_sig
                next_sig += 1
            else:
                sub = comp.subs[(e.cpu.hex(), e.cid)]
                sub_local, next_sig = inline(sub, [local[s] for s in e.ins], next_sig)
                for j in range(sub.n_out):
                    local[e.first_out + j] = sub_local[sub.n_signals - sub.n_out + j]
        return local, next_sig

    local, _ = inline(c, list(range(2, 2 + c.n_in)), 2 + c.n_in)
    outputs = [local[c.n_signals - c.n_out + i] for i in range(c.n_out)]
    return gates, outputs


def eval_flat(gates: list[tuple[int, int]], outputs: list[int], inputs: list[int]) -> tuple[int, ...]:
    vals = [0, 1] + list(inputs)
    for a, b in gates:
        vals.append(1 - (vals[a] & vals[b]))
    return tuple(vals[s] for s in outputs)


def exhaustive(c: Circuit, output_map: list[int] | None = None) -> list[dict]:
    """Exact truth table by full enumeration, cross-checked by two evaluators."""
    if c.n_in > 16:
        raise ResourceLimit("exhaustive enumeration refused for nIn > 16")
    if output_map is None:
        output_map = list(range(c.n_signals - c.n_out, c.n_signals))
    emission = list(range(c.n_signals - c.n_out, c.n_signals))
    gates, flat_outputs = flatten(c)
    rows = []
    for v in range(1 << c.n_in):
        bits = [(v >> i) & 1 for i in range(c.n_in)]
        r = mapped_outputs(c, bits, output_map)
        r_emission = mapped_outputs(c, bits, emission)
        f = eval_flat(gates, flat_outputs, bits)
        if r_emission != list(f):
            raise AssertionError("evaluator disagreement at %s: %s vs %s" % (bits, r_emission, f))
        rows.append({"in": bits, "in_packed": v, "out": r})
    return rows


def witness_table(ref: Circuit, ref_map: list[int], cand: Circuit, cand_map: list[int]) -> dict:
    """Find the first differing input by exhaustive enumeration and replay it."""
    if (ref.n_in, ref.n_out) != (cand.n_in, cand.n_out):
        return {"kind": "INVALID_INPUT", "reason": "interface width mismatch"}
    rt, ct = exhaustive(ref, ref_map), exhaustive(cand, cand_map)
    diffs = []
    for r, c in zip(rt, ct):
        positions = [i for i in range(ref.n_out) if r["out"][i] != c["out"][i]]
        if positions:
            diffs.append({"in": r["in"], "in_packed": r["in_packed"],
                          "reference_out": r["out"], "candidate_out": c["out"],
                          "differing_bits": positions})
    if not diffs:
        return {"kind": "EQUIVALENT", "exhaustive_rows": len(rt),
                "reference_table": rt, "candidate_table": ct}
    w = diffs[0]
    return {"kind": "DIFFERENT", "exhaustive_rows": len(rt),
            "witness": w, "all_differences": diffs,
            "reference_table": rt, "candidate_table": ct,
            "witness_replayed_by": ["recursive", "flat"]}


# ---------------------------------------------------------------------------
# Connection-level signal-cone tracer
# ---------------------------------------------------------------------------
def _source_desc(signal: int, comp: Circuit) -> str:
    if signal == 0:
        return "const0"
    if signal == 1:
        return "const1"
    if signal < 2 + comp.n_in:
        return "input[%d]" % (signal - 2)
    for e in comp.elements:
        if e.first_out <= signal < e.first_out + e.n_out:
            kind = "NAND" if e.op == NAND else "REF"
            return "%s[%d].out[%d]" % (kind, e.first_out, signal - e.first_out)
    return "unknown[%d]" % signal


def trace_cone(c: Circuit, output_signals: list[int], node_cap: int = 512) -> dict:
    """Backward-reachable connections for the given emitted signals.

    Returns relevant computation and explicit cone-boundary information. It does
    not rank, blame or repair anything. Node caps make the trace bounded.
    """
    visited: set[tuple[str, int]] = set()
    queue: list[tuple[str, int, Circuit, str]] = [
        ("out", s, c, "top") for s in output_signals
    ]
    connections: list[dict] = []
    boundaries: list[dict] = []
    truncated = False

    while queue:
        origin, signal, comp, path = queue.pop(0)
        key = (path, id(comp), signal)
        if key in visited:
            continue
        visited.add(key)
        if len(visited) > node_cap:
            truncated = True
            break
        if signal in (0, 1) or signal < 2 + comp.n_in:
            boundaries.append({"path": path, "origin": origin, "signal": signal,
                               "description": _source_desc(signal, comp)})
            continue
        producer = None
        for idx, e in enumerate(comp.elements):
            if e.first_out <= signal < e.first_out + e.n_out:
                producer = (idx, e)
                break
        if producer is None:
            boundaries.append({"path": path, "origin": origin, "signal": signal,
                               "description": "unknown"})
            continue
        idx, e = producer
        for pin, src in enumerate(e.ins):
            connections.append({
                "path": path,
                "connectionRef": "%s/element[%d].in[%d]" % (path, idx, pin),
                "origin": origin,
                "elementIndex": idx,
                "kind": "NAND" if e.op == NAND else "REF",
                "outputPin": signal - e.first_out,
                "inputPin": pin,
                "sourceSignal": src,
                "sourceDescription": _source_desc(src, comp),
            })
            queue.append(("element[%d].in[%d]" % (idx, pin), src, comp, path))
        if e.op == REF:
            sub = comp.subs[(e.cpu.hex(), e.cid)]
            sub_out = signal - e.first_out
            queue.append(("ref[%d].out[%d]" % (idx, sub_out),
                          _sub_output_signal(sub, sub_out), sub,
                          "%s/ref[%d]" % (path, idx)))

    return {
        "outputSignals": output_signals,
        "connections": sorted(connections, key=lambda x: (
            x["path"], x["elementIndex"], x["inputPin"])),
        "coneBoundaries": boundaries,
        "nodesVisited": len(visited),
        "nodeCap": node_cap,
        "truncated": truncated,
        "classification": "RELEVANT_COMPUTATION",
    }


def _sub_output_signal(sub: Circuit, n: int) -> int:
    """Signal number of sub output n inside the sub circuit."""
    return sub.n_signals - sub.n_out + n


def self_test() -> dict:
    """Trusted archived vectors and evaluator cross-check."""
    xor = load(encode([
        nand(2, 3), nand(2, 4), nand(3, 4), nand(5, 6),
    ]), 2, 1, {})
    nand_c = load(encode([nand(2, 3)]), 2, 1, {})
    xor_rows = [r["out"] for r in exhaustive(xor)]
    nand_rows = [r["out"] for r in exhaustive(nand_c)]
    assert xor_rows == [[0], [1], [1], [0]], xor_rows
    assert nand_rows == [[1], [1], [1], [0]], nand_rows
    return {
        "coreVersion": CORE_VERSION,
        "xor_vector": [list(x) for x in xor_rows],
        "nand_vector": [list(x) for x in nand_rows],
        "checks": 2,
    }
