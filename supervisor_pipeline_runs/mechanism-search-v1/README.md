# mechanism-search-v1: can controlled repository-level mechanisms reduce GPT-5.6's fault-localization accuracy?

**Status: runs completed 2026-10-11; reports verified 2026-10-12.** The preregistered global stop rule was met under condition B. 17 mechanism families were
screened, and three recipes built from the failure modes of the strongest families were tested on fresh held-out instances.
None produced a reliable reduction: **GPT-5.6 is robust under
the tested manipulations** (stop rule B).

Start with [`STABLE_ACCURACY_REDUCTION_SUMMARY.md`](STABLE_ACCURACY_REDUCTION_SUMMARY.md).

## Question

The cue-trust-v3 pilot (`../cue-trust-v3`, 27/27 gold at rank 1) was null. This study asks the broader question: which
controlled, interpretable repository-level mechanisms reliably reduce method-level fault-localization accuracy? The focus is
the case where the agent finds and reads the faulty (gold) method but still ranks another method first.

## Design: discovery and confirmation kept apart

1. **Mining** ([`MECHANISM_MINING.md`](MECHANISM_MINING.md), `mining/`). Retrospective analysis of 954 runs from completed
   earlier experiments (GPT-5.6 and Claude), to extract candidate failure mechanisms.
2. **Taxonomy** ([`MECHANISM_TAXONOMY.md`](MECHANISM_TAXONOMY.md)). Mechanisms M0 to M20, with frozen-data accuracy,
   screening and held-out results, and final status.
3. **Screening** ([`MECHANISM_SCREENING_REPORT.md`](MECHANISM_SCREENING_REPORT.md),
   [`MECHANISM_SCREENING_MATRIX.csv`](MECHANISM_SCREENING_MATRIX.csv)). EXPLORATORY, 3 runs per instance.
   - S1: 18 re-hosted earlier adversarial and controlled variants.
   - S2: 12 valid new prototypes built from written recipes ([`SCREENING_BUILD_RECIPES.md`](SCREENING_BUILD_RECIPES.md)).
4. **Phase 4 diagnostics** ([`PROMISING_MECHANISMS.md`](PROMISING_MECHANISMS.md)). Targeted validity repairs of the two 0/3
   screening instances.
5. **Held-out confirmation** ([`HELDOUT_CONFIRMATION_PLAN.md`](HELDOUT_CONFIRMATION_PLAN.md),
   [`HELDOUT_CONFIRMATION_RESULTS.md`](HELDOUT_CONFIRMATION_RESULTS.md)).
   - The three strongest failure modes were frozen as recipes before any Phase 4 result existed.
   - Nine fresh instances (3 per recipe, 3 projects each) were built by separate builder agents instructed not to read model
     output. The plan they read did summarise the S1 outcomes.
   - Each gold was confirmed by an independent auditor.
   - Each instance received 5 runs (HO-HB-COMPRESS-01: 4 valid, X11), and no instance was modified after an agent step.
6. **Failure modes** ([`FAILURE_MODE_ANALYSIS.md`](FAILURE_MODE_ANALYSIS.md)). Two labellers per S1 wrong run (12 runs), not
   shown the coordinator's labels. Adjudication was planned for disagreements, but none was needed. The held-out no-answer is
   classified in the report. The labels use a post-hoc set, mapped onto the preregistered one in AMENDMENTS X12.

**Preregistration and deviations.**

- The design is in [`PREREGISTRATION.md`](PREREGISTRATION.md), which is frozen and hashed into every plan.
- Every deviation is in [`AMENDMENTS.md`](AMENDMENTS.md) (X1 to X11, with corrigenda in X12).
- Provenance of every instance (tier, kind, parent, revision, result) is in
  [`INSTANCE_PROVENANCE.csv`](INSTANCE_PROVENANCE.csv).
- Cost is in [`COST_LEDGER.csv`](COST_LEDGER.csv).

## Protocol

- **Model and harness.** GPT-5.6 through the mini-swe-agent profile, reasoning effort medium, 50 steps, 300 s per run.
- **Workspace.** An external workspace, with the agent bash environment restricted to an allowlist.
- **Integrity.** A contamination and leakage scanner ran on every run, with freeze verification (`FREEZE.json`) before every
  gate and launch. One diagnostic replay call for the halt review was made outside it.
- **Driver.** `scripts/ct_driver.py` applies a uniform provider-failure rule (`scripts/ct_status.py`).
- **Measures.** Per-run measures are defined in the `scripts/mx_metrics.py` docstring.
- **Held-out verdicts.** Computed by `scripts/mx_heldout_report.py`.

## Layout

| Path | Content |
|---|---|
| `scripts/` | Driver, status rules, scanner and metrics, plus the instance builder and validator (`mx_build_validate.py`, gates G0 to G14), revision builder (`mx_derive.py`), harness check (`mx_harness_check.py`), `/private/tmp` audit (`mx_tmp_audit.py`), safe trajectory viewer (`mx_traj_view.py`) and report generators |
| `plans/` | Every frozen run plan (S1, S2, S2_cont, P4, HO, HO_cont, HO_top, and the smoke and proof plans) |
| `instances/<iid>/` | Spec, validation record, independent audit (held-out instances), builder report and validated patches |
| `new_bug_variants/` | The benchmark variants (opaque ids; patches and manifests) as served to the harness |
| `review/VARIANT_KEY.json` | The private answer key (gold, decoys, entry points per variant) |
| `construction/heldout/` | Held-out builder and audit briefs, specs and the recipe freeze record |
| `construction/phase4/` | Phase 4 revision specs |
| `analysis/` | `per_run.csv` and `per_run.json` (all runs), per-instance summaries, screening, held-out and failure-mode outputs |
| `models/mxF0/` | The patched harness copy used for all paid runs (`variant-lab/`); sanitized per-run artifacts under `benchmark_runs/` |
| `diagnostic/` | Driver ledgers (`block_*.jsonl`), driver logs, Phase 1 acceptance, halt review and stall replay |
| `mining/` | Mining annotations and extracted run data |

**Not published:**

- raw provider output (`raw_agent_output.txt`) and full message transcripts;
- agent workspaces and their archive;
- health-probe dumps and smoke runs;
- pristine Defects4J checkouts (reproducible with `defects4j checkout`);
- builder scratch trees;
- any credential.

The per-run measures in `analysis/` were computed from the full artifacts before publication.

## Result in one table

| Recipe (held-out) | Valid runs | Acc@1 | Label |
|---|---|---|---|
| HA entry-point ranking | 15 | 0.933 (14/15; the only miss is a no-answer timeout) | NOT_SUPPORTED |
| HB sink blame | 14 | 1.000 | NOT_SUPPORTED |
| HC convention attribution | 15 | 1.000 | NOT_SUPPORTED |

**The screening reductions** (S1 Acc@1 0.78, 12 wrong runs, all in re-hosted instances tuned against Claude) mostly fit one of
two patterns:

1. **A competing location with a documented argument.** This was defensible on both judgements only in DEPTH-01, where the
   decoy's own doc contradicts its code. The coordinator also flagged a correct sibling (COMPRESS-07) and an under-specified
   convention (CHART-01-ADAPTER), but the blind labellers judged those answers not defensible.
2. **Ranking by proximity to the test** (5 runs).

Not every miss fits either pattern: MASK-01 run 3, DEFINER-01 and the CHART-01-ADAPTER misses went against conventions pinned
in the repository.

In exploratory Phase 4 revisions, both 0/3 instances became 3/3 after targeted validity repairs:

- COMPRESS-07: the correct sibling was removed;
- DEPTH-01: the decoy's doc was fixed and the gold's contract pinned.

The failure modes, rebuilt in valid form without the flagged features, produced no reduction on fresh held-out instances.
Per-recipe Wilson lower bounds of 0.70 to 0.80 do not exclude moderate reductions. GPT-5.6 read the gold in every wrong
answered run.
