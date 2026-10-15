# Stage B on GPT-5.6: results (2026-10-15)

**What was run.** The exact Stage B benchmark that gpt-5.5 ran on 2026-10-14 was re-run with only the model changed: same
instances, cells, gold, prompt, budgets, run order and scoring.

**Rules.** `GPT56_STAGE_B_PREREGISTRATION.md` (sha256 `41ce1903…`) fixed the analysis rules before any GPT-5.6 call on a Stage B
instance. Setup is recorded in `../AMENDMENTS.md` W18 and the run itself in W20.

**gpt-5.5 records.** The gpt-5.5 results are unchanged and are not overwritten:
- `../STAGE_B_RESULTS.md`;
- `../analysis/stageB_cells.json`, which reproduces byte for byte from the current per-run measures, sha256 `ccea0911…`.

## Result

| Cell | What it is | GPT-5.6 Acc@1 (Wilson 95%) | Lang | Chart | Math | gpt-5.5 (reference) |
|---|---|---|---|---|---|---|
| C00 | 1-hop, plain | 15/15 (0.80 to 1.00) | 5/5 | 5/5 | 5/5 | 15/15 |
| C01 | 1-hop, odd-looking correct sibling | 15/15 (0.80 to 1.00) | 5/5 | 5/5 | 5/5 | 14/15 |
| C10 | 5-hop chain + facade lie, plain hop | 15/15 (0.80 to 1.00) | 5/5 | 5/5 | 5/5 | 3/15 |
| C11 | 5-hop chain + facade lie, odd-looking correct hop | 11/15 (0.48 to 0.89) | 3/5 | 3/5 | 5/5 | 4/15 |

**Preregistered contrasts** (Fisher exact, two-sided):

| Contrast | GPT-5.6 | Difference | p |
|---|---|---|---|
| P1: C00 against C10 | 15/15 against 15/15 | 0.00 | 1.0 |
| P2: C01 against C11 | 15/15 against 11/15 | -0.27 | 0.10 |
| P3: 1-hop pooled against 5-hop + lie pooled | 30/30 against 26/30 (0.70 to 0.95) | -0.13 | 0.11 |
| S1: C00 against C01 | 15/15 against 15/15 | 0.00 | 1.0 |
| S2: C10 against C11 | 15/15 against 11/15 | -0.27 | 0.10 |

**Classification under the preregistered rule: ATTENUATED.**
- The 5-hop + lie pooled count is 26/30. That is inside the ATTENUATED band of 13/30 to 26/30, at its top.
- ELIMINATED would have needed 27/30 or more, so one more correct run would have changed the class.
- The P3 difference is not significant.
- No BASELINE_SHIFT: the 1-hop cells are 30/30.
- In substance the result is hard to tell from ELIMINATED. The 95% interval for 26/30 (0.70 to 0.95) spans the 0.90 threshold.
- The excluded stall could not have moved the class towards ELIMINATED. Counted as a miss, it gives 25/30, still ATTENUATED.

**The class hides a different shape from gpt-5.5's.**
- **The plain chain no longer breaks the model.** C10 is 15/15 on GPT-5.6, against 3/15 on gpt-5.5.
- **All four misses are in C11**, the chain with an odd-looking correct hop: 2 in Lang and 2 in Chart, none in Math.
- **On gpt-5.5 the odd hop did nothing**: 18/30 against 18/30.
- **On GPT-5.6 the drop appears only where the odd hop and the chain meet.** The interaction (C11 - C01) - (C10 - C00) is -0.27,
  against +0.13 for gpt-5.5.

Four misses in fifteen are within sampling noise of zero (S2 p = 0.10). They are the GPT-5.6 signal this block can report, not an
established effect. With C00, C01 and C10 all at 15/15, the interaction, P2, P3 and S2 all rest on the same four misses; they are
not independent evidence.

## Execution and identity

| Item | Recorded |
|---|---|
| Model | `gpt-5.6`, the response model in all 61 records; `reasoning_effort: medium` configured and recorded in all 61 |
| Agent and client | mini-swe-agent 2.4.6, litellm 1.98.0, profile `mini-swe-agent-openai-gpt-5-6` (agents.json sha256 `c5dac96e…`, the mechanism-search mxF0 profile) |
| Server | w56, tree sha256 `b62f0a2f…`, byte-identical to w55 and mxF0; external workspace root `/private/tmp/d4jws-w6c3` |
| Prompt and budgets | base prompt sha256 `845e21e7…`; 50 tool calls, 5 test runs, 300 s; protocol identity ok in 61/61, identity diff empty |
| Benchmark | `review/VARIANT_KEY.json` sha256 `e1257e36…`; the 12 Stage B variants unchanged |
| Plans | block 1 `94e481dc…` (40 slots, B1 + B3) and block 2 `e2bc07ef…` (20 slots, B4), generated with seed 1014; slot sequences identical to the gpt-5.5 plans (W18) |
| Freeze | digest `aa1f32f5…` verified before every paid call; Phase 1 re-accepted with smoke run CTV-68B9DE/run-004 ($0.255) |
| Window | block 1 03:49:58 to 04:36:09Z, block 2 04:36:24 to 05:05:42Z on 2026-10-15, back to back under `caffeinate` |
| Health probes | 67, all passed (3.9 to 10.9 s, median 5.0 s) |
| Records | 61: 60 valid behavioural runs (all answered, none timed out) and 1 excluded |
| Integrity | contamination 0/61; source integrity, workspace isolation and scanner ok in 61/61. Four runs had a scanner-flagged call that the scanner cleared with no reason (gpt-5.5's Stage B had 4 such records in 60) |
| Cost | $13.03 for the 61 records ($12.92 valid): B1 $4.78, B3 $4.35, B4 $3.89. The estimate was $11 to $13 with a pause at $25 |

**The one exclusion.** CTV-7C06F2/run-003 (SB-B4-C11, slot 10) is classified `provider_stall` under frozen rule 2.
- It made 6 API calls.
- Its last event was a tool result, after which a request stayed pending for 268.8 s until the kill.
- The slot received its single replacement, CTV-7C06F2/run-004, which was valid (gold rank 1).
- No valid run was replaced. No halt rule fired.

## Per-run outcomes

Each entry is the run's gold rank; for a wrong run, the method ranked first follows in parentheses.

| Instance | Cell | GPT-5.6 runs |
|---|---|---|
| SB-B1-C00, SB-B1-C01, SB-B1-C10 | C00, C01, C10 | 1 ×15 |
| SB-B1-C11 | C11 | 2 (indexOfAnyBut), 1, 3 (indexOfAnyBut), 1, 1 |
| SB-B3-C00, SB-B3-C01, SB-B3-C10 | C00, C01, C10 | 1 ×15 |
| SB-B3-C11 | C11 | 1, 2 (findStackedRangeBounds), 1, 1, 2 (findStackedRangeBounds) |
| SB-B4-C00, SB-B4-C01, SB-B4-C10, SB-B4-C11 | all | 1 ×20 (C11: runs 001, 002, 004, 005 and 006, since run-003 was the excluded stall) |

## Secondary outcomes and process

These come from `GPT55_VS_GPT56_PROCESS.csv` and `process_extra.json`. Medians are per run.

| Measure | GPT-5.6 1-hop | GPT-5.6 5-hop + lie | gpt-5.5 1-hop | gpt-5.5 5-hop + lie |
|---|---|---|---|---|
| MRR | 1.000 | 0.928 | 0.983 | 0.578 |
| gold displayed and read in full | 30/30 | 30/30 | 30/30 | 27/30 |
| gold exposed but misranked | 0 | 4 | 1 | 20 |
| facade ranked first | 0 | 4 | 1 | 22 |
| tool calls | 14.5 | 29.5 | 12 | 19 |
| searches | 11.5 | 25 | 8.5 | 15.5 |
| step of the first gold display | 4 | 23 | 3 | 11 |
| seconds to the first gold display | 9.9 | 40.5 | 9.6 | 30.5 |
| calls after the first gold display | 10 | 6 | 7.5 | 7.5 |
| reasoning tokens | 916 | 1,098 | 1,432 | 1,898 |
| wall time (s) | 41.6 | 73.7 | 54.9 | 82.0 |
| cost per run ($) | 0.149 | 0.280 | 0.286 | 0.429 |

How the two models spent their effort:
- **GPT-5.6 searched more in the chain cells.** It made twice as many tool calls as in its own 1-hop cells, and 10.5 more than gpt-5.5
  made in the chain cells. It reached the gold later: at step 23, against gpt-5.5's step 11.
- **More search is not more reading.** GPT-5.6's chain runs read fewer files than gpt-5.5's (15 against 19.5) and about the same
  number of lines (1,381 against 1,332).
- **It then committed with fewer calls after the gold** (6 against 7.5), and its runs were shorter and cheaper.
- **Reasoning tokens.** GPT-5.6 uses fewer per run than gpt-5.5 in every arm: 1,098 against 1,898 in the chain cells and 916
  against 1,432 in the 1-hop cells. That is a model-level difference, and token counts from two models are not a common scale.
  Against its own 1-hop cells, GPT-5.6's reasoning rises by about a fifth in the chain cells.
- **Wrong against correct, same instances.** The fair comparison for the four wrong runs is the six correct C11 runs on the same
  two bugs (Lang and Chart). Medians, misses against correct runs:
  - tool calls: 34.5 against 30.5;
  - first gold display: step 29 against 26;
  - post-gold calls: 5 against 2.5;
  - reasoning tokens: 828 against 1,004.

  The ranges overlap; two correct runs made 37 calls. With 4 runs against 6, this is description only.

## The four misses: blind labels

Method:
- Two blind labellers looked at each miss, one with a process lens and one with an argument lens. Both used the unchanged
  `construction/stageB/LABEL_BRIEF.md` and were told neither the model nor the cell.
- Blinding to the cell is weaker than that sounds. Each task includes the variant patch, which shows the 5-hop and odd-hop
  structure, and the view directory's name (`traj_views_set2`) marks a second set.
- A disagreement went to an adjudicator, who applied the rules used for the gpt-5.5 blocks.
- Workflow `workflows/label_misses.js`. Raw output is in `../analysis/failure_modes/labels_set2_block1_raw.json` and the finals in
  `labels_set2_final.json`.
- Block 2 had no misses.
- The labellers agreed on all four primaries. One secondary split went to the adjudicator (CTV-E94DC6/run-002).

| Run | Cell | Gold rank (rank 1) | Primary | Secondary | Defensible | Gold named / divergence at gold / lie cited |
|---|---|---|---|---|---|---|
| CTV-5818E6/run-001 | SB-B1-C11 | 2 (indexOfAnyBut) | ENTRY_POINT_BIAS | – | no | yes / yes / no |
| CTV-5818E6/run-003 | SB-B1-C11 | 3 (indexOfAnyBut) | ENTRY_POINT_BIAS | EVIDENCE_INTEGRATION_FAILURE | no | yes / yes / no |
| CTV-E94DC6/run-002 | SB-B3-C11 | 2 (findStackedRangeBounds) | ENTRY_POINT_BIAS | – (adjudicated) | no | yes / yes / no |
| CTV-E94DC6/run-005 | SB-B3-C11 | 2 (findStackedRangeBounds) | ENTRY_POINT_BIAS | EVIDENCE_INTEGRATION_FAILURE | no | yes / yes / no |

What the misses have in common:
- **All four are the gpt-5.5 shape.** The gold is displayed and read in full (frozen measures 4/4). The agent names the gold in its
  final evidence chain and places the first wrong value at the gold's fault line (labels 4/4). It then ranks first the facade the
  test calls.
- **The stated reasons echo gpt-5.5's.** They are "the direct production entry point", "the directly tested method and its
  immediate delegate are the highest-probability modification sites", and "directly tested production method".
- **The W16 extended-view check was not needed.** No miss is coded `gold_exposed = false`, so the frozen and extended readings
  agree.
- **The facade lie is never cited.** No GPT-5.6 evidence chain contains a phrase from it, correct runs included: a phrase scan of
  all 30 chain-cell submissions found none (`lie_scan.json`), and the same holds for gpt-5.5's 30. Whether the lie was read, used or
  discounted is not measured.

## Against the preregistered expectation

- "My expectation is ATTENUATED or ELIMINATED": **met** (ATTENUATED, one run from ELIMINATED).
- "If GPT-5.6 misses, I expect the same shape as gpt-5.5: gold found, fault line on screen, facade ranked first": **met** in 4 of
  4.
- Not anticipated: the misses gathered in the odd-hop chain cell, and the plain chain cell was at ceiling.

## Q1 to Q5 (brief)

1. **Do C10 and C11 still reduce accuracy?** C10 does not (15/15). C11 is lower, 11/15 against 15/15 in C01 (p = 0.10), but that
   difference is not established. Pooled, the chain cells are at 26/30 against 30/30 (p = 0.11).
2. **Replicated, attenuated or eliminated?** ATTENUATED by the preregistered rule, at the boundary with ELIMINATED. The large gpt-5.5
   collapse (7/30) did not transfer. A small residual remains, confined to C11.
3. **Do wrong runs show gold found, faulty line identified and facade ranked first?** Yes, all 4.
4. **Does GPT-5.6 recover?** Largely. It recovers fully in C10 (3/15 to 15/15, p = 1.1e-5) and partly in C11 (4/15 to 11/15,
   p = 0.027). Under the rule that is partial recovery (ATTENUATED).
5. **Does it spend more effort but recover?**
   - **Search.** It makes more search calls: about 30 tool calls per chain run against gpt-5.5's 19, twice its own 1-hop count. It
     does not read more: fewer files, the same lines.
   - **After the gold.** It reaches the gold later, then commits with fewer post-gold calls.
   - **Reasoning.** Its reasoning tokens are below gpt-5.5's in every arm, a model-level offset. Against its own 1-hop cells they
     rise by about a fifth.
   - **Cause.** Whether the extra search is what makes it recover cannot be told from two models.

## Decision (preregistered rule)

ATTENUATED: "the decomposition is still recommended, as the place to locate the capability gap". It is proposed, not launched. The
rule does not say on which model.

## Added interpretation (not preregistered)

The decomposition was described after the gpt-5.5 block (`../SUPERVISOR_UPDATE_STAGE_B.md`) as follows:

- every cell has 5 hops;
- hop placement is varied: inside the facade's own class, or dispersed across five hosts;
- the lie is either present or absent;
- 60 runs at about $0.43 each.

The preregistration's shorthand also lists "hop distance", which the described design does not vary.

Only one of its four cells is the C10 condition: five dispersed hops with the lie, which scored 15/15 on GPT-5.6. The other three
cells are untested on GPT-5.6. I expect them near ceiling, on the assumption that removing a component does not make the task
harder.

On gpt-5.5 the decomposition would show which component drives its -0.73 drop. It bears on the gap with GPT-5.6 only if GPT-5.6 is
at ceiling in every cell, which is expected, not measured. Choosing gpt-5.5 for it is my suggestion, not part of the rule. The full
argument is in `GPT55_VS_GPT56_ANALYSIS.md`.
