# gpt-5 timeouts against completed runs on the same instance

Revised 2026-10-15 after independent verification. The first version is kept at
`analysis/verification/backup/GPT5_TIMEOUT_MATCHED_COMPARISON.v1.md`. It had two flaws: it attributed time with a category split
whose result depends on the order of checking, and it left out the provider-speed confound. The verifier reports are in
`analysis/verification/gpt5_timeout_docs_round1.json`.

Data sources:

- `timeline_runs.json` and `timeline_steps.json`, built by `scripts/gpt5_timeline.py` from the recorded timestamps, using the
  frozen display and command definitions of `scripts/mx_metrics.py`;
- `compare.json`, from `scripts/gpt5_timeout_compare.py`;
- `workload_speed.json`, `time_decomposition.json`, `malformed_commands.json`, `post_gold_reasoning.json` and `call_waits.json`,
  from `scripts/gpt5_workload_speed.py`;
- `facts.json`, from `scripts/gpt5_timeout_facts.py`.

All 27 valid gpt-5 runs share the prompt, the model (`gpt-5-2025-08-07` as served), `reasoning_effort: medium`, the budgets and
the server code. Each of the six instances with a timeout also has completed runs, so every timeout has a comparator on its own
instance; four of those instances have only one. The comparison is descriptive only: 10 timeouts against 17 completed runs, 8 of
which are on the timeouts' instances.

Effect size is Cliff's delta, timeout minus completed; +1 means every timeout is higher. After-gold measures exclude
CTV-9EB2B7/run-003, which never reached the gold.

## The confound: every comparator ran at normal speed

Every completed run on the six timeout instances ran before 13:47Z on 2026-10-13. The provider then served gpt-5 more slowly for a
while.

**Defining the slow period.** The first version of this analysis cut a "window" at 13:47Z. That boundary was set by the first late
timeout, so the timeouts themselves defined it. This version defines the slow period by measured speed instead: the span of slots
in which a run's median speed on calls of 500 or more output tokens was below 50 tok/s (`facts.json`, `slow_period_by_speed`).

- **Bounds:** slots 15 to 25, with runs starting between 14:05 and 15:00Z.
- **Speeds:** 10.1 to 49.3 tok/s for the 9 measurable runs in the period, against 58.9 to 81.6 tok/s for every other run.
- **Outcomes:** on the six timeout instances, 6 of 6 runs in the slow period timed out, against 4 of 12 outside it. On the other
  three instances, 0 of 5 in the period timed out.
- **Submission calls:** the completed runs' submission calls took a median of 45.0 s before 13:47Z (12 runs) and 94.8 s inside the
  period (5 runs; 46.2 to 120.4 s).

A wall-clock comparison between a timeout and its comparator therefore mixes the model's work with the provider's speed. The tables
below report the two separately. Model-side measures are calls, methods, output tokens and reasoning tokens; serving-side measures
are tokens per second and waits.

## Pooled comparison

| Measure | Timeouts (median) | Completed (median) | Cliff's delta |
|---|---|---|---|
| model calls | 17.5 | 22 | -0.32 |
| exploration tool calls (excl. submission) | 17.5 | 21 | -0.27 |
| time to first gold display (s) | 69.5 | 50.4 | +0.27 |
| time to faulty-line display (s) | 69.5 | 50.4 | +0.27 |
| time to full gold read (s) | 69.5 | 50.4 | +0.27 |
| time to decisive evidence (s) | 39.8 | 48.6 | +0.25 |
| time to first test (s) | 17.5 | 10.6 | +0.24 |
| calls up to the first gold display (inclusive) | 12 | 16 | -0.21 |
| calls after gold | 5 | 7 | -0.16 |
| searches after gold | 1 | 1 | -0.07 |
| reads after gold | 3 | 3 | -0.05 |
| tests after gold | 0 | 0 | -0.07 |
| methods newly inspected after gold | 13 | 15 | +0.00 |
| declared alternatives inspected after gold | 0 | 0 | +0.03 |
| revisit reads | 3 | 5 | -0.33 |
| repeated identical commands | 0 | 0 | -0.12 |
| median per-call wait (s, non-test) | 3.5 | 2.7 | +0.38 |
| longest single wait (s) | 58.5 | 37.5 | +0.55 |
| time in test steps (s) | 4.2 | 4.2 | +0.01 |
| reasoning tokens (total) | 10,624 | 5,888 | +0.25 |
| reasoning tokens per call (median) | 0 | 0 | -0.12 |
| seconds per 1k output tokens | 21.5 | 18.6 | +0.22 |
| provider probe wall before launch (s) | 22 | 11.9 | +0.54 |
| tool calls per minute | 3.5 | 7.3 | -0.61 |
| exploration tool calls per minute (excl. submission) | 3.5 | 6.9 | -0.58 |
| reasoning tokens after gold (excl. final call) | 10,560 | 5,184 | +0.31 |
| output tokens after gold (excl. final call) | 11,268 | 5,843 | +0.31 |
| deliberation calls after gold (>= 1,500 reasoning tokens) | 3 | 1 | +0.29 |
| model time after gold (s) | 189.1 | 97.5 | +0.59 |

What the pooled table shows:

- **Searching.** The timeouts did not search, read, test or revisit more. They made fewer calls overall and after the gold. After
  the gold they inspected about as many new methods (13 against 15), and they revisited less.
- **Reasoning.** They produced more reasoning and output tokens after the gold (delta +0.31) and spent more model time after it
  (delta +0.59). That time mixes extra work with slower serving.
- **Pace.** The lower pace (3.5 against 6.9 exploration calls per minute) and the longer waits reflect both slower serving and heavy
  calls. Two normal-speed timeouts, CTV-7CE456/run-002 and CTV-E04F64/run-005, also ran at only 3.4 to 3.6 calls per minute.

## Matched comparison

Each timeout against the completed runs on its own instance; the completed values are medians. "Period" is the speed-defined
slow period above (slow) or the rest of the block (normal). The output column compares the run's output before the kill with the
comparators' output before their submission call. It is a consistency check rather than independent evidence:

- Every timeout ran 300 s, so its output tracks its throughput.
- The comparison depends on the baseline. Against the pooled median of all completed runs, 7 of the 10 would count as having
  produced more.

| Instance | Timeout run | Period | Speed tok/s (TO vs CO) | Output before kill vs CO before submission | Calls after gold | Methods after gold | Reasoning after gold | Gold to kill vs CO gold to submission (s) | Final pending (s) |
|---|---|---|---|---|---|---|---|---|---|
| HA-COMPRESS-01 | CTV-9CE7EA/run-003 | slow | 22.3 vs 67.2 | 5,947 vs 9,172 (-35%) | 5 vs 12 | 31 vs 23.5 | 2,752 vs 5,152 | 140.4 vs 96.0 | 6.9 |
| HA-JACKSONCORE-01 | CTV-E04F64/run-004 | normal | 65.3 vs 59.6 | 14,168 vs 10,730 (+32%) | 14 vs 2 | 56 vs 3 | 10,560 vs 8,512 | 230.5 vs 119.1 | 37.8 |
| HA-JACKSONCORE-01 | CTV-E04F64/run-005 | normal | 61.6 vs 59.6 | 14,679 vs 10,730 (+37%) | 6 vs 2 | 4 vs 3 | 12,672 vs 8,512 | 255.1 vs 119.1 | 39.2 |
| HA-MATH-01 | CTV-9EB2B7/run-003 | slow | 19.2 vs 76.3 | 2,236 vs 10,278 (-78%) | – vs 5.5 | – vs 0.5 | – (no gold) | – | 18.1 |
| HB-MATH-01 | CTV-E65CBB/run-002 | normal | 62.5 vs 58.9 | 15,696 vs 12,041 (+30%) | 33 vs 7 | 21 vs 13 | 13,056 vs 10,752 | 268.3 vs 186.3 | 7.9 |
| HB-MATH-01 | CTV-E65CBB/run-004 | slow | 10.1 vs 58.9 | 1,061 vs 12,041 (-91%) | 2 vs 7 | 15 vs 13 | 576 vs 10,752 | 121.6 vs 186.3 | 14.1 |
| HC-JACKSONCORE-01 | CTV-7CE456/run-002 | normal | 69.6 vs 81.6 | 16,759 vs 12,326 (+36%) | 8 vs 6 | 8 vs 25 | 14,080 vs 9,536 | 259.3 vs 131.3 | 59.4 |
| HC-JACKSONCORE-01 | CTV-7CE456/run-003 | slow | 49.3 vs 81.6 | 10,512 vs 12,326 (-15%) | 2 vs 6 | 8 vs 25 | 3,648 vs 9,536 | 89.0 vs 131.3 | 17.3 |
| HC-MATH-01 | CTV-21982A/run-002 | slow | 34.0 vs 68.4 | 9,558 vs 13,043 (-27%) | 3 vs 6 | 6 vs 12 | 6,464 vs 10,176 | 205.7 vs 151.0 | 36.8 |
| HC-MATH-01 | CTV-21982A/run-004 | slow | 48.5 vs 68.4 | 13,032 vs 13,043 (-0.1%) | 5 vs 6 | 13 vs 12 | 11,136 vs 10,176 | 256.3 vs 151.0 | 3.6 |

### Slow period (6 runs)

- **Speed and output.** They were served at 10.1 to 49.3 tok/s, against their comparators' 58.9 to 81.6. Before the kill they had
  produced 0.1 to 91% less output than their comparators did before submitting.
- **Command loops.** Three also spent much of their time in malformed-command calls with little reasoning: CTV-9CE7EA/run-003 (18
  calls, 207 s), CTV-9EB2B7/run-003 (12 calls, 227 s) and CTV-7CE456/run-003 (16 calls, 95 s).
- **Reading.** Slower serving, compounded by command loops in three, is a sufficient account of these six timeouts. It does not
  show that they would have committed, and non-commitment is not ruled out.
- **The boundary case.** CTV-21982A/run-004 had output equal to its single comparator's, and that comparator took 282 s. It spent
  186 s in heavy post-gold calls, and both coders labelled it found but not committed.

### Normal speed (4 runs)

These four were served at 61.6 to 69.6 tok/s, as fast as or faster than their comparator, except CTV-7CE456/run-002 (69.6 against
81.6). They are the runs in which the non-commitment hypothesis can be examined.

- **CTV-E04F64/run-005: committed.** It made a full submission 153 s after the gold, against its comparator's 119 s. The validator
  rejected it with `duplicate_method` (one method named twice, from two overloads), and the run timed out while rewriting.
- **CTV-7CE456/run-002: no malformed commands.** It spent 193 s in heavy calls after the gold, against its comparator's 119 s, and
  its reasoning after the gold was 48% above the comparator's. Late in the run it re-read the gold, the entry point and a decoy
  with line numbers, which both coders read as gathering citations. Its final request had been pending for 59.4 s at the kill.
- **CTV-E04F64/run-004: heavy calls inside a command loop.** It spent 168 s in heavy calls after the gold, against its
  comparator's 117 s, and every one of them also emitted a malformed command. It also had 16 cheap malformed calls (45 s); 18 of
  its 19 malformed commands failed. Its 56 newly inspected methods (against 3) come mostly from two off-path files printed whole
  with python after `sed` failed: ParserMinimalBase and JsonStringEncoder, 50 methods.
- **CTV-E65CBB/run-002: the same pattern, before 13:47Z.** It spent 177 s in heavy calls after the gold, against its comparator's
  150 s, all of them also emitting malformed commands, plus 25 cheap malformed calls (72 s). All 31 of its malformed commands
  failed. After the gold it also read IntervalsSet and the 3-D Segment, which the coders marked off-path.

For the last two, part of the heavy reasoning may have gone to repairing commands; the reasoning text is hidden.

## Long waits

Of 600 non-test model calls, 52 waited 30 s or more, 33 of them in timeout runs. They are of three kinds (`facts.json`,
`long_waits_ge30s`):

- **Deliberation calls** (38 of the 52) carry 1,500 or more reasoning tokens. They ran at 28.7 to 83.1 output tokens per second,
  and occur in completed runs as well as timeouts.
- **Slow-serving calls** (7 of the 52) produced fewer than 300 output tokens. Counting every such call that waited 20 s or more,
  there were 10, returning 30 to 285 tokens in 21.3 to 53.8 s (1.0 to 9.1 tok/s). They occur only in two timeouts,
  CTV-9EB2B7/run-003 and CTV-E65CBB/run-004 (slots 20 and 21), five in each.
- **Neither** (7 of the 52): 631 to 1,425 output tokens with fewer than 1,500 reasoning tokens, at 10.1 to 38.0 tok/s. All 7 are
  in the slow period: four in CTV-9CE7EA/run-003, one each in CTV-9EB2B7/run-003, CTV-E65CBB/run-004 and the completed
  CTV-B68398/run-003. They are ordinary calls served slowly.

## When the timeouts happened

The block ran in two sessions.

- **2026-10-12.** All 7 valid runs completed. The frozen classifier excluded three more records from that day:
  - CTV-E04F64/run-001 and run-002, provider stalls with final gaps of 131.2 and 87.5 s;
  - CTV-E65CBB/run-001, stretched by the W3 machine sleep, final gap 66.2 s.
- **2026-10-13, slots 7 to 12.** 1 of 6 runs timed out: CTV-E65CBB/run-002, at normal speed.
- **2026-10-13, slots 13 to 26 (13:47 to 15:10Z).** 9 of 14 runs timed out.
  - Six of those 9 fall in the slow period (slots 15 to 25).
  - Three ran at normal speed: slots 13, 14 and 26.
  - Two further records in these slots were excluded as provider stalls: CTV-B68398/run-002 (91.6 s) and CTV-21982A/run-003
    (108.7 s).

Health-probe walls before launch reached 28 s or more only at slots 15, 16 and 19 to 22, probes taken between 14:03 and 14:43Z
(28.2 to 66.9 s). Slot 15 was a completed run with a 40.6 s probe. At the other slots from 13 to 26, probes took 11.1 to 17.7 s.

The driver's health gate recorded one probe before 8 of the 10 timeouts, and three before CTV-E65CBB/run-002 and
CTV-21982A/run-004. Probe wall is a coarse signal and in-run speed is the better measure: the three normal-speed timeouts at slots 13,
14 and 26 had normal probes and normal speed.

The macOS power log shows no sleep or wake event inside any of the 10 timeout runs, and every one ran 300.0 s of wall time
(`GPT5_TIMEOUT_RUN_INDEX.csv`).

## gpt-5's headroom is small

- **Wall time.** The 17 completed runs took 127 to 291 s, median 238 s: 145 to 291 s on the timeout instances, and 127 to 285 s on
  the others.
- **The submission call.** It alone took 30.0 to 120.4 s (median 48.5 s) and 2,132 to 5,643 output tokens.
- **Commitment.** The time from the faulty line's first display to the submission request was 16.0 to 220.4 s (median 97.6 s).
  On the six timeout instances, the per-instance medians are 95.9 to 186.3 s.

With so little slack, any of these can push a run past 300 s: slower serving, a malformed-command loop, a rejected submission, or
extra deliberation.

## Where the wall clock went

`time_decomposition.json` assigns each step's wait to one category, checked in this order:

1. malformed command: the command string ends in a stray `}` after its closing quote;
2. test or build step;
3. slow serving: fewer than 300 output tokens and a wait of at least 20 s;
4. deliberation: at least 1,500 reasoning tokens;
5. ordinary step.

Added to these are the request pending at the kill (timeouts), the submission call (completed runs) and agent startup. The
categories reproduce each run's wall time within 6.3 s; the largest overshoot is 6.24 s, for CTV-9CE7EA/run-002.

Because the split is exclusive, its result depends on the order. A deliberation or slow call that also emits a malformed command
counts as malformed. The same file therefore also gives non-exclusive totals (`malformed_any`, `slow_serving_any`,
`deliberation_any`), in which a call counts in every category it meets. The per-run table in `GPT5_AMBIGUITY_HYPOTHESIS.md` uses
those.

- **Malformed commands** appear in 5 of 10 timeouts and 11 of 17 completed runs. Not all of them fail: 85 of 97 failed in
  timeouts, 112 of 120 in completed runs.
- **Deliberation** is not specific to particular instances. The non-exclusive medians by recipe are HA 81 s, HB 80 s and HC 119 s.
  The largest totals in completed runs are:
  - CTV-E65CBB/run-003 (HB-MATH), 150 s;
  - CTV-9EB2B7/run-002 (HA-MATH), 149 s;
  - CTV-21982A/run-001 (HC-MATH), 139 s;
  - CTV-7CE456/run-001 (HC-JACKSONCORE), 119 s;
  - CTV-E04F64/run-003 (HA-JACKSONCORE), 117 s.

## Two environment findings that affect gpt-5 only

- **Tests through a login shell fail.**
  - The frozen classifier counts 32 test steps across the 27 runs; 34 command strings mention `defects4j test`.
  - All 15 test commands issued as `bash -lc '...'` failed with "Failed to parse Java version".
  - gpt-5.5 issued 27 test commands on the same held-out instances, none through a login shell, so it never met the failure.
  - Among gpt-5 runs, 3 timeouts ran no test at all, and 4 timeouts and 11 completed runs ran only failing tests. So 7 of 10
    timeouts and 11 of 17 completed runs (18 of 27 in all) never had a successful test.
  - This removes most of gpt-5's direct failure evidence: the failure message was displayed in 2 of 10 timeouts and 5 of 17
    completed runs. It does not separate timeouts from completed runs.
- **Duplicate overloads in a submission are rejected.** The validator refuses a ranking that names the same method twice (two
  overloads). This hit 3 gpt-5 runs, each rejected with the validator's `duplicate_method` code (`facts.json`). Two recovered and completed. CTV-E04F64/run-005 had a correct ranking rejected at step 17 and
  timed out while rewriting it.
