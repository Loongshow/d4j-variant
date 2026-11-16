import type { BugDetail, BugSummary, VariantArtifact, VariantDimension, WorkflowStep } from "./types";

const chartSource = `package org.jfree.chart.renderer.category;

import org.jfree.chart.LegendItemCollection;
import org.jfree.data.category.CategoryDataset;

public abstract class AbstractCategoryItemRenderer {
    private CategoryPlot plot;

    public LegendItemCollection getLegendItems() {
        LegendItemCollection result = new LegendItemCollection();
        CategoryPlot cp = getPlot();
        if (cp == null) {
            return result;
        }
        CategoryDataset dataset = cp.getDataset();
        if (dataset == null) {
            return result;
        }
        int seriesCount = dataset.getRowCount();
        for (int i = 0; i < seriesCount; i++) {
            LegendItem item = getLegendItem(0, i);
            if (item != null) {
                result.add(item);
            }
        }
        return result;
    }
}`;

const chartTest = `public void test2947660() {
    AbstractCategoryItemRenderer r = new LineAndShapeRenderer();
    DefaultCategoryDataset dataset = new DefaultCategoryDataset();
    dataset.addValue(1.0, "R1", "C1");
    CategoryPlot plot = new CategoryPlot(dataset, new CategoryAxis("C"), new NumberAxis("V"), r);

    LegendItemCollection items = r.getLegendItems();

    assertEquals("One legend item expected for a valid dataset", 1, items.getItemCount());
}`;

const chartDiff = `diff --git a/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java b/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java
--- a/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java
+++ b/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java
@@ -1794,7 +1794,7 @@ public abstract class AbstractCategoryItemRenderer {
         }
         CategoryDataset dataset = cp.getDataset();
-        if (dataset != null) {
+        if (dataset == null) {
             return result;
         }
         int seriesCount = dataset.getRowCount();`;

const genericJava = (className: string) => `package mock.defects4j;

public class ${className} {
    public String normalize(String input) {
        if (input == null) {
            return "";
        }
        return input.trim();
    }
}`;

const genericTest = (className: string) => `public void testRegressionPath() {
    ${className} subject = new ${className}();
    assertEquals("value", subject.normalize(" value "));
}`;

const baseBugs: BugDetail[] = [
  {
    id: "chart-1",
    name: "Chart-1",
    project: "Chart",
    bugId: 1,
    baselineVersion: "fixed revision: Chart-1f",
    status: "analyzed",
    issue: "Legend items not generated for valid category dataset.",
    modifiedClass: "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java",
    buggyMethod: "getLegendItems()",
    rootCause: "dataset null check was inverted, causing early return when dataset exists.",
    sourceFiles: [
      {
        path: "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java",
        language: "java",
        content: chartSource,
      },
      {
        path: "tests/org/jfree/chart/renderer/category/junit/AbstractCategoryItemRendererTests.java",
        language: "java",
        content: chartTest,
      },
    ],
    tests: [
      {
        name: "test2947660",
        className: "org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests",
        assertion: "assertEquals(1, items.getItemCount())",
        output:
          "junit.framework.AssertionFailedError: One legend item expected for a valid dataset expected:<1> but was:<0>",
      },
    ],
    diff: chartDiff,
    reasoningTree: [
      { code: "R", label: "Regression Expectation", detail: "A valid category dataset should produce legend entries for visible series." },
      { code: "C", label: "Input Constraint", detail: "CategoryPlot owns a non-null DefaultCategoryDataset with one row key." },
      { code: "D", label: "Dataset Branch", detail: "getLegendItems() reads the plot dataset before iterating series keys." },
      { code: "S", label: "State Mutation", detail: "LegendItemCollection is initialized empty and should be populated in the loop." },
      { code: "F", label: "Fault", detail: "The buggy revision returned early when dataset was non-null." },
      { code: "O", label: "Observable Failure", detail: "The legend collection contains zero items." },
      { code: "P", label: "Propagation", detail: "Renderer public API exposes the empty collection to the triggering test." },
    ],
  },
  {
    id: "cli-1",
    name: "CLI-1",
    project: "CLI",
    bugId: 1,
    baselineVersion: "fixed revision: CLI-1f",
    status: "original",
    issue: "Command-line option parser mishandles a compact short option path.",
    modifiedClass: "src/java/org/apache/commons/cli/Parser.java",
    buggyMethod: "processOption()",
    rootCause: "Mock root cause: option token normalization bypasses an expected value check.",
    sourceFiles: [{ path: "src/java/org/apache/commons/cli/Parser.java", language: "java", content: genericJava("Parser") }],
    tests: [
      {
        name: "testCompactOption",
        className: "org.apache.commons.cli.ParserTest",
        assertion: "assertTrue(commandLine.hasOption(\"a\"))",
        output: "AssertionFailedError: expected option -a to be present",
      },
    ],
    diff:
      "diff --git a/src/java/org/apache/commons/cli/Parser.java b/src/java/org/apache/commons/cli/Parser.java\n@@ -44,7 +44,7 @@\n-    return token;\n+    return normalize(token);",
    reasoningTree: [
      { code: "R", label: "Regression Expectation", detail: "Compact short options should be discoverable through the public parser API." },
      { code: "C", label: "Input Constraint", detail: "The argument vector contains a short option with an attached token." },
      { code: "D", label: "Parser Decision", detail: "The parser classifies the token before value consumption." },
      { code: "F", label: "Fault", detail: "Normalization is skipped on one option path." },
      { code: "O", label: "Observable Failure", detail: "The parsed command line reports the option missing." },
    ],
  },
  {
    id: "codec-1",
    name: "Codec-1",
    project: "Codec",
    bugId: 1,
    baselineVersion: "fixed revision: Codec-1f",
    status: "original",
    issue: "Encoder emits an unexpected byte sequence for a boundary input.",
    modifiedClass: "src/java/org/apache/commons/codec/binary/Base64.java",
    buggyMethod: "encode()",
    rootCause: "Mock root cause: terminal padding branch uses an incorrect remaining-byte count.",
    sourceFiles: [{ path: "src/java/org/apache/commons/codec/binary/Base64.java", language: "java", content: genericJava("Base64") }],
    tests: [
      {
        name: "testBoundaryPadding",
        className: "org.apache.commons.codec.binary.Base64Test",
        assertion: "assertArrayEquals(expected, actual)",
        output: "arrays first differed at element [3]",
      },
    ],
    diff:
      "diff --git a/src/java/org/apache/commons/codec/binary/Base64.java b/src/java/org/apache/commons/codec/binary/Base64.java\n@@ -120,7 +120,7 @@\n-    modulus = 0;\n+    modulus = bytes.length % 3;",
    reasoningTree: [
      { code: "R", label: "Regression Expectation", detail: "Boundary inputs preserve RFC-compatible padding." },
      { code: "C", label: "Input Constraint", detail: "Input length leaves one byte after full groups." },
      { code: "D", label: "Padding Branch", detail: "The encoder computes terminal padding from the remaining-byte count." },
      { code: "F", label: "Fault", detail: "The remaining-byte count is reset too early." },
      { code: "O", label: "Observable Failure", detail: "The final encoded bytes differ from expected output." },
    ],
  },
  {
    id: "math-1",
    name: "Math-1",
    project: "Math",
    bugId: 1,
    baselineVersion: "fixed revision: Math-1f",
    status: "original",
    issue: "Numerical solver accepts an invalid bracketing interval.",
    modifiedClass: "src/main/java/org/apache/commons/math/analysis/solvers/BrentSolver.java",
    buggyMethod: "solve()",
    rootCause: "Mock root cause: endpoint validation runs after an early convergence shortcut.",
    sourceFiles: [{ path: "src/main/java/org/apache/commons/math/analysis/solvers/BrentSolver.java", language: "java", content: genericJava("BrentSolver") }],
    tests: [
      {
        name: "testInvalidIntervalRejected",
        className: "org.apache.commons.math.analysis.solvers.BrentSolverTest",
        assertion: "fail(\"Expected IllegalArgumentException\")",
        output: "Expected IllegalArgumentException",
      },
    ],
    diff:
      "diff --git a/src/main/java/org/apache/commons/math/analysis/solvers/BrentSolver.java b/src/main/java/org/apache/commons/math/analysis/solvers/BrentSolver.java\n@@ -88,7 +88,7 @@\n-    verifyInterval(min, max);\n+    verifyBracketing(min, max, f);",
    reasoningTree: [
      { code: "R", label: "Regression Expectation", detail: "Invalid bracketing intervals should be rejected deterministically." },
      { code: "C", label: "Input Constraint", detail: "Function values at both endpoints have the same sign." },
      { code: "D", label: "Validation Branch", detail: "The solver checks bracketing before convergence decisions." },
      { code: "F", label: "Fault", detail: "Validation is delayed behind an early shortcut." },
      { code: "O", label: "Observable Failure", detail: "The solver returns instead of throwing." },
    ],
  },
  {
    id: "gson-1",
    name: "Gson-1",
    project: "Gson",
    bugId: 1,
    baselineVersion: "fixed revision: Gson-1f",
    status: "original",
    issue: "JSON adapter path drops a field under a nested generic type.",
    modifiedClass: "gson/src/main/java/com/google/gson/internal/bind/ReflectiveTypeAdapterFactory.java",
    buggyMethod: "getBoundFields()",
    rootCause: "Mock root cause: field exclusion cache key omits the resolved generic owner.",
    sourceFiles: [
      {
        path: "gson/src/main/java/com/google/gson/internal/bind/ReflectiveTypeAdapterFactory.java",
        language: "java",
        content: genericJava("ReflectiveTypeAdapterFactory"),
      },
    ],
    tests: [
      {
        name: "testNestedGenericField",
        className: "com.google.gson.functional.GenericTypesTest",
        assertion: "assertEquals(\"value\", decoded.payload.name)",
        output: "expected:<value> but was:<null>",
      },
    ],
    diff:
      "diff --git a/gson/src/main/java/com/google/gson/internal/bind/ReflectiveTypeAdapterFactory.java b/gson/src/main/java/com/google/gson/internal/bind/ReflectiveTypeAdapterFactory.java\n@@ -210,7 +210,7 @@\n-    return rawType;\n+    return resolvedType;",
    reasoningTree: [
      { code: "R", label: "Regression Expectation", detail: "Nested generic fields should round-trip through the adapter path." },
      { code: "C", label: "Input Constraint", detail: "The type token resolves a generic owner with a concrete field type." },
      { code: "D", label: "Reflection Decision", detail: "Bound-field discovery applies exclusion rules after type resolution." },
      { code: "F", label: "Fault", detail: "Cache lookup uses the raw owner type." },
      { code: "O", label: "Observable Failure", detail: "The decoded nested field is null." },
    ],
  },
];

export const mockBugs: BugDetail[] = baseBugs;

export const mockBugSummaries: BugSummary[] = mockBugs.map(
  ({ sourceFiles: _sourceFiles, tests: _tests, diff: _diff, reasoningTree: _reasoningTree, ...summary }) => summary,
);

export const workflowTemplate = (): WorkflowStep[] => [
  { id: "agent-1", title: "Agent 1: Original Bug Analyst", status: "pending", artifactNames: ["agent1_report.md"] },
  { id: "agent-2", title: "Agent 2: Variant Designer", status: "pending", artifactNames: ["candidates.md"] },
  { id: "agent-3", title: "Agent 3: Benchmark Reviewer", status: "pending", artifactNames: ["review.md"] },
  { id: "agent-4", title: "Agent 4: Implementer", status: "pending", artifactNames: ["patch.diff"] },
  { id: "agent-5", title: "Agent 5: Validator / Packager", status: "pending", artifactNames: ["validation.log", "variant_report.md"] },
];

export const artifactTemplate = (): VariantArtifact[] => [
  { name: "agent1_report.md", kind: "report", status: "queued" },
  { name: "candidates.md", kind: "candidates", status: "queued" },
  { name: "review.md", kind: "review", status: "queued" },
  { name: "patch.diff", kind: "patch", status: "queued" },
  { name: "validation.log", kind: "log", status: "queued" },
  { name: "variant_report.md", kind: "report", status: "queued" },
];

export const nodeForDimension: Record<VariantDimension, string> = {
  "fault-site relocation": "F: Fault",
  "trigger-condition substitution": "C: Input Constraint",
  "propagation-path modification": "P: Propagation",
  "failure-mode modification": "O: Observable Failure",
  "API-path substitution": "R: Public API Expectation",
};
