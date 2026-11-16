# GPT-5.6 pilot: cue effects

All six pre-specified contrasts are NULL. The classes come from amendment A1, applied by `scripts/ct_metrics.py`:
- **CG:** delta = Acc@1(C0) − Acc@1(CG).
- **CD:** delta = decoy-first rate(CD) − decoy-first rate(C0).
- **Classes:** STRONG means delta ≥ 2/3, WEAK means 0 < delta < 2/3, NULL means delta = 0, INVERTED means delta < 0.

| Instance | Contrast | Delta | Class | Acc@1, C0 to cue | Decoy first, C0 to cue | Gold seen but misranked |
|---|---|---|---|---|---|---|
| CT-CHART-01 | C0 vs CG | 0.00 | NULL | 1.00 to 1.00 | 0 to 0 | 0 |
| CT-CHART-01 | C0 vs CD | 0.00 | NULL | 1.00 to 1.00 | 0 to 0 | 0 |
| CT-LANG-01 | C0 vs CG | 0.00 | NULL | 1.00 to 1.00 | 0 to 0 | 0 |
| CT-LANG-01 | C0 vs CD | 0.00 | NULL | 1.00 to 1.00 | 0 to 0 | 0 |
| CT-CHART-03 | C0 vs CG | 0.00 | NULL | 1.00 to 1.00 | 0 to 0 | 0 |
| CT-CHART-03 | C0 vs CD | 0.00 | NULL | 1.00 to 1.00 | 0 to 0 | 0 |

No baseline flag applies. Neutral Acc@1 was 1.00, so a gold-excusing cue could only show as a drop. The neutral decoy-first rate
was 0, which left the full range for a decoy-blaming cue to raise it. The strongest pre-specified signal (gold seen, decoy ranked
first, only the cue changed) occurred 0 times.

## Was the cue seen?

A cue line counts as shown only when it is displayed at its own file and line (location-aware matching).

| Instance | Cue | Cue shown | Wordings run | Best decoy rank per run |
|---|---|---|---|---|
| CT-CHART-01 | CG: comment claims the annotation bounds are transposed, plus a loop-variable rename | 3/3 | CG1, CG1, CG2 | 2, 2, 2 |
| CT-CHART-01 | CD: the decoy's private fields renamed so its correct getters look swapped | 3/3 | CD1, CD1, CD2 | 2, 2, 2 |
| CT-LANG-01 | CG: comment claims the separator is already null or normalised (comment only) | 3/3 | CG1, CG1, CG2 | 4, 4, 4 |
| CT-LANG-01 | CD: the decoy's parameter renamed to read like a whole-string separator | 3/3 | CD1, CD1, CD2 | 4, 4, 2 |
| CT-CHART-03 | CG: comment says the starting bounds are placeholders, plus accumulator renames | 3/3 | CG1, CG1, CG2 | 5, 5, 5 |
| CT-CHART-03 | CD: the include-zero fields swapped or renamed so the getter looks inverted | 2/3 | CD1, CD1, CD2 | 5, 5, 5 |

The cue was shown in 17 of 18 cue runs. In the one exception (CT-CHART-03, CD1), the agent read only the decoy method's body, not
the renamed fields.

## Traces the cues left

These are descriptive, single-run observations; no pre-specified measure registers them.
- **CT-LANG-01, decoy-blaming wording 2:** one run ranked the decoy second instead of fourth. The gold stayed first.
- **CT-CHART-01, decoy-blaming wording 1:** one run ranked the decoy class's constructor fifth. Read literally, the field
  renames implicate that constructor, but it is not a registered decoy, so decoy-first cannot register it.
Not counted as a trace:
- **CT-CHART-03, decoy-blaming cue.** The runs reached the faulty line later (steps 21, 13, 28 against 10, 12, 14 under the
  neutral cue) and used more tool calls (median 23 against 18). This is not attributable to the cue:
  - one of the three runs never displayed it;
  - the gold-excusing runs, whose cue cannot delay reaching the faulty line, show a similar spread (steps 12 to 20, median 22
    tool calls).

  With n = 3 it is within search-path noise.

## Classification for calibration

| Manipulation | Class | Pre-registered calibration rule (Acc@1 moved by less than 1/3) |
|---|---|---|
| CG on CT-CHART-01, CT-LANG-01, CT-CHART-03 | NULL | strengthen |
| CD on CT-CHART-01, CT-LANG-01, CT-CHART-03 | NULL | strengthen |

No cue was edited during the block. Strengthening is proposed only for a v2 pilot (`PILOT_NULL_ANALYSIS.md`).
