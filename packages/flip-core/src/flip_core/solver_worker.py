"""Private stdlib-only bootstrap, launched by file path under python -I.

No application imports: interpreter/native solver share the worker memory cap.
Protocol and probe modes are internal, never accepted from API jobs.
"""

import json
import math
import os
import sys
import time


def peak_bytes():
    if os.name == "posix":
        import resource

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
            (name, ctypes.c_size_t)
            for name in (
                "peakWorkingSet",
                "workingSet",
                "peakPaged",
                "paged",
                "peakNonpaged",
                "nonpaged",
                "pagefile",
                "peakPagefile",
                "private",
            )
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(
        kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    ):
        return 0
    return counters.peakPagefile


def main():
    memory, timeout, mode = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    if sys.platform.startswith("linux"):
        import ctypes
        import resource

        # Die with parent, including parent crash. Recheck closes the setup race.
        parent = int(sys.argv[5])
        if ctypes.CDLL(None, use_errno=True).prctl(1, 9, 0, 0, 0) != 0 or os.getppid() != parent:
            raise RuntimeError("Parent lifetime containment unavailable")
        resource.setrlimit(resource.RLIMIT_AS, (memory * 1024**2,) * 2)
        resource.setrlimit(resource.RLIMIT_CPU, (math.ceil(timeout / 1000) + 1,) * 2)
    elif os.name != "nt":
        raise RuntimeError("Unsupported containment platform")
    # On Windows parent assigns a kill-on-close Job before sending any work.
    data = sys.stdin.buffer.read(8_388_609)
    if len(data) > 8_388_608:
        raise ValueError("Worker input cap")
    if mode == "timeout-probe":
        time.sleep(100)
    if mode == "crash-probe":
        os._exit(70)
    if mode == "memory-probe":
        try:
            allocation = bytearray(128 * 1024**2)
            print(json.dumps({"probe": "UNCONTAINED", "bytes": len(allocation)}))
        except MemoryError:
            print(json.dumps({"probe": "MEMORY_BLOCKED", "peakBytes": peak_bytes()}))
        return
    sys.path.insert(0, sys.argv[4])  # trusted parent's environment, never job-supplied
    from pysat.solvers import Minisat22

    cfg = json.loads(data)
    clauses, inputs = cfg["clauses"], cfg["inputs"]
    with Minisat22(bootstrap_with=clauses) as solver:
        satisfiable = solver.solve()
        witness = None
        attempts = 0
        if satisfiable:
            positive = set(v for v in solver.get_model() if v > 0)
            witness = [int(v in positive) for v in inputs]
            # Monotonic, bounded greedy removal; never claim global minimality.
            for index in range(len(inputs)):
                if witness[index] == 0:
                    continue
                if attempts >= 64:
                    break
                attempts += 1
                trial = list(witness)
                trial[index] = 0
                assumptions = [v if bit else -v for v, bit in zip(inputs, trial, strict=True)]
                if solver.solve(assumptions=assumptions):
                    witness = trial
        result = {
            "outcome": "SAT" if satisfiable else "UNSAT",
            "witness": witness,
            "minimizationAttempts": attempts,
            "peakBytes": peak_bytes(),
        }
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
