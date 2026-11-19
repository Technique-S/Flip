# Circuit Library tracked follow-ups

## F03-PERF-001 — archival regeneration runtime margin

Owner: Flip lead engineering. Source: OpenCode F-03, review commit
`9741e66ae385979dc0d18c89aec4ec6ed93ff285`, target `dec9420`.

The unchanged inherited test has a 120-second subprocess limit. Earlier full and
focused custom-layout executions timed out; the prescribed layout subsequently
passed. Reconciliation runs both layouts serially using
`python scripts/probe_m45_regeneration.py --out probe.json`. The probe records
interpreter/platform, child-process startup, fixture-copy and hash-scan timing,
exact command/output, elapsed test time and archival source hashes. It neither
changes the inner timeout nor rewrites the original generator or fixtures.

Follow-up: collect timing and host-load samples if the unchanged test again exceeds
120 seconds on a supported runner. Profile the independent archival generator in
scratch, and isolate its generation/verification costs before proposing a change.
Any future optimization must preserve byte-identical regeneration and the existing
custody assertions. Increasing the timeout or skipping the check is not an accepted
fix. A repeat failure in supported platform CI reopens the acceptance gate.

Both layouts passed during this reconciliation. These two runs do not establish a
unique cause for the earlier timeouts or demonstrate that the directory name itself
caused them. Process startup, fixture copying and hashing were subsecond in both
probes; execution inside the inherited test dominated. Archival source bytes are
unchanged and the independent stdlib generator does not import the library code.
No production-library regression was reproduced. Runtime margin/host variability
remains a tracked limitation rather than a claimed performance fix.
