# M3-A solver: containment, distribution and measured limits

Policy: 2,500 gates per design by default, explicit raise to at most 5,000;
maximum REF nesting 64; worker deadline at most 5,000 ms; memory selection at most
64 MiB. These are admission limits, not promises that every admitted SAT problem
finishes. A timeout, crash, unsupported platform or failed containment is UNKNOWN.

## Process isolation

The parent encodes bounded CNF and launches a fresh base CPython interpreter with
`-I` and a fixed private worker file. It passes the trusted environment's installed
package path, not a job-controlled module path. Using the base executable avoids
the Windows venv redirector spawning an extra process. No arbitrary source, shell
command, solver option or probe mode is accepted from a user request.

The fixed worker imports stdlib only before containment and its stdin handshake.
The parent installs Windows Job limits **before sending CNF**. Linux installs
limits before reading CNF or loading PySAT. The native solver and Python objects
share the worker budget. Parent encoding is bounded structurally, not inside that
OS memory allowance: 150,000 variables, 300,000 clauses, 8 MiB worker payload,
250,000 expanded execution/signal work units, and M2 byte/record/closure limits.

| Platform | Implemented mechanism | Meaning and measured probe |
| --- | --- | --- |
| Windows x64 | Job object process-memory cap, active-process limit 1, kill-on-job-close | 64 MiB private commit; 128 MiB allocation raises MemoryError; timeout child killed and reaped |
| Linux | `RLIMIT_AS`, CPU limit, dedicated session/process group, parent-death SIGKILL | 64 MiB virtual address space; allocation/timeout/crash probes run in Linux CI |

The parent enforces elapsed time across spawn, native import, SAT and up to 64
greedy witness-reduction queries. On expiry it kills the child/process group and
waits for it. Worker crashes are reaped; the next job uses a new process. Linux
sets parent-death SIGKILL with a parent-PID race check; Windows closes the Job on
parent exit. The worker never dispatches other work. Cleanup can add scheduler
latency after the deadline; this is not a real-time OS guarantee. It does not
depend on Python/native code cooperating with a cancellation flag.

No portable implementation claims a 64 MiB **RSS** ceiling. Windows private commit
does not count all shared/file-backed pages; Linux virtual address space includes
mapped libraries. No cgroup/container-wide limit or Windows whole-service working
set cap was established. Parent allocations, HTTP concurrency and all service
workers are outside the child cap. Linux is not an arbitrary-code sandbox with
seccomp or a verified aggregate fork-tree memory limit. Failure to assign limits
returns UNKNOWN, never an uncontained retry.

**Public solver deployment remains blocked** pending target-host aggregate memory,
authentication, concurrency/rate controls and process-tree stress validation.
The loopback-only API opt-in is for trusted local use and must not be reverse
proxied publicly. Other OSes fail closed; there is no fallback DPLL or unbounded
native execution.

## Packaging and licensing decision

The runtime pins `python-sat==1.9.dev23` and `six==1.17.0` in `uv.lock`, with
distribution hashes. CPython 3.14 Windows and Linux wheels exist; clean CI tests
installation on both systems. Only Minisat22 is selected, without optional solver
extras. The Python wrapper version and exact native extension SHA-256 are bound
into each comparison's engine identity, along with semantic execution source
hashes. Platform binaries have different hashes by design.

[PySAT's upstream license](https://github.com/pysathq/pysat/blob/master/LICENSE.txt)
is MIT. [MiniSat's upstream license](https://github.com/niklasso/minisat/blob/master/LICENSE)
is permissive MIT-style, requiring copyright/permission notices when redistributed.
The installed PySAT distribution identifies LICENSE.txt; its wrapper metadata and
the primary license sources were inspected on 2026-11-18. `six` is MIT.

Decision: depend on hash-pinned upstream distributions; do not vendor or commit
solver binaries. Preserve upstream notices when distributing installed software.
This milestone does not ship an all-in-one binary or relicense PySAT. Before
bundling a wheel/native executable for standalone redistribution, audit and retain
notices for **all** native solvers in that wheel; selecting Minisat22 at runtime
does not remove other linked components or their license obligations.

TAP-02 semantics are pinned to revision
`527477ecb7cf68ee9e86d8292669d57fe1680572`:
[specification (CC0)](https://github.com/TapeOutProtocol/TAPs/blob/527477ecb7cf68ee9e86d8292669d57fe1680572/TAPs/TAP-02.md),
[reference (MIT)](https://github.com/TapeOutProtocol/TAPs/blob/527477ecb7cf68ee9e86d8292669d57fe1680572/assets/tap-02/reference.py),
[vectors](https://github.com/TapeOutProtocol/TAPs/blob/527477ecb7cf68ee9e86d8292669d57fe1680572/assets/tap-02/vectors.json).
No additional upstream source or raw audit file was vendored. The existing
immutable vector digest remains bound by v1 Semantics. Local replay is a separate
implementation from the SAT encoder and never relies on source alias labels.

## Measurements

`M3_A_BENCHMARK_WINDOWS.json` contains 28 fresh results from the original seven
XOR-chain scales and four modes. Synthetic transport emulates registered source
lookup; circuit #1 bytes are the archived real XOR, not newly observed data.
All 28 verdicts matched; each DIFFERENT completed independent replay.

Windows 5,000-gate self-comparison: 11,254 variables, 30,007 clauses,
1,395 ms worker wall time, 1,810 ms total validation/encoding/check time,
30,842,880 bytes peak private commit (29.41 MiB). Across all 28 cases:
maximum worker wall 1,395 ms, total 1,810 ms, private commit 30,842,880 bytes.
The miter includes complete four-clause XOR Tseitin definitions; its clause counts
are not required to equal the historical experimental encoder's counts.

These observations cover a parity-chain family on this host, not adversarial SAT
complexity or production latency SLOs. CI also runs every scale under real Linux
and Windows containment, and exports its fresh benchmark JSON as workflow
artifacts. Unit tests actually sleep past a shortened deadline, crash a worker,
deny an oversized allocation, run a subsequent solver, and reject replay failures.
