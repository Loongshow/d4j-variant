# OCFLB v1 - Ownership-Controlled Fault Localization Benchmark (NON-CANONICAL RESEARCH BENCHMARK)

**Status (2026-09-29).** 10 pairs / 20 variants built, validated (all gates), frozen and run: claude-sonnet-4-6 98 attempted / 95 valid
/ 80 answered runs, claude-opus-5-5 51 / 50 / 50. Result: no definer bias under explicit, pinned contracts (every answered Sonnet run
and 49 of 50 answered Opus runs rank the gold first on both arms; mean attribution gap 0.02, zero misattributions in 130 answered runs);
Sonnet's only failure mode is exhaustion on two pairs. The Sonnet block ended three runs short (`OCFLB-MATH-06-ADAPTER` 1 valid attempt)
when the Anthropic credit balance ran out; resume path in `diagnostic-sonnet/PROVIDER_BLOCK.md`. Start with `results/OCFLB_RESULTS.md`
and `results/FINAL_THESIS_INTERPRETATION.md`.

Ten matched pairs (target) over five Defects4J projects. Every pair is one semantic fault re-cut into the fixed chain
Facade -> H1 -> H2 (definer) -> H3 (adapter) -> H4 -> H5, with two arms that differ only in which of H2/H3 holds the fault, and a
pin (second caller of H2) that makes ownership unique. Primary model claude-sonnet-4-6 (5 runs per arm), secondary claude-opus-5-5
(3 runs per arm on a pre-registered five-pair subset). All artifacts are labelled NON-CANONICAL until human review.

| Path | Content |
|---|---|
| `TARGET_SELECTION.md` | the ten seeds, their definer/adapter split, accept/reject |
| `review/CONSTRUCTION_TEMPLATE.md` | the frozen construction template every builder follows |
| `review/OCFLB_READINESS.md`, `review/ready_pairs.json` | one row per pair, gate-by-gate; only READY pairs run |
| `review/OPUS_SUBSET.md` | pre-registered Opus subset rule |
| `review/PAIR_OVERVIEW.md` | one-line chain/pin/bug-line summary per pair |
| `results/INTEGRITY.json` | frozen-hash and protocol identity check over every run |
| `diagnostic-sonnet/PROVIDER_BLOCK.md` | the quota block that ended the Sonnet top-ups, with the resume command |
| `review/RUNNER_ENV_PROOF_*.md` | proof that `defects4j test` executes in each server's agent environment |
| `BENCHMARK_MANIFEST.json` | the freeze: pairs, arms, golds, triggers, ownership, hashes, protocol identity |
| `projects/<Project>/bug-XX/` | `TARGET_SPEC.md`, `DEFINER_FAULT/`, `ADAPTER_FAULT/`, `CORRECT/` (reference), `validation/`, `analysis/{LOGIC_CHAIN,OWNERSHIP_PROOF,SEMANTIC_EQUIVALENCE,LEAKAGE_AUDIT,LOCAL_COHERENCE}.md`, `pair.json` |
| `new_bug_variants/<Project>/bug-1/L20/<VID>/` | installed variants served to the model servers |
| `models/<server>/benchmark_runs/mini-swe-claude/<VID>/run-NNN/` | every run (servers sonnetA, sonnetB = claude-sonnet-4-6; opusA = claude-opus-5-5) |
| `diagnostic-sonnet/`, `diagnostic-opus/` | server/driver/probe logs, pids |
| `analysis/per_run/run_metrics.json` | one row per run |
| `results/` | OCFLB_RESULTS.md, ocflb_results.json, BUG_PAIR_RESULTS.csv, RUN_LEVEL_RESULTS.csv, OWNERSHIP_ANALYSIS.md, SONNET_RESULTS.md, OPUS_REPLICATION.md, FAILURE_TAXONOMY.md, PROJECT_SUMMARY.md, THESIS_TABLES.md, THESIS_FIGURE_DATA.md, INFRASTRUCTURE_ACCOUNTING.md, COST_ACCOUNTING.md, THREATS_TO_VALIDITY.md, FINAL_THESIS_INTERPRETATION.md |
| `scripts/` | `ocflb_lib.py`, `pairs/build_*.py`, `ocflb_validate.py`, `ocflb_package.py`, `ocflb_docs.py`, `build_readiness.py`, `freeze_benchmark.py`, `start_server.sh`, `prove_runner_env.sh`, `probe_model.py`, `ocflb_driver.py`, `queue_after.sh`, `ocflb_metrics.py`, `build_results.py` |
| `construction/` | fresh base checkouts (`checkouts/`), per-pair private work/fresh copies (not part of the benchmark) |
