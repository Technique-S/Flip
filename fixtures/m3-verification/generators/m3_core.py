"""Self-contained TAP-02 core for the independent Flip M3 verification corpus.

Written from the TAP-02 netlist/encoding/evaluation specification text (the same
rules implemented by the audit's tape02_reference.py, MIT, and
independent_eval.py). No production Flip code and no Codex M3 work is imported.

The module provides three deliberately different evaluation paths so expected
results are cross-checked rather than taken from a single implementation:

  * ``load`` + ``beat``       -- recursive element-by-element evaluator
  * ``flatten`` + ``eval_flat`` -- inline every REF into a flat NAND list, then
                                  evaluate that list iteratively
  * ``cnf_miter`` + ``solve`` -- Tseitin encoding + a small DPLL solver used to
                                decide pairwise stateless equivalence exactly
                                on small domains

Only the Python standard library is used. Nothing here is a production solver
and no timing produced by ``solve`` is a production performance result.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Callable

NAND, LATCH, REF = 0x00, 0x01, 0x02
MAX_SIGNALS = 1 << 24
MAX_PINS = 1 << 16
MAX_GATES = (1 << 32) - 1

CORE_VERSION = "m3-core-1.0.0"


class Malformed(ValueError):
    """A TAP-02 section 3 well-formedness violation."""


class ResourceLimit(Malformed):
    """A declared or computed size/depth budget was exceeded."""


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
    subs: dict = field(default_factory=dict)   # (cpu_hex, cid) -> Circuit
    n_state: int = 0
    n_gates: int = 0
    cycle_guard: tuple = ()


@dataclass
class FlatNet:
    n_in: int
    n_out: int
    n_signals: int
    gates: list[tuple[int, int]]
    output_signals: list[int]


# --------------------------------------------------------------------------
# Encoding / decoding
# --------------------------------------------------------------------------
def encode(els: list[Element]) -> bytes:
    out = bytearray()
    for e in els:
        out.append(e.op)
        if e.op == REF:
            if len(e.cpu) != 20:
                raise Malformed("REF cpu must be 20 bytes")
            if not (0 <= e.cid < 1 << 64):
                raise Malformed("REF cid must fit uint64")
            out += e.cpu + e.cid.to_bytes(8, "big") + bytes([len(e.ins), e.n_out])
        for s in e.ins:
            if not (0 <= s < 1 << 24):
                raise Malformed("signal must fit uint24")
            out += s.to_bytes(3, "big")
    return bytes(out)


def nand(a: int, b: int) -> Element:
    return Element(NAND, [a, b])


def latch(d: int) -> Element:
    return Element(LATCH, [d])


def ref(cpu: bytes, cid: int, ins: list[int], n_out: int = 1) -> Element:
    return Element(REF, list(ins), cpu, cid, n_out)


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
        elif op == LATCH:
            e = Element(LATCH, [u24()])
        elif op == REF:
            cpu = take(20)
            cid = int.from_bytes(take(8), "big")
            ni, no = take(1)[0], take(1)[0]
            e = Element(REF, [u24() for _ in range(ni)], cpu, cid, no)
        else:
            raise Malformed("unknown opcode 0x%02x at byte %d" % (op, p - 1))
        e.first_out = nxt
        nxt += e.n_out
        els.append(e)
    return els


# --------------------------------------------------------------------------
# Loading / well-formedness / resolution
# --------------------------------------------------------------------------
def load(data: bytes, n_in: int, n_out: int, bank: dict,
         ref_depth_cap: int = 64, gate_cap: int = MAX_GATES,
         _stack: list | None = None, _memo: dict | None = None,
         _depth: int = 0) -> Circuit:
    """Decode and validate. ``bank`` maps (cpu_hex, cid) -> (nIn, nOut, bytes).

    ``_stack``/``_memo``/``_depth`` are shared across nested loads so the cycle
    guard and depth cap apply to the whole dependency graph, not one record.
    """
    if not (0 <= n_in <= MAX_PINS):
        raise Malformed("nIn out of range")
    if not (1 <= n_out <= MAX_PINS):
        raise Malformed("nOut out of range")
    els = decode(data, n_in)
    n_sig = 2 + n_in + sum(e.n_out for e in els)
    if n_sig > MAX_SIGNALS:
        raise Malformed("more than 2^24 signals")
    if n_sig - 2 - n_in < n_out:
        raise Malformed("too few signals for outputs")

    memo: dict = _memo if _memo is not None else {}
    stack: list = _stack if _stack is not None else []

    def resolve(key: tuple, depth: int) -> Circuit:
        if key in stack:
            raise Malformed("REF cycle at %s" % (key,))
        if depth > ref_depth_cap:
            raise ResourceLimit("REF depth exceeds cap %d" % ref_depth_cap)
        if key in memo:
            return memo[key]
        entry = bank.get(key)
        if entry is None:
            raise Malformed("REF target is not a circuit of a registered processor")
        sni, sno, sdata = entry
        stack.append(key)
        try:
            sub = load(sdata, sni, sno, bank, ref_depth_cap, gate_cap,
                       stack, memo, depth)
        finally:
            stack.pop()
        memo[key] = sub
        return sub

    c = Circuit(n_in, n_out, els, n_sig)
    for e in els:
        limit = n_sig if e.op == LATCH else e.first_out
        for s in e.ins:
            if s >= limit:
                raise Malformed("signal %d referenced by element at %d is not available"
                                % (s, e.first_out))
        c.n_state += 1 if e.op == LATCH else 0
        c.n_gates += 1 if e.op in (NAND, LATCH) else 0
        if e.op == REF:
            key = (e.cpu.hex(), e.cid)
            sub = resolve(key, _depth + 1)
            if (sub.n_in, sub.n_out) != (len(e.ins), e.n_out):
                raise Malformed("REF arity does not match the target circuit")
            c.subs[key] = sub
            c.n_state += sub.n_state
            c.n_gates += sub.n_gates
            if c.n_gates > gate_cap:
                raise ResourceLimit("expanded gate count exceeds cap %d" % gate_cap)
    if c.n_state > MAX_SIGNALS:
        raise Malformed("size overflow")
    return c


# --------------------------------------------------------------------------
# Evaluator 1: recursive beat over resolved elements
# --------------------------------------------------------------------------
def beat(c: Circuit, state: list[int], inputs: list[int]) -> tuple[list[int], list[int]]:
    if len(state) != c.n_state or len(inputs) != c.n_in:
        raise ValueError("beat: state/input width mismatch")

    def run(comp: Circuit, st: list[int], ins: list[int]):
        vals = [0, 1] + list(ins)
        ns = list(st)
        cursor = 0
        latch_bases = []
        for e in comp.elements:
            if e.op == NAND:
                vals.append(1 - (vals[e.ins[0]] & vals[e.ins[1]]))
            elif e.op == LATCH:
                latch_bases.append((e, cursor))
                vals.append(st[cursor])
                cursor += 1
            else:
                sub = comp.subs[(e.cpu.hex(), e.cid)]
                sub_ns, sub_outs = run(
                    sub, st[cursor:cursor + sub.n_state], [vals[s] for s in e.ins]
                )
                if sub.n_state:
                    ns[cursor:cursor + sub.n_state] = sub_ns
                cursor += sub.n_state
                vals.extend(sub_outs)
        for e, base in latch_bases:
            ns[base] = vals[e.ins[0]]
        return ns, vals[len(vals) - comp.n_out:]

    return run(c, list(state), list(inputs))


def eval_recursive(c: Circuit, inputs: list[int]) -> tuple[int, ...]:
    if c.n_state:
        raise ValueError("eval_recursive supports stateless circuits only")
    return tuple(beat(c, [], list(inputs))[1])


# --------------------------------------------------------------------------
# Evaluator 2: inline all REFs into a flat NAND list, evaluate iteratively
# --------------------------------------------------------------------------
def flatten(c: Circuit) -> FlatNet:
    if c.n_state:
        raise ValueError("flatten supports stateless circuits only")

    def inline(comp: Circuit, input_sigs: list[int], next_sig: int):
        local = {0: 0, 1: 1}
        for i, s in enumerate(input_sigs):
            local[2 + i] = s
        gates: list[tuple[int, int]] = []
        produced: list[int] = []
        for e in comp.elements:
            if e.op == NAND:
                gates.append((local[e.ins[0]], local[e.ins[1]]))
                local[e.first_out] = next_sig
                produced.append(next_sig)
                next_sig += 1
            else:
                sub = comp.subs[(e.cpu.hex(), e.cid)]
                sub_ins = [local[s] for s in e.ins]
                sub_gates, sub_outs, next_sig = inline(sub, sub_ins, next_sig)
                gates.extend(sub_gates)
                for j, so in enumerate(sub_outs):
                    local[e.first_out + j] = so
                    produced.append(so)
        return gates, produced[-comp.n_out:], next_sig

    gates, outs, total = inline(c, [2 + i for i in range(c.n_in)], 2 + c.n_in)
    return FlatNet(c.n_in, c.n_out, total, gates, outs)


def eval_flat(net: FlatNet, inputs: list[int]) -> tuple[int, ...]:
    vals = [0, 1] + list(inputs)
    for a, b in net.gates:
        vals.append(1 - (vals[a] & vals[b]))
    return tuple(vals[s] for s in net.output_signals)


def exhaustive_table(c: Circuit, max_inputs: int = 1 << 16) -> list[dict]:
    """Exact truth table by full enumeration (only used when 2**nIn is small)."""
    if c.n_in > 24:
        raise ValueError("exhaustive enumeration refused for nIn > 24")
    if c.n_state:
        raise ValueError("exhaustive_table supports stateless circuits only")
    net = flatten(c)
    rows = []
    for v in range(1 << c.n_in):
        bits = [(v >> i) & 1 for i in range(c.n_in)]
        r = eval_flat(net, bits)
        a = eval_recursive(c, bits)
        if r != a:
            raise AssertionError("evaluator disagreement at %s: %s vs %s" % (bits, r, a))
        rows.append({"in": bits, "in_packed": v, "out": list(r)})
    return rows


# --------------------------------------------------------------------------
# Tseitin miter + DPLL: exact pairwise stateless comparison on small circuits
# --------------------------------------------------------------------------
class CNF:
    def __init__(self):
        self.clauses: list[list[int]] = []
        self.nvars = 0

    def fresh(self) -> int:
        self.nvars += 1
        return self.nvars

    def add(self, *lits: int) -> None:
        self.clauses.append(list(lits))


def _encode_flat(cnf: CNF, net: FlatNet, input_lits: list[int], t: int | None = None) -> list[int]:
    if t is None:
        t = cnf.fresh()
        cnf.add(t)  # constant true
    sig = [0] * net.n_signals
    sig[0], sig[1] = -t, t
    for i, lit in enumerate(input_lits):
        sig[2 + i] = lit
    for idx, (a, b) in enumerate(net.gates):
        g = cnf.fresh()
        cnf.add(g, sig[a])
        cnf.add(g, sig[b])
        cnf.add(-g, -sig[a], -sig[b])
        sig[2 + net.n_in + idx] = g
    return [sig[s] for s in net.output_signals]


def cnf_miter(ref_c: Circuit, cand_c: Circuit):
    """Build a miter CNF. Returns (cnf, input_vars) or None if widths mismatch."""
    if ref_c.n_in != cand_c.n_in or ref_c.n_out != cand_c.n_out:
        return None
    if ref_c.n_state or cand_c.n_state:
        raise ValueError("miter supports stateless circuits only")
    cnf = CNF()
    t = cnf.fresh()
    cnf.add(t)  # single shared constant-true variable
    in_lits = [cnf.fresh() for _ in range(ref_c.n_in)]
    r_outs = _encode_flat(cnf, flatten(ref_c), in_lits, t)
    # Re-encode the candidate into the SAME CNF over the SAME input literals so
    # both circuits are compared under one shared input assignment.
    c_outs = _encode_flat(cnf, flatten(cand_c), in_lits, t)
    diffs = []
    for ro, co in zip(r_outs, c_outs):
        d = cnf.fresh()
        cnf.add(-d, ro, co)
        cnf.add(-d, -ro, -co)
        diffs.append(d)
    diff = cnf.fresh()
    cnf.add(-diff, *diffs)
    cnf.add(diff)
    return cnf, in_lits


def solve(cnf: CNF, max_decisions: int | None = None):
    """DPLL with unit propagation. Returns dict(result, decisions, model, timed_out)."""
    clauses = [list(c) for c in cnf.clauses]
    assign: dict[int, bool] = {}
    decisions = 0

    def simplify(cls, lit):
        out = []
        for c in cls:
            if lit in c:
                continue
            if -lit in c:
                nc = [x for x in c if x != -lit]
                if not nc:
                    return None
                out.append(nc)
            else:
                out.append(c)
        return out

    def propagate(cls):
        changed = True
        while changed:
            changed = False
            for c in cls:
                if len(c) == 1:
                    u = c[0]
                    if u in assign:
                        continue
                    assign[u] = True
                    assign[-u] = False
                    nxt = simplify(cls, u)
                    if nxt is None:
                        return None
                    cls = nxt
                    changed = True
                    break
        return cls

    def search(cls):
        nonlocal decisions
        cls = propagate(cls)
        if cls is None:
            return False
        if not cls:
            return True
        lit = cls[0][0]
        for val in (True, False):
            if max_decisions is not None and decisions >= max_decisions:
                return None  # budget exhausted -> UNKNOWN
            decisions += 1
            a2 = dict(assign)
            a2[lit] = val
            a2[-lit] = not val
            chosen = lit if val else -lit
            nxt = simplify(cls, chosen)
            if nxt is None:
                continue
            saved = dict(assign)
            assign.clear(); assign.update(a2)
            ok = search(nxt)
            if ok is True:
                return True
            if ok is None:
                return None
            assign.clear(); assign.update(saved)
        return False

    ok = search(clauses)
    if ok is None:
        return {"result": "UNKNOWN", "decisions": decisions, "model": None, "timed_out": True}
    if ok:
        return {"result": "SAT", "decisions": decisions, "model": dict(assign), "timed_out": False}
    return {"result": "UNSAT", "decisions": decisions, "model": None, "timed_out": False}


def compare_stateless(ref_c: Circuit, cand_c: Circuit, max_decisions: int | None = None):
    """Decide EQUIVALENT / DIFFERENT / UNKNOWN for a stateless pair.

    Every SAT witness is replayed by BOTH independent evaluators before it is
    accepted; a witness that does not reproduce is reported as UNKNOWN. No
    wall-clock timing is returned here: authored fixtures must be byte-stable.
    """
    miter = cnf_miter(ref_c, cand_c)
    if miter is None:
        return {"verdict": "INVALID_INPUT", "reason": "width mismatch"}
    cnf, in_lits = miter
    res = solve(cnf, max_decisions)
    out = {
        "verdict": {"UNSAT": "EQUIVALENT", "SAT": "DIFFERENT", "UNKNOWN": "UNKNOWN"}[res["result"]],
        "solver_result": res["result"],
        "decisions": res["decisions"],
        "timed_out": res["timed_out"],
        "clauses": len(cnf.clauses),
        "variables": cnf.nvars,
    }
    if res["result"] == "SAT":
        bits = [1 if res["model"].get(v, False) else 0 for v in in_lits]
        ro = eval_recursive(ref_c, bits)
        co = eval_recursive(cand_c, bits)
        rf = eval_flat(flatten(ref_c), bits)
        cf = eval_flat(flatten(cand_c), bits)
        replay_ok = (ro != co) and (ro == rf) and (co == cf)
        out.update({
            "witness": bits, "reference_out": list(ro), "candidate_out": list(co),
            "flat_reference_out": list(rf), "flat_candidate_out": list(cf),
            "witness_replayed": replay_ok,
        })
        if not replay_ok:
            out["verdict"] = "UNKNOWN"
            out["reason"] = "SAT witness failed independent replay"
    return out


def minimize_witness(ref_c: Circuit, cand_c: Circuit, bits: list[int]) -> list[int]:
    """Greedy bit clearing; a *small* witness, not a proven minimal one."""
    cur = list(bits)
    for i in range(len(cur)):
        if cur[i] == 1:
            trial = list(cur)
            trial[i] = 0
            if eval_recursive(ref_c, trial) != eval_recursive(cand_c, trial):
                cur = trial
    return cur


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj) -> str:
    import json
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8"))
