# core-benchmark-scaleup-v1 — NON-CANONICAL / CORE BENCHMARK SCALE-UP / NO GPT-5.6 RUNS PERFORMED

Construction-and-validation-only scale-up of the cross-project five-hop benchmark from 3 projects × 1 fault to 3 projects × up to 3 faults. **No GPT-5.6, mini-swe-agent, OpenAI or other paid evaluation was run in this phase**; every artifact here was produced by local deterministic scripts and local Defects4J test execution. Nothing under `new_bug_variants/`, `benchmark_runs/` or the frozen server copies was modified; supervisor sources, prompts, budgets and scoring are untouched.

## Result in one line
Five of the six requested new targets were constructed, validated, reproduced, leakage-audited, equivalence-probed, structurally audited and packaged (10 new variants); the sixth (a second Lang target) could not be supplied without weakening the gates and is recorded as NOT SUPPLIED. With the three existing pairs the benchmark holds 8 bugs / 16 variants.

## Layout
```
README.md · BENCHMARK_MANIFEST.json · PROJECT_SCREENING.md · GLOBAL_TARGET_SHORTLIST.md
lang/   TARGET_SCREENING.md · bug-02/            (bug-03: NOT SUPPLIED)
math/   TARGET_SCREENING.md · bug-02/ · bug-03/
chart/  TARGET_SCREENING.md · bug-02/ · bug-03/
<proj>/bug-NN/  TARGET_SPEC.md · pair_config.json · packages/<VARIANT-ID>/{variant.patch,test.patch,variant_manifest.json,validation.json,NON_CANONICAL.md}
                validation/{CONTROL,TREATMENT}_VALIDATION.json (+ logs) · repro/{CONTROL,TREATMENT}_REPRODUCTION.json (+ fresh checkouts)
                analysis/{FIVE_HOP_DESIGN,SEMANTIC_EQUIVALENCE,LEAKAGE_AUDIT,LOCAL_COHERENCE_AUDIT,STRUCTURAL_QUALITY_AUDIT}.md
                analysis/equivalence/ (probe class, four-state outputs, equivalence.json) · analysis/leakage/ (rendered payloads, lexgate JSONs, token surface) · analysis/structural_audit.json
                work/ (construction checkouts)
analysis/CROSS_BUG_DIVERSITY.md · review/{BENCHMARK_READINESS_TABLE.md,SCALEUP_HUMAN_REVIEW.md}
screening/  checkouts, static lists, probe batches (+results/logs), auto boundary scans
scripts/    mutation_probe.py · auto_boundary_mutations.py · build_{chart_bug02,chart_bug03,math_bug02,math_bug03,lang_bug02}.py · validate_pair.py · repro_pair.py
            render_payload.py · token_surface.py · package_bug.py · structural_audit.py · write_bug_docs.py · build_manifest.py
            repro_and_lexgate.sh · equivalence_probe.sh · finish_bug.sh
```

## Reproduction (per bug, deterministic, no LLM)
```
defects4j checkout -p <Proj> -v 1f -w work/<arm>
python scripts/build_<proj>_bugNN.py <control|treatment> work/<arm> packages/<VARIANT-ID>      # exact asserted edits; emits variant.patch/test.patch
python scripts/validate_pair.py <proj>/bug-NN/pair_config.json <arm> work/<arm> packages/<VARIANT-ID> validation/<ARM>_VALIDATION.json
zsh scripts/finish_bug.sh <proj> bug-NN <Proj> <ProbeClass> <tokens…>   # fresh repro + lexgate, equivalence probe, structural audit, token surface, packaging, docs
```
Validation gates (`validate_pair.py`): A0 clean tree · A patch applies · B2 test patch is byte-identical across arms · C/C2 test patch alone compiles and the trigger fails to compile/run without the variant only where expected · D trigger passes on the original code · E variant applies · M correct chain compiles (treatment) · N/N2 declared imports only, no other diffs · F buggy build compiles · G trigger fails with the exact signature · H no other failing test (collateral) · I full suite clean except the trigger · J/K the surviving-probe regime is confirmed on the buggy build · O/P/Q chain structure (treatment) · L work tree restored. Reproduction gates R0–R4 repeat build/trigger/collateral on fresh checkouts from the packaged patches.

## Labels
Every package carries `status: non_canonical_validated`, `benchmark_eligible: false`, `non_canonical: true` and the label "NON-CANONICAL · CORE BENCHMARK SCALE-UP · NO GPT-5.6 RUNS PERFORMED". Promotion into the paid benchmark requires the human review in `review/SCALEUP_HUMAN_REVIEW.md` and a separate, explicitly authorised paid block.
