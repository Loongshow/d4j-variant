## Per-instance results (F0)

| Instance | Condition | n (valid/attempted) | Answered | Acc@1 | MRR | Gold ranks | Decoy first | Gold exposed, misranked | Full gold read | Top-3 full read | Tests run | Median tools | Median reasoning tok | Median cost (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CT-CHART-01 | C0 | 3/3 | 3 | 1.00 | 1.00 | 1, 1, 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | 14 | 717 | 0.133 |
| CT-CHART-01 | CG | 3/3 | 3 | 1.00 | 1.00 | 1, 1, 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | 13 | 545 | 0.125 |
| CT-CHART-01 | CD | 3/3 | 3 | 1.00 | 1.00 | 1, 1, 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | 18 | 755 | 0.151 |
| CT-LANG-01 | C0 | 3/3 | 3 | 1.00 | 1.00 | 1, 1, 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | 13 | 1056 | 0.173 |
| CT-LANG-01 | CG | 3/5 | 3 | 1.00 | 1.00 | 1, 1, 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | 13 | 915 | 0.168 |
| CT-LANG-01 | CD | 3/3 | 3 | 1.00 | 1.00 | 1, 1, 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | 12 | 856 | 0.161 |
| CT-CHART-03 | C0 | 3/3 | 3 | 1.00 | 1.00 | 1, 1, 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | 18 | 639 | 0.191 |
| CT-CHART-03 | CG | 3/3 | 3 | 1.00 | 1.00 | 1, 1, 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | 22 | 633 | 0.229 |
| CT-CHART-03 | CD | 3/3 | 3 | 1.00 | 1.00 | 1, 1, 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | 23 | 742 | 0.297 |

## Condition totals (F0, pooled over instances; descriptive)

| Condition | n | Answered | Acc@1 | MRR | Decoy first | Entry first | Other first | No answer | Gold exposed, misranked | Strong signal | Cue exposed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C0 | 9 | 9 | 1.00 | 1.00 | 0 | 0 | 0 | 0 | 0 | 0 | – |
| CG | 9 | 9 | 1.00 | 1.00 | 0 | 0 | 0 | 0 | 0 | 0 | 9/9 |
| CD | 9 | 9 | 1.00 | 1.00 | 0 | 0 | 0 | 0 | 0 | 0 | 8/9 |

## Pre-specified contrasts (F0)

| Instance | Contrast | Delta | Class | Baseline flag | n flag | Acc@1 C0 → cue | Decoy first C0 → cue |
|---|---|---|---|---|---|---|---|
| CT-CHART-01 | C0 vs CD | +0.00 | NULL | – | – | 1.00 → 1.00 | 0 → 0 |
| CT-CHART-01 | C0 vs CG | +0.00 | NULL | – | – | 1.00 → 1.00 | 0 → 0 |
| CT-LANG-01 | C0 vs CD | +0.00 | NULL | – | – | 1.00 → 1.00 | 0 → 0 |
| CT-LANG-01 | C0 vs CG | +0.00 | NULL | – | – | 1.00 → 1.00 | 0 → 0 |
| CT-CHART-03 | C0 vs CD | +0.00 | NULL | – | – | 1.00 → 1.00 | 0 → 0 |
| CT-CHART-03 | C0 vs CG | +0.00 | NULL | – | – | 1.00 → 1.00 | 0 → 0 |

## Trajectory measures by condition (F0, valid runs; counts of runs)

| Measure | C0 | CG | CD |
|---|---|---|---|
| Gold faulty line shown | 9/9 | 9/9 | 9/9 |
| Decoy signature shown | 9/9 | 9/9 | 9/9 |
| Full gold method read | 9/9 | 9/9 | 9/9 |
| Full decoy method read | 9/9 | 9/9 | 9/9 |
| Top-3 bodies fully read | 9/9 | 9/9 | 9/9 |
| Tests executed | 9/9 | 9/9 | 9/9 |
| Independent probe | 1/9 | 1/9 | 1/9 |
| Failure values shown | 4/9 | 5/9 | 7/9 |
| Cue line shown | – | 9/9 | 8/9 |

| Sufficiency class | C0 | CG | CD |
|---|---|---|---|
| efficient | 4 | 6 | 7 |
| cue_override | 0 | 0 | 0 |
| premature | 0 | 0 | 0 |
| guess | 5 | 3 | 2 |

## Effort and token distributions (F0; min / Q1 / median / Q3 / max over valid runs)

| Condition | Tool calls | Model calls | Files read | Lines read | Searches | Test runs | Reasoning tokens | Output tokens | Input tokens | Cost (USD, total) | Wall time (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C0 | 12 / 13 / 15 / 17 / 21 | 5 / 5 / 6 / 7 / 8 | 4 / 7 / 11 / 16 / 21 | 674 / 963 / 1047 / 1440 / 1916 | 9 / 10 / 11 / 16 / 20 | 1 / 1 / 1 / 1 / 1 | 450 / 639 / 744 / 910 / 1166 | 2481 / 2855 / 3055 / 3248 / 3272 | 26084 / 43400 / 58580 / 72376 / 87621 | 1.48 | 38 / 42 / 45 / 49 / 51 |
| CG | 11 / 13 / 13 / 18 / 27 | 5 / 5 / 6 / 7 / 10 | 5 / 7 / 10 / 15 / 29 | 835 / 1025 / 1053 / 1203 / 1762 | 8 / 8 / 9 / 19 / 24 | 1 / 1 / 1 / 1 / 1 | 528 / 545 / 736 / 915 / 1211 | 2455 / 2704 / 2845 / 3449 / 4472 | 30825 / 39492 / 51369 / 76739 / 140086 | 1.56 | 36 / 46 / 49 / 54 / 63 |
| CD | 10 / 15 / 18 / 19 / 36 | 4 / 5 / 7 / 8 / 14 | 5 / 7 / 10 / 19 / 38 | 930 / 1048 / 1130 / 1532 / 2572 | 5 / 12 / 14 / 16 / 30 | 1 / 1 / 1 / 1 / 1 | 632 / 742 / 774 / 856 / 1570 | 2295 / 2745 / 3042 / 3347 / 5411 | 33532 / 47901 / 51657 / 99665 / 195402 | 1.76 | 32 / 40 / 42 / 68 / 90 |

## Reasoning tokens by outcome (F0; observational only)

| Rank-1 category | n | Reasoning tokens (min / Q1 / median / Q3 / max) | Tool calls (median) |
|---|---|---|---|
| GOLD | 27 | 450 / 636 / 749 / 912 / 1570 | 15 |

## Excluded runs (F0)

- CTV-F5B88A/run-001 CT-LANG-01 CG1: infrastructure (driver verdict infrastructure; status provider_stall, harness timeout) 
- CTV-F5B88A/run-002 CT-LANG-01 CG1: infrastructure (driver verdict infrastructure; status provider_stall, harness timeout) 

## Pre-registered pilot gate (F0)

| Check | Observed | Criterion | Met |
|---|---|---|---|
| Cue displayed in CG/CD runs | 17/18 | >= 80% | yes |
| Cost per run (max, USD) | 0.320 | <= 1.00 | yes |
| Timeout rate (behavioural timeouts / counted runs) | 0/27 | <= 20% | yes |
| Provider stalls/errors (excluded, reported) | 2 | reported | – |
| Metrics agree with hand labels on 5 runs | manual | 5/5 | – |
