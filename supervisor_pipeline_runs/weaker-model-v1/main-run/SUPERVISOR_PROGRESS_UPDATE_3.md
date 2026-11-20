# Main run: progress update 3 (after batches 1–3)

16–17 October 2026. Model: gpt-5.5 (medium reasoning) on the frozen Stage B protocol. This update replaces update 2; the batch-1
and batch-2 figures are unchanged and were verified against a hash manifest throughout batch 3.

## Headline

**35 validated Defects4J bug instances tested; 27 with at least one shift.**

- 99 of 175 answered runs shifted. A run is a shift when the gold is not ranked first.
- No run timed out.

| Project | Instances tested | With at least one shift |
|---|---|---|
| Lang | 28 | 23 |
| Math | 3 | 2 |
| Chart | 2 | 1 |
| Closure | 1 | 1 |
| JacksonCore | 1 | 0 |

| Batch | Candidates | Validated | With a shift | Shifted / answered runs | Run cost |
|---|---|---|---|---|---|
| 1 | 8 | 8 | 7 | 21/40 | $17.40 |
| 2 | 15 | 10 | 5 | 17/50 | $21.01 |
| 3 ("no local trace" rule) | 21 | 17 | 15 | 61/85 | $30.84 |
| **Total** | 44 | 35 | **27** | 99/175 | $69.25 |

**Total spend: $133.35 recorded, $137.07 with estimates.** This is below your ceiling of about $148.

## Batch 3: the pre-specified "no local trace" rule

The rule was fixed and frozen before any batch-3 instance was designed (W29). Two rounds of independent review sharpened it
first. The faulty method must show none of these four traces after the injected omission:

| Item | Trace |
|---|---|
| T1 | an input that cannot matter |
| T2 | a dead or frozen variable, or a dead branch |
| T3 | a visibly incomplete set of cases |
| T4 | a concrete phrase in its own javadoc, comments or identifiers that the code visibly does not meet (caller preconditions excluded) |

**Construction pipeline.**

1. Each candidate went to a builder.
2. The 17 that reached READY on all 16 gates were checked in parallel by an independent ownership audit and by a separate **blind**
   trace check, which sees only the faulty method's text.
3. A REJECTED audit or a TRACE verdict triggered at most one redesign, before any run. Each redesign was re-validated, then checked
   by a new auditor and a new checker.

Five instances needed that redesign: four for a trace and one for a rejected audit.

**Construction yield: 17 accepted out of 21.** The other 4 are unbuildable:

- Lang-3 and Math-5 have no per-element computation to split, and no test catches an omission of their real steps.
- For Lang-54, Math-16 and Math-5, every omission that exactly one test catches would either leave a local trace under the new rule
  or have no single owner.

So the rule itself excluded some candidates, a selection effect to keep in mind.

**Pre-registered prediction.** It was written before the batch was built:

| Share of tested instances with at least one shift | Reading |
|---|---|
| ≥ 80% | supported |
| ≤ 67% (the batch-1–2 rate) | not supported |
| otherwise | inconclusive |

**Result: SUPPORTED.** 15 of 17 instances shifted (88%), and 61 of 85 runs (72%, against 42% in batches 1–2).

**Robustness.** Two extra blind raters re-checked each batch-3 gold, and I fixed a secondary analysis before reading any batch-3
outcome. The reading holds when doubtful golds are dropped:

| Subset | Instances shifted |
|---|---|
| Majority of 3 raters say no trace | 14 of 15 |
| All 3 raters say no trace | 12 of 13 |

**The two that did not shift.** These are post-hoc readings, not tested:

- **Lang-65.** The omission reuses a parse position across loop iterations, a well-known Java pitfall. Both extra raters had
  flagged it as a trace.
- **Math-15.** The failing test checks numerical accuracy, and the faulty method is the only one on the call chain that computes an
  approximation.

**Batch-3 instances:**

| Instance | Shifted / answered | Gold ranks (5 runs) |
|---|---|---|
| Lang-44 | 5/5 | 2 2 2 2 2 |
| Lang-58 | 5/5 | 2 6 2 6 6 |
| Lang-49 | 5/5 | 2 2 2 2 2 |
| Lang-31 | 5/5 | 2 2 2 2 2 |
| Lang-37 | 5/5 | 2 2 2 2 2 |
| Lang-33 | 5/5 | 2 2 2 2 2 |
| Lang-41 | 5/5 | 2 2 2 2 2 |
| Lang-53 | 5/5 | 3 2 4 2 4 |
| Math-55 | 5/5 | 6 2 2 2 2 |
| Lang-20 | 4/5 | 1 2 2 2 2 |
| Lang-46 | 4/5 | 2 1 2 2 2 |
| Lang-40 | 3/5 | 2 1 1 2 2 |
| Lang-35 | 2/5 | 1 1 2 2 1 |
| Lang-51 | 2/5 | 1 1 2 2 1 |
| Lang-57 | 1/5 | 2 1 1 1 1 |
| Math-15 | 0/5 | 1 1 1 1 1 |
| Lang-65 | 0/5 | 1 1 1 1 1 |

**Retrospective check of batches 1–2** (descriptive only). Three blind raters applied the frozen rule to the 18 earlier golds under
anonymous labels.

The rule's examples were drawn from these same golds after their results were known. This table therefore does not test the
hypothesis; only batch 3 does.

| Verdict | Instances | With at least one shift |
|---|---|---|
| No trace | 5 | 5 |
| Traced | 13 | 7 |

All 6 earlier instances that never shifted are traced. The rule is strict: it also flags three earlier instances that shifted 5/5.
This also corrects my update-2 statement, "9 of 9 against 3 of 9", which was cleaner than the data.

**Caveat.** Batch 3 also differs from batches 1–2 in its bugs, in its Lang versions, and in a construction pipeline with a blind
checker. There is no control arm, so this is a prospective consistency check of the hypothesis, not a causal test.

## Failure mode (all batches)

**All 99 shifted runs ranked the facade first**, that is, the existing method the failing test calls.

- In 95 of them the agent had displayed the gold's faulty line, and in 93 it read the gold in full.
- The gold usually came second; in a few runs the ranking simply follows the call chain from the top.
- In the other 4 runs the frozen matcher found no display of the gold's faulty line. That matcher is known to miss some displays
  (W16).

The labels are mechanical, from the frozen measures; they were not blind-coded.

## Cost

| Item | US$ |
|---|---|
| Main-run runs, batches 1–3 (176 records) | 69.25 |
| Per validated instance (runs only) | 1.98 |
| Per instance with a shift (runs only) | 2.56 |
| Experiment total, recorded / with estimates | **133.35** / 137.07 |

Construction used no OpenAI spend.

Batch 3 ran in seven blocks, each admitted by a pre-registered guard computed from the raw ledgers. A block could start only if
spend would still end at or below $147 with the driver's maximum number of runs and probes, each run priced at the highest cost seen
so far ($0.66). No batch-3 run exceeded that price, and the guard admitted all 17 accepted instances.

## Exceptions

- One run in batch 1 was excluded under the pre-registered contamination rule (W25), and its slot was replaced.
- Batches 2 and 3 had no exclusions.
- 20 new Defects4J checkouts were added to the shared workspace store for batch 3. Nothing existing changed.

## Open decisions

1. **Budget.** About $11 remains under the ceiling. The guard would admit at most one more instance (a worst case of $144.72), but
   building more needs new candidates and checkouts. A meaningful further batch needs a new ceiling.
2. **Attribution.** There is still no baseline arm (hops only, no lie). The counts show where the construction produces
   misrankings, not which component causes them.
3. **Next model.** GPT-5.6 was set aside for this phase. Running the 35 instances on it would show whether the effect carries
   over.
