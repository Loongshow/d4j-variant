# FIRST_AGENT_EXPERIMENT_PLAN — NUMBERUTILS-CONTROL-01 vs NUMBERUTILS-TREATMENT-01 on GPT-5.6 (not executed)

Design principle: the bug designer (claude-opus-5, supervisor pipeline) and the evaluated localizer (GPT-5.6 via mini-swe-agent) are different vendors; cross-vendor coupling is recorded in `research_metadata`. The experiment reuses the frozen Agent Benchmark protocol unchanged; every deviation is listed in §8.

## 1. Protocol elements (all existing)

| Element | Value | Source |
|---|---|---|
| Prompt | `d4j-localization-only/v2`, base sha256 `845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89`; `prompt.txt`/`prompt.json` written per run | `agents/agentAdapter.mjs` |
| Unhashed second prompt | mini-swe `system_template` ("careful benchmark participant…") — record its text hash in the run notes since the harness does not | `miniSweAgentAdapter.mjs:360-363` |
| Agent / provider / model | `mini-swe-agent-openai-gpt-5-6` → mini-swe-agent 2.4.6, provider openai, model from `D4J_OPENAI_MODEL` (=`gpt-5.6`), runtime `openai/gpt-5.6` | `providerConfig.mjs`, `agents.json` |
| Determinism | none available (no temperature/seed/top_p); variability is handled by repetitions only | repo-wide grep |
| Budget | 50 tool calls, 300 s execution, 30 s startup; `max_test_runs: 5` is declared but not enforced (record this) | `benchmarkStore.normalizeBudget` |
| Repetitions | 5 per arm (project default `DEFAULT_TARGET_RUNS = 5`) → 10 runs; `repeats: 5` in one request creates `run-001…run-005` | `index.mjs:createBenchmarkRunsForRequest` |
| Output schema | exactly 10 unique production `Class::method` via `submit_fault_localization`; validated against `method_catalog.json` (JDK parser) | `mini_swe_fault_localization.py`, `parseTopTenRanking` |
| Scoring | exact `FQCN::method` match on `fault.locations[]`; gold rank, Hit@5/10, Acc@1, MRR from `evaluation.json` | `evaluateRanking`, `accuracyStore` |
| Trajectory / evidence | `trajectory.jsonl` (test_run/search/open_file/submission events), behaviour metrics (first gold file open position, searches, files read), `reasoning_workflow.json` with the epistemic-scope disclaimer | `benchmarkStore.computeBehaviorMetrics`, `reasoningWorkflow.mjs` |
| Shortcut audit | `shortcut_audit.json` is produced only on the batch path; for ad-hoc runs compute it post hoc from `trajectory.jsonl` + `lexgate` (already run: `analysis/data/lexgate_*.json`) | `index.mjs:1130-1163` |
| Protocol-violation detection | by construction: `.git` stripped, patches/manifests excluded, private-metadata scan before launch, source-hash before/after → `protocol_violation` on mutation | `agentAdapter.mjs`, `benchmarkStore.mjs:559-632` |

## 2. Workspace isolation (existing adapter)

Fresh copy of `workspaces/defects4j/Lang-1/fixed` (present) → `.git` stripped → `variant.patch` then `test.patch` applied with `patch -p1` (dry-run first) → staging sanitised → copied to `workspace/` → sanitised again → private-metadata scan (`variant.patch`, `test.patch`, `variant_manifest.json`, `validation.json`, `*.patch`, `*.orig/.rej` all banned) → `source_hashes_before.json` → method catalog → failing-test source extracted from the workspace → `defects4j test -t` captured as evidence. The supervisor's `.source_patch.diff`/`.test_patch.diff` never enter: they exist only in `real/repro-checkout`, which is not the package.

**Files the agent receives:** the whole Lang-1f tree (`src/`, `build.xml`, `pom.xml`, `default.properties`, `.defects4j.config`, `defects4j.build.properties`, …) with the variant applied; no `.git`, no patches, no manifests. **Known covariate:** `defects4j.build.properties` names `org.apache.commons.lang3.math.NumberUtils` (the original Lang-1 class = CONTROL gold class = TREATMENT facade class). Keeping it is protocol-consistent with every existing Lang-1 variant run; removing it is a protocol change (see §8).

## 3. Failing-test evidence

`failing_test_identifier` = `org.apache.commons.lang3.math.NumberUtilsTest::testCreateBigIntegerPositiveSigned`; `failing_test_source` = the 7-line method incl. its javadoc ("with an explicit positive sign") and the `"+1234"`/`"+7"` literals; `stack_trace` = Lang's thin stdout (`Failing tests: 1 / - …`), no assertion message. The agent may run the allowed command once and read `failing_tests` to obtain `expected:<1234> but was:<-1234>`.

## 4. Leakage assessment of the trigger name (see `PILOT_LEAKAGE_AUDIT.md`)

`testCreateBigIntegerPositiveSigned` carries (a) the facade/CONTROL-gold method name verbatim — identifying (one declaration), and (b) `PositiveSigned`, which states the fault's input class; together with the `"+1234"` literal it points to the unique `"+"` literal that **is** the gold line in both arms. `lexgate`: EXPOSED in both arms. Against the project's rule ("remove leakage the benchmark introduced; preserve and record what the repository introduces"), the name and javadoc are benchmark-introduced and removable; the input literal is the natural minimal evidence and is a covariate. This is a stronger leak than the corpus's Closure strict conditions (Low) and comparable to the Chart L30 dependency condition (High), which the project already treats as a confound.

## 5. Pre-registered expectations

- E1: Acc@1 = 1.00 in both arms (ceiling), gold rank 1 in ≥ 9/10 runs; first search token in most runs is `createBigInteger`, `+`, or `negate`.
- E2 (alternative): TREATMENT gold rank > 1 in ≥ 2/5 runs with the facade or hop1 ranked above the gold — the "two-horse race" profile already seen for direct-call displacement.
- Decision rule: E1 → the canonical pair cannot measure the recipe; proceed to the leakage-safe pair (§7) and the 2×2 in `ABLATION_DESIGN.md`. E2 → inspect trajectories for whether the miss follows the lie (facade opened, hop not followed) or novelty (hop found by anomaly).

## 6. Analysis outputs

Per run: `evaluation.json` (gold_rank), `ranking.json`, `trajectory.jsonl`, `behavior` metrics (first gold file open position, `search_count`, `production_files_read`), `source_integrity.json` (must be ok), `workspace_manifest.json` (isolation flags). Pair summary: Acc@1/5/10, MRR, mean gold rank, count of runs whose first grep was the `"+"` literal, count where the gold file was opened before any hop name was searched. These runs will **not** enter `accuracy:export` (no cohort, no `-L##-` infix, debug override); analysis is per-run from `evaluation.json`.

## 7. Leakage-safe alternative (designed, not built)

New pair `NUMBERUTILS-CONTROL-02` / `NUMBERUTILS-TREATMENT-02`: identical `variant.patch` files; new `test.patch` with the same two assertions, a style-conforming non-descriptive name (e.g. `testCreateBigIntegerAdditional`), no javadoc sentence; both arms re-validated (compile, 3× signature, collateral, fresh repro) by the external re-validator; lexgate re-run on the rendered payload (expected: CONTROL still EXPOSED via the method name in the assertion — natural evidence; TREATMENT possibly DECOUPLED if the FQN anomaly is normalised). Optionally a formatting-normalised TREATMENT (C1n). The canonical `-01` artifacts remain untouched.

## 8. Deviations / decisions needed before launch

1. **Non-canonical status.** The packages are not `benchmark_eligible` (literal `false`, non-conformant `validation.json`, `reproducibility.status: not_checked`). Running them requires `debug_allow_unreproduced_variant: true`, which the harness records as `debug_override: true`. Acceptable for a ceiling check; not for a reportable result.
2. **Placement.** Packages must be *copied* (never moved) into `new_bug_variants/Lang/bug-1/L20/<ID>/` for discovery; discovery needs only `variant_manifest.json`. This writes two new directories into the canonical tree; it is a reversible, additive step but it is your call.
3. **`defects4j.build.properties`** — keep (protocol-consistent) or strip (protocol change).
4. **API key** — the server reads `OPENAI_API_KEY`/`D4J_OPENAI_MODEL` from its environment; never place keys in files under the repo.

## 9. Prepared commands

See `analysis/scripts/prepared_first_experiment.sh`. It refuses to run unless `CRFLB_APPROVED_PAID_RUN=1` is set, refuses to overwrite any existing directory, and performs: copy packages → start server (foreground, port 8787) → smoke test → two `POST /api/benchmark-runs` requests (5 repeats each) → print `evaluation.json` paths. Estimated cost: 10 runs × ≤ 50 tool calls on gpt-5.6, ≤ 300 s each (≈ 50 min wall clock).
