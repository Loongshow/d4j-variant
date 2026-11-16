# FINAL LEVEL-B SPEC (frozen before construction; NON-CANONICAL RESEARCH BENCHMARK)

Principle: **GLOBALLY UNIQUE OWNERSHIP + LOCALLY AMBIGUOUS OWNERSHIP.** A model reading H2 alone cannot know whether H2 is the owner; a
model reading H3 alone cannot know; the repository as a whole determines the owner uniquely.

Basis. The differential analysis (`ocflb-differential-analysis-v1`) established that both models blame the hop whose body looks wrong for
its name or documentation. OCFLB v1 reached ceiling because 9/10 adapter faults were explicit operators or constants and every H2 javadoc
stated the decisive convention. The differential pilot (V0-V5) could not be run (credits exhausted, re-confirmed 2026-09-30); this spec
follows the leading, artifact-supported hypothesis (CASE C: local self-incrimination) and removes both cue classes. If the pilot later
shows CASE A (a production second caller alone restores accuracy), the external evidence must move off the caller-search path; the
pairs below keep it in production code so that CASE A can be tested on them directly.

## Chain (unchanged from OCFLB v1)

Facade -> H1 (input preparation) -> H2 (semantic definer) -> H3 (adapter) -> H4 (consumer) -> H5 (output); H1 calls H2 and hands the value
to H3; H3 -> H4 -> H5 nested; same facade, hop names, files, trigger, failing input, expected output and failure text in both arms.

## Arms

- DEFINER-FAULT: H2 implements an alternative, natural-looking convention that the rest of the repository does not follow; H3 correct.
- ADAPTER-FAULT: H2 follows the repository's convention; H3 applies it wrongly by omission or by a natural-looking misinterpretation.
- Both arms produce the same observable failure (gate V3d); the two variant patches differ only in the declared H2/H3 lines (V10b).

## Fault style

Omissions (a missing normalisation, a missing second division, a missing sign handling written as the natural opposite binary
operation), convention mismatches (any-vs-all, inward-vs-outward operand order, bits-vs-bytes), representation mismatches (a narrowing
cast on a value that was meant to stay wide). No unary minus, no `* 2` / `/ 2`, no `+ 1` / `- 1`, no bit-shift constant, no visibly
inverted branch at the fault.

## Documentation policy

H2 and H3 javadocs describe purpose only ("Computes the offset between the two points"; "Displaces the bounds of a section by its
offset scaled by the explode percentage"). They contain no sentence that decides between the arms, no worked numbers and no
benchmark prose. Names are convention-neutral (`offset`, not `drift`). Nothing is fake or misleading.

## External ownership evidence (mandatory, identical in both arms)

At least one of: production second caller of H2 in another class whose existing or added test passes in the ADAPTER arm and fails in
the DEFINER arm; sibling implementation; inverse method; external invariant test. Plus the unit pin of H2 (plain asserts, no prose).
Ownership proof by isolated repairs (V11): gold repair passes trigger + pin + external evidence; compensating repair at the other hop
passes the trigger but breaks the pin or the external evidence -> PINNED_UNIQUE.

## Gates

V1-V14 as OCFLB v1 (`scripts/ocflb_validate.py`, extended with V12b external evidence), plus:
- **V15 local blindness**: for each arm, packet A = H2 signature+body (+ its javadoc) only; packet B = H3 likewise; independent blinded
  graders answer "From this method alone, can you confidently determine whether this method is the fault owner?" Pass = NOT confidently
  identifiable for both packets in both arms.
- **V16 two-hop ambiguity**: packet C = H2 + H3 together, no other file. Pass = LOCAL_AMBIGUOUS (the grader can at most say "one of the
  two is wrong"); LOCAL_EXPOSED fails.
Only pairs with V1-V16 pass are frozen; minimum four, target five.

## Runs

claude-sonnet-4-6: 5 pairs x 2 arms x 5 = 50; claude-opus-5-5: 3 pre-registered pairs x 2 arms x 3 = 18 (extend to 5 per arm only for a
pair with Sonnet Acc@1 <= 0.6 by genuine misranking). Corrected runner environment (proof per server in `review/`), uniform stall rule,
no-answers counted, freeze before the first paid run.

## Amendments recorded before the freeze (construction phase, before any paid run)

1. **Revisions.** A pair that failed V15 or V16 in blinded grading was revised and re-validated (V1-V14 + V12b) and re-graded with fresh
   graders; every revision and its grading is archived (`projects/<P>/bug-XX/rev1/`). Four pairs needed one revision each
   (`PAIR_SELECTION.md`, revision history). Fault families, chains, triggers, expected outputs and failure texts did not change.
2. **Exposing-cue classes found and removed** (each is now a construction rule): (a) a guard or range check inside H2 that fixes the unit
   of its input (Lang-03); (b) a definer fault that contradicts an adjacent term of the same method (Lang-04); (c) a canonical idiom
   (`raw & 0xff`) as the correct H2 next to a non-idiomatic H3 transform, which lets a reader discount H2 outright (Compress-07: both hops
   now carry the same textual form); (d) an H3 javadoc that states the unit of a parameter or of the result (Math-05).
3. **H1 javadocs** must not state the decisive unit either when H1 hands the value straight to H2 (Lang-03 H1 no longer says "in bits");
   the facade contract (original project documentation) and the production second caller remain the external evidence.
4. **Validator extension.** `ocflb_validate.py` accepts a declared `expect_absorb: false` compensating probe (class
   `PINNED_UNIQUE_NO_ABSORB`: no edit of the other hop can absorb the fault, the probe must compile and leave the trigger failing). No
   frozen pair uses it; all ten arms are `PINNED_UNIQUE` by an executed compensating repair.
5. **Opus subset** pre-registered in `review/OPUS_SUBSET.md` (one project per slot): `LB-CHART-01`, `LB-COMPRESS-07`, `LB-MATH-05`.
6. **Differential pilot (Phase 1)** could not be run before construction (provider credits exhausted, bounded probes on 2026-09-30); the
   pairs were built under CASE C (local self-incrimination) and keep the external evidence in production code so that CASE A can be
   tested on them directly when credits return.
