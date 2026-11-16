# Next large benchmark: OCFLB v2, externally pinned / locally under-specified

1. **Exact manipulation.** Keep the OCFLB v1 chain, trigger, failure text, matched arms, shared test patch, second caller and ownership
   proof. Change three things in every pair: (a) H2's name and javadoc become convention-neutral (they say what is related, not which
   direction/origin/scale is "correct"); (b) H3's javadoc says that it applies/forwards the quantity, not how; (c) the adapter-arm fault
   is an omission (missing negation, missing `+ at`, missing second division, missing widening) and the definer-arm fault is an
   unconventional-but-natural choice (operand order, unit choice), never an explicit operator or constant. Add a production second caller
   of H2 (on the caller-search path) whose existing test passes in the adapter arm and fails in the definer arm; keep the unit pin. Add
   gate V15: two blinded graders cannot tell the arm from H2 alone or H3 alone, but can from the repository.
2. **Why the old attack failed** (as a benchmark, not as an attack): its correct definer looked unconventional (`point1 - point2` for a
   "drift") and its javadocs were silent, so ownership was locally ambiguous and the models' heuristic chose the wrong hop; it had a pin
   but no production second caller, and it existed for one pair in one project.
3. **Why OCFLB v1 became too easy.** It put the locally odd line at the faulty hop in both arms (explicit operators or constants in 9/10
   adapter arms; body-vs-explicit-javadoc contradictions in 10/10 definer arms and 9/10 adapter arms) and documented every convention;
   the owner is inferable from a single read of the gold in 10/10 pairs.
4. **Cues that must be removed.** Decisive javadoc sentences at H2 and H3; explicit operators/constants at the fault; names that imply the
   convention (`drift`, `padNeeded`, `lastProcessed`, `highSurrogateWeight` imply direction/parity/index/scale); worked numbers in
   javadocs; pin tests whose comments restate the convention in prose (keep the asserts, drop the prose).
5. **Ownership proof that remains.** Production second caller + unit pin; isolated-repair proof (gold repair passes trigger+pin+caller test;
   compensating repair at the other hop passes the trigger but breaks the caller test/pin) -> PINNED_UNIQUE in both arms, exactly as v1.
6. **Local ambiguity that remains.** In each arm H2 and H3 each read as plausible code for their names and docs; only the caller/sibling
   evidence decides. Level B by construction; Level A (no second caller) and Level C (v1) are the two comparison points.
7. **Expected Acc@1 (Sonnet).** Definer arm 0.6-1.0 (the callers reveal an unconventional definer), adapter arm 0.0-0.4 (the models
   blame the definer unless they read the callers); attribution gap 0.4-0.8. Opus similar or slightly higher on the adapter arm.
8. **Expected failure mechanism.** DEFINER_ATTRIBUTION on the adapter arm: gold discovered, both bodies read, definer ranked first with
   "operand order / direction reversed" rationales; recovery only in runs that grep callers across `source tests` and read the second
   caller or the pin (adversarial precedent: 1 of 16).
9. **Pairs buildable quickly.** All ten v1 pairs are convertible by editing H2/H3 bodies, javadocs, names and the pin; the seeds, chains,
   triggers and validators are unchanged. Least ambiguous conversions first: Chart-01 (sign), Lang-03 (offset units), Compress-07 (byte
   sign), Math-05 (scale units), Lang-04 (case folding); then Chart-02, Compress-08, JacksonCore-09; JacksonCore-10 and Math-06 last (v1
   already showed heavy Sonnet exhaustion on them, which would confound attribution with no-answers).
10. **Convert rather than rebuild.** Yes for all ten: the builders in `ocflb-v1/scripts/pairs/build_*.py` take new method texts; each
    conversion is a new builder file plus a v15 grading pass. Estimated 20-40 minutes per pair for construction, 10-15 for validation.

Run plan: primary Sonnet 5 per arm; Opus 3 per arm on the family-diverse subset fixed before results; same servers, runner proof, stall
rule and top-ups as v1. Freeze before runs; no edits after the first paid run.
