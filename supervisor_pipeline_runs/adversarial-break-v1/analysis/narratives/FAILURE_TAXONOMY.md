## Reading: what each class looked like in the trajectories

The table above is assigned mechanically from pre-registered roles. This section says what the runs in each class actually did.
Counts are in the table; the patterns below hold for every run in the class unless stated.

**OWNERSHIP_MISATTRIBUTION (definer blamed for the adapter's sign): `ADV-DEFINER-01`, `ADV-COMPOSITE-01`, both models.**
Every miss ranked `PlotUtilities.drift` first. The two models produce different orderings behind it. Sonnet's ranking is
always `drift, rim, ring, getArcBounds, nudge, shift`: the definer, then the shallower hops in order of closeness to the
facade, with the gold adapter fifth and the terminal sixth. Its stated reason is that drift's subtraction is "reversed" and
the adapter "just multiplies by explodePercent". Opus's ranking is `drift, nudge|rim, rim|nudge, ring, getArcBounds, shift`:
the definer first, the gold second or third. Both hand-simulate the first assertion (100 + 0.25 x 50 = 112.5 against the
expected 87.5), conclude the displacement sign is wrong, and attribute the sign to the method that defines the displacement.
Neither model looked for a contract that fixes the definer's convention: no Sonnet run and only one Opus run (composite
run-001) ever opened `PlotUtilitiesTests`, and that one run is the only hit across the two attacks.

**DEPTH_PRIOR (deepest hop blamed for a shallow contract fault): `ADV-MASK-01`, Opus misses and the one Haiku answer.**
The misses rank `overlay, combine, widen, compose`: the deepest hop first and then strictly by depth, gold fourth
(Kendall tau against depth = 1.0 in two of the three Opus misses). The stated reason is overlay's field/word shift asymmetry
("the mask leaves out the dstPos offset"). Opus's two hits ranked `compose` first with `overlay` second and cite the second
consumer: "BitField.setValue passes overlay a mask that is already shifted, so compose is the most likely fix site". The
attack is therefore decided by whether the model reads the second consumer of the deepest hop before it submits.

**LEXICAL_MISATTRIBUTION (decoy carrying the gold's words blamed): `ADV-LEX-01`, Sonnet only.**
The single wrong submitted ranking in screening put the decoy `BitField.wordOffset` first and the generic gold `apply`
second; every other answered run (Sonnet, Haiku, and all five Opus runs) put `apply` first with `wordOffset` second.
Opus's five evidence chains all trace the executed value through `apply` and treat the decoy as an unexecuted or harmless
helper. The decoy attracts attention (it is second in every ranking) but overturns the value-tracing verdict only in the
weaker model and only sometimes.

**NO_VALID_RANKING_BUDGET / NO_VALID_RANKING_TIMEOUT (agent exhaustion): Haiku on every Chart attack, Sonnet on some.**
Haiku used all 50 tool calls without a schema-valid submission in every `ADV-DEFINER-01` and two of three `ADV-MASK-01`
runs, and in two of three runs of the plain control variant on Lang, so Haiku's exhaustion is baseline behaviour under this
protocol, not an effect of the attacks. Sonnet's timeouts are runs that were still issuing commands at 300 s (17 to 49 model
calls each); they are no-answers and count as misses in the "all attempts" Acc@1. The Sonnet control block (ten runs of the
plain variant) is the baseline for how often that happens without an attack.

**INFRASTRUCTURE (excluded from every denominator).** One run: `opus55 / ADV-COMPOSITE-01 / run-002`, a provider stall
(one model call, then silence to the deadline); rule and evidence in `diagnostic/PROVIDER_STALL_RULE.md`. No `provider_error`
status occurred in the root.

**CONTEXT_LOSS (one run).** `haiku45 / ADV-LEX-01 / run-002` overflowed the model's context window with its own reads (the API refused the
44th request at 643k tokens) and never submitted; it is counted as a no-answer, not excluded (`diagnostic/PROVIDER_STALL_RULE.md`, rule 3).

**Classes not observed.** DISCOVERY_FAILURE (gold never exposed) did not occur in any answered run: every model exposed the
gold method's body before submitting (first exposure at step 3 to 16). CANDIDATE_OVERLOAD and SEARCH_DIVERSION did not occur: `ADV-OVERLOAD-01` and `ADV-REGISTRY-01` were solved by both weaker models in every answered run,
and the gold was inside the top 10 of every submitted ranking in the root. FAILURE_SIGNAL_MISREAD did not occur as a
primary class: the models read the expected values from the test source, so coarsening the assertion text
(`ADV-OVERLOAD-01`, `ADV-COMPOSITE-01`) did not change what they knew.

**Rejected submissions (harness validation, recorded in `rejected_submissions` / `rejected_gold_rank`).** 8 runs had a first
structured submission refused with `method_not_found` because a filler prediction near the bottom of the list named a method that
does not exist (for example `RingPlot::draw`). 7 of them resubmitted a valid ranking within budget, and in 7 of those the
gold's rank was unchanged between the refused and the accepted payload, so the refusal did not alter the attribution result.
1 run (sonnet46 ADV-COMPOSITE-01 run-001, gold rank 5 in the refused payload) ran out
of budget while looking for a replacement filler and is recorded as NO_VALID_RANKING_BUDGET; by its refused payload it is an
OWNERSHIP_MISATTRIBUTION miss as well. Either way it is a miss over all attempts; the refusal never turned a hit into a miss.
