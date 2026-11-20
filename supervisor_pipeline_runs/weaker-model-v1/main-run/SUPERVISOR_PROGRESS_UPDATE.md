# Main run: progress update 9 (final, after batches 1–9)

29 October 2026. Update 8 is superseded; its numbers are unchanged and appear below as the C10, C10f and batch-7/8 rows. Every figure comes
from the frozen per-run measures (`analysis/per_run.json`), `MAIN_RUN_RESULTS.csv`, `MAIN_RUN_C10F_RESULTS.csv`, `MAIN_RUN_C10I_RESULTS.csv`,
the batch prediction files, `analysis/bridge7_pairs.json` and `AMENDMENTS.md` W42–W71. The all-bugs extension's paid runs are complete.

## Headline

- **223 validated instances in 13 Defects4J projects, 146 with at least one shift (520 of 1,114 answered runs).**

| Cell | What differs | Batches | Instances | With ≥ 1 shift | Shifted / answered |
|---|---|---|---|---|---|
| C10 | static facade, hosts ≥ 1,500 lines | 1–5 | 67 | 50 | 194/335 |
| C10f | static facade, five largest classes as hosts | 6 | 38 | 30 | 108/190 |
| C10i | instance-method facade | 7–9 | 118 | 66 | 218/589 |
| | batch 7: paired with a static instance of the same bug | 7 | 17 | 12 | 40/85 |
| | batch 8: no static facade, simplest instance facades | 8 | 60 | 37 | 121/300 |
| | batch 9: no static facade, receiver-style facades and Closure | 9 | 41 | 17 | 57/204 |

- **The effect is strongest where the recipe was designed and weakens tier by tier.** Instances with a shift: C10 0.75, C10f 0.79, batch 7
  0.71, batch 8 0.62, batch 9 0.41. The later tiers are the bugs whose only usable facades are thin wrappers; about 40% of their candidates (37 of 97, 32 of 75) could
  not be built at all.
- **Neither host size nor facade kind explains this.** Fallback hosts shift as often as large ones (batch 6), and on the same bug with the
  same hosts a static and an instance facade shift equally often (batch 7, 14 distinct pairs, 6 up / 5 down). The batch-8 V1/V2 contrast
  did not recur in batch 9.
- **Projects differ strongly and consistently.** Collections shifts in every type (20 of 22 instances), Lang and Closure's static instances
  almost always; JacksonDatabind (5 of 22), Jsoup (8 of 20), Cli (2 of 8) and Chart (5 of 12) rarely.
- **When a run shifts, the model ranks the facade first.** Over the 1,115 counted runs: GOLD_FIRST 594, ENTRY_POINT_BIAS 476,
  GOLD_NOT_REACHED 27, UPSTREAM_HOP_FIRST 9, OTHER_FIRST 8, no answer 1.

## Instances by project and type (with ≥ 1 shift in brackets)

| Project | C10 | C10f | C10i | Total |
|---|---|---|---|---|
| Lang | 35 (30) | — | 8 (6) | 43 (36) |
| Math | 6 (4) | 3 (2) | 20 (13) | 29 (19) |
| Collections | — | 7 (6) | 15 (14) | 22 (20) |
| JacksonDatabind | 6 (1) | 1 (0) | 15 (4) | 22 (5) |
| Jsoup | — | 2 (2) | 18 (6) | 20 (8) |
| Compress | — | 9 (8) | 8 (6) | 17 (14) |
| Closure | 8 (8) | — | 8 (4) | 16 (12) |
| Time | 8 (5) | — | 5 (3) | 13 (8) |
| Chart | 2 (1) | — | 10 (4) | 12 (5) |
| Codec | — | 8 (6) | 3 (3) | 11 (9) |
| Cli | — | 4 (2) | 4 (0) | 8 (2) |
| JacksonCore | 2 (1) | 1 (1) | 4 (3) | 7 (5) |
| Gson | — | 3 (3) | — | 3 (3) |
| **Total** | **67 (50)** | **38 (30)** | **118 (66)** | **223 (146)** |

Empty cells are by rule: projects without five classes of 1,500 lines cannot have C10; projects with them never use the fallback (C10f).

## Batch 9 (the last tier)

| Item | Value |
|---|---|
| Unit | 62 bugs whose best instance facade is receiver-style (V2) and 13 Closure bugs; split 9a (thin cells first) / 9b at the candidate's request |
| Dispositions | 41 ACCEPTED, 2 FLAGGED (run, not counted), 32 not built |
| Robustness raters | majority NO_TRACE 39 of 41 |
| Runs | 43 instances × 5 valid runs; 4 excluded records replaced (1 contamination stop, 3 infrastructure) |
| Interruptions | OpenAI balance (once), machine sleep with the lid closed (once), the cost guard at $600 (cap raised to $650 by the candidate) |
| Result | 17 of 41 with a shift (57/204 runs); distinct facades 11 of 27 |

## Cost

| Item | USD |
|---|---|
| Before the main run | 66.25 (incl. estimates) |
| Batches 1–4 | 95.48 |
| Batch 5 | 41.87 |
| Batch 6 | 78.39 |
| Batch 7 | 36.70 |
| Batch 8 | 127.22 |
| Batch 9 | 105.67 |
| **Cumulative incl. estimates** | **561.77** |

## Not attempted

Mockito (cannot be scored on the frozen evaluation server), Csv (no public host classes), and facades outside the bug's modified classes.
JxPath and JacksonXml produced no buildable instance; Gson has no instance-facade candidate.

## Open items for the supervisor

1. How to present the tier-by-tier decline and the per-project divergence: as a scope limit of the reading (the recipe transfers fully to
   bugs with a substantive facade, partly to thin-wrapper facades), with host size and facade kind excluded as explanations.
2. Whether reused-facade instances (43 so far) are reported inside or beside the primary counts (currently beside).
3. The anchor quirk (hops placed in a nested class of the listed host file; W42, W57, W63) is to be disclosed in the thesis.
4. Thesis integration of batches 5–9 is on hold at the candidate's request; these records are the source when it resumes.
