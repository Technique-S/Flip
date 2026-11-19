"""One bounded native solver per OS process, fail closed on containment failure."""

import json
import os
import signal
import subprocess
import sys
import sysconfig
from pathlib import Path
from time import monotonic

from flip_core.canonical import canonical_bytes
from flip_core.contracts import ContractError


class WindowsJob:
    def __init__(self, process, memory_mib, *, max_processes=1):
        import ctypes
        from ctypes import wintypes

        class Basic(ctypes.Structure):
            _fields_ = [
                ("processTime", ctypes.c_int64),
                ("jobTime", ctypes.c_int64),
                ("flags", wintypes.DWORD),
                ("minWs", ctypes.c_size_t),
                ("maxWs", ctypes.c_size_t),
                ("active", wintypes.DWORD),
                ("affinity", ctypes.c_size_t),
                ("priority", wintypes.DWORD),
                ("scheduling", wintypes.DWORD),
            ]

        class Io(ctypes.Structure):
            _fields_ = [
                (name, ctypes.c_uint64)
                for name in (
                    "readOps",
                    "writeOps",
                    "otherOps",
                    "readBytes",
                    "writeBytes",
                    "otherBytes",
                )
            ]

        class Extended(ctypes.Structure):
            _fields_ = [
                ("basic", Basic),
                ("io", Io),
                ("processMemory", ctypes.c_size_t),
                ("jobMemory", ctypes.c_size_t),
                ("peakProcess", ctypes.c_size_t),
                ("peakJob", ctypes.c_size_t),
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel, self.handle = kernel, kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise OSError("CreateJobObject failed")
        limit = Extended()
        limit.basic.flags = 0x2000 | 0x100 | 0x8  # kill on close, process memory, one process
        limit.basic.active = max_processes
        limit.processMemory = memory_mib * 1024**2
        if not kernel.SetInformationJobObject(
            self.handle, 9, ctypes.byref(limit), ctypes.sizeof(limit)
        ) or not kernel.AssignProcessToJobObject(
            self.handle, wintypes.HANDLE(int(process._handle))
        ):
            self.close()
            raise OSError("Job limit/assignment failed")

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def run_worker(clauses, inputs, limits, *, _probe=None):
    """Deadline includes spawn, native import, SAT and minimization; kill and reap."""
    if not (sys.platform.startswith("linux") or os.name == "nt"):
        return {"outcome": "INTERRUPTED", "reason": "RESOURCE_LIMIT", "wallMs": 0}
    if _probe not in (None, "timeout-probe", "memory-probe", "crash-probe"):
        raise ValueError("invalid internal probe")
    raw = canonical_bytes({"clauses": clauses, "inputs": inputs})
    if len(raw) > 8_388_608:
        raise ContractError("RESOURCE_LIMIT", "Worker input exceeds 8 MiB.")
    start = monotonic()
    process = job = None
    result = {"outcome": "INTERRUPTED", "reason": "INTERNAL_ERROR"}
    try:
        process = subprocess.Popen(
            [
                sys._base_executable,
                "-I",
                str(Path(__file__).with_name("solver_worker.py")),
                str(limits.solverMemoryMiB),
                str(limits.solverTimeoutMs),
                _probe or "solve",
                sysconfig.get_path("platlib"),
                str(os.getpid()),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if os.name == "nt":
            job = WindowsJob(process, limits.solverMemoryMiB)
        remaining = limits.solverTimeoutMs / 1000 - (monotonic() - start)
        if remaining <= 0:
            raise subprocess.TimeoutExpired(process.args, 0)
        stdout, _ = process.communicate(raw, timeout=remaining)
        if process.returncode or len(stdout) > 1_048_576:
            result["reason"] = "RESOURCE_LIMIT" if process.returncode else "INTERNAL_ERROR"
        else:
            value = json.loads(stdout)
            if _probe:
                result = value
            elif (
                isinstance(value, dict)
                and value.get("outcome") in ("SAT", "UNSAT")
                and type(value.get("peakBytes")) is int
                and 0 < value["peakBytes"] <= limits.solverMemoryMiB * 1024**2
                and value.get("peakMetric")
                == ("PRIVATE_COMMIT" if os.name == "nt" else "VIRTUAL_ADDRESS_SPACE")
                and type(value.get("minimizationAttempts")) is int
                and 0 <= value["minimizationAttempts"] <= 64
                and (
                    (value["outcome"] == "UNSAT" and value.get("witness") is None)
                    or (
                        value["outcome"] == "SAT"
                        and isinstance(value.get("witness"), list)
                        and len(value["witness"]) == len(inputs)
                        and all(type(b) is int and b in (0, 1) for b in value["witness"])
                    )
                )
            ):
                result = value
    except subprocess.TimeoutExpired:
        result = {"outcome": "INTERRUPTED", "reason": "SOLVER_TIMEOUT"}
    except (OSError, ValueError, TypeError):
        result = {"outcome": "INTERRUPTED", "reason": "RESOURCE_LIMIT"}
    finally:
        if process is not None:
            if process.poll() is None:
                try:
                    if os.name == "nt":
                        process.kill()
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # exited between poll and kill; still reap below
            process.communicate()
        if job is not None:
            job.close()
    result["wallMs"] = int((monotonic() - start) * 1000)
    result["containment"] = "WINDOWS_JOB_COMMIT" if os.name == "nt" else "LINUX_RLIMIT_AS"
    return result
