# conversion-dispatch-v1 — NON-CANONICAL · INDIRECT-DISPATCH DIAGNOSTIC · GPT-5.6

Isolated root for the indirect-dispatch matched pair derived from the validated five-hop Conversion pair
(`../conversion-long-chain-v1/`). Not part of the canonical CRFLB corpus; not benchmark-eligible; not an L-level /
reasoning-depth measurement (`synthetic_call_hops = 5`, `dispatch_indirections = 1` are construction counts).

| Arm | Gold | Chain |
|---|---|---|
| CONVERSION-DISPATCH-CONTROL-01 | `Conversion#intArrayToLong` | 0 hops (variant.patch byte-identical to CONVERSION-CONTROL-01) |
| CONVERSION-DISPATCH-TREATMENT-01 | `NumberUtils#overlay` | `Conversion.intArrayToLong → ArrayUtils.gather → EnumUtils.compose → BitField.widen → [Folding.STANDARD → StandardFolding.fold] → ObjectUtils.combine → NumberUtils.overlay` |

The manipulation: at hop 3 → hop 4 the literal call `ObjectUtils.combine(...)` is replaced by `Folding.STANDARD.fold(...)`;
`builder.Folding` (abstract class, binding `STANDARD = new StandardFolding()`) and `builder.StandardFolding` (override delegating to
`ObjectUtils.combine`) are new files in the `ToStringStyle`/`StandardToStringStyle` idiom. Everything else is identical to the five-hop pair.

Layout: `CONVERSION-DISPATCH-*/` (packages), `analysis/` (DISPATCH_DESIGN, SEMANTIC_EQUIVALENCE, DISPATCH_LEAKAGE_AUDIT, data, states,
lexgate), `validation/`, `repro/`, `scripts/`, `work/`, `diagnostic/` (isolated root prepared for port 8794 — frozen server copy identical
to the v3 copy — not started because the credential is never available to the agent process; the runs were executed through the running
v3 server on port 8792 as for the five-hop experiment, additively, with before/after inventories; run families linked from
`diagnostic/benchmark_runs/`).
