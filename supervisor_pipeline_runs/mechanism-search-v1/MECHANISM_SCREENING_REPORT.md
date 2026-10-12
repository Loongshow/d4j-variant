# Mechanism screening report (Phase 3, EXPLORATORY)

Model and protocol: GPT-5.6 under the frozen protocol (mini-swe-agent profile, reasoning effort medium, 50 steps, 300 s,
external workspace, leakage scanning). Each valid instance was screened with 3 valid runs (the invalid NEW-R4-M4 got 1 run before it was dropped). All screening instances are
EXPLORATORY: they are discovery evidence, never confirmation. The per-instance data are in `MECHANISM_SCREENING_MATRIX.csv`
and the per-run data in `analysis/per_run.csv`. Classes follow the preregistered rule:

- **PROMISING** if any of:
  - (A) Acc@1 ≤ 1/3;
  - (B) the gold was exposed in at least 2 runs and misranked in at least 2;
  - (C) the same wrong method was ranked above the gold in at least 2 of 3 runs.
- **WEAK** if 1 of 3 runs mislocalizes.
- **NULL** if all 3 runs rank the gold first.

## Blocks

| Block | Instances | Valid runs | Acc@1 | MRR | Wrong rank-1 | Run cost |
|---|---|---|---|---|---|---|
| S1: re-hosted earlier adversarial and controlled variants, never run on GPT-5.6 | 18 | 54 | 0.78 (42/54) | 0.857 | 12 (DECOY 7, ENTRY_POINT 5) | USD 11.47 |
| S2: new prototypes built for this study from the recipes in SCREENING_BUILD_RECIPES.md | 12 valid (+1 invalid) | 36 | 1.00 (36/36) | 1.000 | 0 | USD 6.47 (USD 6.02 for the 36 scored runs) |

**Every valid run in both blocks ran a test** (90/90).

**In all 12 wrong S1 runs, the agent displayed the gold's fault line and read the gold method in full.** The misses are
therefore never "the gold was not found". They are cases where the gold was found, read and ranked below another method.

**Excluded runs** (frozen rules; none is scored):

- CTV-065313/run-002 (NEW-R7-M10): STOP_CONTAMINATION. The agent ran `find` over `/private/tmp` and displayed a stale workspace
  path. The run had ranked the gold first. Its replacement is valid (AMENDMENTS X2).
- CTV-078CEB/run-002 (NEW-R8-M12): an infrastructure attempt. The provider quota was exhausted mid-run (`insufficient_quota`);
  the replacement is valid.
- NEW-R4-M4 is **INVALID**. Its gold class name ends in `Test`, and the harness submission validator rejects such methods. The
  agent's first submission ranked the gold first and was rejected. The instance is excluded from every class (AMENDMENTS X1),
  and a new builder gate, G13, prevents a repeat.

## S1 instances (re-hosted)

| Instance | Family | Project | Acc@1 | Gold ranks | Rank-1 categories | Class | Validity note (coordinator) |
|---|---|---|---|---|---|---|---|
| RH-ADV-DEPTH-01 | M19 | Lang | 0.00 | 2 3 2 | DECOY ×3 (NumberUtils::overlay) | **PROMISING** | decoy documents a mask it does not apply; collateral failure (X3) |
| RH-LB-COMPRESS-07-ADAPTER | M3 | Compress | 0.00 | 3 3 3 | ENTRY_POINT ×3 (TarUtils::computeCheckSum) | **PROMISING** | correct sibling makes an entry-point repair equally small |
| RH-LB-CHART-01-ADAPTER | M3 | Chart | 0.33 | 4 4 1 | DECOY ×2 (CompassPlot::ring), GOLD | **PROMISING** | offset convention under-specified at the gold |
| RH-ADV-MASK-01 | M5 | Lang | 0.33 | 2 1 4 | ENTRY_POINT, GOLD, DECOY | **PROMISING** | |
| RH-ADV-DEFINER-01 | M3 | Chart | 0.67 | 5 1 1 | DECOY (PlotUtilities::drift), GOLD ×2 | WEAK | |
| RH-CF-V1 | M5 | Chart | 0.67 | 1 2 1 | GOLD, ENTRY_POINT, GOLD | WEAK | |
| RH-ADV-COMPOSITE-01 | M20 | Chart | 1.00 | 1 1 1 | GOLD ×3 | NULL | |
| RH-ADV-LEX-01 | M11 | Lang | 1.00 | 1 1 1 | GOLD ×3 | NULL | |
| RH-ADV-OVERLOAD-01 | M16 | Lang | 1.00 | 1 1 1 | GOLD ×3 | NULL | |
| RH-ADV-REGISTRY-01 | M16 | Lang | 1.00 | 1 1 1 | GOLD ×3 | NULL | |
| RH-ADV-OWNER-01 | M7 | Lang | 1.00 | 1 1 1 | GOLD ×3 | NULL | |
| RH-LB-LANG-03-ADAPTER | M3 | Lang | 1.00 | 1 1 1 | GOLD ×3 | NULL | |
| RH-LB-LANG-04-ADAPTER | M3 | Lang | 1.00 | 1 1 1 | GOLD ×3 | NULL | |
| RH-LB-MATH-05-ADAPTER | M3 | Math | 1.00 | 1 1 1 | GOLD ×3 | NULL | |
| RH-OCFLB-CHART-01-ADAPTER | M3-contract | Chart | 1.00 | 1 1 1 | GOLD ×3 | NULL | explicit-contract source of LB-CHART-01-ADAPTER; also a visible negation at the gold |
| RH-CF-V3 | M3-contract | Chart | 1.00 | 1 1 1 | GOLD ×3 | NULL | ADV-DEFINER-01 plus explicit definer javadoc |
| RH-LB-CHART-01-DEFINER | M3-control | Chart | 1.00 | 1 1 1 | GOLD ×3 | NULL | definer arm (the gold is the definer, whose code reads forward; the correct adapter carries the subtraction) |
| RH-CF-V5 | M1-control | Chart | 1.00 | 1 1 1 | GOLD ×3 | NULL | visible operator at the gold |

## S2 instances (new recipe prototypes)

All 12 valid prototypes are **NULL**: 3/3 runs ranked the gold first, read the gold fully and ran a test. They cover:

| Family | Instance | Project |
|---|---|---|
| M1 local oddness | NEW-R1-M1 | Lang |
| M2 omission | NEW-R2-M2 | Compress |
| M3 definer/adapter | NEW-R3-M3 | Math |
| M7 inverse pair | NEW-R5-M7 | Compress |
| M8 cross-caller convention | NEW-R6-M8 | Lang |
| M10 entry point | NEW-R7-M10 | Math |
| M12 same-file competition | NEW-R8-M12 | Lang |
| M13 cross-file competition | NEW-R9-M13 | Compress |
| M14 state propagation | NEW-R10-M14 | Compress |
| M15 fallback path | NEW-R11-M15 | Math |
| M17 type semantics | NEW-R12-M17 | JacksonCore |
| M9 test ambiguity | NEW-R13-M9 | Lang |

NEW-R4-M4 (M4, multiple owners, Math) is INVALID, as described under the exclusions above.

## Family classes (S1 + S2, valid instances only)

| Family | Class | Pooled Acc@1 (runs) | Instances |
|---|---|---|---|
| M19 structural distance plus attribution | PROMISING | 0.00 (3) | 1 |
| M5 distant decisive evidence | PROMISING | 0.50 (6) | 2 |
| M3 definer/adapter split | PROMISING | 0.71 (21) | 7 |
| M1, M2, M7, M8, M9, M10, M11, M12, M13, M14, M15, M16, M17, M20 | NULL | 1.00 each | 1 or 2 each |
| controls: M1-control, M3-contract, M3-control | NULL | 1.00 | 4 |

**Coverage.** 17 mechanism families were screened behaviourally (M1, M2, M3, M5, M7, M8, M9, M10, M11, M12, M13, M14, M15, M16,
M17, M19, M20), against the brief's requirement of at least 12. M4 has no valid screening instance. M6 (the correct method
looks more suspicious) appears only as a tag inside other instances (NEW-R1-M1, ADV-DEFINER-01, P4-DEPTH-01-r1 and the HB
held-out instances). M18 (non-idiomatic correct code) has no instance and is not among the tags in
`MECHANISM_SCREENING_MATRIX.csv`; it appears only in the earlier studies' mining annotations (including those of several
re-hosted S1 instances), so it is untested here. Projects covered are
Lang, Chart, Compress, Math and JacksonCore. S1 has 8 Chart, 8 Lang, 1 Compress and 1 Math instances. S2 has no Chart instance.

## What the screen shows

1. **These fresh recipe builds did not move GPT-5.6.** All 12 valid S2 prototypes are at ceiling, 36/36. Each was built to
   one family's recipe and passed the builder gates, but none was independently audited for recipe realisation, and most
   builders flagged their own instance as likely easy because of local evidence at or near the gold. The S2 null shows that
   these builds did not reduce accuracy; with one S2 instance and 3 runs per family, it does not show that the families cannot.
2. **Every reduction comes from re-hosted instances tuned against Claude in earlier work:** three adversarial-break-v1
   attacks (DEPTH-01, MASK-01, DEFINER-01) and three controlled ocflb variants (COMPRESS-07-ADAPTER, CHART-01-ADAPTER, CF-V1). In 3 of
   the 4 PROMISING instances, the coordinator's validity review, made after the S1 outcomes were known, flagged a gold-validity risk. Blind
   labellers, who saw the code and the trajectories, judged only the 3 DEPTH-01 answers documentation-consistent and the
   other 9 misses not defensible, including both CHART-01-ADAPTER misses and all three COMPRESS-07 misses
   (FAILURE_MODE_ANALYSIS.md). The
   flagged risks were:
   - in DEPTH-01, the blamed decoy's own javadoc promises the mask it omits, and all three wrong runs cite this;
   - in CHART-01-ADAPTER, the gold does not fix the offset convention;
   - in COMPRESS-07, a correct sibling makes "the entry point should call the sibling" an equally small repair.
3. **The explicit-contract and visible-operator variants are all at ceiling (exploratory, 3 runs each).** None is a
   single-factor contrast with a PROMISING instance:
   - OCFLB-CHART-01-ADAPTER (3/3), the instance LB-CHART-01-ADAPTER (1/3) was converted from, states the contract, but it
     also has a visible negation at the gold and a definer that reads forward;
   - CF-V3 (3/3) is ADV-DEFINER-01 (2/3) with the convention stated in the definer's javadoc; the gold is unchanged;
   - CF-V5 (3/3) adds a visible operator at the gold and flips the definer.

   This is consistent with the earlier ocflb-v1 finding (on Claude) that explicit, locally decidable contracts protect. With
   3 runs per arm and these confounds, it does not show that an explicit convention alone restores accuracy.
4. **Read at the level of what the agent did, the 12 wrong runs fall into a few failure modes.** The blind labels
   (FAILURE_MODE_ANALYSIS.md) give:
   - entry-point ranking, 5 runs: the agent names the deep helper as the divergence but ranks the method the test calls first;
   - decoy doc-contradiction blame, 3 runs (all DEPTH-01, with sink blame as the secondary mode);
   - convention or caller-argument attribution, 3 runs (CHART-01-ADAPTER ×2, DEFINER-01), and mask placement, 1 run (MASK-01
     run 3).

   The held-out plan groups the same runs differently, using the coordinator's earlier labels
   (`analysis/failure_modes/labels_S1.json`): entry-point ranking 5, sink or doc-contradiction blame 4 (DEPTH-01 ×3 and
   MASK-01 run 3) and convention or local-oddness attribution 3.

## Selection for confirmation

The held-out plan's three failure modes (the 5/4/3 grouping above) are carried into held-out confirmation as recipes **HA
(entry-point ranking)**, **HB (sink blame)** and **HC (convention attribution)**. The misses behind them came from the
strongest families by screening class (M19, M3 and M5), but the recipes are failure-mode recipes, not replications of those
families. The held-out analysis scores them as M10 (HA), M19 (HB) and M3 (HC). M10 screened NULL (NEW-R7-M10, 3/3), and M5
has no recipe of its own: its three misses fed HA (MASK-01 run 1, CF-V1 run 2) and HB (MASK-01 run 3).

The recipes were written and frozen at 2026-10-10T04:01Z, after S1 was complete but with S2 only partly run (17 of its 36
valid runs had been checked), and before any Phase 4 result existed (HELDOUT_CONFIRMATION_PLAN.md). They rest on the
coordinator's labels of the S1 misses; the blind labels in FAILURE_MODE_ANALYSIS.md were produced later.
They require a gold that the documentation alone makes the unique owner. A mechanism that works only through gold ambiguity
cannot meet the STABLE criteria, so it is tested in its valid form. HB, for example, forbids the decoy doc contradiction
that produced the DEPTH-01 (M19) misses.
