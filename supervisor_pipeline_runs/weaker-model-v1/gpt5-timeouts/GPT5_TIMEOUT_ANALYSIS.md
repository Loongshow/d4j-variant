# What happened in the ten gpt-5 timeouts?

This analysis was revised on 2026-10-15 after two rounds of independent verification, each with a numbers lens and an inference
lens (`analysis/verification/gpt5_timeout_docs_round1.json` and `..._round2.md`). The first version is kept at
`analysis/verification/backup/GPT5_TIMEOUT_ANALYSIS.v1.md`. The revision corrects four things:

- **Time attribution.** Each run's time is no longer attributed by an order-dependent category split.
- **Speed.** The analysis now accounts for the drop in provider speed. That drop confounds the comparison with completed runs, all
  of which ran before it.
- **Slow period.** The slow period is now defined by measured speed rather than by where the timeouts fall.
- **Run-level readings.** Two runs of the same shape are now read the same way.

## Answer for the supervisor

gpt-5 ran close to the limit even when it succeeded: its 17 completed runs took a median of 238 s of the 300 s budget. In 9 of the
10 timeouts the agent had already displayed the faulty method and read it in full. Each timeout is a run in which some added cost
pushed it past 300 s.

**Slow serving by the provider: 6 timeouts.** In slots 15 to 25 (14:05 to 15:05Z on 2026-10-13), every run whose speed could be
measured was served below 50 output tokens per second. Before that period the median was 69.4. On the six timeout instances, 6 of
6 runs in that period timed out, against 4 of 12 outside it. On the other three instances, 0 of 5 in the period timed out.

- None of the six had produced more output before the kill than its completed comparator produced before submitting.
- Three also lost much of their time to malformed commands. gpt-5 often ends a shell command with a stray `}`, and most such
  commands fail.
- Slower serving is a sufficient account of these six, but it does not prove they would have committed.
- One of them, CTV-21982A/run-004, is a boundary case. Its output equalled its comparator's, and both coders labelled it found but
  not committed.

**Normal speed: 4 timeouts.** These ran at 62 to 70 tok/s, and they are where the hypothesis can be examined.

- **CTV-E04F64/run-005** had committed. The validator rejected its ranking because two overloads gave the same method name twice,
  and the run timed out while rewriting it.
- **CTV-7CE456/run-002, CTV-E04F64/run-004 and CTV-E65CBB/run-002** spent 168 to 193 s in heavy-reasoning calls after finding the
  gold, against 117 to 150 s for their comparators. By the kill, each was already 82 to 128 s past the point, measured
  from the gold, at which its comparator had committed. Two of the three were also in malformed-command loops, and every one of their heavy calls also
  emitted a malformed command. Part of that reasoning may therefore have gone to repairing commands; the reasoning text is hidden.

**Is ambiguity a plausible cause? NOT SUPPORTED,** as an explanation of why these 10 runs timed out rather than completed.

- For 7 of 10, an account without non-commitment is sufficient: the six slow-period runs and the validator rejection.
- The brief's two discriminating criteria are negative on everything that can be observed:
  - Time exploring competing suspects did not increase: calls after the gold 5 against 7; declared alternatives newly inspected,
    0 against 0.
  - No behaviour tied to ownership, entry-point or convention uncertainty appeared: no ambiguity-family label in 20 blind coder
    labels.
- In the three heavy-reasoning runs, the behaviour is compatible with the hypothesised non-commitment. Whether the ambiguity
  caused it is INCONCLUSIVE:
  - every gpt-5 run, comparators included, is on an ambiguity instance, so there is no control;
  - the reasoning is hidden.

A reader who weighs those three more heavily could call the overall answer INCONCLUSIVE. The verdict does not say whether the
ambiguity lengthens gpt-5's runs in general.

## The ten runs

The ten runs are listed in `GPT5_TIMEOUT_RUN_INDEX.csv`. They come from the gpt-5 block:

- server w50, served model `gpt-5-2025-08-07`, `reasoning_effort: medium`;
- the frozen protocol: 50 tool calls, 5 tests, 300 s.

The block produced 32 run records:

- **27 valid:** 17 answered, all with the gold ranked first, and 10 behavioural timeouts.
- **5 excluded** by the frozen classifier's provider-stall rule 2: the run's last event is a tool result and more than 60 s were
  left before the kill.
  - CTV-E04F64/run-001 and run-002, CTV-E65CBB/run-001, all on 2026-10-12. CTV-E65CBB/run-001 is the run that the W3 machine-sleep
    incident stretched to 2,373 s of wall time.
  - CTV-B68398/run-002 and CTV-21982A/run-003, both in the slow period.

The ten timeouts are exactly the included runs with status `timeout`. Every one has these properties:

- 300.0 s of wall time;
- ledger verdict valid;
- source integrity ok and workspace isolation ok;
- no sleep or wake event in the macOS power log during the run;
- a passing health gate before launch. The gate recorded one probe for 8 of the 10 and three probes for CTV-E65CBB/run-002 and
  CTV-21982A/run-004.

Probe walls before launch were 8.5 to 18.2 s before most runs, but 28.2 to 66.9 s before five of the timeouts (slots 16 and 19
to 22) and before one completed run (slot 15, 40.6 s).

Some runs sit near the classifier's 60 s boundary. CTV-7CE456/run-002 had a request pending for 59.4 s at the kill, so it is
behavioural by 0.6 s. Three others had 36.8 to 39.2 s pending. These are the timeline's final gaps; the ledger records 36.7 s for
CTV-21982A/run-002.

| Instance (recipe) | Timeouts | Completed on the same instance |
|---|---|---|
| HO-HA-COMPRESS-01 (entry point) | CTV-9CE7EA/run-003 | run-001, run-002 |
| HO-HA-JACKSONCORE-01 | CTV-E04F64/run-004, run-005 | run-003 |
| HO-HA-MATH-01 | CTV-9EB2B7/run-003 | run-001, run-002 |
| HO-HB-MATH-01 (sink) | CTV-E65CBB/run-002, run-004 | run-003 |
| HO-HC-JACKSONCORE-01 (convention) | CTV-7CE456/run-002, run-003 | run-001 |
| HO-HC-MATH-01 | CTV-21982A/run-002, run-004 | run-001 |

The other three instances (HB-COMPRESS, HB-LANG, HC-LANG) completed 9 of 9. That includes 5 runs in the slow period, which were lighter
(median 7,089 output tokens).

## Method

1. **Timelines** (`scripts/gpt5_timeline.py`, which writes `GPT5_TIMEOUT_TIMELINES.csv` and `timeline_steps.json`) are built from
   the recorded timestamps: the harness timer start, each model request's creation time and each tool result's timestamp.
   - The script runs the frozen `mx_metrics.py` display and command definitions verbatim.
   - Its end-of-run values reproduce the frozen per-run measures exactly: tool calls, faulty line shown, gold read in full,
     evidence displayed.
2. **Comparison** (`scripts/gpt5_timeout_compare.py`, writing `compare.json` and `GPT5_TIMEOUT_MATCHED_COMPARISON.md`) pairs each
   timeout with the completed runs on its own instance, and pools all runs with Cliff's delta. After-gold measures exclude the one
   run that never reached the gold.
3. **Workload and speed** (`scripts/gpt5_workload_speed.py`) separate the model's own work from the provider's serving speed.
   - Model side: calls, output tokens and reasoning tokens.
   - Provider side: tokens per second on long calls, and waits on short calls.
   - The same script writes the time decomposition (exclusive and non-exclusive), the malformed-command and test tallies, the
     post-gold reasoning and the counterfactual.
   - `scripts/gpt5_timeout_facts.py` computes every other count quoted in these documents into `facts.json`, including the speed-defined
     slow period, the post hoc output comparison, the counterfactual's calibration and the sensitivity checks.
4. **Blind coding** (`GPT5_TIMEOUT_BLIND_LABELS.json`, brief `TIMEOUT_LABEL_BRIEF.md`) used two independent coders per run, one
   with a time-use lens and one with an evidence lens.
   - The coders saw only the brief, the task file, the safe trajectory view (hidden reasoning excluded), the timing table and the
     variant patch.
   - A third coder adjudicated the four runs where they disagreed on the primary label, the end state or evidence sufficiency. The
     two coders agreed on the primary label in 7 of 10 runs.
   - Limits: the brief's examples for OTHER named the causes later found, and the timing table carried no speed baseline.
5. **Bounded replays** (brief section 8; `replays/`, `scripts/gpt5_replay_next_action.py`) sent one request each from the exact
   pre-timeout state, for three runs selected by a rule fixed before any call.
   - They are diagnostic only and never scored.
   - Recorded usage was 62,275 prompt and 5,207 completion tokens, about $0.13 at gpt-5 list prices without cache discounts. No
     separate charge was recorded.

## Findings

- **The gold had usually been read.** In 9 of 10 timeouts the faulty line was displayed, the gold was read in full and the declared
  evidence was on screen. The exception is CTV-9EB2B7/run-003, which never reached the gold. The coders still judged one of the
  nine, CTV-E65CBB/run-004, to be searching.
- **Exploration did not grow, but reasoning did.** Medians over the 9 timeouts that reached the gold, against the 17 completed
  runs:

  | Measure after the gold | Timeouts | Completed | Delta |
  |---|---|---|---|
  | calls | 5 | 7 | -0.16 |
  | methods newly inspected | 13 | 15 | 0.0 |
  | reasoning tokens | 10,560 | 5,184 | +0.31 |
  | model time | 189 s | 98 s | +0.59 |
  | model time re-timed at the pre-window speed | 144 s | 96 s | +0.28 |

  Post-gold reasoning roughly doubles at the median. Re-timing removes about half of the model-time gap, which is slower serving;
  the rest is more model work.

  Within instances the picture is mixed: 6 of 9 timeouts inspected more methods than their comparator, and 5 of 9 reasoned more.
  Several timeouts read whole off-path files. For example, 50 of CTV-E04F64/run-004's 56 new methods come from two such files
  printed with python after `sed` failed. The coders read these reads as confirmation or broad reading, not as competing owners.
- **The confound.** All 8 comparators ran at normal speed, before 13:47Z. On the six timeout instances, 6 of 6 runs in the slow
  period timed out and 4 of 12 outside it did.
- **Two periods.** The 50 tok/s threshold is post hoc, but the gap between slow-period and other speeds (49.3 against 58.9 tok/s)
  makes it robust.
  - Slow period, 6 timeouts: 10.1 to 49.3 tok/s.
  - Normal speed, 4 timeouts: 61.6 to 69.6 tok/s.

  The comparison of output before the kill with the comparators' output before submission separates the same two groups. It is a
  consistency check, not independent evidence, for two reasons:
  - Every timeout ran 300 s, so its output tracks its throughput.
  - Against a pooled baseline instead of same-instance comparators, 7 of 10 would count as producing more.
- **Where the time went** (non-exclusive totals; per-run table in `GPT5_AMBIGUITY_HYPOTHESIS.md`):
  - **Malformed commands.** Cheap malformed calls in 5 timeouts: CTV-9CE7EA/run-003 207 s, CTV-9EB2B7/run-003 227 s,
    CTV-7CE456/run-003 95 s, CTV-E65CBB/run-002 72 s and CTV-E04F64/run-004 45 s. In the last two, every heavy post-gold call also
    emitted a malformed command. Malformed commands also occur in 11 of 17 completed runs.
  - **Slow serving.** CTV-E65CBB/run-004 had 211 s of it and CTV-9EB2B7/run-003 had 178 s: 5 calls each, waiting 21 to 54 s for 30
    to 285 tokens. No completed run has such calls. Seven further calls of 30 s or more, all in the slow period, returned 631 to
    1,425 tokens at 10 to 38 tok/s.
  - **Deliberation.** Calls of 1,500 or more reasoning tokens occur in 7 timeouts, totalling 110 to 235 s. Completed runs on HA and
    HB reach 117 to 150 s as well, so deliberation is not specific to particular instances.
- **Blind codes.**
  - Primary labels: OTHER 5 (broken command format, slow responses, rejected submission), GOLD_FOUND_BUT_NOT_TRUSTED 3,
    OVER_VERIFICATION 1, TOOL_LOOP 1.
  - No ownership, entry-point or convention label appears in any of the 20 coder labels.
  - Alternation between explanations was seen in 1 of 20.
  - Two of the three GOLD_FOUND_BUT_NOT_TRUSTED runs (CTV-21982A/run-002 and run-004) were in the slow period, at 34 and 48.5 tok/s.
    Neither reasoned more than 9% above its comparator. The coders had no speed baseline, so these labels may partly be a reading
    of slowness.
- **Replays** (one sample each):
  - **CTV-E04F64/run-005.** The replay submitted a ranking with the gold first, in 35 s; the run had committed and was rewriting
    its rejected submission. Whether the validator would have accepted the replayed ranking was not checked.
  - **CTV-7CE456/run-002.** The replay read another file rather than submitting, returning in 19.8 s. The original request had
    been pending for at least 59.4 s. At the run's own speed that is at least about 4,100 tokens: submission-sized,
    deliberation-sized, or a slowly served call, and the data cannot tell which. This one sample points against both coders' end
    state ("plausibly writing the answer") but cannot overturn it.
  - **CTV-E65CBB/run-002.** The replay issued another 48-character shell command. Its content was not recorded, so the replay does
    not show whether the command loop continued.

## Protocol findings to record (not caused by the benchmark)

- **Login-shell tests fail.** gpt-5 runs some tests through a login shell (`bash -lc`). All 15 such test commands failed with
  "Failed to parse Java version"; the frozen classifier counts 32 test steps in all.
  - gpt-5.5 issued 27 test commands on the same instances, none through a login shell.
  - 3 timeouts ran no test at all.
  - 7 of 10 timeouts and 11 of 17 completed runs never had a successful test.
- **Stray brace.** gpt-5 appends a stray `}` to its command strings in 16 of 27 runs. 197 of the 217 such commands failed.
- **Overload rejection.** The submission validator rejects a ranking that lists the same method name twice, which happens with
  two overloads. This hit 3 gpt-5 runs. One of them, CTV-E04F64/run-005, timed out while resubmitting.

These three are interactions between gpt-5 and the harness, and they make the W4 verdict on gpt-5 ("operationally too weak at the
frozen budget") partly a harness verdict. So does the provider's speed on 2026-10-13: 6 of the 10 timeouts fall in the slow period.
None of these is an ambiguity effect. No harness change is proposed here, and the frozen protocol is unchanged.

## What would test the hypothesis properly (not run)

The hypothesis needs a same-bug control of the ambiguity instances without the ambiguity, run under conditions that remove the
operational losses:

- a stable provider speed, or the analysis done on model-side work;
- a fixed login-shell environment;
- a budget that does not count the submission call.

The quantity to compare would be model-side work after the gold (reasoning tokens and calls), not wall time. This is a new
benchmark design, so per the brief it is only proposed.

## Files

| File | Contents |
|---|---|
| `GPT5_TIMEOUT_RUN_INDEX.csv` | the ten runs, with provenance and checks |
| `GPT5_TIMEOUT_TIMELINES.csv` | all 27 runs, timeouts and completed |
| `GPT5_TIMEOUT_MATCHED_COMPARISON.md` | matched and pooled comparisons, serving speed, decomposition, environment findings |
| `GPT5_TIMEOUT_BLIND_LABELS.json` | coder labels and adjudications |
| `GPT5_AMBIGUITY_HYPOTHESIS.md` | measures A to H, per-run groups and the verdict |

Data: `timeline_runs.json`, `timeline_steps.json`, `compare.json`, `workload_speed.json`, `time_decomposition.json`,
`call_waits.json`, `malformed_commands.json`, `post_gold_reasoning.json`, `facts.json`, `replays/`, `label_inputs/`.
