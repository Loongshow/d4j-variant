# Attacks built (Part 6/7): the mandated five plus two critic-top designs

Five attacks were built first so that every mandated target is covered; two more (`ADV-DEFINER-01`, `ADV-MASK-01`) were
built from the catalog's two highest critic-rated buildable ideas, both of which compose the one mechanism measured to
break both models (blame the method whose body contradicts its own contract; `FAILURE_SURFACE_MODEL.md`, lever L1).
All designs and golds were fixed before any model run. Each passed `scripts/validate_attack.py`: compiles, deterministic
failure x3, pre-registered signature, collateral recorded, and gate S (restoring only the declared gold line passes the trigger).

| Variant | Target | Base | Gold | Predicted wrong top-1 | Classification | Collateral (declared) |
|---|---|---|---|---|---|---|
| `ADV-DEPTH-01` | deepest-stage prior | Lang-1f, `testLang1112` | `BitField#widen` | org.apache.commons.lang3.math.NumberUtils#overlay (H5) | DEPTH_PRIOR_TRAP, ATTRIBUTION_TRAP, OWNERSHIP_TRAP, LEXICAL_TRAP, ARTIFACT | testIntArrayToLong |
| `ADV-REGISTRY-01` | symbol-directed search | Lang-1f, `testLang1112` | `Packer32#pack` | org.apache.commons.lang3.Packer16#pack (read first, odd shift) or Packers#forSource or the facade | SEARCH_TRAP, TOOL_BEHAVIOR_TRAP, CANDIDATE_OVERLOAD, MODEL_SPECIFIC, ARTIFACT | testIntArrayToLong |
| `ADV-LEX-01` | lexical/witness heuristics | Lang-1f, `testLang1112` | `NumberUtils#apply` | org.apache.commons.lang3.BitField#wordOffset | LEXICAL_TRAP, ATTRIBUTION_TRAP, CONTEXT_TRAP, ARTIFACT | none |
| `ADV-OVERLOAD-01` | candidate overload (>10) + top-10 limit | Lang-1f, `testLang1180` | `Conversion#hexToLong` | any of the other 17 executed siblings, most likely intArrayToLong or byteArrayToLong (first in the test), or the gold pushed out of the top 10 | CANDIDATE_OVERLOAD, FAILURE_SIGNAL_TRAP | none |
| `ADV-OWNER-01` | ownership/attribution | Lang-1f, `testLang1185` | `Conversion#longToHex` | org.apache.commons.lang3.Conversion#hexToLong (the consumer) | OWNERSHIP_TRAP, ATTRIBUTION_TRAP, FAILURE_SIGNAL_TRAP | testLongToHex |
| `ADV-DEFINER-01` | ownership/attribution + depth prior (critic-top idea CMB-01) | Chart-1f, `test2986548` | `Plot#nudge` | org.jfree.chart.plot.PlotUtilities#drift (definer) at rank 1; gold Plot#nudge rank 2 | ATTRIBUTION_TRAP, OWNERSHIP_TRAP, DEPTH_PRIOR_TRAP, CONTEXT_TRAP | none |
| `ADV-MASK-01` | depth prior + context (critic-top idea CTX-01) | Lang-1f, `testLang1112` | `EnumUtils#compose` | org.apache.commons.lang3.math.NumberUtils#overlay ('the field is not shifted by at') | DEPTH_PRIOR_TRAP, CONTEXT_TRAP, ATTRIBUTION_TRAP, OWNERSHIP_TRAP | none |

## Designs

### ADV-DEPTH-01: non-terminal gold at H3 (mask dropped) with a deeper, correct, javadoc-loud terminal H5

**Mechanism.** the corruption (sign-extended words) is introduced at H3 by dropping a mask, but the place where corrupted bits visibly land in the result is the deepest hop H5, whose arithmetic is the natural suspect and whose javadoc promises the masking; depth prior + fix-looking terminal + doc/code mismatch all point at H5; the gold's javadoc is worded so that its unmasked body reads as textbook widening (lever L1/L2), while H5's javadoc promises the masking

**Fault.** `words[i] = run[i];` in place of `words[i] = run[i] & field;`. Effect: negative int words are sign-extended into the long and pollute the bits above their field; the first assertion (positive word) passes, the second (0xCDF1F0C1) fails

**Structure.** linear five-hop chain, gold at H3. Declared candidates: 6. Roles: {"org.apache.commons.lang3.math.NumberUtils#overlay": "deeper-stage", "org.apache.commons.lang3.ObjectUtils#combine": "deeper-stage", "org.apache.commons.lang3.EnumUtils#compose": "shallower-stage", "org.apache.commons.lang3.ArrayUtils#gather": "shallower-stage", "org.apache.commons.lang3.Conversion#intArrayToLong": "facade"}

**Validation.** 17/17 gates pass. Signature: `junit.framework.AssertionFailedError: expected:<1311899830481706736> but was:<-55035966660880>`

**Builder.** `scripts/attacks/build_depth.py`; package `construction/packages/ADV-DEPTH-01/`.

**Note.** a one-line repair at H5 ((word & field) << shift) also fixes the trigger; ownership is contested by design (E4) and the declared gold is the method whose javadoc contract is to mask

### ADV-REGISTRY-01: runtime-type registry over five real `pack` implementations; fault in the selected one, odd-looking correct sibling registered first

**Mechanism.** the facade reaches the fault through Packers.forSource(src).pack(...): the symbol `pack` names five methods in five classes, the selected one depends on the runtime type of the source array, and the first-registered sibling (Packer16) has a correct but unusual shift expression; grep-the-next-symbol returns five equally named candidates

**Fault.** `shift = (i + holderPos) * 32;` in place of `shift = i * 32 + holderPos;`. Effect: int words are placed at (i + dstPos) * 32 instead of i * 32 + dstPos; any packing with a non-zero destination offset is wrong

**Structure.** facade -> registry lookup by runtime type -> one of five same-named implementations. Declared candidates: 7. Roles: {"org.apache.commons.lang3.Packer16#pack": "implementation-sibling", "org.apache.commons.lang3.Packer8#pack": "implementation-sibling", "org.apache.commons.lang3.Packer4#pack": "implementation-sibling", "org.apache.commons.lang3.Packer1#pack": "implementation-sibling", "org.apache.commons.lang3.Packers#forSource": "registry", "org.apache.commons.lang3.Conversion#intArrayToLong": "facade"}

**Validation.** 16/16 gates pass. Signature: `junit.framework.AssertionFailedError: expected:<64729929216> but was:<252851286>`

**Builder.** `scripts/attacks/build_registry.py`; package `construction/packages/ADV-REGISTRY-01/`.

### ADV-LEX-01: witness inversion: generic undocumented gold (`apply`) vs a loud, documented, executed decoy (`wordOffset`) whose javadoc states the correct formula and whose body computes the wrong-shaped one

**Mechanism.** every local witness that previously pointed at the gold (name, javadoc, parameter names, constant) is removed from the gold and planted on an executed decoy that additionally contradicts its own javadoc; the decoy's value never reaches the result

**Fault.** `final int p = (i + a) * n;` in place of `final int p = i * n + a;`. Effect: int words are placed at (i + at) * width instead of i * width + at

**Structure.** five-hop chain with an executed decoy at H3's class. Declared candidates: 7. Roles: {"org.apache.commons.lang3.BitField#wordOffset": "decoy-lexical", "org.apache.commons.lang3.BitField#widen": "shallower-stage", "org.apache.commons.lang3.ObjectUtils#combine": "shallower-stage", "org.apache.commons.lang3.EnumUtils#compose": "shallower-stage", "org.apache.commons.lang3.ArrayUtils#gather": "shallower-stage", "org.apache.commons.lang3.Conversion#intArrayToLong": "facade"}

**Validation.** 17/17 gates pass. Signature: `junit.framework.AssertionFailedError: expected:<64729929216> but was:<252851286>`

**Builder.** `scripts/attacks/build_lex.py`; package `construction/packages/ADV-LEX-01/`.

### ADV-OVERLOAD-01: 18 sibling conversions executed by one boolean-only test; fault in one

**Mechanism.** the trigger executes 18 near-identical sibling methods and asserts only a boolean, so neither the failure text nor dynamic participation singles out a candidate; 18 candidates exceed the 10 ranking slots

**Fault.** `shift = i * 4 + dstPos + (i / 8);` in place of `shift = i * 4 + dstPos;`. Effect: hex digits at index 8..15 are placed one bit too high, so any 16-digit hex-to-long conversion of a value with a non-zero upper word is wrong; no existing test exercises that region

**Structure.** flat: one facade-less test calling 18 static siblings; no chain. Declared candidates: 18. Roles: {"org.apache.commons.lang3.Conversion#intArrayToLong": "sibling", "org.apache.commons.lang3.Conversion#longToIntArray": "sibling", "org.apache.commons.lang3.Conversion#shortArrayToLong": "sibling", "org.apache.commons.lang3.Conversion#longToShortArray": "sibling", "org.apache.commons.lang3.Conversion#byteArrayToLong": "sibling", "org.apache.commons.lang3.Conversion#longToByteArray": "sibling", "org.apache.commons.lan

**Validation.** 16/16 gates pass. Signature: `junit.framework.AssertionFailedError`

**Builder.** `scripts/attacks/build_overload.py`; package `construction/packages/ADV-OVERLOAD-01/`.

### ADV-OWNER-01: round trip: producer (longToHex) emits spec-shaped but wrong upper digits; consumer (hexToLong) is correct and exposes it

**Mechanism.** the failure is a mismatch between a value and its decode(encode(value)); encoder and decoder are symmetric siblings executed in the same test; the encoder's output is layout-conformant (16 valid hex digits), and lever L13 says models exonerate a spec-shaped writer and blame the reader

**Fault.** `shift = i * 4 + srcPos + (i / 8);` in place of `shift = i * 4 + srcPos;`. Effect: hex digits 8..15 are taken from one bit too high in the source long, so the emitted string is wrong for any value with a non-zero upper word while remaining a valid hex string

**Structure.** flat round trip, two executed production methods plus two digit helpers. Declared candidates: 4. Roles: {"org.apache.commons.lang3.Conversion#hexToLong": "consumer", "org.apache.commons.lang3.Conversion#intToHexDigit": "sibling", "org.apache.commons.lang3.Conversion#hexDigitToInt": "sibling"}

**Validation.** 16/16 gates pass. Signature: `junit.framework.AssertionFailedError: expected:<-7296712173568108936> but was:<-3648356086631344520>`

**Builder.** `scripts/attacks/build_owner.py`; package `construction/packages/ADV-OWNER-01/`.

**Note.** the encoder fault also fails the pre-existing encoder test; visible only to an agent that runs the whole test class (neither model did so in the pilot)

### ADV-DEFINER-01: CHART-PIE-03 rebuilt: pure definer (drift, pinned by its own unit test) + NON-TERMINAL gold (nudge drops the negation) + correct textbook terminal (shift)

**Mechanism.** composes the only measured double-model failure (both models blame the method that DEFINES the wrong-looking quantity, drift = point1 - point2) with a non-terminal gold: the missing negation now lives in the adapter Plot.nudge, which both models ranked 2nd in every PIE-03 run; drift's convention is pinned by a passing unit test and shift is a textbook utility whose javadoc matches its body

**Fault.** `double deltaX = drift.getX() * explodePercent;` in place of `double deltaX = -drift.getX() * explodePercent;`. Effect: the exploded section is displaced away from the pie centre by the drift instead of toward it: expected 87.5, actual 112.5

**Structure.** five-hop chain, gold at H4, definer at H3 pinned by PlotUtilitiesTests.testDrift. Declared candidates: 6. Roles: {"org.jfree.chart.plot.PlotUtilities#drift": "producer", "org.jfree.chart.util.ShapeUtilities#shift": "deeper-stage", "org.jfree.chart.plot.dial.StandardDialScale#rim": "shallower-stage", "org.jfree.chart.plot.CompassPlot#ring": "shallower-stage", "org.jfree.chart.plot.PiePlot#getArcBounds": "facade"}

**Validation.** 17/17 gates pass. Signature: `junit.framework.AssertionFailedError: expected:<87.5> but was:<112.5>`

**Builder.** `scripts/attacks/build_definer.py`; package `construction/packages/ADV-DEFINER-01/`.

**Note.** testDrift pins the definer's convention; it exists only with the variant, and gate K confirms it passes under the buggy variant (it is not a new failure)

### ADV-MASK-01: pre-positioned field contract: unpositioned field built at H2 with the template's verbatim line; H5's field/word shift asymmetry reads as the bug; a second real consumer pins H5

**Mechanism.** the locally inconsistent formula sits at the deepest hop (overlay shifts the field by index*width but the word by at+index*width), which is where both models look for the fault; the gold's line is the verbatim line of a previously validated chain and reads as correct; a passing second consumer makes 'fix overlay' wrong

**Fault.** `final long field = (1L << width) - 1;` in place of `final long field = ((1L << width) - 1) << at;`. Effect: the field is never shifted to the destination bit position, so the placed word is masked at the wrong bits

**Structure.** five-hop chain, gold at H2, second real consumer of H5. Declared candidates: 7. Roles: {"org.apache.commons.lang3.math.NumberUtils#overlay": "deeper-stage", "org.apache.commons.lang3.ObjectUtils#combine": "deeper-stage", "org.apache.commons.lang3.BitField#widen": "deeper-stage", "org.apache.commons.lang3.ArrayUtils#gather": "shallower-stage", "org.apache.commons.lang3.Conversion#intArrayToLong": "facade", "org.apache.commons.lang3.BitField#setValue": "consumer"}

**Validation.** 17/17 gates pass. Signature: `junit.framework.AssertionFailedError: expected:<64729929216> but was:<305419776>`

**Builder.** `scripts/attacks/build_mask.py`; package `construction/packages/ADV-MASK-01/`.

### ADV-COMPOSITE-01 (Part 17, maximum difficulty): pinned pure definer + non-terminal generic undocumented guard-padded gold + loud correct terminal + boolean-only failure

**Mechanism.** stacks every manipulation that produced misses in screening/confirmation on the design that worked best. Base: the `ADV-DEFINER-01` patch (definer attribution with a non-terminal gold: 0/5 Opus, 0/3 Sonnet in screening). Added: (1) witness removal at the gold (`nudge` becomes `resolve(Rectangle2D r, double f, Point2D d)`, no javadoc, no meaningful names); (2) guard padding (null/NaN/negative/empty/zero fast paths returning a clone) so the two delta lines sit more than twenty lines below the declaration; (3) a loud terminal: `ShapeUtilities.shift` gets a javadoc that claims the exploded-section semantics ("Resolves the bounds of an exploded pie section from the unexploded area and its scaled drift: the section is displaced along the drift"); (4) the trigger's two assertion blocks are coarsened to single booleans so the failure text is a bare `AssertionFailedError` with no 87.5/112.5 clue, which both models used in PIE-03 and DEFINER-01 to reason about the sign.

**Fault.** `double dx = d.getX() * f;` / `double dy = d.getY() * f;` in place of `double dx = -d.getX() * f;` / `double dy = -d.getY() * f;`. Effect: the exploded section is displaced away from the pie centre instead of toward it.

**Structure.** five-hop chain, gold at H4 (`Plot.resolve`), definer at H3 (`PlotUtilities.drift`, pinned by `PlotUtilitiesTests.testDrift`), loud terminal at H5 (`ShapeUtilities.shift`). Declared candidates: 6. Roles: {"org.jfree.chart.plot.PlotUtilities#drift": "producer", "org.jfree.chart.util.ShapeUtilities#shift": "deeper-stage", "org.jfree.chart.plot.dial.StandardDialScale#rim": "shallower-stage", "org.jfree.chart.plot.CompassPlot#ring": "shallower-stage", "org.jfree.chart.plot.PiePlot#getArcBounds": "facade"}

**Validation.** 17/17 gates pass (gate F initially failed because `git apply` of the base test patch left the companion test file untracked and it was omitted from the composite's `test.patch`; fixed in the builder with an intent-to-add, rebuilt, re-validated). Signature: `junit.framework.AssertionFailedError` (boolean assertion, no expected/actual values). Collateral: none beyond `ADV-DEFINER-01`'s; `testDrift` is a companion test that passes under the variant (gate K).

**Builder.** `scripts/attacks/build_composite.py`; package `construction/packages/ADV-COMPOSITE-01/`.

**Plan.** claude-sonnet-4-6 x10, claude-opus-5-5 x5, one slot per server; gold and roles fixed before any run (this file and `attack.json` were written before launch).

**Classification.** ATTRIBUTION_TRAP, OWNERSHIP_TRAP, DEPTH_PRIOR_TRAP, LEXICAL_TRAP, TOOL_BEHAVIOR_TRAP, FAILURE_SIGNAL_TRAP, CONTEXT_TRAP, ARTIFACT. Its clean core is `ADV-DEFINER-01`; everything else is a steering artifact (see `CLEAN_VS_ARTIFACT_ATTACKS.md`).
