# What actually breaks LLM fault localization

Root: `supervisor_pipeline_runs/adversarial-break-v1/`. Models: claude-opus-5-5 (strong), claude-sonnet-4-6 (primary weaker),
claude-haiku-4-5 (much weaker, tool-capable). Protocol: the frozen `d4j-localization-only/v2` prompt, 50 tool calls, 5 test runs,
300 s, structured top-10 submission, identical to the GPT-5.6 benchmark. Acc@1 is reported over answered runs and over all
attempts the agent was allowed to finish (timeouts and budget exhaustion are misses; provider errors and one provider stall are
excluded). Numbers: `SCREENING_RESULTS.md`, `CONFIRMATION_RESULTS.md`, `MAX_DIFFICULTY_RESULTS.md`, `MODEL_COMPARISON.md`.

## A protocol deviation found during the run, and what it does to the results

Every Claude run in this root, and every run in the Claude pilot, could not execute `defects4j test`: the servers were started without
`PERL5LIB`, so the command returned a Perl module error in 0.1 s. The frozen GPT-5.6 runs it is compared with executed their tests
through ant (64 of 64 scanned). Evidence and decision: `diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`. Consequences:

- The main tables are labelled protocol `v2` = frozen prompt, budgets and parser, repository access, no executable test. Comparisons
  with GPT-5.6 must carry that qualifier; the pilot's NEAR_EQUIVALENT verdict is overstated in this one respect (addendum filed).
- Opus issued no test command in any v2 run of the three confirmed attacks, so its misses were not caused by the deviation. A bounded
  validity block re-ran the headline attack with the runner fixed (`VALIDITY_TEST_RUNNER.md`): Opus 2, 2, 2, 2, 1 (Acc@1 0.2) against
  2, 3, 2, 2, 3 under v2; the one run that executed the test still blamed the definer; the one hit came from reading the pinning unit
  test. The headline survives. Sonnet's validity block: 5, 5, 5, 5 and one exhaustion (Acc@1 0.0, as under v2), with the test executing through ant in 5 of 5 runs. The deviation did not make either model wrong on the headline attack.
- Sonnet and Haiku did try to run the test in every run and then spent tool calls hunting for `mvn`, `ant` or `java`, or writing their
  own check programs. Their tool-call counts and part of Haiku's exhaustion are inflated by the deviation. Their attribution verdicts
  (definer first, gold fifth) are the same as Opus's and were reached after the gold body had been read.
- Separately, twenty runs (nineteen Sonnet, one Opus) ended as single hung API requests with the agent alive and no reply for 86 to 295 s;
  replaying two of those states answered normally in under four seconds. They are excluded as provider stalls, never counted as
  misses, and the affected attacks are topped up (`diagnostic/PROVIDER_STALL_RULE.md`).

## The answer in five lines

1. **What breaks both models is an attribution judgement, not discovery.** In every answered run in this root the agent exposed
   the gold method's body before submitting. The misses happen afterwards, when a sign or mask convention is split across two
   methods and the model has to decide which one owns it.
2. **The strongest lever is definer attribution with a non-terminal gold.** Put the wrong-looking quantity in a pure definer
   whose convention is pinned by its own unit test, and the missing negation in the adapter that consumes it: Opus 0/5
   (`ADV-DEFINER-01`), Sonnet 0/10, Haiku 0/3. Opus blames the definer in six to eight tool calls without running the test; Sonnet's ten valid attempts include seven answers, all with the gold fifth.
3. **The depth prior is the second lever and it is conditional.** When the deepest hop looks locally inconsistent but is pinned by
   a second consumer and the fault is a shallow contract violation (`ADV-MASK-01`), Opus is wrong 3 of 5 times; the two hits are
   the two runs in which it read the second consumer.
4. **Lexical, search and overload attacks do not transfer.** Witness inversion with a planted decoy (`ADV-LEX-01`) is 5/5 correct
   on Opus and only sometimes wrong on Sonnet; a registry over five same-named implementations (`ADV-REGISTRY-01`), 18 sibling
   conversions under one boolean assertion (`ADV-OVERLOAD-01`) and a producer/consumer round trip (`ADV-OWNER-01`) were solved by
   both weaker models in every answered run.
5. **Stacking artifacts on the clean lever changes exhaustion, not attribution.** The maximum-difficulty composite (definer core
   plus witness removal, guard padding, a loud correct terminal and boolean-only assertions) gave Opus 0.2 against the core's 0.0
   and moved the gold from rank 2 to rank 3; on Sonnet it gave 0.0 like the core, with the gold fifth in every answer, but half the
   runs now ended in budget exhaustion instead of one in ten. The extra manipulations did not change where a model that answers puts
   the gold, because the models read the expected numbers from the test source, read whole methods with `sed` when a grep window
   is cut off, and judge the adapter by what it does with the definer's value rather than by its name.

## What broke both models: definer attribution (`ADV-DEFINER-01`, `ADV-COMPOSITE-01`)

The construction is CHART-PIE-03's chain rebuilt so that `PlotUtilities.drift(point1, point2)` returns `point1 - point2` (a
convention pinned by a unit test that passes under the variant), `Plot.nudge` (composite: `Plot.resolve`) multiplies the drift by
the explode fraction and is missing the negation, and `ShapeUtilities.shift` is a textbook translate. The failing assertion
expects the section displaced toward the centre (87.5) and gets it displaced away (112.5).

Every miss of both models ranked `drift` first. The reasoning is the same in every evidence chain: compute the first assertion by
hand, find the displacement has the wrong sign, and locate the sign where the displacement is defined ("drift has the sign
reversed", "the subtraction is reversed"). Sonnet then ranks the shallower hops above the adapter (gold fifth in all seven answered
runs); Opus keeps the adapter second or third. Neither model asked whether the definer's convention was fixed by anything: no
Sonnet run opened `PlotUtilitiesTests`, and the one Opus run that did (composite run-001, via a caller grep that happened to
include the `tests` tree) reversed its verdict and ranked the gold first. That single run is the whole difference between the
composite's 0.2 and the core's 0.0 on Opus. On Sonnet the composite gave ten valid attempts, five answers all with the gold fifth
and five budget exhaustions (`MAX_DIFFICULTY_RESULTS.md`).

This lever is largely CLEAN. The chain, the definer, the adapter and the terminal are plausible production code; the only
artifacts are that the pinning test exists only in the variant arm and that the definer's convention was chosen to read as
reversed. The mirror image (`ADV-OWNER-01`, gold in the producer, correct consumer) was solved every time, which is the
control that says the lever is the location of the sign relative to the definer, not the round-trip structure.

## What broke Opus partly: the depth prior against a pinned deepest hop (`ADV-MASK-01`)

The gold `EnumUtils.compose` (H2) builds a bit field that is never shifted to its destination position; the deepest hop
`NumberUtils.overlay` (H5) shifts the field by `index*width` and the word by `at+index*width`, which is correct for a
pre-positioned field and looks inconsistent otherwise; `BitField.setValue` is a second, passing consumer of `overlay`. Opus's
three misses rank `overlay, combine, widen, compose`, the chain in strict depth order with the gold fourth; its two hits rank
`compose` first and cite `setValue`. Haiku's one answer had the same miss ordering; Sonnet's eight answers all ranked `compose` fourth behind `overlay`, with no hit in ten valid attempts (six further attempts were hung requests and are excluded).

The lever is the depth prior: with the fault under-determined between "H2 should have shifted" and "H5 should shift", the model
picks the deepest hop unless it has read a second consumer that pins H5. The artifact is `overlay`'s asymmetric parameterisation,
which is what makes H5 look like the candidate at all.

## What broke only the weaker models

- **Witness inversion (`ADV-LEX-01`).** Gold stripped to `apply(h, w, i, a, n, f)` with no javadoc; a decoy `wordOffset` carries
  the name, the javadoc and the correct formula in prose while computing the wrong-shaped one, executed only through a trivially
  true guard. Opus 5/5 correct; Sonnet's only wrong submitted ranking in screening put the decoy first; Sonnet confirmation
  gave eight gold-first answers out of nine (the screening signal was a three-run artefact). The decoy is second in every ranking of every model, so it attracts attention without overturning the
  value trace in the stronger model.
- **Agent exhaustion.** Haiku used its 50 tool calls without a valid submission in every Chart attack run and in two of three
  plain-control runs; that is baseline behaviour, not an attack effect. Sonnet's timeouts (17 to 49 model calls, still working
  at 300 s) are no-answers that count as misses over all attempts; the control block of ten plain runs measures how often that
  happens without an attack: seven of eight valid attempts answered with the gold first (Acc@1 over valid attempts 0.875), one budget exhaustion without a valid submission, five hung requests excluded (thirteen launched). Sonnet's no-answer rate without an attack is therefore about one in eight valid attempts, against three in ten on `ADV-DEFINER-01`, two in ten on `ADV-MASK-01` and five in ten on the composite.

## What did not break anything

`ADV-REGISTRY-01` (runtime-type registry, five `pack` implementations, odd-looking correct sibling registered first),
`ADV-OVERLOAD-01` (18 sibling conversions under one boolean) and `ADV-OWNER-01` (producer emits a spec-shaped wrong string,
consumer exposes it) were solved by Sonnet and Haiku in every answered run; they were not advanced to Opus. `ADV-DEPTH-01`
(non-terminal gold at H3 with a javadoc-loud correct H5) was solved in the only answered Sonnet and Haiku runs. Search cost,
candidate count and failure-signal coarsening slow the agents down and push Haiku into exhaustion, but they do not change
where a model that finishes puts the gold. The models trace values; they do not rank by proximity to the grep hit.

## The general statement

LLM fault localization under this protocol fails at attribution, not at discovery or search. The models find the faulty
method's body in every run. When the failure is fully determined by one method's body they rank it first regardless of naming,
depth, sibling count or how the assertion is phrased. When the failure is a convention split across a definer and an adapter,
or across a shallow contract and a deep consumer, they resolve the ambiguity with a prior (blame the definer of the wrong-looking
quantity; blame the deepest hop that looks inconsistent) and they do not go looking for the contract that would settle it. The
only observed corrections came from accidentally reading that contract (a unit test, a second consumer). That is the same
mechanism the pilot measured on CHART-PIE-03 and the supervisor-chain benchmark saw as "rank 1 holds except where the chain
loses a unique fault owner", now produced on demand with a pre-registered gold in two projects and three models.

## Caveats

Samples are small (five Opus runs per attack; ten Sonnet; three Haiku). Three Claude models under one protocol; GPT-5.6 was
not run (no credits) and the pilot showed GPT-5.6 behaving like Opus on PIE-03. Acc@1 over all attempts for Sonnet and Haiku
mixes attribution misses with exhaustion; the answered-run column and the control block separate them. The definer's pin
is variant-only in `ADV-DEFINER-01`; the clean thesis version needs it in both arms (`NEXT_STEP.md`). No completed run was
altered; the one reclassification (a provider stall) is documented with its evidence in `diagnostic/PROVIDER_STALL_RULE.md`.
