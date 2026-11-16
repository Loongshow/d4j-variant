# Halt review: pilot slot 8 (2026-10-09)

**Halt.** `plans/pilot.json` slot 8 (CT-LANG-01, CG1, `CTV-F5B88A`) failed twice as infrastructure. The driver halted at
05:14:48Z under the pre-registered rule "a slot failing twice as infrastructure". Slots 0 to 7 were valid.

**Both attempts are provider stalls under the uniform rule (rule 2).**

| Run | Model calls | Commands | Last recorded event | Time left before the 300 s kill |
|---|---|---|---|---|
| run-001 | 3 | 9 | tool results at 21.2 s | 278.8 s |
| run-002 | 2 | 6 | tool results at 10.3 s | 289.7 s |

- Every issued command had finished and its output was recorded, so no agent command was still running.
- The raw output has no retry lines, so no exception was raised: one in-flight request never returned. litellm's default
  request timeout (600 s) is longer than the 300 s run.

**Mechanism check: replay** (`scripts/replay_stall_gpt.py`, results in `diagnostic/stall_replays/`). The exact conversation
state at each stall was sent to the same model with the same tools and `reasoning_effort: medium`, twice per state.

| State | Replay | Latency | Reasoning tokens | Result |
|---|---|---|---|---|
| run-001 | r1 | 5.3 s | 24 | 3 tool calls |
| run-001 | r2 | 7.3 s | 110 | 3 tool calls |
| run-002 | r1 | 9.6 s | 322 | 3 tool calls |
| run-002 | r2 | 13.6 s | 509 | 3 tool calls |

The states do not induce long deliberation. The stalls were transient provider hangs, not a cue-related behaviour, so the
infrastructure classification stands.

**Continuation, under the existing uniform provider-failure rule** (adversarial-break-v1: stalled attempts are topped up after
the planned block, capped at six extra attempts per cell). `plans/pilot_cont.json` holds:
- the frozen slots 9 to 26 in their original order;
- then one top-up of slot 8 with the same level (CG1), so the wording balance is unchanged.

It is frozen as an added plan bound to gptF0 (`freeze_gpt_pilot.py --add-plan`). The acceptance digest is unchanged, and no
frozen code, instance, cue or slot was changed. This decision depends only on the infrastructure evidence above, not on any
run's ranking.
