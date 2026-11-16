# OCFLB Level B v1 (NON-CANONICAL RESEARCH BENCHMARK)

Five OCFLB v1 pairs converted to Level B: globally unique ownership (production second caller + unit pin + isolated-repair proof) with
locally ambiguous ownership (neutral H2/H3 javadocs, omission-type or convention-mismatch faults, blinded local-cue gates V15/V16).
Design: `FINAL_LEVEL_B_SPEC.md`; pairs: `PAIR_SELECTION.md`; gates: `READINESS.md`; freeze: `BENCHMARK_MANIFEST.json` / `FREEZE_MANIFEST.json`.
Servers sonnetA (8821), sonnetB (8822) = claude-sonnet-4-6; opusA (8823) = claude-opus-5-5; runner proofs in `review/`.
Status notes are appended at the end of this file as the build proceeds.

## Status 2026-09-30T08:31Z: CONSTRUCTED, VALIDATED, FROZEN; paid runs BLOCKED_PROVIDER_QUOTA

- 5/5 pairs READY (`READINESS.md`): V1-V14 + V12b pass, both arms `PINNED_UNIQUE`, V15 pass, V16 LOCAL_AMBIGUOUS (60 blinded graders,
  zero confident verdicts). Four pairs needed one revision after blinded grading (`PAIR_SELECTION.md`, revision history; revision-1
  records under `projects/<P>/bug-XX/rev1/`).
- Frozen 2026-09-30T08:30:37Z: `BENCHMARK_MANIFEST.json` sha256 `b32d353fb006a93d...`, 10 variants installed under `new_bug_variants/`;
  `results/INTEGRITY.json` PASS (0 runs). Opus subset pre-registered in `review/OPUS_SUBSET.md`.
- Credits: direct bounded probe 2026-09-30T08:30Z -> HTTP 400 "credit balance is too low"; harness probe on sonnetA hung 90 s (the
  silent-retry signature). No run was launched. Servers sonnetA (pid 36914, 8821), sonnetB (36917, 8822), opusA (36920, 8823) are left
  running with `PERL5LIB` exported (proofs in `review/`); `scripts/resume_after_credits.sh` restarts and re-proves them if they are gone.
- Resume: `scripts/resume_after_credits.sh sonnet`, then `scripts/resume_after_credits.sh opus`, then `sh scripts/finalize_lb.sh`;
  the differential pilot: `scripts/resume_after_credits.sh pilot`. Interpretation and reading guide: `results/FINAL_THESIS_INTERPRETATION.md`.

## Status 2026-10-01T11:10Z: EXECUTED (pilot CONFIRMED CASE C; Level-B Sonnet 50/50, Opus 22/22; servers stopped)

- Pilot (`PILOT_RESULTS.md`, differential root): 18 Sonnet + 6 Opus runs, 7.94 USD; only V5 (explicit operator at the gold) restores
  Sonnet; V1-V4 0/3 each; CASE C CONFIRMED. Level B run unchanged.
- Level B: Sonnet adapter-arm Acc@1 0.64 / definer 0.76 (50 valid, 0 stalls, 4 no-answers); Opus 0.545 / 0.733 (22 valid; LB-CHART-01
  extended to 5 per arm by the pre-registered rule). Level A 0.0 / 0.1, Level C 0.867 / 0.96. RESULT 1. Failures = gold discovered but
  misranked, concentrated on LB-CHART-01 (convention prior: offset assumed outward), mediated by external-evidence retrieval
  (Sonnet Group E 0.771 vs N 0.533). Cost 20.70 USD (Level B) + 7.94 (pilot).
- Integrity PASS, independent verification PASS (`results/VERIFICATION.md`, 72 runs, hashes equal the frozen manifest, earliest run
  after the freeze). Documents: `results/FINAL_THESIS_INTERPRETATION.md`, `FINAL_EXPERIMENT_SUMMARY.md`, `analysis/MECHANISM_GRADING.md`.
- Servers sonnetA/sonnetB/opusA and the pilot servers were stopped by recorded PID (`diagnostic-*/server_lifecycle.log`).
