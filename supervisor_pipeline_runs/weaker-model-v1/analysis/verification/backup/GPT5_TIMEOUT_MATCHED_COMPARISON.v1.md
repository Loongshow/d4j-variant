# GPT-5 timeouts against completed runs on the same task

Source data: `gpt5-timeouts/timeline_runs.json`, `timeline_steps.json` (built by `scripts/gpt5_timeline.py` from the recorded timestamps, with the
frozen display and command definitions of `scripts/mx_metrics.py`), `compare.json`, `post_gold_reasoning.json`, `call_waits.json`.
All 27 valid gpt-5 runs share the prompt, model (`gpt-5-2025-08-07` served), `reasoning_effort: medium`, budgets and server code; each of
the six instances with a timeout also has completed runs, so every timeout has a same-task comparison. Descriptive only: 10 timeouts against
17 completed runs (8 of them on the timeouts' instances). Effect size: Cliff's delta (timeout minus completed; +1 = every timeout higher).

## Pooled comparison

| Measure | Timeouts (median) | Completed (median) | Cliff's delta |
|---|---|---|---|
| model calls | 17.5 | 22 | -0.32 |
| exploration tool calls (excl. submission) | 17.5 | 21 | -0.27 |
| time to first gold display (s) | 69.5 | 50.4 | 0.27 |
| time to faulty-line display (s) | 69.5 | 50.4 | 0.27 |
| time to full gold read (s) | 69.5 | 50.4 | 0.27 |
| time to decisive evidence (s) | 39.8 | 48.6 | 0.25 |
| time to first test (s) | 17.5 | 10.6 | 0.24 |
| calls before gold | 12.0 | 16 | -0.21 |
| calls after gold | 5.0 | 7 | -0.25 |
| searches after gold | 0.5 | 1 | -0.12 |
| reads after gold | 2.5 | 3 | -0.13 |
| tests after gold | 0.0 | 0 | -0.09 |
| methods newly inspected after gold | 10.5 | 15 | -0.09 |
| declared alternatives inspected after gold | 0.0 | 0 | -0.02 |
| revisit reads | 3.0 | 5 | -0.33 |
| repeated identical commands | 0.0 | 0 | -0.12 |
| median per-call wait (s, non-test) | 3.5 | 2.7 | 0.38 |
| longest single wait (s) | 58.5 | 37.5 | 0.55 |
| time in test steps (s) | 4.2 | 4.2 | 0.01 |
| reasoning tokens (total) | 10624.0 | 5888 | 0.25 |
| reasoning tokens per call (median) | 0.0 | 0 | -0.12 |
| seconds per 1k output tokens | 21.5 | 18.6 | 0.22 |
| provider probe wall before launch (s) | 22.0 | 11.9 | 0.54 |
| tool calls per minute | 3.5 | 7.3 | -0.61 |
| reasoning tokens after gold (excl. submission) | 8512.0 | 5184 | 0.18 |
| deliberation calls (>= 1,500 reasoning tokens) after gold | 2.5 | 1 | 0.19 |
| model time after gold (s) | 179.14999999999998 | 97.5 | 0.44 |

Reading: the timeouts did not do more work. They made fewer calls overall and after the gold, inspected fewer methods after the gold, and
revisited less. They ran at half the pace (3.5 against 7.3 tool calls per minute), had longer single waits, and the provider health probe
taken just before each launch was about twice as slow. They spent somewhat more reasoning after the gold and much more model time after it.

## Matched comparison (each timeout against the completed runs on its own instance; completed values are medians)

| Instance (recipe) | Timeout run | tool calls | gold first shown (s) | calls after gold | methods inspected after gold | deliberation calls after gold | median wait (s) | probe before launch (s) | final pending request (s) | completed: gold -> submission request (s) | completed: submission call (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HO-HA-COMPRESS-01 | CTV-9CE7EA/run-003 | 24 vs 33.0 | 159.6 vs 79.0 | 5 vs 12.0 | 31 vs 23.5 | 0 vs 1.0 | 4.5 vs 2.6 | 28.8 vs 8.7 | 6.9 | 95.9 | 41.1 |
| HO-HA-JACKSONCORE-01 | CTV-E04F64/run-004 | 32 vs 12 | 69.5 vs 47.9 | 14 vs 2 | 56 vs 3 | 3 vs 1 | 2.4 vs 3.5 | 15.8 vs 9.9 | 37.8 | 119.1 | 71.1 |
| HO-HA-JACKSONCORE-01 | CTV-E04F64/run-005 | 18 vs 12 | 44.9 vs 47.9 | 6 vs 2 | 4 vs 3 | 4 vs 1 | 3.0 vs 3.5 | 14.3 vs 9.9 | 39.2 | 119.1 | 71.1 |
| HO-HA-MATH-01 | CTV-9EB2B7/run-003 | 13 vs 21.0 | None vs 43.5 | 0 vs 5.5 | 0 vs 0.5 | 0 vs 2.0 | 21.3 vs 3.0 | 51.5 vs 15.1 | 18.1 | 118.2 | 56.3 |
| HO-HB-MATH-01 | CTV-E65CBB/run-002 | 45 vs 18 | 31.7 vs 30.0 | 33 vs 7 | 21 vs 13 | 4 vs 4 | 2.3 vs 4.2 | 9.3 vs 10.9 | 7.9 | 186.3 | 34.7 |
| HO-HB-MATH-01 | CTV-E65CBB/run-004 | 7 vs 18 | 178.4 vs 30.0 | 2 vs 7 | 15 vs 13 | 0 vs 4 | 45.5 vs 4.2 | 66.9 vs 10.9 | 14.1 | 186.3 | 34.7 |
| HO-HC-JACKSONCORE-01 | CTV-7CE456/run-002 | 17 vs 16 | 40.7 vs 33.3 | 8 vs 6 | 8 vs 25 | 4 vs 3 | 3.6 vs 3.9 | 12.6 vs 13.0 | 59.4 | 131.3 | 39.4 |
| HO-HC-JACKSONCORE-01 | CTV-7CE456/run-003 | 28 vs 16 | 211.0 vs 33.3 | 2 vs 6 | 8 vs 25 | 2 vs 3 | 3.5 vs 3.9 | 50.1 vs 13.0 | 17.3 | 131.3 | 39.4 |
| HO-HC-MATH-01 | CTV-21982A/run-002 | 13 vs 15 | 94.4 vs 50.4 | 3 vs 6 | 6 vs 12 | 2 vs 3 | 3.0 vs 4.8 | 28.2 vs 11.9 | 36.8 | 151.0 | 80.8 |
| HO-HC-MATH-01 | CTV-21982A/run-004 | 15 vs 15 | 43.7 vs 50.4 | 5 vs 6 | 13 vs 12 | 3 vs 3 | 3.4 vs 4.8 | 12.0 vs 11.9 | 3.6 | 151.0 | 80.8 |

## What the long waits were

Of 600 non-test model calls, 52 waited 30 s or more (33 of them in timeout runs). Two kinds:
- **Deliberation calls**: 1,500 to 8,500 reasoning tokens generated at 45 to 83 output tokens per second. They occur in completed runs as
  well as in timeouts and are part of this model's normal working pattern on these instances.
- **Slow-serving calls**: few output tokens (under 300) but waits of 20 to 54 s (about 1 to 5 tokens per second). They occur only in timeout
  runs (CTV-9EB2B7/run-003 and CTV-E65CBB/run-004, five each), during the window when the health probes were slow. On calls with fewer than
  100 output tokens the longest wait was 53.8 s in timeout runs against 13.8 s in completed runs; generation speed on calls with at
  least 500 output tokens was 56.0 against 68.9 tokens per second.

## When the timeouts happened

The block ran in two sessions. All 7 runs on 2026-10-12 completed. On 2026-10-13, 1 of the first 6 runs (slots 7-12) timed out and 9 of the
last 14 (slots 13-26, 13:47-15:10Z) did, in the same window as the two provider stalls excluded by the frozen classifier (slots 15 and 25).
Probe walls before launch rose to 28-67 s at slots 16 and 19-22, against 9-18 s for almost every completed run. The macOS power log shows no
sleep or wake event inside any of the 10 timeout runs, and every one ran 300.0 s of wall time (`GPT5_TIMEOUT_RUN_INDEX.csv`).

## The submission itself is expensive for this model

In completed runs the final submission request (one model call writing the ten-method ranking and the evidence chain) took 30 to 121 s
(median 48 s) and 2,100 to 5,600 output tokens. Completed runs started that request between 66 and 242 s (median 164 s), and between 16
and 220 s after the gold's faulty line first appeared. Any run that has not started its submission by roughly 180 to 250 s is at risk,
whatever it is doing.

## Where the wall clock went (exclusive categories, `time_decomposition.json`)

Each step's wait is assigned to one category, checked in this order: malformed command (the command string ends in a stray `}`
after its closing quote); test or build step; slow serving (fewer than 300 output tokens and a wait of at least 20 s); deliberation
(at least 1,500 reasoning tokens); ordinary step. The final request pending at the kill (timeouts), the submission call (completed
runs) and agent startup are added. The categories sum to each run's wall time within 6 s.

| Category | Timeouts (median s) | Completed (median s) |
|---|---|---|
| malformed commands | 58.4 | 22.3 |
| slow serving | 0 | 0 |
| deliberation | 54.9 | 55.6 |
| tests and builds | 2.1 | 3.5 |
| ordinary steps | 55.5 | 57.8 |
| final pending request / submission call | 17.7 | 48.5 |

The medians are similar; the difference is in the tails. Every timeout has one sink that grew far larger than usual: malformed
commands of 117 to 249 s (5 runs), slow serving of 211 s (1 run), deliberation of 166 to 213 s (4 runs, one of which includes a
correct submission rejected by the validator). The same sinks occur in completed runs, smaller (largest: malformed 151 s, which
still completed). In 11 of 17 completed runs and 5 of 10 timeouts the model emitted malformed commands, so the quirk is general to
gpt-5 with this harness and is not specific to timeouts (count delta 0.04, time delta 0.14).

Deliberation is a property of the instance. Median deliberation per recipe: HA 0 s, HB 23 s, HC 119 s. Within HC it is entirely
HC-MATH (139, 166, 186 s) and HC-JACKSONCORE (119, 176, 110 s); HC-LANG has none.

## Two environment findings that affect gpt-5 only

- **Tests through a login shell fail.** All 15 `defects4j test` calls that gpt-5 issued as `bash -lc '...'` failed with "Failed
  to parse Java version". All 19 issued without the login flag ran normally. gpt-5.5 issued all of its 27 held-out test calls
  without it and never hit the failure. 15 of 27 gpt-5 runs (11 of 17 completed, 4 of 10 timeouts) never saw a successful test.
  This affects gpt-5's evidence (the failure message was displayed in 2 of 10 timeouts and 5 of 17 completed runs) but does not
  separate timeouts from completed runs.
- **Duplicate overloads in a submission are rejected.** The submission validator refuses a ranking that names the same method
  twice (two overloads). This hit 3 gpt-5 runs. Two recovered and completed; CTV-E04F64/run-005 had its correct ranking rejected
  at step 17 and timed out while resubmitting.
