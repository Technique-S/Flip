# Stable CLI exits — 1.0.0

JSON fields are authoritative; command completion never implies equivalence.
Help/version exit 0 and print text. Other recognized commands emit one JSON object
on stdout plus a transport newline. Argument/file/contract errors use the error
envelope and exit 3.

| Exit | Meaning | M1 use |
| --- | --- | --- |
| 0 | Contract operation completed, or later satisfactory complete result | validate/canonical/hash; no proof implied |
| 1 | Reproduced behavioral difference | reserved |
| 2 | UNKNOWN / inconclusive | reserved |
| 3 | Invalid arguments/input, unsupported version, wrong chain, unreadable file | implemented |
| 4 | RPC/infrastructure failure | reserved |
| 5 | Internal implementation failure | reserved |
| 6 | NOT_IMPLEMENTED | every reserved product command |
| 7 | Stale environment requiring revalidation | reserved |
| 8 | Structural preflight rejection | reserved |

Later mapping prioritizes failure/UNKNOWN: invalid input ->3, internal bug ->5,
infrastructure ->4, unimplemented ->6, UNKNOWN ->2, otherwise stale ->7,
reproduced difference ->1, structural rejection ->8, conclusive accepted result ->0.
JSON preserves proof/freshness independently. Reserved codes are not workflows.
Interrupted processes retain normal OS signal exits.

API: contract validation 200 (consistency only), invalid input 422, contract body
>1 MiB 413, reserved product operations 501 / `NOT_IMPLEMENTED`. `/healthz` is
liveness only. Future RPC outage 503 and completed comparison 200 remain reserved.
