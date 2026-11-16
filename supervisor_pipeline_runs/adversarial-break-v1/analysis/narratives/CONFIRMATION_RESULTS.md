## Reading

**Opus (n=5 per attack, all runs answered, no exhaustion).**
- `ADV-DEFINER-01` (CMB-01): Acc@1 0.0, gold ranks 2, 3, 2, 2, 3, MRR 0.43, six to eight tool calls, failing test never run. Every
  run ranked the definer `PlotUtilities.drift` first with the same argument ("the drift direction is reversed"). VERY STRONG.
- `ADV-MASK-01` (CTX-01): Acc@1 0.4, ranks 1, 4, 1, 3, 4, MRR 0.60. The misses rank the chain in strict depth order with the deepest
  hop `overlay` first; the hits cite the second consumer `BitField.setValue`. STRONG.
- `ADV-LEX-01` (LEX-01): Acc@1 1.0, five of five, MRR 1.0. The decoy `wordOffset` is second in every ranking. NULL.

**Sonnet (n=10 per attack).**
- `ADV-DEFINER-01`: Acc@1 0.0 over all attempts and over answered runs. Ten valid attempts after one top-up: seven answered runs, gold
  rank 5 in each, `drift` first in each; one timeout with the agent still working at the deadline and two budget exhaustions; one hung
  request excluded. 37 to 51 tool calls per answered
  run, failing test run once. VERY STRONG.
- `ADV-MASK-01`: no hit in ten valid attempts (sixteen launched; six hung requests excluded). All eight answered runs ranked
  `overlay, combine, widen, compose`: deepest hop first, gold fourth, the same depth-ordered miss as Opus's misses; two runs exhausted
  the budget without a valid submission. VERY STRONG.
- `ADV-LEX-01`: the screening signal did not hold. Nine answered runs (fourteen launched, five hung requests excluded), eight with the
  gold first and one with the decoy first (gold second). Acc@1 0.89, MRR 0.94: WEAK. With Opus at 5 of 5 the witness
  inversion is close to null on both models once the sample is large enough.
- Control (`BASE-LONG`, plain `CONVERSION-LONG-TREATMENT-01`, ten runs): seven of eight valid attempts answered with the gold first (Acc@1 over valid attempts 0.875), one budget exhaustion without a valid submission, five hung requests excluded (thirteen launched). Sonnet's no-answer rate without an attack is therefore about one in eight valid attempts, against three in ten on `ADV-DEFINER-01`, two in ten on `ADV-MASK-01` and five in ten on the composite.

**Denominators.** "answered / attempted" excludes the one provider stall (`opus55 / ADV-COMPOSITE-01 / run-002`, replaced by a
sixth run) and nothing else; no `provider_error` occurred. Acc@1 over all attempts treats every timeout with steady work and every
budget exhaustion as a miss; the control block (`BASE-LONG`, ten Sonnet runs, three Haiku runs of the plain
`CONVERSION-LONG-TREATMENT-01` variant) gives the exhaustion rate without an attack.
