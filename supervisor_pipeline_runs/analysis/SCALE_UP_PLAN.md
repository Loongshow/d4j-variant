# SCALE_UP_PLAN — staged generation plan (prepared, not executed)

Preconditions: all MUST-FIX items in `NEXT_STAGE_DECISION.md` resolved; re-validator and provenance mapper exist; leakage rule decided; extractor declared.

## 0. What the observed rates actually are

| Quantity | Observed | Basis |
|---|---|---|
| Design attempts to acceptance | 1 of 4 allowed | one real target (n = 1) |
| Mechanical stage pass rate | 2/2 runs (synthetic smoke + real) | n = 2 |
| Wall time per accepted pair | ≈ 6 min (Lang; full suite ≈ 1 min) | run.log |
| Paid API calls per accepted pair | 1 | cache dir |
| Targets eligible at 1200/900 in Lang-1f | 9 classes; seeds 1–10 map to only 3 distinct targets (`createBigInteger`, `intArrayToLong`, `toMap`, plus `DateUtils#round` which cannot be relocated) | seed sweep 2026-09-20 |
| Leakage-gate pass rate (lexgate DECOUPLED on rendered payload) | 0/2 arms | pilot |

The acceptance rate with a leakage gate in force is therefore **unknown and possibly low**; the plan below is sized to measure it, not to hit a count.

## Stage 1 — Pilot (done, pending re-validation)
Lang-1f, seed 42, one pair. Deliverables: re-validated, provenance-complete package; ceiling check on GPT-5.6 (10 runs). Exit: a decision whether the target family can measure anything.

## Stage 2 — Small replication (Lang only)
- Goal: measure per-target acceptance and leakage-gate rates; obtain 3 accepted pairs.
- Draw: seeds chosen to hit the three distinct Lang targets above (e.g. 42 → NumberUtils, 1 → Conversion, 3 → ArrayUtils); `--exclude-class` for already-used targets so seeds are not wasted on repeats.
- Budget: ≤ 4 paid design calls per target (the generator's own cap), ≤ 12 calls total, ≈ 1 h machine time.
- Every candidate pair passes: compile, 3× deterministic value-mismatch signature, class-qualified collateral vs baseline, fresh reproduction of both arms, lexgate on the rendered payload (rule from item 3), formatting normalisation or covariate, provenance block, matched-pair identity, generator + extractor hashes, model/prompt metadata.
- Exit: report acceptance rate *with* gates; if lexgate rejects all, stop and revise the trigger-naming rule before spending more.

## Stage 3 — Cross-project replication
- Projects with Maven/Ant layouts already supported by the code's `_test_class_from_path`: Chart (`source`/`tests`, JUnit 3), Closure, Math, Time (raise `--full-suite-timeout`; suite > 20 min per supervisor note), JacksonCore.
- Goal: 2 accepted pairs per project on 3 projects (6 pairs) to check that the recipe and the gates transfer, and to widen the population beyond Commons Lang utilities.
- Budget: ≤ 4 calls per target, ≤ 24 calls; machine time dominated by full suites (Time ≈ 25 min each ×4 per pair).
- Exit: per-project acceptance and leakage rates; any project where no static self-contained candidate exists (the supervisor's own Joda-Time observation) is recorded, not forced.

## Stage 4 — Scale-up
- Only if Stages 2–3 show a non-ceiling result on GPT-5.6 for at least one pair. Size by the effect observed: with a ceiling everywhere, further generation is wasted; with an effect, target ≈ 10 accepted pairs per project family where the effect appeared, using the measured acceptance rate to budget calls.
- Quality gates are never relaxed to reach a count; a stage that cannot reach its target reports the shortfall.

## Per-variant requirements (checklist carried by every package)
semantic validity (baseline passes, variant fails 3× with the same value-mismatch signature) · deterministic trigger · zero non-baseline collateral (class-qualified) · fresh reproduction of both arms · leakage gate result on the rendered payload (and the decided pass rule) · formatting-anomaly count · canonical provenance (generator hashes, extractor hash, seed, thresholds, pools, anchor seeds) · matched CONTROL/TREATMENT identity (`pair_id`, `semantic_bug.id`, `arm`, `paired_variant`) · generator version · extractor version · design model, SDK, prompt hash, cache file hash, attempts.
