Hi Hong Jin,

Update on the weaker-model direction, now with a result worth building on.

**Ladder.** Under the frozen protocol (same prompt, tools, 300 s budget, scoring), gpt-5.5 solved all 27 runs on the nine
held-out instances that GPT-5.6 had solved. gpt-5 answered only 17 of 27 within the budget: every miss was a 300 s timeout, and in 9 of
the 10 it had already found and read the faulty method; none of the 17 answered runs misranked, so at this budget it is
operationally too slow rather than demonstrably a worse localizer (its ranking on the ten unanswered runs is unobserved).
I paused the ladder there (W5) rather than run the preregistered next rung, the untried intermediate gpt-5.4, or the older
models below gpt-5, since the thesis should be about a current model; no preregistered stop rule was reached, so the ladder
is paused rather than closed.

**Stage A: the instances GPT-5.6 had missed, re-run unchanged on gpt-5.5.** Seven instances GPT-5.6 had missed (three
re-hosted frozen instances, the CHART treatment arm and two Closure ownership splits, 5 runs each; four exploratory S1
screening instances copied from mechanism-search-v1, 3 runs each) plus the matched control of the CHART pair: eight
instances, 32 valid runs. One control run was excluded by a scanner false positive and replaced, and the scanner's
sibling-token test was narrowed mid-block (W7).

- gpt-5.5 got **1 of 27** right on the seven breakers.
- The matched pair holds the fault, the test and the failure values fixed; the treatment arm adds the 5-hop decomposition
  (CompassPlot.ring → StandardDialScale.rim → PlotUtilities.drift → Plot.nudge → ShapeUtilities.shift, across five existing
  classes of which only Plot.java exceeds 1500 lines) together with a correct mid-chain hop whose arithmetic reads backwards
  and an ownership split in which hops 3 to 5 are equivalent repair sites, so it contrasts that bundle against the
  undecomposed method rather than isolating the chain. **gpt-5.5: treatment 0/5, control 5/5.** This matched the expectation
  written into amendment W5 before the Stage A calls; Stage A is a post-hoc addition to the preregistration, and that
  expectation restated GPT-5.6's 0/5 vs 5/5 and Claude's 0/3 on the same pair rather than forecasting anything new.
- Every one of the 26 misses has the mechanical shape we wanted: the gold's faulty line displayed, the method read in full,
  a test executed, and another method ranked first. No search failures, no timeouts. Two qualifications: the blind labellers
  judged the rank-1 answer defensible in 4 of the 26 (the three CHART-treatment runs that ranked `drift` first, one DEPTH-01
  run citing the decoy's javadoc contradiction) and partly defensible in 5 more (all Closure); and the DEPTH-01 and
  COMPRESS-07 misses (6 of the 26) fall on instances whose validity-repaired revisions GPT-5.6 solved 3/3, so those two
  floors may reflect instance under-specification as much as model failure.
- Blind labelling (two labellers per run; the 11 disagreements adjudicated by a third) puts entry-point ranking first (12 of
  26, with both labellers agreeing in 11), then evidence-integration failures (6, of which 5 were settled by the adjudicator)
  and convention priors (5). gpt-5.5 is at or below GPT-5.6 on every instance and below it on three (by one or two runs at
  n = 3 to 6, so the intervals overlap).

**What this means.** The same current model sits at ceiling on documented, single-owner instances and near zero on the seven
Stage A breakers (1/27). Two of those pair a long chain with a correct hop that looks locally wrong next to a quiet gold
(CHART treatment 0/5, DEPTH-01 0/3); the rest break through ownership splits, distant decisive evidence and definer/adapter
attribution. The chain alone never produced more than a single misranking in any September chain-only pair; the chain plus
that asymmetry took both GPT-5.6 and gpt-5.5 from 5/5 to 0/5 on the one CHART pair, but which element drives it is not
isolated there, and GPT-5.6 solved every answered run on at least one September instance of the same shape
(MATH-NORM-TREATMENT-01: 4/4 answered at rank 1, 3 timeouts).

**Your generator.** It is the same recipe as the copy I audited (two large hosts, anonymous insertion, facade narrative lie).
The lie has been tested on GPT-5.6 only with the generator's own two-hop chain, on a ceiling instance
(NUMBERUTILS-TREATMENT-01: 5/5 at rank 1, the lie read in every run and diverting none); the later September variants
(NUMBERUTILS-02 and the 5-hop pairs) carried no lie, so its effect beside a 5-hop chain on a non-ceiling instance is untested. So I plan to use your machinery for Stage B and include the lie, with the asymmetry element added.

**Stage B proposal.** Fresh bugs in Lang, Math and a third project, each as a 2×2: chain (your recipe, with the lie) × odd
correct hop, 5 runs per cell on gpt-5.5, about $20. Golds pinned by evidence elsewhere in the repository (second caller,
passing test, distant geometry) but not restated locally, so an ownership audit cannot dissolve the result; the CHART
instance does not meet that bar, which is why I will not rest the claim on it alone.

Three choices for you: keep the lie inside the chain arm or make it a third factor (double the runs); gpt-5.5 at 300 s with
GPT-5.6 as reference, or re-run GPT-5.6 on the fresh pairs too; and the third project (your screener finds targets in Lang
and Math, none in JacksonCore; Chart outside the pie-plot classes would work).

Spend so far: about $29 in this phase, about $58 across both.

Best regards
