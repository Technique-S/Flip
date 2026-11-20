# M4.5-1 — Portability acceptance matrix

**Tested SHA:** `bba6f3d301b08c0dcbbfd0b363b99a15179414db`.
**Result:** 12/12 cases executed; independent verifier `PASS`.

| ID | Case | Classification | Observed | Pass |
|---|---|---|---|---|
| P01 | Web export → CLI import | EXECUTED | compose accepted browser-saved execution request; 81-byte netlist `3dbb65a6…3ce` | yes |
| P02 | CLI export → web import | EXECUTED | browser openProject validates via compose; reimport EQUIVALENT | yes |
| P03 | Project edits and re-import | EXECUTED | edited output map composed successfully | yes |
| P04 | Embedded/referenced test vectors | EXECUTED | `vectors` absent from project; separate VectorRequest produced VECTORS_MATCH | yes (gap documented) |
| P05 | Changed processor implementation | PARTIAL_LOCAL_DOUBLE | loopback changed beacon → STALE; composition blocked | yes (synthetic) |
| P06 | Missing dependency closure | EXECUTED | compose rejected (exit 3) before build | yes |
| P07 | Stale evidence | EXECUTED | replay preserved STALE; no promotion to CURRENT | yes |
| P08 | Incorrect schema version | EXECUTED | exit 3 INVALID_INPUT | yes |
| P09 | Cross-project evidence substitution | EXECUTED | verify-bundle against other project rejected | yes |
| P10 | Corrupted hashes | EXECUTED | contentHash mismatch rejected (exit 3) | yes |
| P11 | Incompatible project revision | EXECUTED | toolVersion `99.0.0` rejected (exit 3) | yes |
| P12 | Complete historical offline reproduction | EXECUTED | sample→compose→compare→export→verify-bundle; EQUIVALENT, HISTORICAL, byte-identical | yes |

## Required-field coverage

| Required in portable project | Covered by | Embedded? |
|---|---|---|
| Schema version | P08, P11 | yes |
| Project identity | P09 | yes |
| Processor/circuit identities | P01, P02, P12 | yes |
| Component mappings | P03 | yes |
| Import snapshots | P01, P06 | yes |
| Dependency closure | P06 | yes |
| Test vectors + expected behavior | P04 | **no — external** |
| Comparison intent + selected reference | P12 | yes |
| Verification evidence | P07, P09, P10 | **no — external bundle** |
| Revision ancestry / edit history | P03, P11 | **no — absent** |
| Hashes to reproduce | P10, P12 | yes (across project + bundle) |
| Historical/current freshness | P05, P07, P12 | yes |

## Unexecuted / specification-only

- Live X Layer revalidation of a genuinely upgraded processor (P05 used a loopback double).
- Human developer and coding-agent usability sessions required by M4.5-1.
- Linux execution; CI success is recorded externally, not re-run here.
- Any wallet, signing, publication or chain write.

## Overall

**PARTIAL** against the complete pre-M5 portable-project specification: the exchange
mechanism is sound and reproducible, but the project unit does not embed named tests,
evidence digests or revision ancestry. Those require the versioned extension described in
`SCHEMA_EXTENSION_PROPOSAL.md`.
