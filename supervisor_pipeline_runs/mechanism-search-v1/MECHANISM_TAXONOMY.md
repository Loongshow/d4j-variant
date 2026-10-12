# Mechanism taxonomy (final v2, 2026-10-11; supersedes draft v1 of 2026-10-10)

**Target phenomenon:** the gold method is found and its code inspected, yet a wrong method is ranked above it.

**Columns:**

- **Frozen GPT-5.6 Acc@1** is the tag-level accuracy over completed earlier experiments (`analysis/screening/mining_tag_acc.json`,
  from MECHANISM_MINING.md). Tags overlap, and many of those instances had under-specified ownership, so these numbers
  describe where misses occurred, not causal effects.
- **Screening** is this study's EXPLORATORY screen: 3 valid runs per valid instance (NEW-R4-M4 was dropped as invalid after 1 run), frozen GPT-5.6 protocol
  (MECHANISM_SCREENING_REPORT.md).
- **Held-out** is Phase 5 with fresh instances (no gold, decoy or entry point is in construction/USED_METHODS.txt), built and audited by agents described as independent; the audit records name the auditor only as "independent agent", so independence is not verifiable from them (HELDOUT_CONFIRMATION_RESULTS.md).

**Final status values:**

- **NOT_SUPPORTED (held-out):** on its 3 fresh instances, the recipe met neither the STABLE criteria nor the PARTIALLY_SUPPORTED thresholds of AMENDMENTS.md X8 (pooled Acc@1 ≤ 0.80, or any instance ≤ 0.60). This is a point-estimate classification, not a demonstration that the effect is absent: the per-recipe Wilson 95% lower bounds are 0.70 (HA), 0.785 (HB) and 0.796 (HC). The recipes tested each failure mode in a form where the documentation makes the gold the unique owner, and the result covers GPT-5.6 at medium effort under this harness only.
- **NULL in screening:** every screened instance whose primary mechanism is this one scored 3/3. Some of these mechanisms are also secondary tags on S1 instances that did show reductions: M1 on ADV-DEPTH-01 (0/3) and ADV-MASK-01 (1/3), M2 on LB-CHART-01-ADAPTER (1/3) and ADV-DEFINER-01 (2/3), M17 on LB-COMPRESS-07-ADAPTER (0/3), and M20 on ADV-DEFINER-01 (2/3).
- **Screening effect not confirmed:** a screening reduction whose instances were not re-run in a repaired form, and whose failure modes were carried by held-out recipes that showed no reduction; no held-out recipe was tagged with the mechanism itself (M5).
- **No reduction (frozen evidence):** not re-screened in this study; frozen tag-level Acc@1 was near ceiling (M0, 0.97).
- **Untested:** no valid instance whose primary mechanism is this one. **Untested as a carrier** marks a mechanism that appears only as a secondary tag on other instances (M4, M6).

| ID | Mechanism | Frozen GPT-5.6 Acc@1 (runs, inst.) | Screening (this study) | Held-out | Final status |
|---|---|---|---|---|---|
| M0 | Structural displacement only (depth, hops) | 0.97 (168, 67) | not re-screened; displacement families 0.90 to 1.00 in frozen data (valid behavioural runs) | none | no reduction (frozen evidence) |
| M1 | Local oddness: a correct method looks wrong | 0.57 (30, 15) | NEW-R1-M1 3/3 (Lang); RH-CF-V5 control 3/3 | as a tag only, not a held-out target: HC 15/15 | NULL in screening |
| M2 | Bug by omission | 0.85 (88, 38) | NEW-R2-M2 3/3 (Compress) | as a tag only, not a held-out target: HA 14/15, HB 14/14 | NULL in screening |
| M3 | Definer vs adapter, convention split | 0.80 (109, 37) | 6 S1 instances: LB-COMPRESS-07-ADAPTER 0/3, LB-CHART-01-ADAPTER 1/3, ADV-DEFINER-01 2/3, LB-LANG-03, LB-LANG-04 and LB-MATH-05 3/3 each; explicit-contract twins 3/3 each; M3-control LB-CHART-01-DEFINER 3/3; NEW-R3-M3 (S2) 3/3 (M3 family: 7 instances, 15/21) | **HC: 15/15** (Lang, Math, JacksonCore); as a tag in HA: 14/15 | **NOT_SUPPORTED (held-out)** |
| M4 | Multiple plausible owners | 0.81 (118, 42) | NEW-R4-M4 INVALID (the harness rejects a gold whose class ends in "Test"); as a tag only: RH-ADV-OWNER-01 3/3, RH-ADV-REGISTRY-01 3/3 | none | Untested as a carrier |
| M5 | Distant decisive evidence | 0.86 (135, 32) | ADV-MASK-01 1/3, CF-V1 2/3 | failure modes carried by HA (MASK-01 run 1, CF-V1 run 2) and HB (MASK-01 run 3): 14/15 and 14/14; no held-out instance is tagged M5 | screening effect not confirmed |
| M6 | The correct method looks more suspicious than the gold | 0.36 (36, 11) | as a tag only: ADV-DEFINER-01 2/3, NEW-R1-M1 3/3, P4-DEPTH-01-r1 3/3 | as a tag only, not a held-out target: HB 14/14 | Untested as a carrier |
| M7 | Symmetry or inverse-pair confusion | 0.91 (22, 5) | RH-ADV-OWNER-01 3/3; NEW-R5-M7 3/3 | none | NULL in screening |
| M8 | Cross-caller convention conflict | 0.88 (34, 13) | NEW-R6-M8 3/3 | none | NULL in screening |
| M9 | Test-evidence ambiguity | 0.95 (22, 10) | NEW-R13-M9 3/3 | none | NULL in screening |
| M10 | Entry-point blame or ranking | 0.93 (106, 35) | NEW-R7-M10 3/3. As a failure mode it appeared in 5 of 12 S1 misses (COMPRESS-07 ×3, MASK-01, CF-V1). P4-COMPRESS07-r1, with the sibling removed, scored 3/3 | **HA: 14/15**; the only miss is a no-answer timeout | **NOT_SUPPORTED (held-out)** |
| M11 | A nearby decoy matches the name or vocabulary better | 0.77 (26, 13) | RH-ADV-LEX-01 3/3 | none | NULL in screening |
| M12 | Same-file competing methods | 0.87 (138, 51) | NEW-R8-M12 3/3 | none | NULL in screening |
| M13 | Cross-file competing methods | 0.92 (208, 75) | NEW-R9-M13 3/3 | none | NULL in screening |
| M14 | Subtle state propagation | 0.79 (85, 29) | NEW-R10-M14 3/3 | none | NULL in screening |
| M15 | Faulty default or fallback path | 0.81 (21, 9) | NEW-R11-M15 3/3 | none | NULL in screening |
| M16 | Overload or dispatch ambiguity | 0.90 (72, 23) | RH-ADV-OVERLOAD-01 3/3; RH-ADV-REGISTRY-01 3/3 | none | NULL in screening |
| M17 | Type-semantic confusion | 0.93 (246, 59) | NEW-R12-M17 3/3 | none | NULL in screening |
| M18 | Valid but non-idiomatic correct code | 0.42 (19, 5) | no dedicated instance | none | Untested |
| M19 | Structural distance plus attribution ambiguity | 0.76 (94, 23) | ADV-DEPTH-01 0/3 (the decoy's doc contradicts its code); P4-DEPTH-01-r1 3/3 after two javadoc edits made at once (decoy contradiction removed, gold contract pinned; exploratory, effects not separable) | **HB: 14/14** (Lang, Math, Compress) | **NOT_SUPPORTED (held-out)** |
| M20 | Evidence competition (local vs global) | 0.56 (36, 19) | RH-ADV-COMPOSITE-01 3/3 | none | NULL in screening |

## How the taxonomy maps onto what GPT-5.6 actually does

The failure-mode analysis (FAILURE_MODE_ANALYSIS.md, which uses a post-hoc label set rather than the preregistered Phase 7 labels) describes two settings in which GPT-5.6 ranked a
wrong method first. They cover 10 of the 12 S1 misses; ADV-DEFINER-01 run 1 and ADV-MASK-01 run 3 fit neither. In all 12 misses the agent had already read the gold.

1. **A competing location with a documented argument exists.** On the blind labels it was defensible only for DEPTH-01 (3 runs); the blind labellers judged the other 9 S1 rank-1 answers not defensible, while the coordinator's earlier labels were more lenient (5 yes, 5 partly, 2 no). Examples are a decoy whose own javadoc contradicts its code, a correct
   sibling that permits an alternative repair, or a convention not fixed at the gold. In this study these were M3 and M19 instances (LB-COMPRESS-07-ADAPTER, LB-CHART-01-ADAPTER, ADV-DEPTH-01), all as
   built in earlier studies. Only two screening effects were revised, in exploratory Phase 4 diagnostics (X4): DEPTH-01 (two javadoc edits at once) and COMPRESS-07 (the sibling and its test removed) each went from 0/3 to 3/3 (two-sided Fisher p = 0.10; which change mattered is not identified). The explicit-contract twins of LB-CHART-01-ADAPTER (OCFLB-CHART-01-ADAPTER, which also differs in other features) and ADV-DEFINER-01 (CF-V3, an explicit javadoc on the definer only) scored 3/3. MASK-01 and CF-V1 were not re-run in a repaired form.
2. **Proximity ranking (M10 as a failure mode).** Even after naming the deep cause, the agent sometimes ranked the method the
   test calls first (5 runs). Three were on COMPRESS-07, where a correct sibling offered an alternative repair at that method. The other two (MASK-01 run 1, CF-V1 run 2) had no documentation-supported alternative; the held-out plan attributes them to long helper
   chains, but the mining annotations give MASK-01 3 hops and CF-V1 4 hops, no more than COMPRESS-07's 3, so chain length is not shown to explain them. Held-out HA instances (3- or 4-class chains, a documented unique owner and no alternative repair site) scored 14/15, the only miss a no-answer. This is consistent with the account but does not establish it: every freshly built instance in the study was at ceiling whatever its mechanism (S2 36/36, held-out 43/43 answered).

Mechanisms that act on search (M10 as search, M12, M13, M14, M15), on lexical cues (M11), on test ambiguity (M9) or on
local oddness alone (M1) showed no misses in this study's screen, each tested on one or two instances with 3 runs. M0 was not re-screened (frozen data only), and M6 had no dedicated carrier. This is weak, exploratory evidence against a large effect, and it is confounded with build provenance: most of these prototypes were fresh builds, and every freshly built instance in the study was at ceiling. For M1 and M6, the frozen tag-level Acc@1 was 0.57 and 0.36. Across all 140 valid runs in this study, every run executed a test. The gold's
fault line was displayed in all 139 answered runs. The gold was read in full in 138 of them, and the one exception
(RH-ADV-REGISTRY-01, run-001) still ranked the gold first.
