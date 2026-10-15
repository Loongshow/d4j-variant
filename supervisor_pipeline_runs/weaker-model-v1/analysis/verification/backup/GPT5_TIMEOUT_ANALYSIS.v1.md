# What happened in the ten gpt-5 timeouts?

## Answer for the supervisor

The ten gpt-5 timeouts are not an ambiguity effect. In 9 of 10 the agent had already displayed and fully read the faulty method,
so search had usually finished; the time was lost in four other ways.

- **Malformed-command loop (5 runs).** gpt-5 often puts a stray `}` at the end of its shell commands. Each such command fails and
  is retried, and in these runs this consumed 117 to 249 s.
- **Slow serving (1 run).** Calls took 40 to 60 s to return about 50 tokens, during a 90-minute window in which the provider's
  health probes were also slow. That window contains 9 of the 10 timeouts.
- **Validator rejection (1 run).** The agent submitted a correct ranking, the validator rejected it for naming an overloaded method
  twice, and time ran out during the resubmission.
- **Long deliberation (3 runs).** After the evidence was on screen, two or three long hidden-reasoning turns produced only
  confirmation reads. These three runs are on two instances where every gpt-5 run, including the completed ones, deliberates for
  110 to 186 s.

Against the completed runs, the timeouts did less work, not more: fewer calls after the gold, fewer methods inspected, fewer
revisits, at half the pace. Two blind coders per run found no ownership, entry-point or convention competition in any run. On the
brief's scale the hypothesis is **NOT SUPPORTED**. The three deliberation cases are compatible with a weak non-commitment reading,
but the same deliberation appears in completed runs on those instances, and without an unambiguous control it cannot be tied to the
ambiguity.

## The ten runs

`GPT5_TIMEOUT_RUN_INDEX.csv`. The gpt-5 block (server w50, `gpt-5-2025-08-07` served, `reasoning_effort: medium`, frozen
protocol: 50 tool calls, 5 tests, 300 s) produced 32 run records:

- 27 valid: 17 answered (all with the gold first) and 10 behavioural timeouts.
- 5 excluded by the frozen classifier's provider-stall rule 2 (the run's last event is a tool result and more than 60 s were left
  before the kill): CTV-E04F64/run-001 and run-002, CTV-E65CBB/run-001 (the run that the machine-sleep incident, W3, stretched to
  2,373 s of wall time), CTV-B68398/run-002 and CTV-21982A/run-003.

The ten timeouts are exactly the included runs with status `timeout`. Every one has these properties:

- 300.0 s of wall time;
- ledger verdict valid;
- source integrity ok;
- workspace isolation ok;
- no sleep or wake event in the macOS power log during the run;
- a passing three-probe health gate immediately before launch.

The gate is the provider-health check. Its probe walls were 9 to 18 s before most runs, but 28 to 67 s before five of the timeouts.

Two runs sit close to the classifier's boundary, so they are behavioural only by a small margin:
- CTV-7CE456/run-002 had a 59.4 s request pending at the kill, against the 60 s stall threshold.
- Four others had 36 to 39 s pending.

| Instance (recipe) | Timeouts | Completed on the same instance |
|---|---|---|
| HO-HA-COMPRESS-01 (entry point) | CTV-9CE7EA/run-003 | run-001, run-002 |
| HO-HA-JACKSONCORE-01 | CTV-E04F64/run-004, run-005 | run-003 |
| HO-HA-MATH-01 | CTV-9EB2B7/run-003 | run-001, run-002 |
| HO-HB-MATH-01 (sink) | CTV-E65CBB/run-002, run-004 | run-003 |
| HO-HC-JACKSONCORE-01 (convention) | CTV-7CE456/run-002, run-003 | run-001 |
| HO-HC-MATH-01 | CTV-21982A/run-002, run-004 | run-001 |

The other three instances (HB-COMPRESS, HB-LANG, HC-LANG) completed 9 of 9.

## Method

1. **Timelines** (`scripts/gpt5_timeline.py` → `GPT5_TIMEOUT_TIMELINES.csv`, `timeline_steps.json`). Built from the recorded
   timestamps:
   - the harness timer start;
   - each model request's creation time;
   - each tool result's timestamp.

   The script uses the frozen `mx_metrics.py` display and command definitions, executed verbatim. Its end-of-run values reproduce
   the frozen per-run measures exactly (tool calls, faulty line shown, gold read in full, evidence displayed).
2. **Matched comparison** (`scripts/gpt5_timeout_compare.py` → `GPT5_TIMEOUT_MATCHED_COMPARISON.md`). Each timeout against the
   completed runs on its own instance, plus the pooled comparison with Cliff's delta.
3. **Time decomposition** into exclusive categories (`time_decomposition.json`).
4. **Blind coding** (`GPT5_TIMEOUT_BLIND_LABELS.json`, brief `TIMEOUT_LABEL_BRIEF.md`). Two independent coders per run: a time-use
   lens and an evidence lens. They saw only the brief, the task file, the safe trajectory view (hidden reasoning excluded), the timing
   table and the variant patch. A third coder adjudicated the four runs where the coders disagreed on the primary label, the end state
   or evidence sufficiency. The coders agreed on the primary label in 7 of 10 runs.
5. **Bounded replays** (brief section 8; `replays/`, `scripts/gpt5_replay_next_action.py`). One request each, from the exact
   pre-timeout state, for three runs selected by a rule fixed before any call. They are diagnostic only and never scored. Cost was
   under $0.10.

## Findings

- **Search had usually finished.** In 9 of 10 timeouts the faulty line was displayed and the gold read in full, with the declared
  evidence on screen. The exception is CTV-9EB2B7/run-003, which never reached the gold.
- **The timeouts did less work.** After the gold they made fewer calls, inspected fewer methods and revisited less than completed
  runs did, with no extra tests or probes. Their pace was 3.5 against 7.3 tool calls per minute. Their longest single wait was
  58.5 s against 37.5 s, and their pre-launch probes were 22 s against 12 s.
- **Where the time went.** Each timeout has one dominant sink (table in `GPT5_AMBIGUITY_HYPOTHESIS.md`):
  - malformed commands, 5 runs;
  - slow serving, 1 run;
  - deliberation turns, 3 runs;
  - a rejected correct submission, 1 run.

  Completed runs show the same sinks at smaller sizes, and they pay about 48 s (30 to 121 s) for the submission call itself. A run
  that has not begun submitting by about 180 to 250 s is at risk whatever it is doing.
- **Blind codes.** Primary labels: OTHER 5 (broken command format, slow responses, rejected submission), GOLD_FOUND_BUT_NOT_TRUSTED
  3, OVER_VERIFICATION 1, TOOL_LOOP 1. No ownership, entry-point or convention label appears in any of the 20 coder labels.
  Alternation between explanations was seen in 1 of 20.
- **Replays.** CTV-E04F64/run-005 submitted a correct ranking in 35 s, so it had committed and was resubmitting. CTV-7CE456/run-002
  read another file, so it was still verifying. CTV-E65CBB/run-002 issued another shell command, so it was still in its command loop.
- **Timing.** 9 of 10 timeouts fall in the last 14 slots on 2026-10-13 (13:47 to 15:10Z), alongside the two excluded provider
  stalls. All 7 runs on 2026-10-12 completed.

## Protocol findings to record (not caused by the benchmark)

- **Login-shell tests fail.** gpt-5 runs some tests through a login shell (`bash -lc`). All 15 such test calls failed with "Failed
  to parse Java version". All 19 non-login calls ran, and gpt-5.5 never used a login shell. 15 of 27 gpt-5 runs never saw a
  successful test.
- **Stray brace.** gpt-5 often appends a stray `}` to the end of its shell command strings. This happened in 16 of 27 runs.
- **Overload rejection.** The submission validator rejects a ranking that lists two overloads of the same method. This hit 3 gpt-5
  runs; one of them is a timeout.

These three are interactions between gpt-5 and the harness. They make the W4 verdict on gpt-5 ("operationally too weak at the
frozen budget") partly a harness verdict. None of them is an ambiguity effect. No harness change is proposed here, and the frozen
protocol is unchanged.

## What would test the hypothesis properly (not run)

The instances that drive gpt-5 into long deliberation are HC-MATH and HC-JACKSONCORE. A same-bug control of those two without the
convention ambiguity, run under a budget that removes the operational losses, would test whether the ambiguity is what demands the
extra reasoning. Fixing the login-shell environment, and either a longer budget or excluding submission time from it, would remove
the other causes. This is a new benchmark design, so per the brief it is only proposed.

## Files

| File | Contents |
|---|---|
| `GPT5_TIMEOUT_RUN_INDEX.csv` | the ten runs, with provenance and checks |
| `GPT5_TIMEOUT_TIMELINES.csv` | 27 runs: timeouts and completed runs |
| `GPT5_TIMEOUT_MATCHED_COMPARISON.md` | matched and pooled comparisons, decomposition and environment findings |
| `GPT5_TIMEOUT_BLIND_LABELS.json` | coder labels and adjudications |
| `GPT5_AMBIGUITY_HYPOTHESIS.md` | measures A to H and the verdict |

Data: `timeline_runs.json`, `timeline_steps.json`, `compare.json`, `post_gold_reasoning.json`, `call_waits.json`,
`malformed_commands.json`, `time_decomposition.json`, `replays/`, `label_inputs/`.
