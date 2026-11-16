# conversion-long-chain-v1 — NON-CANONICAL · LONG-CHAIN EXPERIMENT · GPT-5.6 DIAGNOSTIC

Isolated root for the five-hop matched pair derived from the validated locally-coherent Conversion fault
(`../locally-coherent-conversion-v1/`). Not part of the canonical CRFLB corpus; not benchmark-eligible; not an L-level /
reasoning-depth measurement (`synthetic_call_hops = 5` is a construction count).

| Arm | Gold | Chain |
|---|---|---|
| CONVERSION-LONG-CONTROL-01 | `Conversion#intArrayToLong` | 0 hops (variant.patch byte-identical to CONVERSION-CONTROL-01) |
| CONVERSION-LONG-TREATMENT-01 | `NumberUtils#overlay` | `Conversion.intArrayToLong → ArrayUtils.gather → EnumUtils.compose → BitField.widen → ObjectUtils.combine → NumberUtils.overlay` |

Layout: `CONVERSION-LONG-*/` (packages), `analysis/` (design, implementation, equivalence, leakage, coherence audits, data, states),
`validation/`, `repro/`, `scripts/` (build, validate, repro, emulate, token surface, package, launcher, analyzer), `work/` (construction
checkouts), `diagnostic/` (isolated diagnostic root prepared for port 8793: frozen server copy identical to the v3 copy, packages, run
records). Execution note: on 2026-09-22 the only credentialed frozen server was the v3 root's on port 8792 (the credential is never
available to the agent process), so the 5 + 5 runs were executed through that server (`scripts/run_long_chain_attach.sh`,
`LONG_CHAIN_SERVER_ROOT` = v3 root); run families are linked from `diagnostic/benchmark_runs/` and hashed in `EXPERIMENT_MANIFEST.json`.
