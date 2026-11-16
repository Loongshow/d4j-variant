# CHART-1-L10-SECONDARY-02

## Source

- Original Defects4J bug: Chart-1
- Fixed baseline revision: 2266
- Depth level: L10
- Reasoning unit count: 11

## Variant

The variant preserves the original legend/item semantic expectation but changes
the API path inside `AbstractCategoryItemRenderer::getLegendItem`. Instead of
fetching the dataset by the renderer's `datasetIndex`, it fetches the plot's
default dataset.

## Fault

`source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java`

```diff
- CategoryDataset dataset = p.getDataset(datasetIndex);
+ CategoryDataset dataset = p.getDataset();
```

## Trigger

`org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests::testLegendItemsForSecondaryDataset`

Renderer under test:
`org.jfree.chart.renderer.category.LevelRenderer`

`LevelRenderer` inherits `AbstractCategoryItemRenderer::getLegendItem`, so
the triggering test exercises the affected base method.

Expected label: `Secondary`
Observed label on the variant: `Primary`

## Validation

- Clean fixed baseline compiles: PASS
- New triggering test passes on fixed baseline: PASS
- Variant compiles: PASS
- New triggering test fails on variant: PASS
- Deterministic failure across three runs: PASS
- Original Chart-1 `test2947660`: PASS
- Full suite caveat: Java 11 AlphaComposite serialization failure is pre-existing and unrelated.

## Difference From Original Bug

The original Chart-1 bug was the inverted null check in `getLegendItems()`
that returned early when a valid dataset existed. This variant relocates the
fault to `getLegendItem(int, int)` and changes the dataset lookup API path for
secondary datasets.

## Limitations

The migrated files were reconstructed from the pasted known evidence because no
canonical source directory named `CHART-1-L10-SECONDARY-02` was present locally.
