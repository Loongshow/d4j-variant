# conversion-branch-dispatch-v1 — NON-CANONICAL · BRANCH-DISPATCH DIAGNOSTIC · GPT-5.6

Isolated root for the conditional-dispatch matched pair derived from the unique-dispatch pair (`../conversion-dispatch-v1/`).
Not part of the canonical CRFLB corpus; not benchmark-eligible; not an L-level / reasoning-depth measurement
(`synthetic_call_hops = 5`, `dispatch_indirections = 1`, `dispatch_implementations = 2` are construction counts).

| Arm | Gold | Chain |
|---|---|---|
| CONVERSION-BRANCH-CONTROL-01 | `Conversion#intArrayToLong` | 0 hops (variant.patch byte-identical to CONVERSION-CONTROL-01) |
| CONVERSION-BRANCH-TREATMENT-01 | `NumberUtils#overlay` | `Conversion.intArrayToLong → ArrayUtils.gather → EnumUtils.compose (width = 32) → BitField.widen → Folding.forWidth(width) → {STANDARD: StandardFolding.fold → ObjectUtils.combine → NumberUtils.overlay (gold) \| NARROW: NarrowFolding.fold (widths 8/16, correct, no gold)}` |

Selector: `Folding.forWidth(int width)` = `width < Integer.SIZE ? NARROW : STANDARD`. The trigger takes STANDARD.

Layout: `CONVERSION-BRANCH-*/` (packages), `analysis/` (BRANCH_DISPATCH_DESIGN, SEMANTIC_EQUIVALENCE, BRANCH_LEAKAGE_AUDIT, data, states,
lexgate), `validation/` (incl. two-branch probe gates BP1/BP2), `repro/` (incl. probe step R5), `scripts/` (build, validate, repro,
BranchProbe.java, emulate, package, launcher, analyzer, renderer), `work/`, `diagnostic/` (isolated root prepared for port 8795 with a
frozen server copy identical to the v3 copy — not started because the credential is never available to the agent process; runs executed
through the running v3 server on 8792 additively with before/after inventories; run families linked from `diagnostic/benchmark_runs/`).

**Supplementary block (2026-09-22, 07:57–08:15 UTC): CONVERSION-BRANCH-TREATMENT-01 run-006…015** — ten further TREATMENT-only runs under the unchanged protocol (launcher `scripts/run_branch_supplementary_attach.sh`, two sequential batches of 5 through the v3 server on 8792; no CONTROL runs; nothing rerun). Result: 10/10 gold rank 1, facade-first 0/10; combined n = 15: ranks 14 × 1 + 1 × 2, Acc@1 0.933, MRR 0.967, facade-first 1/15 → the preregistered 3/15 ownership threshold was **not** reached. Reports: `BRANCH_SUPPLEMENTARY_RESULTS.md`, `branch_supplementary_results.json`, `BRANCH_SUPPLEMENTARY_TRAJECTORY_AUDIT.md`, `OWNERSHIP_ATTRIBUTION_N15.md`, `BRANCH_N15_COMBINED_INTERPRETATION.md`, `NEXT_EXPERIMENT_DECISION_N15.md`; tables in `analysis/tables_branch_supplementary*.md`; scripts `analyze_branch_supplementary.py`, `post_run_integrity_supplementary.sh`; integrity records in `analysis/data/*_supp*`. The original block's files are unchanged (hash-verified).
