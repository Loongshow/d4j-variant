# Stage B preregistration (2026-10-14; block 1 = B1 + B3 frozen with plans/B_stageB_gpt55_block1.json; B2 withdrawn, W14; B2' is added as block 2 under the same rules when audited)

## Question

On fresh instances whose gold is externally pinned and uniquely owned, does placing the same fault behind a 5-hop delegate
chain built with the supervisor's recipe (two existing classes of at least 1500 lines, hops inserted at anonymous interior
points, a procedural narrative lie in the facade javadoc) lower gpt-5.5's method-level Acc@1 relative to the same fault one
hop below the facade, and does a correct hop that looks locally wrong change that effect?

## Decisions fixed by the user (2026-10-14)

1. The facade lie stays inside the chain arm (the chain arm is the recipe as the supervisor ran it); it is not a separate factor.
2. Evaluation model: gpt-5.5 under the frozen protocol (server w55, `reasoning_effort: medium`, 50 tool calls, 5 test runs,
   300 s). GPT-5.6 is not run; its frozen records are the only reference. Running GPT-5.6 on a cell that drops is a possible
   later amendment, not part of this block.
3. Projects: Lang (`StringUtils` or `ArrayUtils`), Math (`FastMath` or `DSCompiler`), Chart (`DatasetUtilities`, outside
   `org.jfree.chart.plot`). One fresh fault per project, hosted on the existing fixed checkouts of bug-1 of each project
   (`construction/fresh/<Project>`, identical to mechanism-search-v1's fixtures).

## Design

Three bugs x four cells x 5 runs = 60 runs, all on gpt-5.5. Within a bug, every cell shares the fault line, the trigger test,
the failing assertion and its actual/expected values, the prompt and the budget. Cells:

| Cell | Hops from facade to gold | Odd hop | Facade lie | What it is |
|---|---|---|---|---|
| C00 | 1 (gold is a helper the facade calls) | no | no | control |
| C01 | 1 | yes: an odd-looking correct sibling helper in the same file | no | asymmetry alone |
| C10 | 5, across two host classes >= 1500 lines, anonymous insertion | no | yes | the recipe |
| C11 | 5, as C10 | yes: one mid-chain hop written in a valid but locally odd form | yes | the CHART-PIE-03 shape |

Constraints every cell must meet before any run (checked by the builder and by an independent audit that did not see the
builder's notes):

- **Gold never at the entry point.** In C00/C01 the test calls the facade, which calls the gold; the facade itself is unchanged
  except for the delegation.
- **Single owner.** No one-line edit at any method other than the gold makes the trigger pass while staying consistent with the
  documentation of the method edited (ownership-counterfactual gate; every hop and the facade are tried). Refined before any run
  (AMENDMENTS W13): the edit must also keep every method on the trigger path used as its documentation describes; a passing edit
  that replaces the gold's result with another implementation or makes a hop's output dead is a *bypass*, recorded per bug as a
  limitation but not a second owner.
- **Externally pinned, locally under-specified.** The gold's javadoc, read idiomatically, does not state the omitted step; a
  second production caller with a passing test (or distant arithmetic) fixes the correct behaviour. The odd hop is pinned the
  same way. Neither the lie nor any comment names the gold, the odd hop or the fault.
- **Exactly one failing test method** on the variant beyond the fixed baseline (full-suite comparison recorded in
  `validation.json`); the trigger passes on the fixed checkout.
- **No LLM in construction.** The lie sentence is hand-written in the host file's own documentation voice; hop names are
  neutral and do not reuse names from earlier studies (`ring`, `rim`, `drift`, `nudge`, `shift`, `overlay`, `tally`, ...).
- **Scanner clean** under the W7 scanner; cue tokens from sibling cells must not leak (each cell's workspace holds only its own
  patch).

## Measures (frozen definitions, `scripts/mx_metrics.py`)

Primary: Acc@1 per cell pooled over the three bugs (n = 15 per cell), Wilson 95% intervals; chain main effect
(C10 + C11) vs (C00 + C01); odd-hop main effect (C01 + C11) vs (C00 + C10); interaction (C11 - C01) - (C10 - C00).
Secondary: gold rank, first-gold step, tool calls, reasoning tokens, wall time; for every miss the mechanical split
(NO_ANSWER / SEARCH_FAILURE / DISCOVERY_WITHOUT_INSPECTION / ATTRIBUTION_FAILURE) and a blind two-lens Phase 7 label.

## Expectations stated before any run

From the records (STAGE_B_DESIGN.md lever table): chains without an odd hop did not move GPT-5.6's rank (43/44 on 5-hop arms),
the lie was read and ignored on the one 2-hop instance, and the only shape that broke both current models bundled chain and
odd hop. Stated expectations: C00 and C01 at or near ceiling (>= 0.8); C10 near ceiling unless the lie plus the 5-hop chain
does work the 2-hop test did not reveal (C10 <= 0.6 would say so); C11 the lowest cell. The result of interest is the
interaction. If C11 >= 0.8 under the single-owner constraint, the CHART-PIE-03 drop does not generalise beyond instances
with an ownership split, and that is the finding.

## Execution

- Plans interleave cells and bugs (slot order C00, C10, C01, C11 per bug, bugs rotating) so time-of-day and provider drift
  do not align with a cell; the frozen driver's health gate, stall rules and halt rules apply unchanged.
- Cost cap for the block: $25 run cost. Timeouts above 30% in any cell are reported as operational and that cell is not extended.
- No instance is run before its `validation.json` is accepted and the independent ownership audit is recorded in
  `construction/stageB/audits/`.
- Builders and auditors are separate agents; the labellers for misses do not see cell identity.

## Instance table (variant ids filled at packaging; construction records in construction/stageB/)

| Bug | Project / facade (entry point) | Gold (identical text and fault in all four cells) | Trigger (existing test) and signature | Hosts of hops 1-5 (C10/C11; seed 1014 recipe draw) | Odd element (C01 sibling / C11 hop 3) | Variant ids |
|---|---|---|---|---|---|---|
| B1 | Lang / `StringUtils.indexOfAnyBut(CharSequence, char...)` | `isAnyOf(cs, index, searchChars, pair)`: the comparison of the second unit of a surrogate pair is omitted (C00/C01 in `StringUtils`; C10/C11 in `ArrayUtils`) | `StringUtilsEqualsIndexOfTest::testIndexOfAnyBut_StringCharArrayWithSupplementaryChars`, `expected:<2> but was:<0>` | ToStringStyle, StrBuilder, Conversion, DateUtils, ArrayUtils | pair-start predicate written as a triple negation (`!(index >= len-1 \|\| !isSurrogate \|\| isLowSurrogate)`) instead of `isHighSurrogate` | CTV-860AD4, CTV-73BEA3, CTV-4DE6D2, CTV-5818E6 |
| B2 | Math / `FastMath.atanh(double)` | `smallArgumentSeries(a)`: the series tier for 0.031 < a <= 0.087 is omitted (C00/C01 in `FastMath`; C10/C11 in `BOBYQAOptimizer`) | `FastMathTest::testHyperbolicInverses`, `expected:<0.0> but was:<7071.0>` | RealVector, DSCompiler, BlockRealMatrix, Dfp, BOBYQAOptimizer | sign restoration as a raw-bits XOR (the idiom of `FastMath.copySign`) instead of `copySign` | WITHDRAWN after audit (W14: a half-angle reduction at the facade/hop 4 is a competing repair); replaced by B2' when its audit is CONFIRMED |
| B3 | Chart / `DatasetUtilities.findStackedRangeBounds(CategoryDataset, double)` | `signedSums(dataset, column)`: the strict `< 0.0` guard of the negative total becomes `else`, admitting NaN (C00/C01 in `DatasetUtilities`; C10/C11 in `AbstractCategoryItemRenderer`) | `DatasetUtilitiesTests::testFindStackedRangeBounds_CategoryDataset2`, `expected:<2.0> but was:<NaN>` | StandardChartTheme, AbstractXYItemRenderer, AbstractRenderer, ValueAxis, AbstractCategoryItemRenderer (org.jfree.chart.plot excluded) | stack extent formed as `top - height` instead of `base + negative` | CTV-2D0374, CTV-C5E772, CTV-4D1CCD, CTV-E94DC6 |

External pins (recorded per spec as `evidence` and `ownership_tests`): B1 `indexOfAny` and the CharSequence overload of
`indexOfAnyBut` compare the second unit explicitly, `containsOnly` is a passing second caller; B2 `asinh` keeps four tiers,
the class documents 0.5-ulp accuracy, `DSCompiler.atanh` and `DfpTest.testAtanh` pass; B3 `StackedAreaRenderer.getStackValues`
and the TableXYDataset overload skip NaN, `StackedBarRenderer.findRangeBounds` passes `getBase()` with its own passing test.
In no cell does the gold's javadoc state the omitted step.

Cell structure, identical for the three bugs: C00/C01 facade -> gold, with a plain/odd helper the facade also calls (the
helpers follow the facade directly in its file); C10/C11 facade (pure delegate with the lie, the recipe's `rewrite_facade`)
-> hop 1 -> hop 2 -> hop 3 (plain/odd) -> hop 4 -> hop 5 = gold, each hop inserted at the recipe's seeded anonymous anchor in
a different class of at least 1500 lines.
