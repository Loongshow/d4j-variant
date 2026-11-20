# Stage B design draft (written 2026-10-14, while Stage A runs; not yet frozen)

**Goal set by the user.** Show a stable method-level accuracy drop on a current model (gpt-5.5 first, GPT-5.6 as reference)
that is attributable to a long reasoning chain, using the supervisor's generator recipe where it helps, and dropping levers the
data say are ineffective.

## What the records say about each lever (current models only)

| Lever | Evidence | Verdict |
|---|---|---|
| Structural chain alone (2 to 5 hops, two large hosts) | GPT-5.6 43/44 pooled on the nine odd-hop-free 5-hop arms, 37/42 on the six 6-hop arms (three of the five misses timeouts), 0.80 to 1.00 per arm on answered runs (W10); Claude Opus 3/3 on both odd-hop-free TREATMENT arms; first-gold step rises from ~1 to ~20 | raises search cost, does not move rank |
| Host file size alone | never completed on GPT-5.6 (2 of 30 slots); Claude 3/3 on both arms of one pair; the supervisor's own code uses size only as a ≥1500-line gate | no evidence of effect; keep as a gate, not a factor |
| Misleading naming or comment cues alone | cue-trust pilot 27/27 on GPT-5.6 | ineffective alone |
| Facade narrative lie (the script's distinctive element) | untested on GPT-5.x at scale: the September 5-hop variants carried no lie; the one real generator run (NUMBERUTILS, Lang) was solved | unknown in combination; cheap to include |
| Chain + a correct hop that looks locally wrong + a quiet terminal gold, convention unpinned | CHART-PIE-TREATMENT-03: GPT-5.6 0/5, Claude 0/3, gpt-5.5 0/5 (control 5/5) | the shape that breaks current models most consistently, but the pair bundles chain, odd hop and an ownership split and its control gold is the entry point (W10), so the chain's own share is unmeasured |
| Ownership split with an omission gold | CLOSURE-12: GPT-5.6 0.20, gpt-5.5 0.20; CLOSURE-131: 0.33, 0.00 | breaks current models; harder to build fresh |

**Stage A outcome (2026-10-14):** gpt-5.5 missed the CHART treatment arm 5/5 and passed the control 5/5, and got 1/27 over
the seven breakers. The drop exists on a current model; because the pair does not isolate the chain (W10), Stage B is about
measuring the chain's own contribution on fresh instances, not about generalising an already-isolated effect.

## Design: a 2×2 on fresh bugs, matched within pair

Factor 1, **chain**: the supervisor's recipe as code (`host_search.pick_two_hosts`, `chain_transform.insert_method_at_anonymous_point`):
the fault's method is decomposed into a chain of 5 hops that crosses two existing classes of ≥1500 lines, each hop inserted at
an anonymous interior point in its host; the facade's javadoc carries a procedural narrative lie, written in the file's own
documentation voice (the script's `lie_sentence` requirement, authored by hand here, no LLM in construction). Control: the same
fault in the undecomposed method, no lie.

Factor 2, **asymmetry**: one correct mid-chain hop is written in a valid but locally odd form (operand order that reads
backwards, or a mask that looks missing) whose correctness is fixed by evidence elsewhere in the repository; the terminal gold
is a quiet omission in the idiomatic reading of its own javadoc. Control: every hop reads as plainly correct.

Cells: chain+asym (the CHART-PIE-03 shape, with the lie), chain only, asym only (odd sibling in the same file, no chain), neither
(see the refinement at the end: the no-chain cells keep the gold one hop below the facade, never at the entry point).
Three fresh bugs (Lang, Math and a third project: open question 3), 5 runs per cell on gpt-5.5: 60 runs, about $20.

## Validity rule (so the result survives an audit)

From ocflb-differential-analysis-v1: **externally pinned, locally under-specified.** The gold's convention is not restated in
the gold's own javadoc (otherwise GPT-5.x reads it and recovers, as in OCFLB and the HC held-out set), but it is fixed by
evidence the agent can reach: a second production caller with a passing test, or distant geometry or arithmetic in the same
project. Each gold must be the unique method whose documented contract is violated on the trigger input, confirmed by an
independent audit, and one-line repairs at other hops must not be documentation-consistent. The CHART-PIE-03 instance fails
this rule (its hops 3, 4 and 5 are behaviourally equivalent repair sites), which is why fresh instances are needed before a
claim is made.

## What is measured

Per cell: Acc@1 with Wilson intervals, gold rank, first-gold step, tool calls; for every wrong run the split
NO_ANSWER / SEARCH_FAILURE / DISCOVERY_WITHOUT_INSPECTION / ATTRIBUTION_FAILURE and the preregistered Phase 7 label. The
chain's own contribution is the chain-vs-no-chain contrast within each asymmetry level; the interaction is the quantity of
interest.

## Open questions for the user before freezing

1. Whether to keep the facade lie in the chain arm (it is the script's element, but it is a comment-level cue, and the thesis
   framing is about chain length; it can be a third factor at double the cost).
2. Whether gpt-5.5 at the frozen 300 s budget is the evaluation model, or GPT-5.6 is re-run on the fresh pairs for the reference.
3. Which three Defects4J projects to use. Chart is excluded to avoid the PIE-03 neighbourhood. A dry run of the script's own
   host search (`candidate_search.find_large_classes`, 1500-line gate) on the pristine checkouts gives: Lang 6 eligible hosts,
   Math 10, JacksonCore 4, Compress 1 (BZip2CompressorOutputStream only), Chart 20. Compress therefore cannot carry a
   two-large-host chain under the recipe's own gate, and the shortlist below finds no JacksonCore target either; the proposal
   is Lang, Math and Chart outside the pie-plot classes (`DatasetUtilities`, package `org.jfree.data.general`, no shared code
   with the PIE-03 hosts).

## Target shortlist (the script's own filter, run 2026-10-14; no model calls)

`candidate_search.score_candidate_methods(require_static=True)` on classes ≥ 1800 lines, keeping public static methods of 4 to
50 body lines with self-containedness > 0 and a direct test call, minus methods already used in earlier studies.

| Project | Class (lines) | Candidates (body lines, self-containedness) |
|---|---|---|
| Lang | StringUtils (7356) | containsNone (28, 24), abbreviate (27, 24), substring (31, 24), repeat (37, 24), join (26, 22), containsAny (28, 22) |
| Lang | ArrayUtils (5826) | toMap (25, 27), addAll (28, 24), lastIndexOf (23, 20), removeElements (29, 18), indexOf (21, 17) |
| Lang | DateUtils (1888) | round, truncate, iterator (11 lines each, low self-containedness) |
| Math | FastMath (3882) | asinh (24, 79), atanh (24, 60), log1p (30, 40), cos (46, 36), min (18, 25) |
| Math | DSCompiler (1823) | getCompiler (40, 40) |
| Chart, outside the pie-plot classes | DatasetUtilities (2180) | createCategoryDataset (43, 26), findStackedRangeBounds (34, 20), findCumulativeRangeBounds (30, 18), findMaximumRangeValue (43, 16) |

JacksonCore has no candidate under this gate; Compress has one eligible host only. Hosts (≥ 1500 lines, two per chain,
different packages preferred) are drawn by `host_search.pick_two_hosts` from the same pools.

The asymmetry element is added by hand in the chain: one hop's correct arithmetic is written in a locally odd but valid form,
pinned by a second production caller with a passing test; the terminal gold omits a step promised by its own javadoc in a way
that its idiomatic reading hides. Each instance passes the mechanism-search builder gates (G0 to G14) and an independent
ownership audit before any run.

## Refinement after the Stage A verification (2026-10-14)

The CHART pair's control puts the gold at the entry point and its treatment bundles three things (chain, odd hop, ownership
split). Stage B therefore adds two constraints so the factors separate:

- **Control arm gold is never the entry point.** In every cell the fault sits in a helper the facade calls, so the no-chain
  cells have a 1-hop helper gold and the chain cells a 5-hop gold; the comparison is 1 hop vs 5 hops, not entry point vs deep.
- **Single owner in every cell**, checked by the ownership-counterfactual gate (G9) and the independent audit: no one-line
  edit at a non-gold hop may pass the trigger while staying documentation-consistent. The odd hop is pinned by a second
  production caller with a passing test, as the "externally pinned, locally under-specified" rule requires.

With these, the four cells are: 1-hop plain, 1-hop odd sibling, 5-hop plain (with the facade lie), 5-hop odd hop (with the
lie). The lie can be moved to a separate factor if the user prefers (open question 1).
