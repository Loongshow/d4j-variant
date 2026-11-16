# CLOSURE-1-L10-STRICT-001

- **Variant ID:** `CLOSURE-1-L10-STRICT-001`
- **Original:** Defects4J `Closure-1`
- **Fixed baseline revision:** `1dfad504` (Closure-1f)
- **Depth level:** L10 (strict rubric: at least 10 irreducible semantic units)
- **Declared units:** 14 · **Conservative audited floor:** 12
- **Gold:** `com.google.javascript.jscomp.RemoveUnusedVars::removeUnreferencedFunctionArgs`
- **Trigger:** `com.google.javascript.jscomp.IntegrationTest::testAccessorFormalRetainedUnderUnusedCleanup`

## Semantic root cause

`removeUnreferencedFunctionArgs` contains a guard whose stated purpose is to exempt
object-literal accessors from unused-formal elimination, because a setter must declare
exactly one parameter. The variant makes that guard inspect the function node itself
rather than its parent accessor key. An object-literal setter is represented as
`SETTER_DEF -> FUNCTION`, so the guard can never observe an accessor key and is
unconditionally inert. The trailing-formal strip loop then removes the setter's mandatory
formal, and the compiler's own AST validator rejects the resulting tree.

## Production change

One token, in one production method:

```
-    if (NodeUtil.isGetOrSetKey(function.getParent())) {
+    if (NodeUtil.isGetOrSetKey(function)) {
```

## Trigger

The trigger compiles an object literal containing both a setter with an unused formal and
an ordinary function with an unused formal, and asserts that the ordinary formal is
removed while the accessor's formal is kept. The contrast is deliberate: it establishes
that unused-formal removal is working as intended, so the defect cannot be attributed to
the feature as a whole or to reference collection.

The trigger lives in `IntegrationTest`, not in the gold class's own test file, so the gold
owner is not named in the agent-visible file path.

## Difference from the original Closure-1 bug and from the existing variants

| | Original Closure-1 | `CLOSURE-1-L10-001` | **this variant** |
|---|---|---|---|
| Guard at fault | global-removal guard (absent) | global-removal guard (widened) | accessor exemption guard (inert) |
| Trigger condition | global removal disabled | call-site modification enabled | object-literal accessor present |
| Observable failure | function arity changes | function arity changes | AST invariant violation |

The semantic family is preserved (unused function-argument removal producing an
externally invalid function shape) while the trigger condition and the observable failure
mode both change, satisfying the AGENTS.md transformation requirement.

## Validation

Every figure below is captured output; see `validation.log`.

| Gate | Result |
|---|---|
| Fresh Closure-1f reconstruction | PASS |
| `test.patch` application to baseline | PASS |
| Baseline compile | PASS |
| Baseline trigger | PASS (Failing tests: 0) |
| Baseline full classes | PASS (83 + 170 + 111 tests) |
| `variant.patch` + `test.patch` application | PASS |
| Variant compile | PASS |
| Deterministic trigger failure | 3/3, identical signature |
| Original Closure-1 regressions | 8/8 PASS on the variant |
| Method catalog | PASS, 8226 production methods, gold present |
| Source integrity | 916 files hashed before and after, exactly 2 modified |
| VCS isolation | no `.git`, no `.svn` |
| Patch residue | the three `.bak` files present are PRE-EXISTING in the Defects4J checkout |
| Agent-visible leakage | gold class, gold method and guard helper each occur 0 times in `test.patch` and 0 times in the failure output |

## Blast radius

Beyond the trigger, exactly one pre-existing developer test fails:
`RemoveUnusedVarsTest::testDoNotOptimizeSetters`. That test is the dedicated regression
test for the guard this variant disables, so its failure confirms the fault is real. This
is comparable to `CHART-1-L10-STRICT-001`, which also carries one additional failure.

## Limitations

- The audited depth rests on a **single rater**. No agreement statistic exists.
- Validated on linux x86_64 with Temurin JDK 11.0.25 rather than the macOS `openjdk@11`
  host used for the earlier packages. The method catalog independently reproduces the
  8226-method count recorded by `CLOSURE-1-L30-STRICT-001`'s macOS validation, which
  cross-checks the two environments, but they are not identical.
- The failure output names `AstValidator` prominently. That component is a reporter, not
  a mutator, and eliminating it is one of the counted semantic units; but it is a salient
  decoy and should be recorded as a covariate in the shortcut audit.
