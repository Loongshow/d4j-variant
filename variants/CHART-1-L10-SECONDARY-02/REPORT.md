# CHART-1-L10-SECONDARY-02

## Status and identity

- Status: validated L10 semantic bug variant
- Original project/bug: Defects4J Chart-1
- Fixed baseline: Chart-1f, SVN r2266
- Git mirror baseline: `19998781c35b4f68a509f6b630f4815392769f38`
- Depth: L10
- Variant reasoning units: 13
- Production fault size: one changed statement in one production file
- Triggering tests added: one deterministic JUnit 3 test method

The Git mirror commit is dated 2010-02-09 and is titled with bug 2947660. Its
historical diff changes `getLegendItems()` from `dataset != null` to
`dataset == null` and adds `test2947660()`.

## Implementation

Changed production file:

- `source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java`

Changed test file:

- `tests/org/jfree/chart/renderer/category/junit/AbstractCategoryItemRendererTests.java`

Production change:

```diff
-        CategoryDataset dataset = p.getDataset(datasetIndex);
+        CategoryDataset dataset = p.getDataset();
```

New test:

- `AbstractCategoryItemRendererTests.testLegendItemsForSecondaryDataset`
- Dataset 0 has row key `Primary`.
- Dataset 1 has row key `Secondary`.
- A `LevelRenderer` is registered at renderer index 1. `LevelRenderer`
  inherits the affected `AbstractCategoryItemRenderer.getLegendItem()`.
- The test requests that renderer's legend items and asserts one item labelled
  `Secondary`.

## Semantic root cause

The variant discards the `datasetIndex` supplied by `getLegendItems()` when it
delegates to `getLegendItem(datasetIndex, series)`. The helper reads the plot's
primary dataset instead. For a renderer at index 1, the legend item therefore
gets its label, series key, and dataset object from dataset 0 while retaining
dataset index 1. This creates internally inconsistent legend-item provenance.

## Original Chart-1 reasoning tree

The original tree has 14 auditable units.

1. **R1** — A renderer's legend collection represents the visible series in
   its associated dataset.
2. **C1** — Calling `getLegendItems()` on an unattached renderer is valid.
3. **D1** — The plot-null guard returns a non-null empty collection.
4. **C2** — The renderer is attached to a plot with a non-null dataset.
5. **F1** — The buggy `dataset != null` guard returns early for every ordinary
   attached dataset.
6. **C3** — The dataset gains row `S1`, so one legend item is required.
7. **D2** — Intended behavior is to return early only when the dataset is
   null.
8. **D3** — Read the dataset row count and rendering order.
9. **D4** — Check series visibility in the legend.
10. **S1** — Delegate to `getLegendItem(index, series)`.
11. **S2** — Generate the series label from the dataset row key.
12. **S3** — Add the generated item to the collection.
13. **O1** — The buggy revision returns count 0 where the test expects count 1
    and label `S1`.
14. **P1** — The original fix changes the guard to `dataset == null`.

## Variant reasoning tree

The variant tree has 13 auditable units.

1. **R1** — Each legend item must represent the visible series in the
   renderer's own dataset.
2. **C1** — Dataset 0 contains row key `Primary`.
3. **C2** — Dataset 1 contains row key `Secondary`, and a `LevelRenderer` is
   registered at renderer index 1.
4. **C3** — The public call is `renderer.getLegendItems()`.
5. **D1** — `getLegendItems()` resolves the renderer's plot index as 1.
6. **D2** — It resolves dataset 1 and passes the fixed null guard.
7. **D3** — It enumerates the one visible series at row 0.
8. **S1** — It calls `getLegendItem(1, 0)`.
9. **F1** — The helper ignores argument 1 and calls the primary-dataset
   accessor `p.getDataset()`.
10. **S2** — The label generator and row-key lookup consume dataset 0 and
    produce `Primary`.
11. **S3** — The item stores the primary dataset object but dataset index 1.
12. **O1** — The collection count remains 1, but the assertion expects
    `Secondary` and observes `Primary`.
13. **P1** — Restoring `p.getDataset(datasetIndex)` repairs the association.

## Changed and preserved reasoning nodes

Changed node:

- Dataset resolution inside the direct legend-item helper changes from indexed
  lookup to primary-dataset lookup. This changes the propagation path and the
  non-zero dataset API path.

Preserved nodes:

- the legend/item semantic contract;
- renderer-to-plot index discovery;
- the fixed dataset-null guard;
- row-count and rendering-order enumeration;
- series visibility filtering;
- delegation to `getLegendItem(index, series)`;
- label generation from a dataset row key;
- construction and collection of one legend item;
- a deterministic legend assertion as the observable failure.

## Difference from the original bug

The original Chart-1 defect inverted the dataset-null guard in
`getLegendItems()`. It suppressed all legend items for a normal non-null
dataset, including dataset index 0.

This variant leaves that guard fixed. It succeeds for index 0 and preserves the
collection count for index 1, but associates a non-zero renderer with dataset
0 during helper processing. The original regression method `test2947660`
passes on the variant. The trigger, fault site within the method, propagation
path, affected API path, and failure symptom are therefore distinct from the
original bug.

## Validation environment

- OpenJDK Temurin 11.0.32
- Apache Ant 1.10.15
- Repository-provided JUnit and dependency JARs
- Windows validation was run from a disposable local temp checkout because the
  sandbox account could not close JAR file systems stored under OneDrive.
- The two validated source files and the packaged working-copy files have
  matching SHA-256 hashes, recorded in `manifest.json`.

The repository has no local Defects4J or Ant installation. The packaged
`validation-build.xml` reproduces the source/test compilation and JUnit
commands without modifying the historical project's build files.

## Validation results

| Check | Result |
|---|---|
| Fixed baseline production compile | PASS — 593 source files |
| Fixed baseline test compile | PASS — 382 source files |
| Fixed baseline developer suite | PRE-EXISTING FAILURE documented below |
| Final trigger on fixed production | PASS — affected class: 9/9 |
| Variant production/test compile | PASS — 593/382 source files |
| New trigger on variant, run 1 | EXPECTED FAIL — `Secondary` vs `Primary` |
| New trigger on variant, run 2 | EXPECTED FAIL — `Secondary` vs `Primary` |
| New trigger on variant, run 3 | EXPECTED FAIL — `Secondary` vs `Primary` |
| Original `test2947660` on variant | PASS — 1/1 |
| `git diff --check` | PASS |

### Passing output

Fixed production with the final triggering test:

```text
Tests run: 9, Failures: 0, Errors: 0, Skipped: 0
Testcase: testLegendItemsForSecondaryDataset
Testcase: test2947660
BUILD SUCCESSFUL
```

Original Chart-1 regression method on the variant:

```text
Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
Testcase: test2947660
BUILD SUCCESSFUL
```

### Failing output

Each of the three isolated variant runs produced the same failure:

```text
Tests run: 1, Failures: 1, Errors: 0, Skipped: 0
Testcase: testLegendItemsForSecondaryDataset
FAILED
expected:<Second...> but was:<Prim...>
junit.framework.ComparisonFailure
  at AbstractCategoryItemRendererTests.java:399
```

### Pre-existing baseline failure

Before any source or test edit, the complete developer-suite command compiled
all production and test sources, then stopped at this Java 11 serialization
failure:

```text
Test: org.jfree.chart.renderer.junit.DefaultPolarItemRendererTests
Method: testSerialization
java.io.NotSerializableException: java.awt.AlphaComposite
expected:<org.jfree.chart.renderer.DefaultPolarItemRenderer@...> but was:<null>
```

This failure is unrelated to the changed class and was present on the clean
fixed baseline. Because the validation target halts on the first failure, no
claim is made about developer classes scheduled after it. The directly
affected renderer test class is green on fixed production.

## Validation commands

From a Chart-1f checkout, with `JAVA_HOME` pointing to JDK 11 and Ant on
`PATH`, define the package path and use a fresh output directory for clean
compilation:

```powershell
ant -f <package>\validation-build.xml `
  -Dproject.dir=<Chart-1f-checkout> `
  -Dvalidation.dir=<fresh-output> test

ant -f <package>\validation-build.xml `
  -Dproject.dir=<Chart-1f-with-final-test> `
  -Dvalidation.dir=<fresh-baseline-output> test-class

ant -f <package>\validation-build.xml `
  -Dproject.dir=<variant-checkout> `
  -Dvalidation.dir=<fresh-variant-output> test-class

ant -f <package>\validation-build.xml `
  -Dproject.dir=<variant-checkout> `
  -Dvalidation.dir=<fresh-variant-output> `
  -Dtest.method=test2947660 test-method

ant -f <package>\validation-build.xml `
  -Dproject.dir=<variant-checkout> `
  -Dvalidation.dir=<fresh-variant-output> test-method
```

Run the final command three times. It must fail identically each time. Apply
the artifact with:

```powershell
git apply <package>\variant.patch
```

## Limitations and possible equivalent behavior

- Only category renderers that inherit
  `AbstractCategoryItemRenderer.getLegendItem()` are affected. Renderers such
  as `LineAndShapeRenderer` and `BarRenderer` override that method and bypass
  this fault.
- Dataset index 0 is unaffected because the indexed and primary accessors
  resolve the same dataset.
- If dataset 0 and the selected non-zero dataset have identical row keys and
  compatible series layouts, the label symptom can be observationally
  equivalent for that input.
- If dataset 0 is null while a non-zero dataset exists, the variant can fail
  earlier with a null-related exception rather than a wrong label.
- The complete historical developer suite is not fully green on modern Java
  11 because of the documented pre-existing serialization incompatibility.

