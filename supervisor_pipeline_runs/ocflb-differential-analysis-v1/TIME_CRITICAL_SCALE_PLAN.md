# Time-critical scale plan for the externally-pinned / locally-under-specified benchmark (OCFLB v2)

All options convert EXISTING OCFLB pairs (same seeds, chains, triggers, validators, servers) by editing only H2/H3 bodies, javadocs and the
pin, following `SOLUTION_DESIGN.md`. Construction and validation reuse `ocflb-v1/scripts/*` unchanged except the builders. Estimates assume
the OCFLB v1 experience: one builder-agent pass of 20-40 minutes per pair, validation 10-15 minutes per pair (full suite x3), Sonnet
runs 4-5 minutes each on two servers, Opus runs about 1 minute.

| Option | Pairs | Runs | Construction | Validation | Paid runs (wall) | Cost (Sonnet 0.40, Opus 0.08 USD/run) | Scientific value |
|---|---|---|---|---|---|---|---|
| FAST | 3 (Chart-01 converted, Lang-03 converted, Compress-07 converted: sign, offset units, byte sign) | 30-40: Sonnet 5 per arm (30) + Opus 3 per arm on 1-2 pairs (6-12) | 1.5-2 h (template first, then two agents in parallel) | 45 min | ~1.5 h Sonnet on two servers, 15 min Opus | 14-17 USD | shows whether the effect returns under unique-but-locally-ambiguous ownership on three families; enough for a thesis section if the pilot already fixed the mechanism |
| MEDIUM | 5 (+ Math-05 scale units, Lang-04 case folding) | 50-70: Sonnet 5 per arm (50) + Opus 3 per arm on 3 pairs (18) | 3-4 h (five agents in parallel) | 1.5 h | ~2.5 h Sonnet, 20 min Opus | 22-30 USD | five families, per-pair replication unit; supports a benchmark-wide gap estimate with a median and counts |
| FULL | 8-10 (all convertible OCFLB pairs) | 80-120: Sonnet 5 per arm (80-100) + Opus 3 per arm on 5 pairs (30) | 6-8 h | 2.5-3 h | ~4.5 h Sonnet on two servers (plus stall top-ups), 35 min Opus | 35-45 USD | full replacement of OCFLB v1 as the thesis benchmark; three-level comparison (A/B/C) possible on the pairs that also exist in v1 |

Prerequisites for any option: Anthropic credits (v1 exhausted them), and the differential pilot (15-18 Sonnet runs, about 7 USD) having
shown that the V5-type cue (explicit operator at the gold) or the V3/V4-type cue (explicit javadoc) is what restores accuracy, so that the
conversion rules in `SOLUTION_DESIGN.md` are the right ones. If time does not allow the pilot, FAST can be run directly: its three
pairs are the three whose conversions are least ambiguous (sign, offset units, byte sign), and the pilot's V5 condition is implied by
their v1 forms already measured.

Recommended: MEDIUM. It fits in one working day (construction in the morning, runs in the afternoon), covers five families, and keeps the
per-pair replication logic that made v1 interpretable.
