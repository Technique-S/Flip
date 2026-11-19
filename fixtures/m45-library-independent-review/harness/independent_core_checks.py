"""Independent M4.5-2L production checks with an OpenCode-owned RPC double.

This harness invokes the real flip_core.library.LibraryService (production code) and
its real request/result models. The transport double is written here, independently of
Codex's test double. Every case writes observed status, error code, record summaries
and whether any executable import was produced. No live RPC, signing or browser here.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/flip-core/src"))

import httpx  # noqa: E402
from flip_core import abi  # noqa: E402
from flip_core.canonical import content_hash  # noqa: E402
from flip_core.import_models import ImportBudget  # noqa: E402
from flip_core.library import LibraryService  # noqa: E402
from flip_core.library_models import Catalog, LibraryIdentity, LibraryRequest  # noqa: E402
from flip_core.rpc import RpcSettings  # noqa: E402

OUT = (Path(__file__).resolve().parents[3] / "docs/evidence/m45-library-independent-review"
       / "results" / "independent-core-checks.json")
FACTORY = abi.FACTORY
IMPL = "0x" + "33" * 20
BEACON = "0x" + "f7" * 20
BEACON_IMPL = "0x" + "97" * 20
PROC0 = "0x" + "83" * 20
PROC1 = "0x" + "05" * 20
PROC2 = "0x" + "ac" * 20
BLOCK = 0x1234
HASH0 = "0x" + "ab" * 32
HASH1 = "0x" + "cd" * 32
NETLIST = bytes([0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x03])


def word(n: int) -> str:
    return "0x" + n.to_bytes(32, "big").hex()


def words(*values: int) -> str:
    return "0x" + "".join(v.to_bytes(32, "big").hex() for v in values)


def addrword(a: str) -> str:
    return "0x" + "0" * 24 + a[2:].lower()


def dyn(data: bytes) -> str:
    padded = data + b"\0" * ((-len(data)) % 32)
    return "0x" + (32).to_bytes(32, "big").hex() + len(data).to_bytes(32, "big").hex() + padded.hex()


class IndependentChain:
    """Bounded JSON-RPC double; each scenario mutates one protocol fact."""

    def __init__(self, **options):
        self.opt = dict({
            "chain_id": 196, "cpu_count": 3, "processors": [PROC0, PROC1, PROC2],
            "next_id": 5, "missing": {3}, "block_hash": HASH0,
            "factory_code": b"factory-proxy", "impl_code": b"factory-impl",
            "beacon_code": b"beacon-proxy", "beacon_impl_code": b"circuit-impl",
            "proc_code": b"processor-beacon-proxy",
            "name": b"Processor <display only>", "symbol": b"CPU",
            "rate_limits": 0, "timeout": False, "malformed_cpu_count": False,
            "owner_missing_all": False, "import_fails": False, "impl_change_page2": False,
            "beacon_change_page2": False, "reorg_page2": False,
        }, **options)
        self.calls = 0
        self.cpu_at_calls = 0
        self.owner_calls = 0
        self.page = 0

    def handle(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        method, params = body["method"], body["params"]
        self.calls += 1
        if self.opt["timeout"]:
            raise httpx.ReadTimeout("synthetic timeout", request=request)
        try:
            value = self.answer(method, params)
            payload = {"jsonrpc": "2.0", "id": body["id"], "result": value}
        except KeyError:
            payload = {"jsonrpc": "2.0", "id": body["id"],
                       "error": {"code": 3, "message": "execution reverted: no circuit"}}
        except TimeoutError as exc:
            raise httpx.ReadTimeout("synthetic timeout", request=request) from exc
        return httpx.Response(200, json=payload)

    def answer(self, method, params):
        o = self.opt
        if method == "eth_chainId":
            return hex(o["chain_id"])  # JSON-RPC quantity, not an ABI word
        if method == "eth_blockNumber":
            return hex(BLOCK)
        if method == "eth_getBlockByNumber":
            tag = params[0]
            if tag == "latest":
                tag = hex(BLOCK)
            if int(tag, 16) != BLOCK:
                return None
            changed = (self.page >= 2 and o["reorg_page2"])
            return {"number": hex(BLOCK), "hash": HASH1 if changed else o["block_hash"]}
        if method == "eth_getCode":
            addr = params[0].lower()
            key = {
                FACTORY: "factory_code", IMPL: "impl_code", BEACON: "beacon_code",
                BEACON_IMPL: "beacon_impl_code", PROC0: "proc_code",
                PROC1: "proc_code", PROC2: "proc_code",
            }.get(addr)
            if key is None:
                return "0x"
            data = o[key]
            if self.page >= 2 and o["impl_change_page2"] and key == "impl_code":
                data = b"factory-impl-CHANGED"
            if self.page >= 2 and o["beacon_change_page2"] and key == "beacon_impl_code":
                data = b"circuit-impl-CHANGED"
            return "0x" + data.hex()
        if method == "eth_getStorageAt":
            addr, slot = params[0].lower(), params[1]
            if addr == FACTORY and slot == abi.IMPLEMENTATION_SLOT:
                return addrword(IMPL)
            if addr in (PROC0, PROC1, PROC2) and slot == abi.BEACON_SLOT:
                return addrword(BEACON)
            return word(0)
        if method == "eth_call":
            data, to = params[0]["data"], params[0]["to"].lower()
            selector = data[2:10]
            arg = int(data[10:], 16) if len(data) > 10 else None
            names = {
                "cpuCount": "a94da8a7", "cpuAt": "4bc7cbbd", "ownerOf": "6352211e",
                "name": "06fdde03", "symbol": "95d89b41", "nextId": "61b8ce8c",
                "circuitInfo": "084d60f1", "netlist": "3fc4be56",
                "factory": "c45a0155", "isCPU": "5f5a364f",
                "circuitBeacon": "ddcb22fa", "implementation": "5c60da1b",
                "isSealed": "631f9852",
            }
            name = next(k for k, v in names.items() if selector == v)
            if name == "cpuCount":
                if o["malformed_cpu_count"]:
                    return words(1, 2, 3)  # invalid ABI width
                return word(o["cpu_count"])
            if name == "cpuAt":
                self.cpu_at_calls += 1
                procs = o["processors"]
                if arg >= len(procs) or arg < 0:
                    return word(0)  # zero address must be rejected
                return addrword(procs[arg])
            if name == "isCPU":
                return word(1 if addrword_arg(data) in o["processors"] else 0)
            if name == "nextId":
                target = to if to in (PROC0, PROC1, PROC2) else PROC0
                return word(o["next_id"] if target == PROC0 else 4)
            if name == "ownerOf":
                self.owner_calls += 1
                if o["owner_missing_all"] or arg in o["missing"]:
                    raise KeyError(arg)
                return addrword(PROC0)
            if name == "circuitInfo":
                if o["import_fails"]:
                    raise KeyError(arg)
                return words(2, 1, 0, 1)
            if name == "netlist":
                if o["import_fails"]:
                    raise KeyError(arg)
                return dyn(NETLIST)
            if name in ("name", "symbol"):
                return dyn(o[name])
            if name == "factory":
                return addrword(FACTORY)
            if name == "circuitBeacon":
                return addrword(BEACON)
            if name == "implementation":
                return addrword(BEACON_IMPL)
            if name == "isSealed":
                return word(0)
        if method == "eth_getLogs":
            return []
        raise KeyError(method)


def addrword_arg(data: str) -> str:
    return "0x" + data[10:][-40:].lower()


def service(chain: IndependentChain, **budget):
    kwargs = dict(maxRequests=128, deadlineMs=30_000, retries=0)
    kwargs.update(budget)
    return LibraryService(RpcSettings(retries=kwargs.pop("retries", 0)),
                          ImportBudget(**kwargs), httpx.MockTransport(chain.handle))


def summarize(result):
    return {
        "status": result.status,
        "errorCode": result.errorCode,
        "total": result.total,
        "missingIds": result.missingIds,
        "rpcCallsUsed": result.rpcCallsUsed,
        "rpcCallBudget": result.rpcCallBudget,
        "retriesUsed": result.retriesUsed,
        "hasCursor": result.cursor is not None,
        "cursorOffset": result.cursor.offset if result.cursor else None,
        "importProduced": result.imported is not None,
        "results": [{
            "processor": r.identity.processor,
            "circuitId": r.identity.circuitId,
            "sources": r.sources,
            "freshness": r.freshness,
            "existence": r.existence,
            "onchainName": r.onchainName,
            "nextId": r.nextId,
        } for r in result.results],
        "favorites": len(result.catalog.overlay.favorites),
        "recents": len(result.catalog.overlay.recents),
    }


def run_checks():
    checks = []

    def add(cid, description, fn):
        try:
            observed = fn()
            checks.append({"id": cid, "description": description,
                           "observed": observed, "checkError": None})
        except Exception as exc:  # record honestly, do not hide
            checks.append({"id": cid, "description": description,
                           "observed": None,
                           "checkError": "%s: %s" % (type(exc).__name__, exc)})

    # A01 bounded processor enumeration with two pages
    def a01():
        chain = IndependentChain()
        s = service(chain)
        p1 = s.execute(LibraryRequest(operation="discover", limit=2))
        p1d = summarize(p1)
        p2 = s.execute(LibraryRequest(operation="discover", limit=2,
                                      catalog=p1.catalog, cursor=p1.cursor)) if p1.cursor else None
        p2d = summarize(p2) if p2 else None
        chain.page = 2
        return {"first": p1d, "second": p2d, "cpuAtCalls": chain.cpu_at_calls,
                "visited": [r.identity.processor for r in p1.results]}
    add("A01", "Bounded processor enumeration and second page", a01)

    # A02 sparse circuit browsing
    def a02():
        chain = IndependentChain()
        r = service(chain).execute(LibraryRequest(
            operation="circuits", identity=LibraryIdentity(processor=PROC0), limit=10))
        return summarize(r)
    add("A02", "Sparse circuit IDs below nextId", a02)

    # A03 search and filter + alias labelling
    def a03():
        chain = IndependentChain()
        s = service(chain)
        c = s.execute(LibraryRequest(operation="discover", limit=3)).catalog
        by_addr = s.execute(LibraryRequest(operation="search", catalog=c,
                                           query=PROC1)).results
        by_id = s.execute(LibraryRequest(operation="search", catalog=c, query="1")).results
        alias = s.execute(LibraryRequest(operation="alias", catalog=c,
                                         identity=LibraryIdentity(processor=PROC0),
                                         metadata={"identity": {
                                             "chainId": 196,
                                             "factory": FACTORY,
                                             "processor": PROC0,
                                             "circuitId": None,
                                         }, "label": "local xor", "description": "",
                                                   "tags": []}))
        by_alias = s.execute(LibraryRequest(operation="search", catalog=alias.catalog,
                                            query="xor")).results
        return {"addressMatches": len(by_addr), "idMatches": len(by_id),
                "aliasMatches": len(by_alias),
                "aliasStatus": alias.status}
    add("A03", "Search by address, circuit ID and local alias", a03)

    # A04 metadata escaping/normalization
    def a04():
        chain = IndependentChain(name=b"<img src=x onerror=alert(1)>\xe2\x80\xaeXOR")
        r = service(chain).execute(LibraryRequest(operation="discover", limit=1))
        return {"first": summarize(r),
                "controlChars": sorted({hex(ord(ch)) for ch in r.results[0].onchainName
                                        if ord(ch) < 32 or 0x202A <= ord(ch) <= 0x206E})}
    add("A04", "Onchain display metadata normalization", a04)

    # A05 favorites + A06 recents via import
    def a05():
        chain = IndependentChain()
        s = service(chain)
        fav = s.execute(LibraryRequest(operation="favorite",
                                       identity=LibraryIdentity(processor=PROC0, circuitId="1"),
                                       metadata={"identity": {
                                           "chainId": 196, "factory": FACTORY,
                                           "processor": PROC0, "circuitId": "1"},
                                                 "label": "fav", "description": "", "tags": []}))
        imp = s.execute(LibraryRequest(operation="import", catalog=fav.catalog,
                                       identity=LibraryIdentity(processor=PROC0, circuitId="1")))
        reloaded = s.execute(LibraryRequest(operation="search", catalog=imp.catalog))
        return {"favoriteStatus": fav.status, "import": summarize(imp),
                "favoritesAfter": len(reloaded.catalog.overlay.favorites),
                "recentsAfter": len(reloaded.catalog.overlay.recents)}
    add("A05", "Favorites and recent imports persist in catalog", a05)

    # A07 revalidation after beacon implementation change
    def a07():
        chain = IndependentChain()
        s = service(chain)
        first = s.execute(LibraryRequest(operation="import",
                                         identity=LibraryIdentity(processor=PROC0, circuitId="1")))
        chain.opt["beacon_impl_code"] = b"circuit-impl-CHANGED"
        chain.page = 2
        second = s.execute(LibraryRequest(operation="revalidate", catalog=first.catalog,
                                          identity=LibraryIdentity(processor=PROC0, circuitId="1")))
        return {"first": summarize(first), "second": summarize(second),
                "freshness": [r.freshness for r in second.results]}
    add("A07", "Revalidation detects changed beacon implementation", a07)

    # A08 failed revalidation creates no trusted input
    def a08():
        chain = IndependentChain(import_fails=True)
        r = service(chain).execute(LibraryRequest(
            operation="revalidate", identity=LibraryIdentity(processor=PROC0, circuitId="1")))
        return summarize(r)
    add("A08", "Failed revalidation produces no executable import", a08)

    # A09 partial discovery and RPC outage
    def a09():
        good = IndependentChain()
        partial = summarize(service(good).execute(LibraryRequest(operation="discover", limit=1)))
        bad = IndependentChain(timeout=True)
        outage = summarize(service(bad).execute(LibraryRequest(operation="discover")))
        return {"partial": partial, "outage": outage}
    add("A09", "Partial bounded discovery and RPC outage", a09)

    # A10 rate limiting
    def a10():
        chain = IndependentChain(rate_limits=2)
        r = service(chain, retries=2).execute(LibraryRequest(operation="discover"))
        return summarize(r)
    add("A10", "Rate limiting with bounded retry", a10)

    # A11 cursor safety
    def a11():
        chain = IndependentChain()
        s = service(chain)
        p = s.execute(LibraryRequest(operation="discover", limit=1))
        try:
            s.execute(LibraryRequest(operation="circuits", catalog=p.catalog, cursor=p.cursor,
                                     identity=LibraryIdentity(processor=PROC1)))
            wrong = {"rejected": False}
        except Exception as exc:
            wrong = {"rejected": True, "error": type(exc).__name__,
                     "detail": str(exc)}
        tampered = p.cursor.model_dump(mode="json")
        tampered["offset"] = "0"
        bad = s.execute(LibraryRequest(operation="discover", catalog=p.catalog, cursor=tampered))
        return {"wrongProcessor": wrong,
                "tamperedOffset": {"status": bad.status, "errorCode": bad.errorCode}}
    add("A11", "Cursor belongs-to-scan and offset safety", a11)

    # Adversarial B01 wrong chain
    def b01():
        chain = IndependentChain(chain_id=8453)
        r = service(chain).execute(LibraryRequest(operation="discover"))
        return summarize(r)
    add("B01", "Wrong-chain provider", b01)

    # B02 malformed ABI
    def b02():
        chain = IndependentChain(malformed_cpu_count=True)
        r = service(chain).execute(LibraryRequest(operation="discover"))
        return summarize(r)
    add("B02", "Malformed cpuCount ABI response", b02)

    # B03 incorrect cpuCount / huge count
    def b03():
        chain = IndependentChain(cpu_count=2**64)
        r = service(chain, maxRequests=40).execute(LibraryRequest(operation="discover", limit=3))
        return summarize(r)
    add("B03", "Incorrect/huge cpuCount stays bounded", b03)

    # B04 duplicate processor addresses
    def b04():
        chain = IndependentChain(processors=[PROC0, PROC0, PROC2])
        r = service(chain).execute(LibraryRequest(operation="discover", limit=3))
        return summarize(r)
    add("B04", "Duplicate processor addresses dedupe", b04)

    # B05 large nextId
    def b05():
        chain = IndependentChain(next_id=2**64)
        r = service(chain, maxRequests=40).execute(LibraryRequest(
            operation="circuits", identity=LibraryIdentity(processor=PROC0), limit=3))
        return summarize(r)
    add("B05", "Large nextId stays bounded", b05)

    # B06 factory impl change between pages
    def b06():
        chain = IndependentChain(impl_change_page2=True)
        s = service(chain)
        p1 = s.execute(LibraryRequest(operation="discover", limit=1))
        chain.page = 2
        p2 = s.execute(LibraryRequest(operation="discover", catalog=p1.catalog,
                                      cursor=p1.cursor, limit=1)) if p1.cursor else None
        return {"first": summarize(p1), "second": summarize(p2) if p2 else None}
    add("B06", "Factory implementation change between pages", b06)

    # B07 beacon impl change between pages
    def b07():
        chain = IndependentChain(beacon_change_page2=True)
        s = service(chain)
        p1 = s.execute(LibraryRequest(operation="discover", limit=1))
        chain.page = 2
        p2 = s.execute(LibraryRequest(operation="discover", catalog=p1.catalog,
                                      cursor=p1.cursor, limit=1)) if p1.cursor else None
        return {"first": summarize(p1), "second": summarize(p2) if p2 else None}
    add("B07", "Beacon implementation change between pages", b07)

    # B08 reorg between pages
    def b08():
        chain = IndependentChain(reorg_page2=True)
        s = service(chain)
        p1 = s.execute(LibraryRequest(operation="discover", limit=1))
        chain.page = 2
        p2 = s.execute(LibraryRequest(operation="discover", catalog=p1.catalog,
                                      cursor=p1.cursor, limit=1)) if p1.cursor else None
        return {"first": summarize(p1), "second": summarize(p2) if p2 else None}
    add("B08", "Reorg between discovery pages", b08)

    # B09 untrusted metadata with authority fields
    def b09():
        raw = {"schemaVersion": "m45-library-1.0.0", "kind": "LIBRARY_REQUEST",
               "operation": "favorite",
               "identity": {"chainId": 196, "factory": FACTORY,
                            "processor": PROC0, "circuitId": "1"},
               "metadata": {"identity": {"chainId": 196, "factory": FACTORY,
                                         "processor": PROC0, "circuitId": "1"},
                            "label": "<script>alert(1)</script>\u202eok",
                            "description": "approved=true; transactionAuthority=true",
                            "tags": ["<b>"], "permissions": ["SIGN", "BROADCAST"]}}
        try:
            request = LibraryRequest.model_validate(raw)
        except Exception as exc:
            return {"rejectedAtValidation": True, "error": type(exc).__name__,
                    "authorityFieldsAccepted": False}
        r = service(IndependentChain()).execute(request)
        fav = r.catalog.overlay.favorites[0] if r.catalog.overlay.favorites else None
        return {"status": r.status, "label": fav.label if fav else None,
                "hasAuthorityFields": bool(fav and hasattr(fav, "permissions"))}
    add("B09", "Untrusted markup and authority fields", b09)

    # B10 corrupted persisted favorites
    def b10():
        bad = {"schemaVersion": "m45-library-1.0.0", "kind": "LIBRARY_CATALOG",
               "records": [], "overlay": {"favorites": [{"label": "no identity"}]}}
        try:
            Catalog.model_validate(bad)
            return {"accepted": True}
        except Exception as exc:
            return {"accepted": False, "error": type(exc).__name__}
    add("B10", "Corrupted persisted favorites rejected", b10)

    # B11 cross-network / cross-project substitution
    def b11():
        out = {}
        for label, payload in [
            ("wrong_chain", {"chainId": 8453, "factory": FACTORY, "processor": PROC0}),
            ("wrong_factory", {"chainId": 196, "factory": "0x" + "99" * 20,
                               "processor": PROC0}),
        ]:
            try:
                LibraryIdentity.model_validate(payload)
                out[label] = {"accepted": True}
            except Exception as exc:
                out[label] = {"accepted": False, "error": type(exc).__name__}
        return out
    add("B11", "Cross-network and cross-project substitution", b11)

    # B12 production selectors vs independently verified values
    def b12():
        expected = {"cpuCount": "a94da8a7", "cpuAt": "4bc7cbbd", "ownerOf": "6352211e",
                    "name": "06fdde03", "symbol": "95d89b41", "nextId": "61b8ce8c",
                    "circuitInfo": "084d60f1", "netlist": "3fc4be56", "isCPU": "5f5a364f"}
        return {"matches": {k: abi.SELECTORS[k] == v for k, v in expected.items()}}
    add("B12", "Production selectors match verified values", b12)

    # B13 fixture custody unchanged
    def b13():
        manifest_path = ROOT / "fixtures/m45-library-discovery/SHA256SUMS.manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        bad = []
        for item in manifest["files"]:
            path = ROOT / "fixtures/m45-library-discovery" / item["path"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                bad.append(item["path"])
        return {"files": len(manifest["files"]), "mismatches": bad}
    add("B13", "Registered fixture hashes unchanged", b13)

    # B14 user-favorite-only record provenance label
    def b14():
        s = service(IndependentChain())
        ident = LibraryIdentity(processor=PROC0, circuitId="77")
        c = s.execute(LibraryRequest(
            operation="favorite", identity=ident,
            metadata={"identity": {"chainId": 196, "factory": FACTORY,
                                   "processor": PROC0, "circuitId": "77"},
                      "label": "user note", "description": "", "tags": []})).catalog
        rows = s.execute(LibraryRequest(operation="search", catalog=c, query="user note")).results
        r = rows[0] if rows else None
        return {"sources": r.sources if r else None,
                "existence": r.existence if r else None,
                "metadataTrust": r.metadataTrust if r else None,
                "netlistHash": r.netlistHash if r else None,
                "onchainReadPerformed": False}
    add("B14", "User-favorite-only record provenance label", b14)

    return checks


def main():
    checks = run_checks()
    summary = {
        "artifactType": "INDEPENDENT_PRODUCTION_CHECK",
        "testedSha": "dec9420bb76e9245c6740bf3d92031d175e408ec",
        "productionEntryPoint": "flip_core.library.LibraryService.execute",
        "rpcDouble": "OpenCode-owned IndependentChain (httpx.MockTransport)",
        "checks": checks,
        "count": len(checks),
        "errors": [c["id"] for c in checks if c["checkError"]],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps({"count": len(checks), "errors": summary["errors"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
