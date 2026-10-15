# Are the gpt-5 timeouts caused by the introduced ambiguity?

**Answer: NOT SUPPORTED, as an explanation of why these 10 runs timed out rather than completing.** For 3 of the 10, the agent's
behaviour is compatible with the hypothesised non-commitment. Whether the ambiguity caused it cannot be tested with these data, so
for those 3 the honest answer is INCONCLUSIVE.

**gpt-5 has little headroom.** Its 17 completed runs took a median of 238 s of the 300 s budget.

**6 timeouts happened during a period of slow serving.** In slots 15 to 25 (14:05 to 15:05Z on 2026-10-13), every run whose speed
could be measured was served below 50 output tokens per second, against 69.4 before. On the six timeout instances, 6 of 6 runs in
that period timed out, against 4 of 12 outside it.

- None of these six had produced more output than its completed comparator had before submitting.
- Three of them also lost much of their time to malformed commands.
- Slower serving is a sufficient account for these six. It does not rule out non-commitment, and CTV-21982A/run-004 is a boundary
  case.

**4 timeouts ran at normal speed.** These are the runs that can test the hypothesis.

- CTV-E04F64/run-005 had committed: the validator rejected its ranking because it named the same method twice (two overloads).
- The other three ran heavy-reasoning calls after the gold for 168 to 193 s, against 117 to 150 s for their comparators. They
  committed later than their comparators did, or not at all. These are CTV-7CE456/run-002, CTV-E04F64/run-004 and
  CTV-E65CBB/run-002.
- Two of those three were also in malformed-command loops, so part of that reasoning may have gone to command repair.
- In none of the three did the coders see behaviour tied to competing owners or an ambiguous convention.

**Why the verdict is NOT SUPPORTED, and not PARTIALLY SUPPORTED or INCONCLUSIVE overall.**

- The brief has two criteria that separate ambiguity from other causes: more time exploring competing suspects, and behaviour that
  reflects ownership or convention uncertainty. Both are negative on everything that can be observed. The reasoning text cannot be
  observed.
- For 7 of the 10 timeouts, an account without non-commitment is sufficient: the six slow-period runs and the validator rejection.
- The extra deliberation in the remaining three is not specific to ambiguity. The comparators are ambiguity runs too, and they
  committed.

A reader who gives the three compatible runs more weight could call the overall answer INCONCLUSIVE.

**Scope.** This verdict concerns why these runs timed out instead of completing. It is not a verdict on whether the ambiguity
lengthens gpt-5's runs in general: every comparator is also an ambiguity run, and the HC-MATH comparator itself needed 282 s.

Hypothesis tested (supervisor): the ambiguity built into these instances does not make gpt-5 rank the wrong method first. Instead
it raises uncertainty, so the agent keeps verifying, does not commit, and exhausts the 300 s budget.

Data: the 27 valid gpt-5 runs on the nine held-out instances (10 timeouts; 17 completed, all correct). Sources:

- `timeline_runs.json` and `timeline_steps.json`, built from the recorded timestamps by `scripts/gpt5_timeline.py`;
- `workload_speed.json`, `time_decomposition.json`, `call_waits.json`, `malformed_commands.json` and `post_gold_reasoning.json`,
  built by `scripts/gpt5_workload_speed.py`;
- `facts.json`, built by `scripts/gpt5_timeout_facts.py`;
- the blind labels and the coders' rationales in `GPT5_TIMEOUT_BLIND_LABELS.json`;
- `replays/`.

Statistics are medians with Cliff's delta (timeouts minus completed). With 10 timeouts against 17 completed runs, nothing here is a
significance claim.

## Serving speed and the model's own work

The model produces its calls and its output and reasoning tokens. The seconds those calls take depend on the provider as well.
Speed here is the median number of output tokens per second over a run's calls of 500 tokens or more.

### When the provider was slow

The earlier version of this analysis started its window at 13:47Z, the start of the first late timeout, so the timeouts themselves
set its bounds. This version defines the slow period by measured speed instead. It is the span of slots in which a run's speed was
below 50 tok/s (`facts.json`, `slow_period_by_speed`): slots 15 to 25, with runs starting between 14:05 and 15:00Z.

| | Slow period (slots 15 to 25) | Rest of the block |
|---|---|---|
| speed of runs | 10.1 to 49.3 tok/s (9 measurable runs; slots 23 and 24 made no call that long) | 58.9 to 81.6 tok/s |
| timed out, on the six timeout instances | 6 of 6 | 4 of 12 |
| timed out, on the other three instances | 0 of 5 (median output 7,089 tokens) | 0 of 4 |
| submission call, completed runs | 46.2 to 120.4 s (median 94.8 s; 5 runs) | median 45.0 s (12 runs) |

The four timeouts outside the slow period ran at 61.6 to 69.6 tok/s: CTV-E65CBB/run-002 before 13:47Z, then CTV-7CE456/run-002,
CTV-E04F64/run-004 and CTV-E04F64/run-005 at slots 13, 14 and 26. Each was as fast as its comparator or faster, except
CTV-7CE456/run-002 (69.6 against 81.6).

### What each timeout had done

The output comparison sets a run's output before the kill against its comparators' median output before their submission call.
It is a consistency check, not independent evidence, for two reasons:

- **It tracks speed by construction.** Every timeout ran exactly 300 s, so its output before the kill is close to its average
  throughput.
- **It depends on the baseline.** Against same-instance comparators, the six slow-period runs produced equal or less output and the
  four normal-speed runs 30 to 37% more. Against the pooled median of all 17 completed runs (7,767 tokens), 7 of the 10 would count
  as producing more. Same-instance comparators are the fairer baseline, but four instances have only one each.

| Run | Period | Speed (tok/s) | Output vs comparator | Heavy calls after gold, s (comparator) | Malformed cheap calls (n, s) | Counterfactual end (s) | Coders' primary |
|---|---|---|---|---|---|---|---|
| CTV-E65CBB/run-004 | slow | 10.1 | -91% | 0 (150) | 0 | 82* | OTHER (slow responses) |
| CTV-9EB2B7/run-003 | slow | 19.2 | -78%, never reached the gold | – | 12, 227 | 111* | OTHER (format, slow responses) |
| CTV-9CE7EA/run-003 | slow | 22.3 | -35% | 0 (51 to 75) | 18, 207 | 186 | OTHER (command format) |
| CTV-21982A/run-002 | slow | 34.0 | -27% | 166 (139) | 0 | 220 | GOLD_FOUND_BUT_NOT_TRUSTED |
| CTV-7CE456/run-003 | slow | 49.3 | -15% | 72 (119) | 16, 95 | 266 | OTHER (command format) |
| CTV-21982A/run-004 | slow | 48.5 | -0.1% | 186 (139) | 0 | 284 | GOLD_FOUND_BUT_NOT_TRUSTED |
| CTV-7CE456/run-002 | normal | 69.6 | +36% | 193 (119) | 0 | 290 | OVER_VERIFICATION |
| CTV-E04F64/run-005 | normal | 61.6 | +37% | 213, including the rejected submission (117) | 0 | 296 | OTHER (rejected submission) |
| CTV-E04F64/run-004 | normal | 65.3 | +32% | 168, all also malformed commands (117) | 16, 45 | 298 | GOLD_FOUND_BUT_NOT_TRUSTED |
| CTV-E65CBB/run-002 | normal, before 13:47Z | 62.5 | +30% | 177, all also malformed commands (150) | 25, 72 | 331 | TOOL_LOOP |

Column definitions:

- **Heavy calls:** non-test calls with 1,000 or more reasoning tokens after the gold's first display, excluding the final pending
  or submission call.
- **Malformed cheap calls:** calls whose command ends in a stray `}` and which carry fewer than 1,000 reasoning tokens. Most such
  commands fail.
- **Counterfactual end:** every non-test wait re-timed at the pre-window speed (2 s plus output tokens divided by 69.4 tok/s, never
  longer than observed), plus a median submission of 3,450 tokens. It assumes each run would have committed after the work it had
  done.

**How far to trust the counterfactual.**

- **Calibration.** On the 12 completed runs before the window, the counterfactual end minus the actual wall time has a median of
  +0.2 s and a range of -28.9 to +18.7 s.
- **Ends within the error band.** Ends of 266 to 298 s are within the method's error of 300 s.
- **Ends that are clear.** Only 186 to 220 s and 331 s are.
- **Ends that are not completion estimates.** The two marked * are not. The coders judged CTV-E65CBB/run-004 still searching, and
  CTV-9EB2B7/run-003 never reached the gold. For those two, their comparators' completions are the better evidence.

**Three runs need a note.**

- **CTV-21982A/run-004 is the boundary case.** Its output equalled its single comparator's (13,032 against 13,043), and that
  comparator itself took 282 s. It spent 186 s in heavy post-gold calls, and its last action was a read at 296 s. Both coders
  labelled it found but not committed.
- **CTV-E04F64/run-005 submitted 153 s after the gold's first display**, against its comparator's 119 s. Had that submission been
  accepted, the run would have ended at about 261 s.
- **CTV-7CE456/run-002 is behavioural by a margin of 0.6 s.** Its last request had been pending 59.4 s, against the 60 s stall
  threshold.

## The operational measures (A to H)

Medians below exclude CTV-9EB2B7/run-003, which never reached the gold: 9 timeouts against 17 completed runs.

**A. Search after the gold.**

| Measure | Timeouts | Completed | Delta |
|---|---|---|---|
| calls after the gold | 5 | 7 | -0.16 |
| model time after the gold | 189 s | 98 s | +0.59 |
| the same, re-timed at the pre-window speed | 144 s | 96 s | +0.28 |

Re-timing removes about half of the model-time gap. Slower serving explains that half; more model work explains the rest.

**B. Suspect churn.**

- **Methods newly inspected after the gold:** 13 against 15 (delta 0.0). Within instances, 6 of the 9 inspected more than their
  comparator.
- **Declared alternatives newly inspected after the gold** (decoys, entry points, evidence methods): median 0 in both groups. The
  measure counts only first inspections, not returns. CTV-7CE456/run-002 re-read the entry point and a decoy at steps 14 and 15;
  both coders read these re-reads as gathering line-numbered citations.
- **Off-path reads:** several timeouts read whole files that are off the call chain. The coders read these as confirmation or
  broad reading, not as competing owners.
  - CTV-E04F64/run-004: ParserMinimalBase and JsonStringEncoder, which supply 50 of its 56 newly inspected methods.
  - CTV-21982A/run-002: Covariance.
  - CTV-7CE456/run-002: UTF8Writer.
  - CTV-E65CBB/run-002: IntervalsSet and the 3-D Segment.
- **Suspect lists:** each coder's list of suspects examined after the gold holds 0 to 3 names for every timeout except
  CTV-E65CBB/run-002 (5 and 7).

**C. Revisits.** Revisit reads over the whole run: 3 against 5 (delta -0.33). Repeated identical commands: median 0 in both
groups.

**D. Verification looping.** Tests after the decisive evidence: median 0 in both groups, and at most 1 in any timeout. No probes.

**E. Commitment delay.**

- **Completed runs.** The time from the faulty line to the submission request ranges from 16 to 220 s (median 98 s). On the six
  timeout instances, the per-instance medians are 96 to 186 s.
- **Timeouts.** They are censored at the kill. In 7 of the 9 that reached the gold, the time from the gold to the kill already
  exceeds the comparator's time from the gold to submission.
- **Confounding.** For the slow-period runs this comparison is confounded by speed. For the four normal-speed runs it is not:

| Run | Gold to kill (s) | Comparator gold to submission (s) |
|---|---|---|
| CTV-7CE456/run-002 | 259 | 131 |
| CTV-E04F64/run-004 | 231 | 119 |
| CTV-E04F64/run-005 | 255 (its own submission came at 153 s and was rejected) | 119 |
| CTV-E65CBB/run-002 | 268 | 186 |

**F. Deliberation.** Reasoning tokens after the gold, excluding the final pending or submission call, roughly double at the
median: 10,560 against 5,184 (delta +0.31). Five of the 9 reasoned more than their comparator:

- CTV-E04F64/run-005: +49%, including the rejected submission
- CTV-7CE456/run-002: +48%
- CTV-E04F64/run-004: +24%
- CTV-E65CBB/run-002: +21%
- CTV-21982A/run-004: +9%

The other four reasoned 36 to 95% less. The text of the reasoning is hidden and was not read, and none of the 27 runs has visible
assistant text (`facts.json`). From actions alone, the coders saw alternation between competing explanations in 1 of 20 coder
labels.

**G. Evidence sufficiency.**

- **Before the kill.** 9 of 10 timeouts had displayed the faulty line and read the gold in full, and 9 of 10 had displayed the
  declared evidence. The coders judged the evidence sufficient in 9 of 10. They still judged CTV-E65CBB/run-004 to be searching,
  although it had read the gold.
- **The failure message.** It was displayed in only 2 of 10 timeouts and 5 of 17 completed runs, for three reasons:
  - 3 timeouts ran no test.
  - Every login-shell test failed with "Failed to parse Java version". These are 15 of the 34 commands that mention
    `defects4j test`, all issued as `bash -lc`. The frozen classifier counts 32 test steps, and 13 of the 15 failures are among
    them.
  - 7 of 10 timeouts and 11 of 17 completed runs never had a successful test.

**H. Searching or attributing at the end?** The coders' end states were: found but not committed 5, plausibly writing the answer 3,
still searching 2. The three replays were each one request from the exact pre-timeout state, for runs selected by a rule fixed
beforehand.

- **CTV-E04F64/run-005** submitted a ranking with the gold first in 35 s. The run had already committed once (the rejected
  submission) and was rewriting. Whether the validator would accept the replayed ranking was not checked.
- **CTV-7CE456/run-002**'s next action was a read, not a submission, returned in 19.8 s (1,966 tokens).
  - The original request had been pending for at least 59.4 s. At this run's own speed that is at least about 4,100 output tokens:
    the size of a submission (completed submissions were 2,132 to 5,643 tokens) or of a long deliberation.
  - It may also have been served slowly. Which of these it was cannot be told.
  - This single sample points against the coders' "plausibly writing the answer", but cannot overturn it.
- **CTV-E65CBB/run-002**'s next action was another 48-character shell command, neither a read nor a test. Its content was not
  recorded.

## Against the brief's criteria

| Criterion for SUPPORTED | Observed |
|---|---|
| gold already discovered and read | yes, 9 of 10 |
| decisive evidence already available | yes, 9 of 10, though the failure message was usually missing because tests broke |
| timeouts spend substantially more time exploring competing suspects | no: calls after the gold 5 against 7; newly inspected methods 13 against 15; declared alternatives 0 against 0. Off-path whole-file reads occur but were not read as competing owners; one normal-speed run re-read the entry point and a decoy to gather citations |
| rationales or behaviour repeatedly reflect ownership or convention uncertainty | rationales cannot be observed (hidden reasoning, no visible text). In behaviour, no OWNERSHIP_AMBIGUITY, ENTRY_POINT_COMPETITION or CONVENTION_AMBIGUITY label in 20 coder labels, and alternation in 1 of 20 |
| matched completed runs commit much earlier | yes in wall time (7 of 9), confounded by speed in the slow period. At normal speed, yes for the three heavy-reasoning runs: their comparators committed 82 to 128 s earlier, measured from the gold. The fourth had committed and was rejected |

| Criterion for NOT SUPPORTED | Observed |
|---|---|
| timeouts dominated by slow serving, command problems or tool overhead | yes for the 6 slow-period runs (three also in command loops) and for the validator rejection; partly for two of the three heavy-reasoning runs, which were also in command loops |
| no extra ambiguity-related behaviour | no competing-owner or convention behaviour observed. Extra post-gold deliberation at normal speed in 3 runs, which the hypothesis predicts but which is not specific to ambiguity |
| failure to locate sufficient evidence | 1 of 10 |

## Limits

- **No control.** Every gpt-5 run is on an instance built around an ambiguity, so this tests behaviour, not cause.
- **Few comparators.** Four of the six timeout instances have one completed comparator each.
- **Censoring by the frozen 60 s stall rule.** Five runs were excluded under it, so every count here is conditional on that rule.
  - CTV-E04F64/run-001 and run-002, and CTV-E65CBB/run-001, ran on 2026-10-12. CTV-E65CBB/run-001 was stretched by the W3 machine
    sleep.
  - CTV-B68398/run-002 and CTV-21982A/run-003 ran in the slow period.
  - All five had read the gold in full and had a request pending for 66 to 131 s at the kill. That is what either a long
    post-gold deliberation or a submission looks like.
  - The two day-1 HA-JACKSONCORE runs (131.2 and 87.5 s pending) ran at normal speed. That instance's only completed run made a
    single 117 s call of 8,567 tokens.
- **Coder priming.** The brief's examples for OTHER named slow responses and a submission in progress. The timing tables gave no
  speed baseline, and one coder judged 30 to 46 tok/s "not slow" where the norm was about 70.
- **Single samples.** Each replay is one request.
- **Post hoc partitions.** The 50 tok/s speed threshold and the output comparison were both chosen after looking at the data.
  - Every slow-period speed is at most 49.3 tok/s, and every other measurable run is at 58.9 tok/s or above, so any threshold in
    that gap gives the same period.
  - The output comparison depends on its baseline, as described above.
