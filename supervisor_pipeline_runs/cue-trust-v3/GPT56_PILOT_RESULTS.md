# GPT-5.6 cue-trust pilot: results

**Outcome: a null pilot.** GPT-5.6 ranked the true faulty method first in all 27 valid runs, across the neutral, gold-excusing
and decoy-blaming conditions on all three instances. Every pre-specified contrast is NULL. Under the pre-registered rule
(amendment A1) this stops the work:
- the forced-inspection follow-up (Phase 3) is not triggered;
- the ~200-run main block is not started.

`PILOT_NULL_ANALYSIS.md` gives the diagnosis and a minimal redesigned pilot.

Companion files:
- `GPT56_CUE_EFFECTS.md`
- `GPT56_TRAJECTORY_ANALYSIS.md`
- `GPT56_REASONING_USAGE.md`
- `GPT56_RUN_LEVEL_RESULTS.csv` (one row per attempt)
- `analysis/gpt56_tables_F0.md` (all generated tables)

## Setup and integrity

| Item | Value |
|---|---|
| OpenAI credential | `D4J_OPENAI_API_KEY`, authorized env file, available 2026-10-09; never printed or stored by the harness |
| Model | `gpt-5.6`, profile `mini-swe-agent-openai-gpt-5-6`; every response reported `gpt-5.6`; OpenAI Responses API through litellm 1.98.0's bridge, as in the earlier GPT-5.6 runs |
| Reasoning effort | `medium`, passed explicitly; recorded in every run's prompt record and model config. Per OpenAI's documentation and litellm's code, this is the default the earlier runs would have received without sending it; the earlier run records do not echo it |
| Prompt arm | F0, the frozen localization-only prompt (base sha256 `845e21e7…`) |
| Budgets | 50 model calls (step limit), 300 s timeout, 5-test budget recorded but not enforced, all as in the earlier runs |
| Freeze | `FREEZE_GPT56_PILOT.json` (2026-10-08T10:53:56Z), verified by the driver before every paid call |
| Smoke run (not counted) | `gptDiag` `CTV-BEE8CB/run-001`: completed, gold rank 1, USD 0.12; all ten Phase 1 proof items passed (`diagnostic/PHASE1_ACCEPTANCE.json`) |
| Leakage and integrity | 0 contaminated runs, 0 integrity breaks, protocol identity held on all 27 valid runs, every workspace outside the repository |
| Scanner-flagged calls | 3 calls in 2 runs: the agent wrote its own Java probe file to `/tmp`; no harness content touched; not contamination |

## Runs

| Attempted | Valid | Answered | Excluded |
|---|---|---|---|
| 29 | 27 | 27 | 2 provider stalls |

Both stalls hit slot 8 (CT-LANG-01, gold-excusing wording 1). The block halted under the pre-registered rule.
- *Replays:* the exact stalled states answered in 5 to 14 s with normal reasoning, so these were transient hung requests, not
  cue-induced deliberation (`diagnostic/HALT_REVIEW_slot8.md`).
- *Continuation:* the block continued with the frozen slots 9 to 26 in order, then one top-up of slot 8 at the same wording.
- *Deviation, disclosed:* the top-up was a third attempt at slot 8. That exceeds A1 and A3's one-replacement-per-slot limit,
  under which the block halts. It was an operator decision after the halt review, following the adversarial-break-v1 practice
  of topping up stalled attempts after the planned block (at most six extra per cell). It is recorded as an added, frozen plan.

## Ranks and accuracy

| Instance | Neutral (C0) gold ranks | Gold-excusing (CG) gold ranks | Decoy-blaming (CD) gold ranks |
|---|---|---|---|
| CT-CHART-01 | 1, 1, 1 | 1, 1, 1 | 1, 1, 1 |
| CT-LANG-01 | 1, 1, 1 | 1, 1, 1 | 1, 1, 1 |
| CT-CHART-03 | 1, 1, 1 | 1, 1, 1 | 1, 1, 1 |

| Condition | n | Acc@1 | MRR | Decoy first | Gold seen but misranked | Cue shown |
|---|---|---|---|---|---|---|
| C0 | 9 | 1.00 | 1.00 | 0 | 0 | not applicable |
| CG | 9 | 1.00 | 1.00 | 0 | 0 | 9/9 |
| CD | 9 | 1.00 | 1.00 | 0 | 0 | 8/9 |

## Process

| Measure | Result |
|---|---|
| Full gold method read | 27/27 |
| Full decoy method read | 27/27 |
| All top-three bodies read | 27/27 |
| Trigger test run | 27/27, always at the first or second tool call |
| Failure values seen | 16/27 (C0 4, CG 5, CD 7) |
| Independent probe run | 3/27 |
| Reasoning tokens per run | median 749 (450 to 1,570) |
| Tool calls per run | median 15 (10 to 36) |

**Cost.**
- *Valid runs:* USD 4.80, a mean of USD 0.18 per run.
- *Excluded stalls:* USD 0.12.
- *Overall:* USD 5.21, including the smoke run and 38 paid health probes, plus four stall replays of a few cents each.

**Pre-registered pilot gate: all four checks pass.**
- the cue was shown in 17/18 cue runs;
- the most expensive run cost USD 0.32;
- 0 behavioural timeouts;
- five blind hand labels agree with the computed metrics on 50/50 fields.

## Answers

- **Do the cues move attribution?** No. Every pre-specified contrast is NULL (delta 0). No instance shows a cue effect.
- **Phase 3 (forced inspection):** not triggered, because no contrast is STRONG. It would also add nothing here: GPT-5.6 already
  read the full code of its top three in 27/27 runs.
- **Strong enough for the main experiment?** No. The manipulation as built does not move GPT-5.6.
- **Next step:** do not start the main block. Build the minimal v2 pilot in `PILOT_NULL_ANALYSIS.md`: the same protocol, three
  instances and 27 runs, with cue construction under four coherence rules. It also extends the decoy sets and changes
  CT-LANG-01's trigger test; both fall outside the pre-registered calibration lever. Pre-register it as a new amendment before
  any run.

Earlier GPT-5.6 experiments are set beside this descriptively, never pooled (`GPT56_TRAJECTORY_ANALYSIS.md`). Their families
ranged from Acc@1 0.86 (205 runs) to 1.00 (small families), with tests run in every run.
