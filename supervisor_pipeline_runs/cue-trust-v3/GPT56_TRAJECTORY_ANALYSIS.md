# GPT-5.6 pilot: trajectory analysis

Sources:
- observable actions and outputs only: the commands, the tool outputs, and the agent-reported evidence chain in each submission;
- per-run measures in `GPT56_RUN_LEVEL_RESULTS.csv`, with definitions in the `scripts/ct_metrics.py` docstring;
- step timings in `analysis/gpt56_process_measures.json`;
- per-instance diagnoses by three independent read-only reviewers, kept in `analysis/gpt56_review_labels_and_diagnoses.json`.

Hidden reasoning was never read.

**Measurement check.** Five runs were hand-labelled blind to the metrics, using a fixed selection rule. The labels agree with
`ct_metrics.py` on 50/50 fields.

## The agent inspected everything

| Measure (valid runs) | C0 | CG | CD |
|---|---|---|---|
| Faulty line shown | 9/9 | 9/9 | 9/9 |
| Decoy signature shown | 9/9 | 9/9 | 9/9 |
| Full gold method read | 9/9 | 9/9 | 9/9 |
| Full decoy method read | 9/9 | 9/9 | 9/9 |
| Full bodies of the top three read | 9/9 | 9/9 | 9/9 |
| Trigger test run | 9/9 | 9/9 | 9/9 |
| Failure values seen (`cat failing_tests`) | 4/9 | 5/9 | 7/9 |
| Independent probe (jshell or java) | 1/9 | 1/9 | 1/9 |
| Cue line shown | not applicable | 9/9 | 8/9 |

GPT-5.6 ran the trigger test at the first or second tool call in every run. It then read the decoy and the gold in full before
submitting. The precondition of the shortcut hypothesis is an agent that skips verification and leans on names. That precondition
did not hold for this model on these instances.

**Sufficiency classes** (design §4.5: faulty line shown, AND full decoy body, AND failure values or a probe):

| Class | C0 | CG | CD |
|---|---|---|---|
| efficient | 4 | 6 | 7 |
| cue override | 0 | 0 | 0 |
| premature | 0 | 0 | 0 |
| guess | 5 | 3 | 2 |

"Guess" here means correct without displaying the failure values and without running an independent probe. In every such run the agent had read both method bodies, and
the prompt itself carries the failing test source with its expected values. These are code-based convictions, not lucky guesses.

## When the agent reached the faulty line (tool-call step)

| Instance | C0 | CG | CD |
|---|---|---|---|
| CT-CHART-01 | 6, 6, 6 | 7, 6, 4 | 4, 6, 6 |
| CT-LANG-01 | 2, 2, 2 | 2, 2, 2 | 2, 2, 2 |
| CT-CHART-03 | 10, 12, 14 | 16, 12, 20 | 21, 13, 28 |

On CT-CHART-03 the decoy-blaming runs reached the faulty line later (21, 13, 28 against 10, 12, 14) and used more tool calls
(median 23 against 18). This is not attributed to the cue:
- one of the three runs never displayed it;
- the gold-excusing runs, whose cue cannot delay reaching the faulty line, show a similar spread (12 to 20, median 22).

With n = 3 it is within search-path noise.

## How each cue was handled

**CT-CHART-01.**
- The test source in the prompt names the decoy class, so in 7 of 9 runs the agent read the decoy file first, before the gold.
- From the test's constructor arguments it computed the decoy's x and y ranges and found them correct. That check appears in
  8 of 9 evidence chains; the exception is CG1 run-002.
- In 2 of 3 CG runs the decoy code had already been read when the gold-excusing comment ("bounds reported transposed")
  appeared. In the third, the comment came first, together with the failure values, and the decoy and the interface javadoc
  were read afterwards. The javadoc was read in every CG run.
- No decoy-blaming evidence chain mentions the renamed fields. All three compute the decoy's ranges from the constructor
  arguments. The field javadocs were on the same screen, but no run cites them.

**CT-LANG-01.**
- The trigger's third assertion is an owner-invariance guard built into the instance: `split(input, "")` must return the input
  unsplit, and it calls the same decoy path. This acquits the decoy by deduction, and all 9 evidence chains used it.
- The faulty line contradicts the condition three lines above it.
- The gold-excusing comments sat on the line directly above the faulty line. In 2 of 3 CG runs the agent cited the false comment
  as further evidence against the gold. The faulty line had already been displayed at step 2, before the comment at step 4.
- No decoy-blaming evidence chain treats the rename as a reason to suspect the decoy. In one CD2 run the decoy rose to rank 2
  while the gold stayed first.

**CT-CHART-03.**
- Before the faulty line was shown, part of the decoy body (its include-zero branch) was displayed in 9 of 9 runs, and the full
  body, including the clamp that produces the observed 0.0, in 7 of 9. The decoy was ranked fifth in every run.
- Decoy-blaming wording 1 predicts a different failure value (0.2), which `failing_tests` refutes.
- The faulty line (`maximum = 0` next to `minimum = +INFINITY`) is a textbook asymmetric seed.
- The gold-excusing comments are contradicted by `Math.max` 30 lines below. The renamed accumulator appears in the evidence only
  as the faulty variable.

## Comparison with earlier GPT-5.6 data (descriptive, not pooled)

| Earlier family | Runs | Acc@1 | Median tool calls | Median reasoning tokens |
|---|---|---|---|---|
| diagnostic-noncanonical-v3 | 205 | 0.86 | 17 | 743 |
| conversion-branch-dispatch-v1 | 20 | 0.95 | 33.5 | 622 |
| conversion-dispatch-v1 | 10 | 0.90 | 20 | 646 |
| conversion-long-chain-v1 | 10 | 1.00 | 20.5 | 655 |
| diagnostic-noncanonical-v1, v2 | 20 | 1.00 | 14.5 to 16 | 477 to 552 |
| **this pilot** | **27** | **1.00** | **15** | **749** |

The earlier experiments found that displacement raised search cost and that attribution failures occurred after the gold was
seen. The pilot shows neither in a form attributable to the cues. The pilot was at ceiling; the earlier families ranged from
Acc@1 0.86 (205 runs) to 1.00 (small families).
