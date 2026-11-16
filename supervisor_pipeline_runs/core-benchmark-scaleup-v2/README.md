# core-benchmark-scaleup-v2 — NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6

End-to-end scale-up of the cross-project five-hop benchmark from 8 bugs / 3 projects to **14 bugs / 5 projects**: project selection, target screening, bug design, CONTROL/TREATMENT construction, validation, fresh reproduction, leakage and local-coherence audits, ownership-uniqueness counterfactuals, readiness gate, the paid GPT-5.6 block (6 new bugs × 2 arms × 5 runs = 60 runs), trajectory analysis and thesis tables.

Design is identical to the established manipulation: CONTROL keeps the semantic fault in the original target; TREATMENT relocates the same fault behind exactly five **direct** semantic call hops (facade → H1 → H2 → H3 → H4 → H5/gold). No reflection, dispatch, interfaces, string lookup, name obfuscation or narrative changes.

Layout: `PROJECT_SELECTION.md`, `TARGET_SHORTLIST.md`, `SCALEUP_MANIFEST.json`, `projects/<Project>/{TARGET_SCREENING.md,bug-NN/{TARGET_SPEC.md,pair_config.json,packages/,validation/,repro/,analysis/}}`, `analysis/` (cross-bug), `review/`, `scripts/`, `screening/`, `diagnostic-gpt56/` (paid-block execution records), `results-gpt56/` (results and thesis tables).

Every artefact is labelled NON-CANONICAL; packages carry `benchmark_eligible: false` until the readiness review is signed. Nothing under `new_bug_variants/`, `benchmark_runs/`, the frozen server copies or the existing experiment roots is modified.
