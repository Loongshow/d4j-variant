# Weaker-model results (weaker-model-v1), as of 2026-10-14

Two questions were asked of this root, in order.

1. **Ladder (PREREGISTRATION.md).** Does a weaker OpenAI model, under the frozen protocol, lose accuracy on the nine held-out
   instances that GPT-5.6 solved?
2. **Stage A (AMENDMENTS W5), after the user's redirection.** Do the frozen instances that GPT-5.6 itself missed also break
   gpt-5.5, and does the matched CHART pair isolate the chain?

Protocol for every run in this root: the mechanism-search-v1 harness (prompt sha `845e21e7…`, 50 tool calls, 300 s, effort medium,
external workspace, scanner, freeze) with the server tree byte-identical to mxF0; only the model id differs (the scanner and
freeze library took the bug-id and precision fixes of W6 and W7). GPT-5.6 was never re-run. Its held-out and RH reference
numbers come from mechanism-search-v1 under this protocol; its references for the four FZ instances come from the September
roots (the canonical Closure block and diagnostic-noncanonical-v3) under the same base prompt, 50 tool calls and 300 s, but
before the external-workspace, scanner and freeze hardening. Measures are the frozen definitions in `scripts/mx_metrics.py`.

## 1. Ladder on the held-out set (9 instances: HA, HB, HC × 3 projects)

| Model | Valid runs | Answered | Acc@1 (Wilson 95%) | HA | HB | HC | Misses | Decision |
|---|---|---|---|---|---|---|---|---|
| gpt-5.6 (reference) | 44 | 43 | 0.977 (0.88–1.00) | 14/15 | 14/14 | 15/15 | 1 no-answer | reference |
| gpt-5.5 (L1) | 27 | 27 | 1.000 (0.88–1.00) | 9/9 | 9/9 | 9/9 | 0 | STEP_DOWN (≥ 0.90) |
| gpt-5 (L2) | 27 | 17 | 0.630 (0.44–0.79) | 5/9 | 7/9 | 5/9 | 10 timeouts, 0 misrankings | TOO_WEAK (answered 0.63 < 0.70) |

- gpt-5's drop is entirely no-answer: in 9 of its 10 timeouts it had already displayed and fully read the gold; it is slower
  per step (answered runs: median 22 model calls, 238 s; all 27 valid runs: median 276 s), not lost. That is the operational-collapse outcome the brief said not to count.
- gpt-5.5 at the frozen budget is operationally sound (every run answered, median 12 tool calls) and at ceiling on instances
  whose gold is pinned by documentation.
- The ladder was paused here (W4, W5) at the user's redirection: the preregistered next step, the untried intermediate gpt-5.4
  (stage step 4), and the rungs below gpt-5 were not run, so no stop rule (A, B or C) was reached and the preregistered
  weaker-model question stays open; the user's goal is a current model.

## 2. Stage A: the frozen breakers on gpt-5.5 (AMENDMENTS W5, W7, W8)

Seven instances GPT-5.6 had missed, re-hosted with byte-identical variant and test patches and unchanged golds (the four FZ
manifests were rewritten for the re-host, the two Closure ones relabelled to the L20 namespace, W6c), plus the matched control
of the CHART pair: eight instances, 32 valid runs.

| Instance | What it is | gpt-5.5 | GPT-5.6 ref | gpt-5.5 gold ranks | Rank-1 when wrong |
|---|---|---|---|---|---|
| FZ-CHART-PIE-CONTROL-03 | same fault, undecomposed method (0 hops) | **5/5** | 5/5 | 1 1 1 1 1 | — |
| FZ-CHART-PIE-TREATMENT-03 | same fault behind a 5-hop chain inserted across four host classes (only Plot is over 1500 lines); definer hop reads backwards | **0/5** | 0/5 | 6 6 6 6 >10 | `PiePlot::getArcBounds` ×2 (the entry point, which the key also lists as a decoy; scored DECOY), `PlotUtilities::drift` ×3 |
| FZ-CLOSURE-12-OWN-001 | ownership split, omission gold | 1/5 | 0.20 | 2 2 2 1 2 | `computeMayUse` ×2, `Candidate::canInline` ×2 |
| FZ-CLOSURE-131-OWN-001 | ownership split, static-table writer | 0/5 | 0.33 | 6 6 6 2 5 | `NodeUtil::isSimpleNameChars` ×5 |
| RH-ADV-DEPTH-01 | 5-hop chain, decoy doc contradicts its code | 0/3 | 0/3 | 3 3 3 | entry point ×2, `overlay` |
| RH-ADV-MASK-01 | distant decisive evidence (second caller) | 0/3 | 0.33 | 3 2 2 | entry point ×3 |
| RH-LB-CHART-01-ADAPTER | definer/adapter split, convention under-specified | 0/3 | 0.33 | 3 2 3 | `CompassPlot::ring` ×2, entry point |
| RH-LB-COMPRESS-07-ADAPTER | adapter chain with a correct sibling | 0/3 | 0/3 | 4 3 3 | entry point ×2, `tally` |

- **Pooled over the seven breakers: 1/27.** With the control: 6/32 = 0.188 (Wilson 0.09–0.35).
- **Every miss is attribution after discovery.** In all 26 wrong runs the gold's fault line was displayed, the gold read in
  full, and a test executed. Rank-1 categories by the frozen `rank1_category`: a declared decoy 18, the entry point 8 (the two
  CHART-treatment `getArcBounds` runs count as decoys). No search failures, no timeouts. Blind
  labelling (W9) judged the rank-1 answer defensible in 4 of the 26 (the three CHART-treatment runs ranking `drift`, one
  DEPTH-01 run), partly defensible in 5 (CLOSURE-131 ×4, CLOSURE-12 ×1) and not defensible in 17.
- **The CHART pair reproduces the chain-shaped drop on a current model.** Treatment and control share the fault, the trigger,
  the failure (`87.5` vs `112.5`), the prompt and the budget. gpt-5.5: 0/5 vs 5/5, the pattern GPT-5.6 had shown on the same
  pair. The arms differ in the 5-hop decomposition, but that decomposition brings with it a mid-chain definer whose code reads
  backwards and the loss of a uniquely owned gold (section 4), so the pair does not separate the chain's own contribution from
  those two; Stage B's 2×2 is designed to. The W5 expectation (treatment ≤ 0.2, control 1.0), recorded before any Stage A call
  but restating GPT-5.6's and Claude's results on the same pair rather than a preregistered prediction (W10), was met. Stage A
  sits outside the preregistered ladder: its instances were chosen because GPT-5.6 missed them, four are
  mechanism-search EXPLORATORY-tier instances, none of PREREGISTRATION.md's success criteria or stop rules applies to it, and
  W5 defers any chain claim to Stage B.
- **gpt-5.5 is at or below GPT-5.6 on every instance**: equal on five (three of them references already at 0/n, where no
  improvement was possible) and nominally below on three (ADV-MASK-01 1/3 → 0/3, LB-CHART-01-ADAPTER 1/3 → 0/3, CLOSURE-131
  2/6 → 0/5), differences within sampling noise (two-sided Fisher p = 1.0, 1.0, 0.45). The held-out ceiling and the breaker
  floor sit side by side in the same model: the gap lies in the instances, not in the model's competence; which design
  features drive it is Stage B's question.

## 3. What distinguishes the instances that break current models

Across GPT-5.6 (September blocks, mechanism-search screening) and gpt-5.5 (Stage A), the instances with Acc@1 near zero share
a shape that the instances at ceiling lack:

1. a chain of several hops, so the fault's effect is separated from its origin;
2. a correct hop whose code looks locally wrong (an operand order that reads backwards, a mask that looks missing, a
   documented promise the decoy does not keep), or an ownership split in which a decision site looks responsible;
3. a quiet gold that is the idiomatic reading of its own javadoc;
4. no local restatement of the convention at the gold.

Chains without element 2 (the September treatment arms without an odd hop: GPT-5.6 43/44 pooled on the nine 5-hop arms, 37/42
on the six 6-hop arms with three of those five misses timeouts, 0.80–1.00 per arm on answered runs, mechanism-search-v1
`mining/run_data.json`; Claude Opus 3/3) sit at ceiling. So do the nine held-out instances (gpt-5.5 27/27), but they are helper
chains of two to four hops whose gold is pinned by documentation (HELDOUT_CONFIRMATION_PLAN.md: "Documentation decides
ownership"), so they test element 2 with a shorter chain and a stated convention, not element 2 without a chain. No arm so far
has varied chain length or documentation pinning separately; the interaction is what Stage B is designed to measure on fresh
bugs (STAGE_B_DESIGN.md).

## 4. Caveats that belong in any write-up

- **Gold ownership in the frozen breakers.** CHART-PIE-TREATMENT-03's hops 3, 4 and 5 are behaviourally equivalent repair
  sites (one-line edits at any of them pass the trigger); its gold is fixed by the label and by the control arm's unique
  attribution, not by in-repository documentation. ADV-DEPTH-01's decoy contradicts its own javadoc, and the variant also fails a
  second test (mechanism-search X3). LB-COMPRESS-07-ADAPTER's correct sibling makes an entry-point repair equally small.
  Mechanism-search's P4 revisions that repaired those two features returned GPT-5.6 to 3/3 on each (exploratory, n = 3 per
  arm), so the 0/3 results on the unrepaired re-hosts are partly a property of those defects; 11 of the 27 breaker runs sit on
  these three instances. Fresh Stage B instances
  must pin the gold externally (second caller, test, distant geometry) while keeping it locally under-specified.
- **Sample sizes.** 3 to 5 runs per instance; per-instance intervals are wide. The pooled 1/27 is not, but it describes these
  27 runs on seven instances that derive from five underlying bugs (CHART-PIE-TREATMENT-03 and LB-CHART-01-ADAPTER share
  `PiePlotTests::test2986548`; ADV-DEPTH-01 and ADV-MASK-01 share `ConversionTest::testLang1112` and an identical test patch)
  and were selected because GPT-5.6 failed on them; it is not an estimate of the failure rate on fresh instances of this shape.
- **Scanner false positive (W7)** cost one run and a re-acceptance: FZ-CHART-PIE-CONTROL-03 run-001 (gold rank 1) was stopped
  on lines from its own test file, stays excluded under the frozen rule and was replaced. The scanner, a guarded script, was
  changed between that stop and the rest of Stage A; the fix only narrows a sibling-token test to text that is actually foreign
  to the run's own workspace, the freeze digest was refreshed and Phase 1 re-accepted with a third smoke run before Stage A
  resumed.
- **Closure signatures** were captured as the first assertion line only; this affects one secondary process measure.

## 5. Cost

Run cost in this root $28.90 (L1 $9.29, L2 $6.06, Stage A $12.60, three smokes $0.95), plus 128 health probes at the
mechanism-search-v1 ledger estimate of about $0.008 each (about $1; this root records probe status and wall time, not cost).
Cumulative across mechanism-search-v1 ($28.83, probe estimates included) and this root: about $58 in run cost, about $59 with
this root's probes.
