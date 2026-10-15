# Weaker-model results (weaker-model-v1), as of 2026-10-14

Two questions were asked of this root, in order.

1. **Ladder (PREREGISTRATION.md).** Does a weaker OpenAI model, under the frozen protocol, lose accuracy on the nine held-out
   instances that GPT-5.6 solved?
2. **Stage A (AMENDMENTS W5), after the user's redirection.** Do the frozen instances that GPT-5.6 itself missed also break
   gpt-5.5, and does the matched CHART pair isolate the chain?

Protocol throughout: the mechanism-search-v1 harness unchanged (prompt sha `845e21e7…`, 50 tool calls, 300 s, effort medium,
external workspace, scanner, freeze), only the model id differs. GPT-5.6 was never re-run; its numbers are the frozen
reference. Measures are the frozen definitions in `scripts/mx_metrics.py`.

## 1. Ladder on the held-out set (9 instances: HA, HB, HC × 3 projects)

| Model | Valid runs | Answered | Acc@1 (Wilson 95%) | HA | HB | HC | Misses | Decision |
|---|---|---|---|---|---|---|---|---|
| gpt-5.6 (reference) | 44 | 43 | 0.977 (0.88–1.00) | 14/15 | 14/14 | 15/15 | 1 no-answer | reference |
| gpt-5.5 (L1) | 27 | 27 | 1.000 (0.88–1.00) | 9/9 | 9/9 | 9/9 | 0 | STEP_DOWN (≥ 0.90) |
| gpt-5 (L2) | 27 | 17 | 0.630 (0.44–0.79) | 5/9 | 7/9 | 5/9 | 10 timeouts, 0 misrankings | TOO_WEAK (answered 0.63 < 0.70) |

- gpt-5's drop is entirely no-answer: in 9 of its 10 timeouts it had already displayed and fully read the gold; it is slower
  per step (median 22 model calls, 238 s), not lost. That is the operational-collapse outcome the brief said not to count.
- gpt-5.5 at the frozen budget is operationally sound (every run answered, median 12 tool calls) and at ceiling on instances
  whose gold is pinned by documentation.
- The ladder was paused here (W4, W5); rungs below gpt-5 were not run, because the user's goal is a current model.

## 2. Stage A: the frozen breakers on gpt-5.5 (AMENDMENTS W5, W7, W8)

Eight instances GPT-5.6 had missed, re-hosted byte-for-byte, plus the matched control of the CHART pair. 32 valid runs.

| Instance | What it is | gpt-5.5 | GPT-5.6 ref | gpt-5.5 gold ranks | Rank-1 when wrong |
|---|---|---|---|---|---|
| FZ-CHART-PIE-CONTROL-03 | same fault, undecomposed method (0 hops) | **5/5** | 5/5 | 1 1 1 1 1 | — |
| FZ-CHART-PIE-TREATMENT-03 | same fault behind a 5-hop chain through two large hosts; definer hop reads backwards | **0/5** | 0/5 | 6 6 6 6 >10 | entry point ×2, `PlotUtilities::drift` ×3 |
| FZ-CLOSURE-12-OWN-001 | ownership split, omission gold | 1/5 | 0.20 | 2 2 2 1 2 | `computeMayUse` ×2, `Candidate::canInline` ×2 |
| FZ-CLOSURE-131-OWN-001 | ownership split, static-table writer | 0/5 | 0.33 | 6 6 6 2 5 | `NodeUtil::isSimpleNameChars` ×5 |
| RH-ADV-DEPTH-01 | 5-hop chain, decoy doc contradicts its code | 0/3 | 0/3 | 3 3 3 | entry point ×2, `overlay` |
| RH-ADV-MASK-01 | distant decisive evidence (second caller) | 0/3 | 0.33 | 3 2 2 | entry point ×3 |
| RH-LB-CHART-01-ADAPTER | definer/adapter split, convention under-specified | 0/3 | 0.33 | 3 2 3 | `CompassPlot::ring` ×2, entry point |
| RH-LB-COMPRESS-07-ADAPTER | adapter chain with a correct sibling | 0/3 | 0/3 | 4 3 3 | entry point ×2, `tally` |

- **Pooled over the eight breakers: 1/27.** With the control: 6/32 = 0.188 (Wilson 0.09–0.35).
- **Every miss is attribution after discovery.** In all 26 wrong runs the gold's fault line was displayed, the gold read in
  full, and a test executed. Rank-1 categories: a declared decoy 18, the entry point 8. No search failures, no timeouts.
- **The CHART pair isolates the chain on a current model.** Treatment and control share the fault, the trigger, the failure
  (`87.5` vs `112.5`), the prompt and the budget; the arms differ only in the 5-hop decomposition. gpt-5.5: 0/5 vs 5/5. The
  W5 prediction (treatment ≤ 0.2, control 1.0) was met.
- **gpt-5.5 is at or below GPT-5.6 on every instance**, and below it on three (ADV-MASK-01, LB-CHART-01-ADAPTER,
  CLOSURE-131); the other five are equal. The held-out ceiling and the breaker floor sit
  side by side in the same model: the difference is the instance design, not the model's competence.

## 3. What distinguishes the instances that break current models

Across GPT-5.6 (September blocks, mechanism-search screening) and gpt-5.5 (Stage A), the instances with Acc@1 near zero share
a shape that the instances at ceiling lack:

1. a chain of several hops, so the fault's effect is separated from its origin;
2. a correct hop whose code looks locally wrong (an operand order that reads backwards, a mask that looks missing, a
   documented promise the decoy does not keep), or an ownership split in which a decision site looks responsible;
3. a quiet gold that is the idiomatic reading of its own javadoc;
4. no local restatement of the convention at the gold.

Chains without element 2 (the September 5-hop variants, 0.88–1.00 for GPT-5.6; Claude Opus 3/3) and element 2 without a chain
in documented form (the nine held-out instances, gpt-5.5 27/27) both sit at ceiling. The interaction is what Stage B is designed
to measure on fresh bugs (STAGE_B_DESIGN.md).

## 4. Caveats that belong in any write-up

- **Gold ownership in the frozen breakers.** CHART-PIE-TREATMENT-03's hops 3, 4 and 5 are behaviourally equivalent repair
  sites (one-line edits at any of them pass the trigger); its gold is fixed by the label and by the control arm's unique
  attribution, not by in-repository documentation. ADV-DEPTH-01's decoy contradicts its own javadoc. Fresh Stage B instances
  must pin the gold externally (second caller, test, distant geometry) while keeping it locally under-specified.
- **Sample sizes.** 3 to 5 runs per instance; per-instance intervals are wide. The pooled 1/27 is not.
- **Scanner false positive (W7)** cost one run and a re-acceptance; the fix only narrows a sibling-token test to text that
  is actually foreign to the run's own workspace.
- **Closure signatures** were captured as the first assertion line only; this affects one secondary process measure.

## 5. Cost

Run cost in this root $28.90 (L1 $9.29, L2 $6.06, Stage A $12.60, three smokes $0.95), plus health probes at about $0.008
each. Cumulative across mechanism-search-v1 and this root: about $58.
