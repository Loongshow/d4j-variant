# Promising mechanisms: screening and Phase 4 diagnostics (all EXPLORATORY)

"Promising" is the preregistered screening class. The S1 instances here are re-hosted adversarial and controlled variants
from earlier studies. They were tuned against Claude and had never been run on GPT-5.6, so they are discovery evidence only.
The two Phase 4 instances are revisions of two of them, derived in this study (AMENDMENTS X4), and are also exploratory. Held-out
confirmation is reported separately in HELDOUT_CONFIRMATION_RESULTS.md.

## PROMISING in screening (S1)

| Instance | Family | S1 Acc@1 | Rank-1 answers | Failure mode (blind labels) | Gold validity: coordinator review / blind labellers (blind to the coordinator's labels, but told the designated gold) |
|---|---|---|---|---|---|
| RH-ADV-DEPTH-01 (Lang) | M19 | 0/3 | `NumberUtils::overlay` ×3 | the decoy's documentation contradicts its code (3/3), with sink blame as secondary | **Both judge the answer defensible.** `overlay`'s javadoc says the value "is masked to the field", but the code does not mask it, and all 3 runs cite this. |
| RH-LB-COMPRESS-07-ADAPTER (Compress) | M3 (tags M17, M5) | 0/3 | `TarUtils::computeCheckSum` (the entry point) ×3 | entry-point ranking (3/3); alternative repair site as secondary in 2 of the 3 | **The review flagged a risk.** The correct sibling `TarBuffer.digest` and its passing test offer an equally small entry-point repair. **The blind labellers judge the answer not defensible:** the entry point's delegation is correct by contract, and the agent itself named the gold as the divergence. |
| RH-LB-CHART-01-ADAPTER (Chart) | M3 | 1/3 | `CompassPlot::ring` ×2 | caller-argument blame (1), convention attribution (1) | **The review judges the answer defensible:** `Plot.nudge`'s javadoc ("Displaces the bounds of a section by its offset scaled by the explode percentage") does not state the offset's sign. **The blind labellers judge the answer not defensible:** the offset convention is pinned by tests and a second caller, and `nudge` must return the exploded bounds. |
| RH-ADV-MASK-01 (Lang) | M5 (tags M19, M1) | 1/3 | `Conversion::intArrayToLong` (entry), `NumberUtils::overlay` | entry-point ranking (1); mask-placement attribution (1) | **Both judge the gold well supported** (blind labellers: "no" for both runs; coordinator: "no" for run 1 and "partly", a documented argument but a better-supported gold, for run 3; no validity flag). The second production caller (`BitField`) passes an already positioned field, which pins `overlay`'s convention. Run 3 displayed that evidence but did not use it; run 1 named the gold as the divergence and still ranked the entry point first. |

RH-ADV-DEPTH-01 carries the AMENDMENTS X3 caveat: the variant also fails `ConversionTest::testIntArrayToLong`, so an agent
that runs the full suite sees two failing tests, not one. P4-DEPTH-01-r1 keeps the same failure set (gate D3).

**WEAK (1 of 3 wrong):**

- RH-ADV-DEFINER-01 (Chart, M3): blamed the definer whose operand order reads backwards.
- RH-CF-V1 (Chart, M5): ranked the entry point first.

## Phase 4 differential diagnostics (EXPLORATORY revisions, AMENDMENTS X4)

P4-COMPRESS07-r1 changes only the feature the validity review flagged. P4-DEPTH-01-r1 changes two javadocs: the flagged
decoy contradiction in `overlay`, and the gold `widen`'s contract, which it pins to unsigned words. In both revisions the
fault and the odd-looking lines are unchanged. The revisions ran on 2026-10-11, a day after their parents, with 3 runs each.

| Revision | Parent (S1) | What changed | Acc@1 | Reading |
|---|---|---|---|---|
| P4-DEPTH-01-r1 | RH-ADV-DEPTH-01, 0/3 | Javadocs only. `overlay` now says the value "is placed as given and must already fit within the field"; `widen` now says it produces unsigned words. The odd-looking `overlay` line is unchanged. | **3/3** (gold `BitField::widen`) | With both contracts pinned, the unchanged odd-looking sink line did not mislead. The recovery cannot be split between removing the decoy's contradiction and pinning the gold's contract (the blind labellers had noted that the parent's `widen` javadoc did not say signed or unsigned). Exploratory, n = 3 per arm. |
| P4-COMPRESS07-r1 | RH-LB-COMPRESS-07-ADAPTER, 0/3 | Removed the correct sibling `TarBuffer.digest` and its test. The chain and the fault are unchanged. | **3/3** (gold `ExtraFieldUtils::widen`) | Consistent with the sibling driving the parent's entry-point answers. The removal also took away `digest`'s role as the declared second production caller, and its test, which asserts the same value (461) as the trigger. One instance, exploratory, n = 3 per arm; RH-CF-V1 run 2 also ranked the entry point first, with no alternative-repair site tagged by the blind labellers. |

**Related controls for the Chart instances are already in S1.**

- RH-CF-V3 differs from RH-ADV-DEFINER-01 (2/3) only in an explicit `drift` javadoc, and scored 3/3.
- The visible-operator control RH-CF-V5 (DEFINER-01 with `drift` reading outward and an explicit negation at the gold) also
  scored 3/3.
- RH-OCFLB-CHART-01-ADAPTER, the ocflb-v1 explicit-contract control that LB-CHART-01-ADAPTER was converted from, scored 3/3.
  It differs from LB-CHART-01-ADAPTER in several features at once: explicit contracts at the definer and the gold, a definer
  that reads forwards (`point2 - point1`), a visible negation at the gold like CF-V5's, and no `RingPlot.collapse` second
  caller. It therefore does not isolate the effect of contract explicitness.
- CF-V3 is a sibling of RH-CF-V1, not its twin: it lacks V1's second caller `PlotUtilities.retreat`, and V1's one miss was
  an entry-point ranking, not a convention attribution.

## What remains promising

**Conclusion from screening and Phase 4.** Each 0/3 effect disappears once its flagged feature is repaired. For DEPTH-01, that
feature is the decoy's doc contradiction, which both judgements call a defensible answer; the revision also pinned the gold's
contract, so the two repairs are not separable. For COMPRESS-07, it is the correct
sibling that offers an alternative repair. The blind labellers judge the COMPRESS-07 answers not documentation-consistent. They tagged
alternative-repair reasoning in 2 of the 3 runs, and removing the sibling (with its test) gave 3/3. This is consistent with
the sibling driving the misses, but rests on n = 3 per arm.

**Reductions not explained by an ambiguous gold, on both judgements (MASK-01) or on the blind reading only (CHART-01-ADAPTER):**

- **RH-ADV-MASK-01 (1/3).** Its gold is pinned by distant evidence: a second production caller (`BitField.setValue`) fixes the convention.
  Run 3 displayed that call but did not use it; run 1 named the gold as the divergence and still ranked the entry point first.
- **RH-LB-CHART-01-ADAPTER (1/3), contested.** The blind labellers judge the answers not defensible; the coordinator review
  judged the blamed caller a defensible repair site. RH-OCFLB-CHART-01-ADAPTER (3/3) differs from it in several features at
  once (see above), so it does not show which feature matters.

The frozen plan (HELDOUT_CONFIRMATION_PLAN.md) groups the S1 misses into three failure modes, a grouping made before the
blind labels, and carries them forward as held-out recipes, each in its valid form:

- **HA, entry-point ranking**, from COMPRESS-07, MASK-01 run 1 and CF-V1 run 2;
- **HB, sink blame**, from DEPTH-01 and MASK-01 run 3 (in the blind labels, sink blame is the secondary mode of these four
  runs);
- **HC, convention attribution with a second production caller**, from CHART-01-ADAPTER (2 runs) and DEFINER-01 (1 run).

The recipes were frozen at 2026-10-10T04:01Z, before any Phase 4 run existed. The Phase 4 outcomes therefore did not shape
them. They are consistent with the plan's stated rationales for HA (the COMPRESS-07 sibling) and HB (the DEPTH-01 decoy's doc
contradiction). As exploratory revisions they are not evidence for the held-out predictions themselves (AMENDMENTS X4). Those
predictions (HELDOUT_CONFIRMATION_PLAN.md) were: HA pooled Acc@1 between 0.4 and 1.0, direction uncertain; HB Acc@1 ≥ 0.6;
HC Acc@1 ≥ 0.8.
