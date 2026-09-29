# adversarial-break-v1: making the localization model wrong

Isolated root for the ADVERSARIAL LLM FAULT-LOCALIZATION BREAKING mode. Nothing here modifies the frozen GPT-5.6 root, the pilot
root or any completed run; the model servers are copies of the pilot's patched Variant Lab, one per model, one paid slot each.

| File | Content |
|---|---|
| `FAILURE_SURFACE_MODEL.md` | Part 2: levers mined from the GPT-5.6 and Claude pilot trajectories |
| `ATTACK_IDEA_CATALOG.md` | Part 3: 66 attack ideas across families A to M, each classified |
| `ATTACK_RANKING.md` | Part 4/5: ranking by expected Acc@1 reduction, designer/critic verdicts |
| `TOP5_ATTACKS.md` | Parts 6/7/17: the seven built attacks and the composite, with pre-registered gold, roles and validation |
| `SCREENING_RESULTS.md` | Part 9: weaker-model screening (generated table + reading) |
| `CONFIRMATION_RESULTS.md` | Part 10: n=10 Sonnet and n=5 Opus on the top three (generated) |
| `MAX_DIFFICULTY_RESULTS.md` | Part 17: the composite (generated table + reading) |
| `MODEL_COMPARISON.md` | transfer from the weaker model to Opus (generated + reading) |
| `FAILURE_TAXONOMY.md` | Part 12: every incorrect run classified (generated + reading) |
| `WHAT_ACTUALLY_BREAKS_LLM_FL.md` | synthesis |
| `CLEAN_VS_ARTIFACT_ATTACKS.md` | per attack: clean component, artifact component, trap classes, cleanability |
| `NEXT_STEP.md` | the one recommended follow-up experiment, plus harness fixes |
| `VALIDITY_TEST_RUNNER.md` | the headline attack re-run with an executable test runner (protocol v2+runner), kept out of the main tables |
| `diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`, `diagnostic/PROVIDER_STALL_RULE.md`, `diagnostic/stall_replays/` | the two anomalies found during the run: no executable test for Claude agents; hung API requests (with replays) |
| `construction/packages/<VID>/` | per attack: `attack.json` (gold, roles, candidates, mechanism), `variant.patch`, `test.patch`, `validation.json`, `variant_manifest.json`, `NON_CANONICAL.md` |
| `new_bug_variants/<Project>/bug-1/L20/<VID>/` | installed variants served to the three model servers |
| `models/<name>/benchmark_runs/mini-swe-claude/<VID>/run-NNN/` | every run: trajectory, ranking, evaluation, manifests, workspace |
| `analysis/per_run/attack_run_metrics.json` | one row per run (rank, MRR, discovery step, tool calls, taxonomy, cost) |
| `analysis/per_attack/<attack>.json`, `analysis/tables/attack_by_model.json` | per attack and per attack x model aggregates |
| `analysis/narratives/*.md` | hand-written readings appended to the generated reports |
| `diagnostic/` | server and driver logs, health-gate probe logs, `PROVIDER_STALL_RULE.md`, server PID files and stop log |
| `scripts/` | builders (`attacks/build_*.py`, `buildlib.py`), `validate_attack.py`, `package_attack.py`, `attack_driver.py`, `probe_model.py`, `attack_run_metrics.py`, `build_break_reports.py`, `start_model_server.sh`, `start_model_server_tests.sh` (adds PERL5LIB), `queue_after.sh`, `topup_valid.py`, `replay_stall.py`, `build_manifest_break.py` |

Regenerate every table: `python scripts/attack_run_metrics.py analysis/per_run/attack_run_metrics.json && python scripts/build_break_reports.py`.
