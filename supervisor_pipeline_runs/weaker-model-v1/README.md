# weaker-model-v1

The fault-localization benchmark root that followed mechanism-search-v1. Every run uses the frozen mechanism-search-v1 harness:

- base prompt sha256 `845e21e7…`;
- 50 tool calls, 5 test runs, 300 s per run;
- `reasoning_effort: medium`;
- external workspaces, a leakage scanner, and freeze verification before every paid call.

Only the model differs between blocks. Decisions and deviations are logged in order in `AMENDMENTS.md` (W1 to W20).

## Studies, in order

| Study | Question | Report |
|---|---|---|
| Ladder | Do weaker OpenAI models lose accuracy on the nine held-out instances that GPT-5.6 solved? | `PREREGISTRATION.md`, `WEAKER_MODEL_RESULTS.md` |
| Stage A | Do the frozen instances that GPT-5.6 missed also break gpt-5.5? | `WEAKER_MODEL_RESULTS.md`, `MECHANISM_BY_MODEL.md`, `FAILURE_MODE_COMPARISON.md` |
| Stage B (gpt-5.5) | Does a 5-hop chain with a facade lie, and/or an odd-looking correct hop, reduce Acc@1 on three fresh bugs? | `STAGE_B_DESIGN.md`, `STAGE_B_PREREGISTRATION.md`, `STAGE_B_RESULTS.md`, `SUPERVISOR_UPDATE_STAGE_B.md` |
| Study 1 (gpt-5 timeouts, retrospective) | What caused gpt-5's ten held-out timeouts, and is the introduced ambiguity a plausible cause? | `gpt5-timeouts/GPT5_TIMEOUT_ANALYSIS.md`, `GPT5_AMBIGUITY_HYPOTHESIS.md`, `GPT5_TIMEOUT_MATCHED_COMPARISON.md`, `GPT5_TIMEOUT_RUN_INDEX.csv`, `GPT5_TIMEOUT_TIMELINES.csv`, `GPT5_TIMEOUT_BLIND_LABELS.json` |
| Study 2 (Stage B on GPT-5.6) | Does the Stage B drop transfer to GPT-5.6 when only the model changes? | `stageB-gpt56/GPT56_STAGE_B_PREREGISTRATION.md`, `GPT56_STAGE_B_RESULTS.md`, `GPT55_VS_GPT56_STAGE_B.csv`, `GPT55_VS_GPT56_ANALYSIS.md`, `CROSS_MODEL_FAILURE_MODES.md`, `SUPERVISOR_UPDATE_STAGE_B_GPT56.md` |
| Report to the supervisor (16 Oct 2026) | Both studies, with the decisions still needed | `stageB-gpt56/SUPERVISOR_REPORT_2026-10-16.md` (the report as sent), `stageB-gpt56/SUPERVISOR_QUESTIONS_2026-10-16.md` (open questions, English and Chinese) |

## Headline results

**Held-out set (nine instances).**

| Model | Acc@1 | Note |
|---|---|---|
| gpt-5.5 | 27/27 | |
| gpt-5 | 17/27 | all 10 failures are timeouts, never misrankings |
| GPT-5.6 (reference) | 43/44 | |

**Stage B (Acc@1 per cell).**

| Cell | gpt-5.5 | GPT-5.6 |
|---|---|---|
| C00 (1-hop) | 15/15 | 15/15 |
| C01 (1-hop + odd sibling) | 14/15 | 15/15 |
| C10 (5-hop + lie) | 3/15 | 15/15 |
| C11 (5-hop + lie + odd hop) | 4/15 | 11/15 |

- gpt-5.5's chain effect is -0.73 (p = 3.4e-9).
- On GPT-5.6 the drop is ATTENUATED by the preregistered rule: 26/30 in the chain cells, against 30/30 in the 1-hop cells
  (p = 0.11). One more correct chain run would have made it ELIMINATED.
- Every miss by either model that the labellers coded ENTRY_POINT_BIAS has the same shape: the agent names the gold, then ranks
  the facade the test calls first.

**Study 1.** The ambiguity hypothesis is NOT SUPPORTED as the reason the gpt-5 runs timed out.

- 6 of the 10 timeouts fall in a provider slow-serving period.
- 1 timeout was a validator rejection of an answer the agent had already committed to.
- In 3 runs the behaviour is consistent with non-commitment. Whether the ambiguity caused it is INCONCLUSIVE.

## Layout

| Path | Contents |
|---|---|
| `scripts/` | Driver, freeze, scanner and frozen measures. `mx_metrics.py` is frozen. `gpt5_*.py` scripts belong to Study 1; `stageB_*.py` scripts produce the Stage B tables, labels and comparisons. |
| `analysis/` | Per-run measures (`per_run.json`), Stage B cells, failure-mode labels (`failure_modes/`), safe trajectory views (`traj_views*/`), and verification records with backups (`verification/`). |
| `diagnostic/` | Driver logs, ledgers (`block_*.jsonl`), server lifecycle, Phase 1 acceptance. |
| `plans/`, `FREEZE.json` | Run plans and the freeze manifest. |
| `models/<server>/` | Server setup, agent profile, server source, and per-run artifacts (whitelisted files only). |
| `instances/`, `new_bug_variants/`, `review/VARIANT_KEY.json` | The benchmark instances and their keys. |
| `construction/stageB/` | Stage B designs, specs, audits, validation logs and the labelling brief. |
| `COST_LEDGER.csv` | Spend by block: $64.10 recorded run cost, about $66 including estimates. |

## Not published

- Raw provider output (`raw_agent_output.txt`) and full message transcripts (`mini-swe-agent.traj.json`).
- Agent workspaces and their archive.
- Health-probe dumps and smoke-run scratch.
- Builder scratch trees (`construction/fresh/`).
- Any credential.

Per-run measures and safe views were computed from the full artifacts before publication.
