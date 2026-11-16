# Held-out confirmation plan (Phase 5)

Written and frozen on 2026-10-10. This is after S1 and part of S2 had been scored, and **before the Phase 4 diagnostic runs
returned any result**. The recipe text below is hashed in `construction/heldout/RECIPES_FROZEN.json` and is not edited
afterwards. Held-out instances are built from these recipes by builders who did not build any screening instance and never
see a GPT-5.6 trajectory or result. Each gold is then checked by an auditor who did not build that instance. No held-out
variant is modified after its first behavioural run.

## Why these three mechanisms

The S1 screen (18 re-hosted instances, 54 valid runs) produced 12 wrong rank-1 answers, all on 6 instances. Classified by what
the agent actually did, they fall into three failure modes:

| Failure mode | S1 wrong runs | Instances |
|---|---|---|
| **HA, entry-point ranking**: the agent names the deep helper as the divergence, but ranks the public method the test calls first | 5 of 12 | LB-COMPRESS-07-ADAPTER (3/3), ADV-MASK-01 (1), CF-V1 (1) |
| **HB, sink blame**: the agent blames the terminal method whose code looks like it lacks a normalisation, instead of the upstream method that omits it | 4 of 12 | ADV-DEPTH-01 (3/3), ADV-MASK-01 (1) |
| **HC, convention attribution**: with a sign or direction convention split across hops, the agent blames a neighbouring hop | 3 of 12 | LB-CHART-01-ADAPTER (2), ADV-DEFINER-01 (1) |

By screening label these are the strongest families: M19 (DEPTH, PROMISING), M3 (COMPRESS-07 and CHART-01-ADAPTER, PROMISING;
DEFINER, WEAK) and M5 (MASK, PROMISING; CF-V1, WEAK). The S2 recipe prototypes were at ceiling, apart from one invalid
instance (AMENDMENTS X1). Mechanism mining agrees: ENTRY_POINT was 7 of 26 frozen GPT-5.6 misses, and local oddness or
attribution made up the rest.

**Validity is fixed first, outcome second.** Several S1 misses rest on a gold an auditor could reject:

- DEPTH-01: the decoy documents a mask it does not apply.
- CHART-01-ADAPTER: the convention is under-specified, so the blamed caller is a defensible repair site.
- COMPRESS-07: a correct sibling makes "the entry point should call the sibling" an equally small repair.

Every recipe below therefore requires a gold that the documentation alone makes the unique owner of the defect. A mechanism
that works only through gold ambiguity cannot meet STABLE criteria 5 and 6, so it is tested in its valid form. The Phase 4
revisions measure the same question on the old instances, but their results do not feed back into these recipes.

## Rules common to all recipes

1. **Base and fault.**
   - Base: a Defects4J `bug-1` fixed checkout (`construction/fresh/<Project>`).
   - Exactly one single-fault variant, built and gated with `scripts/mx_build_validate.py` (G0 to G13) and accepted only when
     READY.
   - The fault is one small edit inside the gold method. The minimal repair restores exactly that method.
2. **Freshness.**
   - No class::method listed in `construction/USED_METHODS.txt` may be used as a gold, a decoy, an entry point or a helper
     host method. That file lists every gold, decoy and entry point of the 34 instances built so far.
   - The trigger test and all helper names are new.
3. **Context edits.**
   - The helper chain is created by behaviour-preserving context edits. The CORRECT configuration (context edits and tests,
     no fault) must pass the full suite (G1).
   - Every helper is a `public static` method in an existing production class, chosen so that the chain crosses at least two
     packages.
   - No helper name, comment or javadoc may contain fault vocabulary (G2b) or name the defect.
4. **Documentation decides ownership.**
   - The gold's javadoc states a postcondition or behaviour that its code violates on the trigger input.
   - Every non-gold method on the trigger path either satisfies its own javadoc exactly, or is unchanged upstream code.
   - No javadoc may contradict its own code, except the gold's.
   - No javadoc may be loose enough that the observed behaviour is consistent with a non-gold method being at fault.
5. **No alternative repair site.**
   - No correct sibling, duplicate or alternative implementation of the computation that the entry point or a caller could
     be rerouted to.
   - No configuration flag that selects between implementations.
6. **Submittability (G13).** The gold, decoys and entry points must not be in a class ending in `Test` or `Tests`, must not be
   in a `.test.` or `.junit.` package, and must not be methods named `test*`.
7. **Trigger.**
   - A new, neutrally named JUnit method that calls the public entry point E directly and fails deterministically on E's
     return value.
   - Exactly one test fails on the variant (G5).
8. **Declarations and checks.**
   - Declare the gold, the decoys (every helper on the path that is not the gold), the entry point(s), the decisive-evidence
     locations, a one-paragraph ownership reason, at least one ownership test (an existing or new test that passes on the
     variant and pins a decoy's contract), and at least two natural one-line compensating edits at non-gold methods for G9.
   - Under G9, no declared decoy edit may absorb the fault.
9. **Budget.**
   - At most two validator attempts per instance.
   - If an instance cannot reach READY, the builder abandons that location and starts a fresh one. Builders never tune
     against a model.

## HA: delegating entry point, with a deep helper that violates its own contract

- **Hypothesis.** GPT-5.6 ranks the public method the failing test calls (E) above the deep helper it has itself identified
  as producing the wrong value, when E's whole body is one delegation into a chain of small, locally plausible helpers.
- **Construction.**
  - E is an existing public method with a small, self-contained computation that the trigger calls directly, for example a
    checksum, a numeric conversion, a field encoding or a bounded transform.
  - Context edit: E's body becomes exactly one statement that delegates to a new helper H1 in another class. H1 composes H2
    and H3, each in a further class; the whole chain spans 3 or 4 classes across at least 2 packages.
  - The gold is H2 or H3, never E or H1.
  - The fault is quiet. It is either a double application of a step the gold's input contract says is already done, or the
    omission of a step its javadoc promises. A plain assignment or call reads as complete, with no unusual operator.
- **Decoys:** E (declared as the entry point), H1 and the non-gold helper.
- **Forbidden:** a correct sibling that E could call instead (rule 5), and a decoy javadoc that promises the step the gold
  violates.
- **Projects:** Math, Compress, JacksonCore, one instance each.

## HB: documented sink precondition, with a quiet upstream omission

- **Hypothesis.** GPT-5.6 blames the terminal sink S, whose line visibly lacks a normalisation, over the upstream method G that
  promises the normalisation and silently omits it. It does so even when S's javadoc states the precondition that makes S
  correct.
- **Construction.**
  - A chain E → H1 → G → H3 → S across at least 4 classes, created by context edits.
  - S places or accumulates a value with a line that looks like it is missing a step, for example clearing the target bits
    but inserting the value as given, adding without clamping, or indexing with the value as given.
  - S's javadoc states the precondition explicitly, for example "the value must already fit within the field; it is placed
    as given".
  - G's javadoc states the postcondition explicitly, for example "returns unsigned / non-negative / normalised values".
  - G's fault omits that normalisation with a quiet line, for example a plain widening assignment, a missing mask or a
    missing absolute value.
  - The trigger input makes the omission visible through E.
- **Decoys:** S, H1, H3 and E.
- **Forbidden:**
  - any decoy javadoc that promises the normalisation G omits;
  - a precondition stated anywhere other than S's own javadoc.
- **Projects:** Lang, Math, Compress, one instance each.

## HC: documented convention split, with an adapter that applies the convention backwards

- **Hypothesis.** When a definer D returns a difference whose orientation looks backwards locally but is documented, GPT-5.6
  blames D, or the caller that supplies D's arguments, rather than the adapter A that applies D's value with the wrong sign.
  It does so even when A's javadoc states the resulting direction explicitly.
- **Construction.**
  - D is a new helper whose code reads backwards, for example `inner - outer` or `start - end`. Its javadoc fixes the
    orientation ("the offset from the X to the Y").
  - A second production caller P2 uses D correctly. An ownership test that passes on the variant covers P2, which pins D's
    convention.
  - A (the gold) applies D's value to produce a result. A's javadoc states the direction of that result explicitly. The
    fault flips the direction in an ordinary-looking line, for example `base + offset * f` where the contract needs
    `base - offset * f`.
  - Path: E → caller C → D, and C → A, or an equivalent arrangement.
- **Decoys:** D, C, P2 and E.
- **Forbidden:** under-specified orientation, meaning any javadoc on the path that allows both readings.
- **Projects:** Lang, Math, JacksonCore, one instance each.

## Audit (STABLE criterion 6)

For each READY instance, an independent auditor receives the spec, both patches and the validation record. The auditor builds
nothing and sees no model output. Working from the code and documentation only, the auditor answers:

- (a) Is the gold the unique method whose documented contract is violated on the trigger input?
- (b) Does any non-gold method deviate from its own javadoc?
- (c) Is there an equally small, documentation-consistent repair at a non-gold method?
- (d) Is there leakage, such as names, comments, test names or vocabulary?
- (e) Does the instance actually realise its recipe?

The verdict is CONFIRMED only if (a) is yes, (b) and (c) are no, (d) is no, and (e) is yes. A REJECTED instance is replaced
by a fresh build from the same recipe **before any run**; it is never modified after a run.

## Runs and analysis

- **Runs.** 9 instances × 5 runs = 45 runs, under the frozen GPT-5.6 protocol (server mxF0, effort medium, 50 steps, 300 s).
  The plan is seeded and interleaved in rounds and frozen with `mx_freeze.py` before the first call. The tier is HELDOUT.
- **Expected cost.** About $10, giving a cumulative total of about $33. This stays under the $60 check-in.
- **Per mechanism:** pooled Acc@1, per-instance Acc@1, provider-error and no-answer counts, and gold exposure among the wrong
  answered runs.
- **STABLE requires all six criteria in PREREGISTRATION.md.** Preferred: pooled Acc@1 ≤ 0.50.
- **Stop rule.**
  - A: at least two STABLE mechanisms. Report them, then run Phase 6 combinations only if moderate effects are present.
  - B: none at or below 0.60. Report that GPT-5.6 is robust under the tested manipulations, since at least 12 families have
    been screened and the 3 strongest have been held-out tested.

## Predictions (recorded before any held-out run)

- **HA.** Pooled Acc@1 is between 0.4 and 1.0. The direction is uncertain: the S1 entry-point misses came from instances with
  a correct sibling (COMPRESS-07) or a 5-hop chain (CF-V1, MASK).
- **HB.** Acc@1 ≥ 0.6. The DEPTH-01 effect relied on the decoy's own documentation contradiction.
- **HC.** Acc@1 ≥ 0.8. The explicit-contract controls (OCFLB-CHART-01-ADAPTER, CF-V3) scored 3/3 in S1, as in the earlier
  ocflb-v1 study.
