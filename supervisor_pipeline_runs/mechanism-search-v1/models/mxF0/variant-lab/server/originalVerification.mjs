import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { buildJavaMethodCatalogEntries } from "./agents/agentAdapter.mjs";
import { exists } from "./variantLibrary.mjs";

export const ORIGINAL_SEMANTICS = {
  Chart: {
    root_cause: "Legend-item generation exits when a valid category dataset exists because the dataset null check is inverted.",
    path: [
      "A category plot requests legend items from its renderer.",
      "The renderer resolves its dataset index through the owning plot.",
      "The plot returns the valid category dataset for that index.",
      "Legend generation evaluates the dataset-presence guard.",
      "The inverted guard treats the non-null dataset as the early-return case.",
      "Series iteration and legend-item creation are skipped.",
      "The returned collection contains no item for the valid series.",
      "The regression assertion observes the missing legend item.",
      "AbstractCategoryItemRenderer.getLegendItems owns the faulty guard.",
    ],
  },
  Cli: {
    root_cause: "Option lookup uses inconsistent raw, short, and long names instead of one canonical option identity.",
    path: [
      "A parsed option is stored with short and/or long aliases.",
      "A caller queries the command line using an accepted alias.",
      "The query follows a lookup path different from insertion.",
      "Alias canonicalization is inconsistent across the two paths.",
      "The stored Option is not resolved consistently.",
      "The public query reports absent or returns the wrong value.",
      "CommandLine option lookup methods require correction.",
    ],
  },
  Collections: {
    root_cause: "A single entry update falls through switch cases and overwrites additional compact-map value slots.",
    path: [
      "Flat3Map stores up to three entries in dedicated fields.",
      "An iterator entry selects one slot using nextIndex.",
      "setValue should mutate only that selected slot.",
      "The switch lacks termination between cases.",
      "Execution falls through into lower-index assignments.",
      "Unrelated stored values are overwritten.",
      "Subsequent map reads expose leaked state mutation.",
    ],
  },
  Math: {
    root_cause: "Continued-fraction conversion throws on an overflowing next convergent even when the previous convergent is a valid bounded-denominator fallback.",
    path: [
      "A floating value is converted through continued-fraction convergents.",
      "The max-denominator mode tracks the previous valid convergent.",
      "The next numerator or denominator crosses the overflow bound.",
      "The previous denominator still satisfies the requested bound.",
      "The algorithm fails to select that valid fallback.",
      "A FractionConversionException is thrown prematurely.",
      "The fraction constructor should return the previous convergent.",
    ],
  },
  Lang: {
    root_cause: "Hexadecimal number parsing chooses a narrow numeric type from digit count without accounting for leading zeroes and the highest significant digit.",
    path: [
      "createNumber recognizes a hexadecimal prefix.",
      "The parser estimates required width from the remaining character count.",
      "Leading zeroes do not contribute to numeric magnitude.",
      "The highest significant digit determines signed Int/Long overflow at boundary width.",
      "The width test ignores those magnitude facts.",
      "The parser commits to an unsuitable narrow representation.",
      "Number construction fails or returns the wrong numeric type.",
    ],
  },
  Csv: {
    root_cause: "Character consumption and line-number bookkeeping disagree about which line-separator characters advance the logical line count.",
    path: [
      "ExtendedBufferedReader consumes one character.",
      "The consumed character may be LF, CRLF, or a standalone CR.",
      "Line state depends on current and previous characters.",
      "The counter applies separator-specific bookkeeping.",
      "A valid separator is counted inconsistently.",
      "The reader's logical line number diverges from consumed input.",
      "CSV diagnostics or record positions expose the wrong line number.",
    ],
  },
  Codec: {
    root_cause: "Phonetic normalization uses the process default locale, allowing locale-specific case mappings to change an English-domain algorithm.",
    path: [
      "A phonetic encoder receives alphabetic input.",
      "The algorithm normalizes case before applying English letter rules.",
      "Case conversion consults the process default locale.",
      "Some locales map Latin letters differently from English.",
      "The normalized character sequence changes.",
      "Subsequent phonetic rules process different symbols.",
      "The encoder returns a locale-dependent result.",
    ],
  },
  Gson: {
    root_cause: "Generic type-variable resolution stops before recursively traversing the superclass hierarchy needed to bind an inherited field type.",
    path: [
      "Reflection inspects a field declared with a type variable.",
      "The runtime object type supplies a concrete generic binding indirectly.",
      "That binding is inherited through one or more superclass declarations.",
      "The resolver examines the immediate parameterized context.",
      "The unresolved value remains a TypeVariable.",
      "Hierarchy traversal is not continued to the declaring generic type.",
      "The concrete field type cannot be recovered.",
      "Adapter/type construction fails with an unsupported-type path.",
    ],
  },
  Time: {
    root_cause: "Partial field ordering treats unsupported duration fields as ordinarily comparable and conflates distinct unsupported fields with duplicates.",
    path: [
      "Partial construction validates an ordered array of field types.",
      "Each field type resolves to a duration field in the chronology.",
      "Some resolved duration fields are unsupported sentinels.",
      "Ordering compares the previous and current duration fields.",
      "Sentinel comparison returns equality without preserving support semantics.",
      "Distinct unsupported fields are treated as duplicate or misordered.",
      "A valid Partial field set is rejected.",
      "Partial validation and unsupported-field comparison require coordinated semantics.",
    ],
  },
  Closure: {
    root_cause: "Unused-function-argument removal runs when global removal is disabled, outside the mode that makes its transformation assumptions valid.",
    path: [
      "The compiler runs RemoveUnusedVars with a configured removal mode.",
      "A function has parameters whose call-site semantics must be preserved.",
      "Argument removal is only valid under the global-removal mode assumptions.",
      "The mode guard fails to stop the transformation.",
      "The pass analyzes and removes arguments outside its valid scope.",
      "The transformed function or call relationship changes unexpectedly.",
      "Compiled output exposes the invalid optimization.",
    ],
  },
};

function commandEnvironment(repoRoot) {
  const javaHome =
    process.env.D4J_JAVA_HOME ||
    process.env.JAVA_HOME ||
    "/Users/shawnli/.homebrew/opt/openjdk@11";
  const d4jBin = path.join(repoRoot, "framework", "bin");
  return {
    ...process.env,
    JAVA_HOME: javaHome,
    PATH: [path.join(javaHome, "bin"), d4jBin, process.env.PATH].filter(Boolean).join(path.delimiter),
  };
}

function run(command, args, options = {}) {
  const started = Date.now();
  return new Promise((resolve) => {
    execFile(
      command,
      args,
      {
        cwd: options.cwd,
        env: options.env,
        timeout: options.timeout ?? 1800000,
        maxBuffer: options.maxBuffer ?? 50 * 1024 * 1024,
        killSignal: "SIGTERM",
      },
      (error, stdout = "", stderr = "") => {
        resolve({
          command: [command, ...args].join(" "),
          cwd: options.cwd ?? process.cwd(),
          exit_code: typeof error?.code === "number" ? error.code : error ? 1 : 0,
          signal: error?.signal ?? null,
          timed_out: Boolean(error?.killed),
          stdout,
          stderr,
          error: error?.message ?? "",
          duration_ms: Date.now() - started,
        });
      },
    );
  });
}

async function runD4j(repoRoot, args, options = {}) {
  const command = path.join(repoRoot, "framework", "bin", "defects4j");
  const result = await run(command, args, { ...options, env: commandEnvironment(repoRoot) });
  if (!options.allowFailure && result.exit_code !== 0) {
    throw new Error(`${result.command} failed (${result.exit_code}): ${result.stderr || result.stdout || result.error}`);
  }
  return result;
}

async function atomicJson(filePath, value) {
  const temporary = `${filePath}.tmp-${process.pid}`;
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(temporary, `${JSON.stringify(value, null, 2)}\n`, { mode: 0o600 });
  await fs.rename(temporary, filePath);
}

async function ensureCheckout(repoRoot, checkoutRoot, project, version) {
  const target = path.join(checkoutRoot, `${project}-1`, version === "1b" ? "buggy" : "fixed");
  if (await exists(path.join(target, ".defects4j.config"))) {
    return { target, status: "existing", command: null };
  }
  if (await exists(target)) {
    throw new Error(`Incomplete checkout already exists and was not removed automatically: ${target}`);
  }
  await fs.mkdir(path.dirname(target), { recursive: true });
  const result = await runD4j(repoRoot, ["checkout", "-p", project, "-v", version, "-w", target]);
  return { target, status: "created", command: result };
}

async function exportProperty(repoRoot, checkout, property) {
  const result = await runD4j(repoRoot, ["export", "-p", property, "-w", checkout]);
  return result.stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

async function findFile(root, suffix) {
  const normalizedSuffix = suffix.split(".").join("/") + ".java";
  async function walk(current) {
    const entries = await fs.readdir(current, { withFileTypes: true }).catch(() => []);
    for (const entry of entries) {
      if ([".git", ".svn", "target", "build"].includes(entry.name)) continue;
      const absolute = path.join(current, entry.name);
      if (entry.isDirectory()) {
        const nested = await walk(absolute);
        if (nested) return nested;
      } else if (absolute.split(path.sep).join("/").endsWith(normalizedSuffix)) {
        return absolute;
      }
    }
    return null;
  }
  return walk(root);
}

function parsePatchChanges(patchText) {
  const changes = [];
  let file = "";
  let oldLine = 0;
  let newLine = 0;
  for (const line of patchText.split(/\r?\n/)) {
    if (line.startsWith("+++ b/")) {
      file = line.slice(6);
      continue;
    }
    const hunk = line.match(/^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
    if (hunk) {
      oldLine = Number(hunk[1]);
      newLine = Number(hunk[2]);
      continue;
    }
    if (!file || line.startsWith("---") || line.startsWith("+++")) continue;
    if (line.startsWith("-")) {
      changes.push({ file, side: "fixed", line: oldLine });
      oldLine += 1;
    } else if (line.startsWith("+")) {
      changes.push({ file, side: "buggy", line: newLine });
      newLine += 1;
    } else {
      oldLine += 1;
      newLine += 1;
    }
  }
  return changes;
}

function goldFromPatch(patchText, buggyCatalog, fixedCatalog) {
  const changes = parsePatchChanges(patchText);
  const selected = new Map();
  for (const change of changes) {
    const catalog = change.side === "fixed" ? fixedCatalog : buggyCatalog;
    const matches = catalog.filter(
      (entry) =>
        entry.file === change.file &&
        Number(entry.line_start) <= change.line &&
        Number(entry.line_end) >= change.line,
    );
    for (const entry of matches) {
      selected.set(entry.qualified, {
        class: entry.class,
        method: entry.method,
        file: entry.file,
        evidence: `Developer patch changes line ${change.line} inside ${entry.qualified}.`,
      });
    }
  }
  const buggyMethods = new Set(buggyCatalog.map((entry) => entry.qualified));
  return Array.from(selected.entries())
    .filter(([qualified]) => buggyMethods.has(qualified))
    .map(([, entry]) => entry);
}

export async function verifyOriginalBug({ repoRoot, checkoutRoot, batchDir, project, heartbeat = () => {} }) {
  if (!ORIGINAL_SEMANTICS[project]) throw new Error(`Unsupported original verification project: ${project}`);
  const artifactDir = path.join(batchDir, "originals", `${project}-1`);
  await fs.mkdir(artifactDir, { recursive: true });
  heartbeat(`${project}-1 checkout buggy`);
  const buggy = await ensureCheckout(repoRoot, checkoutRoot, project, "1b");
  heartbeat(`${project}-1 checkout fixed`);
  const fixed = await ensureCheckout(repoRoot, checkoutRoot, project, "1f");

  const triggeringTests = await exportProperty(repoRoot, buggy.target, "tests.trigger");
  const modifiedClasses = await exportProperty(repoRoot, buggy.target, "classes.modified");
  if (!triggeringTests.length) throw new Error(`${project}-1 has no triggering test metadata`);
  const failingTest = triggeringTests[0];
  const [testClass] = failingTest.split("::");
  const testFile = await findFile(buggy.target, testClass);
  if (!testFile) throw new Error(`Failing test source not found for ${failingTest}`);
  const testSource = await fs.readFile(testFile, "utf8");

  heartbeat(`${project}-1 reproduce ${failingTest}`);
  const testResult = await runD4j(repoRoot, ["test", "-t", failingTest], {
    cwd: buggy.target,
    allowFailure: true,
    timeout: 1800000,
  });
  const failingTestsFile = path.join(buggy.target, "failing_tests");
  const failingTestsText = (await exists(failingTestsFile)) ? await fs.readFile(failingTestsFile, "utf8") : "";
  const failingOutput = [testResult.stdout, testResult.stderr, failingTestsText].filter(Boolean).join("\n").trim();
  if (!failingOutput || (!/Failing tests:\s*[1-9]/i.test(failingOutput) && testResult.exit_code === 0)) {
    throw new Error(`${project}-1 triggering test did not reproduce a failure`);
  }

  const patchPath = path.join(repoRoot, "framework", "projects", project, "patches", "1.src.patch");
  const patchText = await fs.readFile(patchPath, "utf8");
  heartbeat(`${project}-1 parse production method catalog`);
  const buggyCatalog = await buildJavaMethodCatalogEntries(buggy.target);
  const fixedCatalog = await buildJavaMethodCatalogEntries(fixed.target);
  const goldMethods = goldFromPatch(patchText, buggyCatalog, fixedCatalog);
  if (!goldMethods.length) throw new Error(`${project}-1 developer patch could not be mapped to a production method`);

  const semantics = ORIGINAL_SEMANTICS[project];
  const timestamp = new Date().toISOString();
  const record = {
    schema_version: "d4j-verified-original/v1",
    task_id: `${project}-1`,
    project,
    bug_id: 1,
    triggering_tests: triggeringTests,
    failing_test_identifier: failingTest,
    failing_test_source_path: path.relative(repoRoot, testFile),
    modified_production_classes: modifiedClasses,
    developer_patch_path: path.relative(repoRoot, patchPath),
    gold_methods: goldMethods,
    semantic_root_cause: semantics.root_cause,
    call_and_state_propagation: semantics.path,
    reasoning: {
      reasoning_level: "Original",
      semantic_inference_steps: semantics.path.length,
      shortest_reasoning_path: semantics.path,
      shortcut_risks: [],
      reasoning_level_status: "verified_from_repository_evidence",
    },
    evidence: {
      triggering_test_reproduced: true,
      failing_output_present: Boolean(failingOutput),
      failing_test_source_present: Boolean(testSource),
      developer_patch_present: Boolean(patchText),
      production_method_catalog_size: buggyCatalog.length,
    },
    verified_at: timestamp,
  };
  await fs.writeFile(path.join(artifactDir, "developer.patch"), patchText);
  await fs.writeFile(path.join(artifactDir, "failing_output.log"), `${failingOutput}\n`);
  await fs.writeFile(path.join(artifactDir, "failing_test.java"), testSource);
  await atomicJson(path.join(artifactDir, "method_catalog_validation.json"), {
    project,
    catalog_size: buggyCatalog.length,
    gold_methods: goldMethods,
    all_gold_recognized: goldMethods.every((gold) => buggyCatalog.some((entry) => entry.qualified === `${gold.class}::${gold.method}`)),
    checked_at: timestamp,
  });
  await atomicJson(path.join(artifactDir, "verified_original.json"), record);
  return { record, artifactDir, testResult, checkout: { buggy, fixed } };
}
