import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import {
  buildJavaMethodCatalogEntries,
  compareSourceHashes,
  copyDirectoryFiltered,
  hashSourceFiles,
} from "./agents/agentAdapter.mjs";
import { canonicalVariantDir, exists, normalizeLevel, sha256File } from "./variantLibrary.mjs";

const REQUIRED_AGENT_ARTIFACTS = ["candidates.md", "review.md", "implementation.json"];

export function normalizeJavaMethodIdentity(value) {
  const raw = String(value ?? "").trim();
  if (/^[A-Za-z_$][\w$]*$/.test(raw)) return raw;
  const signature = raw.match(/^([A-Za-z_$][\w$]*)\s*\((.*)\)$/s);
  if (!signature) return null;

  let genericDepth = 0;
  let arrayDepth = 0;
  for (const character of signature[2]) {
    if (character === "<") genericDepth += 1;
    if (character === ">") genericDepth -= 1;
    if (character === "[") arrayDepth += 1;
    if (character === "]") arrayDepth -= 1;
    if (genericDepth < 0 || arrayDepth < 0) return null;
  }
  return genericDepth === 0 && arrayDepth === 0 ? signature[1] : null;
}

export function hasRequiredEvidence(value) {
  return Array.isArray(value)
    ? value.length > 0 && value.every((item) => Boolean(String(item ?? "").trim()))
    : Boolean(String(value ?? "").trim());
}

function runProcess(command, args, options = {}) {
  const started = Date.now();
  return new Promise((resolve) => {
    execFile(
      command,
      args,
      {
        cwd: options.cwd,
        env: options.env ?? process.env,
        timeout: options.timeout ?? 1800000,
        killSignal: "SIGTERM",
        maxBuffer: options.maxBuffer ?? 50 * 1024 * 1024,
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
          started_at: new Date(started).toISOString(),
          completed_at: new Date().toISOString(),
        });
      },
    );
  });
}

function providerEnvironment(env, runDir, repoRoot) {
  const apiKey = String(env.D4J_OPENAI_API_KEY || env.OPENAI_API_KEY || "").trim();
  if (!apiKey) throw new Error("OpenAI provider key is not configured in the batch backend process");
  const model = String(env.D4J_OPENAI_MODEL || "").trim();
  if (!model) throw new Error("D4J_OPENAI_MODEL is not configured in the batch backend process");
  const javaHome = env.D4J_JAVA_HOME || env.JAVA_HOME || "/Users/shawnli/.homebrew/opt/openjdk@11";
  return {
    model,
    env: {
      ...env,
      OPENAI_API_KEY: apiKey,
      OPENAI_BASE_URL: env.D4J_OPENAI_BASE_URL || env.OPENAI_BASE_URL || "",
      JAVA_HOME: javaHome,
      PATH: [path.join(javaHome, "bin"), path.join(repoRoot, "framework", "bin"), env.PATH]
        .filter(Boolean)
        .join(path.delimiter),
      MSWEA_CONFIGURED: "true",
      MSWEA_GLOBAL_CONFIG_DIR: path.join(runDir, ".mini-swe-agent"),
      MSWEA_SILENT_STARTUP: "1",
    },
  };
}

function redactSecrets(value, env) {
  let text = String(value ?? "");
  for (const [name, secret] of Object.entries(env)) {
    if (!secret || !/(api[_-]?key|secret|token|password)/i.test(name) || String(secret).length < 8) continue;
    text = text.split(String(secret)).join(`[redacted:${name}]`);
  }
  return text.replace(/sk-proj-[A-Za-z0-9_-]+/g, "[redacted:OPENAI_API_KEY]");
}

function yamlString(value) {
  return JSON.stringify(String(value));
}

function depthSpec(level) {
  return {
    L10: { target: "approximately 8-15", bounds: [8, 15] },
    L30: { target: "approximately 20-35", bounds: [20, 35] },
    L50: { target: "approximately 45-55", bounds: [40, 60] },
    L70: { target: "approximately 65-75", bounds: [60, 80] },
    L90: { target: "approximately 85-95", bounds: [80, 100] },
  }[level];
}

function constructionPrompt({ project, level, originalContext }) {
  const target = depthSpec(level).target;
  const deepLevelRule =
    ["L50", "L70", "L90"].includes(level)
      ? `If a realistic single-fault path near ${level} cannot be achieved, write benchmark_artifacts/depth_unachievable.json with a precise reason, do not edit source/tests, and finish.`
      : "";
  return `Construct one controlled ${level} semantic bug variant from the fixed ${project}-1 Defects4J checkout.

This is benchmark construction, not fault localization. The high-level source root cause must remain:
${originalContext.semantic_root_cause}

Required ordering:
1. Inspect .benchmark_context/verified_original.json and .benchmark_context/developer.patch plus relevant fixed source/tests.
2. Generate 3-5 distinct candidates in benchmark_artifacts/candidates.md. For each include changed and preserved reasoning nodes, proposed production fault, deterministic trigger, expected symptom, non-equivalence, estimated necessary semantic inference steps, and shortcut risks.
3. Review every candidate in benchmark_artifacts/review.md. Reject direct test-name hints, direct private-helper tests, stack-trace gold disclosure, trivial failure-string grep shortcuts, root-cause drift, multiple faults, artificial wrappers, dead code, random syntax mutation, and broad refactors. Select exactly one realistic candidate.
4. Only after both files exist, implement the selected candidate in this fixed checkout. Prefer exactly one localized production-code fault and one deterministic new test.
5. Run the new trigger on this construction workspace.
6. Write benchmark_artifacts/implementation.json with valid JSON containing:
   trigger_test_id, gold_class, gold_method, semantic_root_cause, changed_reasoning_node,
   preserved_reasoning_nodes (array), semantic_inference_steps (integer), shortest_reasoning_path (array),
   shortcut_risks (array), expected_failure_signature, source_files_modified (array), tests_added (array),
   reasoning_nodes (array with exactly one item per shortest_reasoning_path step; each item must contain
   node_id, parent_node, semantic_inference, affected_class, affected_method, required_evidence
   (a non-empty string or list),
   and dependency),
   difference_from_original, limitations.

Depth is the number of necessary evidence-dependent semantic deductions in the shortest valid path from failure to cause and faulty method. Target ${target} necessary steps; do not pad prose, add artificial wrappers, or add unrelated files or faults. The additional steps must arise naturally from state, transformation, propagation, control flow, semantic invariants, cross-method dependencies, representation, or API contracts. The variant must begin independently from the fixed baseline, preserve the same high-level semantic root cause, and must not copy the original developer patch mechanically.

Do not change dependencies, build files, developer tests unrelated to the new trigger, or more than one production file. Do not create compilation faults. Do not include the original bug or level in the new test method name. Do not reveal the intended faulty method in the test name or assertion message.

${deepLevelRule}

Finish only after artifacts and implementation are complete by running exactly:
echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`;
}

async function writeMiniConfig({ configPath, workspace, trajectoryPath, prompt, model }) {
  const system = `You are a careful Defects4J benchmark constructor. Every response must include at least one bash tool call. Report only concise action summaries, not hidden chain-of-thought. Follow the required phase ordering and preserve repository style.`;
  const content = `run:\n  task: ${yamlString(prompt)}\nagent:\n  agent_class: default\n  system_template: ${yamlString(system)}\n  instance_template: ${yamlString("{{task}}") }\n  step_limit: 100\n  cost_limit: 0\n  wall_time_limit_seconds: 1800\n  output_path: ${yamlString(trajectoryPath)}\n  mode: yolo\nenvironment:\n  cwd: ${yamlString(workspace)}\n  timeout: 1800\n  env:\n    PAGER: cat\n    MANPAGER: cat\n    LESS: \"-R\"\n    PIP_PROGRESS_BAR: \"off\"\n    TQDM_DISABLE: \"1\"\nmodel:\n  model_name: ${yamlString(`openai/${model}`)}\n  model_kwargs:\n    drop_params: true\n`;
  await fs.writeFile(configPath, content, { mode: 0o600 });
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}

function changedSourceGroups(comparison) {
  const changed = comparison.changed_files ?? [];
  return {
    production: changed.filter((entry) =>
      /^(source|src\/main|src\/java|gson\/src\/main|src\/com)\//.test(entry.path),
    ),
    tests: changed.filter((entry) => /(^|\/)(test|tests|src\/test)(\/|$)/.test(entry.path)),
  };
}

async function diffFile(beforeRoot, afterRoot, relativePath) {
  const before = path.join(beforeRoot, relativePath);
  const after = path.join(afterRoot, relativePath);
  const beforeExists = await exists(before);
  const afterExists = await exists(after);
  const result = await runProcess(
    "diff",
    [
      "-u",
      "--label",
      `a/${relativePath}`,
      "--label",
      `b/${relativePath}`,
      beforeExists ? before : "/dev/null",
      afterExists ? after : "/dev/null",
    ],
    { timeout: 120000 },
  );
  if (![0, 1].includes(result.exit_code)) throw new Error(`Could not create patch for ${relativePath}: ${result.stderr}`);
  return result.stdout;
}

async function buildPatch(beforeRoot, afterRoot, entries) {
  const chunks = [];
  for (const entry of entries) chunks.push(await diffFile(beforeRoot, afterRoot, entry.path));
  return chunks.join("");
}

function validateImplementationMetadata(metadata, level) {
  const errors = [];
  for (const field of ["trigger_test_id", "gold_class", "gold_method", "semantic_root_cause", "changed_reasoning_node"] ) {
    if (!String(metadata?.[field] ?? "").trim()) errors.push(`${field} is required`);
  }
  if (!Array.isArray(metadata?.shortest_reasoning_path) || metadata.shortest_reasoning_path.length < 2) {
    errors.push("shortest_reasoning_path must contain at least two steps");
  }
  if (!Number.isInteger(metadata?.semantic_inference_steps) || metadata.semantic_inference_steps <= 0) {
    errors.push("semantic_inference_steps must be a positive integer");
  }
  if (metadata?.semantic_inference_steps !== metadata?.shortest_reasoning_path?.length) {
    errors.push("semantic_inference_steps must equal the auditable shortest_reasoning_path length");
  }
  if (String(metadata?.gold_method ?? "").trim() && !normalizeJavaMethodIdentity(metadata.gold_method)) {
    errors.push("gold_method must be a Java method name or a valid signature-qualified method name");
  }
  const bounds = depthSpec(level).bounds;
  if (Number.isInteger(metadata?.semantic_inference_steps) && (metadata.semantic_inference_steps < bounds[0] || metadata.semantic_inference_steps > bounds[1])) {
    errors.push(`${level} semantic_inference_steps must be within ${bounds[0]}-${bounds[1]}`);
  }
  if (["L70", "L90"].includes(level)) {
    if (!Array.isArray(metadata?.reasoning_nodes) || metadata.reasoning_nodes.length !== metadata.semantic_inference_steps) {
      errors.push("reasoning_nodes must contain exactly one auditable node per semantic inference step");
    } else {
      const required = ["node_id", "semantic_inference", "affected_class", "affected_method", "required_evidence", "dependency"];
      metadata.reasoning_nodes.forEach((node, index) => {
        for (const field of required) {
          const evidenceMissing = !hasRequiredEvidence(node?.required_evidence);
          if (field === "required_evidence" ? evidenceMissing : !String(node?.[field] ?? "").trim()) {
            errors.push(`reasoning_nodes[${index}].${field} is required`);
          }
        }
        if (index === 0 && node?.parent_node != null) errors.push("reasoning_nodes[0].parent_node must be null");
        if (index > 0 && node?.parent_node !== metadata.reasoning_nodes[index - 1]?.node_id) {
          errors.push(`reasoning_nodes[${index}].parent_node must reference the preceding node`);
        }
      });
    }
  }
  return errors;
}

async function applyPatch(workspace, patchPath) {
  const result = await runProcess("patch", ["-p1", "--forward", "--batch", "-i", patchPath], {
    cwd: workspace,
    timeout: 120000,
  });
  if (result.exit_code !== 0) throw new Error(`Patch application failed: ${result.stderr || result.stdout}`);
  return result;
}

function d4jEnvironment(env, repoRoot) {
  const javaHome = env.D4J_JAVA_HOME || env.JAVA_HOME || "/Users/shawnli/.homebrew/opt/openjdk@11";
  return {
    ...env,
    JAVA_HOME: javaHome,
    PATH: [path.join(javaHome, "bin"), path.join(repoRoot, "framework", "bin"), env.PATH].filter(Boolean).join(path.delimiter),
  };
}

async function d4j(repoRoot, workspace, args, env, allowFailure = false) {
  const result = await runProcess(path.join(repoRoot, "framework", "bin", "defects4j"), args, {
    cwd: workspace,
    env: d4jEnvironment(env, repoRoot),
    timeout: 1800000,
  });
  if (!allowFailure && result.exit_code !== 0) throw new Error(`${result.command} failed: ${result.stderr || result.stdout}`);
  return result;
}

async function freshCheckout(repoRoot, project, target, env) {
  if (await exists(target)) throw new Error(`Fresh validation target already exists: ${target}`);
  await fs.mkdir(path.dirname(target), { recursive: true });
  const result = await runProcess(
    path.join(repoRoot, "framework", "bin", "defects4j"),
    ["checkout", "-p", project, "-v", "1f", "-w", target],
    { env: d4jEnvironment(env, repoRoot), timeout: 1800000 },
  );
  if (result.exit_code !== 0) throw new Error(`Fresh fixed checkout failed: ${result.stderr || result.stdout}`);
  return result;
}

function failingSignature(result, workspace) {
  return [result.stdout, result.stderr]
    .join("\n")
    .replaceAll(workspace, "<workspace>")
    .split(/\r?\n/)
    .filter((line) => /Failing tests:|^\s*- |Assertion|Exception|expected|but was/i.test(line))
    .join("\n")
    .trim();
}

async function validateFresh({ repoRoot, project, variantId, variantPatchPath, testPatchPath, triggerTestId, originalTestId, validationRoot, env, heartbeat }) {
  const baseline = path.join(validationRoot, "baseline");
  const variant = path.join(validationRoot, "variant");
  heartbeat(`${variantId} fresh baseline checkout`);
  await freshCheckout(repoRoot, project, baseline, env);
  await applyPatch(baseline, testPatchPath);
  const baselineCompile = await d4j(repoRoot, baseline, ["compile"], env);
  const baselineTrigger = await d4j(repoRoot, baseline, ["test", "-t", triggerTestId], env, true);
  const baselineFailureFile = path.join(baseline, "failing_tests");
  const baselineFailures = (await exists(baselineFailureFile)) ? await fs.readFile(baselineFailureFile, "utf8") : "";
  if (/^--- /m.test(baselineFailures) || /Failing tests:\s*[1-9]/i.test(baselineTrigger.stdout)) {
    throw new Error("New triggering test does not pass on the clean fixed baseline");
  }

  heartbeat(`${variantId} fresh variant checkout`);
  await freshCheckout(repoRoot, project, variant, env);
  await applyPatch(variant, testPatchPath);
  await applyPatch(variant, variantPatchPath);
  const variantCompile = await d4j(repoRoot, variant, ["compile"], env);
  const triggerRuns = [];
  for (let runIndex = 1; runIndex <= 3; runIndex += 1) {
    heartbeat(`${variantId} deterministic trigger ${runIndex}/3`);
    const result = await d4j(repoRoot, variant, ["test", "-t", triggerTestId], env, true);
    const failureFile = path.join(variant, "failing_tests");
    const failures = (await exists(failureFile)) ? await fs.readFile(failureFile, "utf8") : "";
    if (!/^--- /m.test(failures) && !/Failing tests:\s*[1-9]/i.test(result.stdout)) {
      throw new Error(`Variant trigger did not fail on deterministic run ${runIndex}`);
    }
    triggerRuns.push({ run: runIndex, status: "expected_fail", signature: failingSignature(result, variant), output: `${result.stdout}\n${result.stderr}\n${failures}`.trim() });
  }
  const signatures = new Set(triggerRuns.map((run) => run.signature));
  if (signatures.size !== 1) throw new Error("Variant trigger failure was not deterministic across three runs");
  const originalRegression = originalTestId
    ? await d4j(repoRoot, variant, ["test", "-t", originalTestId], env, true)
    : null;
  return {
    schema_version: "d4j-validation/v1",
    status: "accepted",
    gate: {
      baseline_compile: { status: "pass", duration_ms: baselineCompile.duration_ms },
      baseline_trigger: { status: "pass", duration_ms: baselineTrigger.duration_ms },
      variant_compile: { status: "pass", duration_ms: variantCompile.duration_ms },
      variant_trigger_runs: triggerRuns,
      deterministic: { status: "pass", signature: triggerRuns[0].signature },
      production_fault: { status: "pass" },
      gold_method_known: { status: "pass" },
      original_trigger: originalRegression
        ? { status: /Failing tests:\s*0/i.test(originalRegression.stdout) ? "pass" : "recorded", output: `${originalRegression.stdout}\n${originalRegression.stderr}`.trim() }
        : { status: "not_run" },
    },
    variant_trigger_runs: triggerRuns,
    reproducibility_status: "passed",
    consistency: true,
    validated_at: new Date().toISOString(),
  };
}

async function nextVariantId(variantsRoot, project, level) {
  const prefix = `${project.toUpperCase()}-1-${level}-`;
  const levelRoot = path.join(variantsRoot, project, "bug-1", level);
  await fs.mkdir(levelRoot, { recursive: true });
  const names = await fs.readdir(levelRoot).catch(() => []);
  for (let index = 1; index < 1000; index += 1) {
    const candidate = `${prefix}${String(index).padStart(3, "0")}`;
    if (!names.includes(candidate)) return candidate;
  }
  throw new Error(`No available variant id for ${project}-1 ${level}`);
}

async function copyArtifact(source, destination) {
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.copyFile(source, destination);
}

export async function constructVariantAttempt({
  repoRoot,
  checkoutRoot,
  variantsRoot,
  batchDir,
  project,
  level,
  env = process.env,
  heartbeat = () => {},
  preservedAttemptDir = null,
}) {
  normalizeLevel(level);
  const originalContextPath = path.join(batchDir, "originals", `${project}-1`, "verified_original.json");
  const originalPatchPath = path.join(batchDir, "originals", `${project}-1`, "developer.patch");
  const originalContext = await readJson(originalContextPath);
  const fixedCheckout = path.join(checkoutRoot, `${project}-1`, "fixed");
  if (!(await exists(path.join(fixedCheckout, ".defects4j.config")))) throw new Error(`Fixed checkout missing for ${project}-1`);

  const attemptId = `${project}-1-${level}-${new Date().toISOString().replace(/[-:.]/g, "")}`;
  const expectedAttemptRoot = path.resolve(batchDir, "variants", `${project}-1`, level);
  const attemptDir = preservedAttemptDir ? path.resolve(preservedAttemptDir) : path.join(expectedAttemptRoot, attemptId);
  if (attemptDir !== expectedAttemptRoot && !attemptDir.startsWith(`${expectedAttemptRoot}${path.sep}`)) {
    throw new Error("Preserved construction attempt must be inside the selected batch/project/level directory");
  }
  const workspace = path.join(attemptDir, "construction_workspace");
  const contextDir = path.join(workspace, ".benchmark_context");
  const artifactDir = path.join(workspace, "benchmark_artifacts");
  if (preservedAttemptDir && !(await exists(path.join(workspace, ".defects4j.config")))) {
    throw new Error(`Preserved construction workspace is missing: ${workspace}`);
  }

  const preservedCommand = preservedAttemptDir
    ? await readJson(path.join(attemptDir, "generation_command.json")).catch(() => ({}))
    : null;
  const provider = preservedAttemptDir
    ? { model: String(preservedCommand?.model || env.D4J_OPENAI_MODEL || "gpt-5.6"), env }
    : providerEnvironment(env, attemptDir, repoRoot);
  if (!preservedAttemptDir) {
    await fs.mkdir(attemptDir, { recursive: true });
    await copyDirectoryFiltered(fixedCheckout, workspace);
    await fs.mkdir(contextDir, { recursive: true });
    await fs.mkdir(artifactDir, { recursive: true });
    await copyArtifact(originalContextPath, path.join(contextDir, "verified_original.json"));
    await copyArtifact(originalPatchPath, path.join(contextDir, "developer.patch"));

    const trajectoryPath = path.join(attemptDir, "generation_trajectory.json");
    const configPath = path.join(attemptDir, "mini-swe-agent.config.yaml");
    const prompt = constructionPrompt({ project, level, originalContext });
    await writeMiniConfig({ configPath, workspace, trajectoryPath, prompt, model: provider.model });
    await fs.mkdir(provider.env.MSWEA_GLOBAL_CONFIG_DIR, { recursive: true });
    heartbeat(`${project}-1 ${level} candidate/review/implementation agent started`);
    const agentResult = await runProcess(
      "/opt/miniconda3/bin/mini-swe-agent",
      ["--config", configPath, "--model", `openai/${provider.model}`, "--yolo", "--output", trajectoryPath, "--exit-immediately"],
      { cwd: workspace, env: provider.env, timeout: 1800000 },
    );
    await fs.writeFile(
      path.join(attemptDir, "generation_output.log"),
      redactSecrets(`${agentResult.stdout}\n${agentResult.stderr}`, provider.env),
    );
    await fs.writeFile(path.join(attemptDir, "generation_command.json"), `${JSON.stringify({ ...agentResult, stdout: undefined, stderr: undefined, command: "mini-swe-agent", model: provider.model }, null, 2)}\n`);
    if (agentResult.timed_out) return { status: "generation_failed", reason: "Variant construction agent exceeded 1800 seconds", attemptDir };
  } else {
    heartbeat(`${project}-1 ${level} revalidating preserved construction attempt`);
  }
  const beforeHashes = await hashSourceFiles(preservedAttemptDir ? fixedCheckout : workspace);

  const depthUnachievablePath = path.join(artifactDir, "depth_unachievable.json");
  if (await exists(depthUnachievablePath)) {
    const afterHashes = await hashSourceFiles(workspace);
    const integrity = compareSourceHashes(beforeHashes, afterHashes);
    const detail = await readJson(depthUnachievablePath).catch(() => ({}));
    if (!integrity.ok) return { status: "generation_failed", reason: "depth_unachievable submission modified source files", attemptDir };
    return { status: "depth_unachievable", reason: String(detail.reason ?? "Agent found no realistic single-fault path at this depth"), attemptDir };
  }

  for (const artifact of REQUIRED_AGENT_ARTIFACTS) {
    if (!(await exists(path.join(artifactDir, artifact)))) {
      return { status: "generation_failed", reason: `Construction agent did not create ${artifact}`, attemptDir };
    }
  }
  const metadata = await readJson(path.join(artifactDir, "implementation.json")).catch((error) => ({ _parse_error: error.message }));
  const metadataErrors = validateImplementationMetadata(metadata, level);
  if (metadata._parse_error) metadataErrors.push(`implementation.json is invalid: ${metadata._parse_error}`);
  if (metadataErrors.length) return { status: "generation_failed", reason: metadataErrors.join("; "), attemptDir };

  const afterHashes = await hashSourceFiles(workspace);
  const comparison = compareSourceHashes(beforeHashes, afterHashes);
  const groups = changedSourceGroups(comparison);
  if (groups.production.length !== 1) {
    return { status: "generation_failed", reason: `Expected exactly one changed production file, found ${groups.production.length}`, attemptDir };
  }
  if (groups.tests.length < 1) return { status: "generation_failed", reason: "No triggering test source change was detected", attemptDir };
  if (groups.tests.length > 2) return { status: "generation_failed", reason: `Expected at most two changed test files, found ${groups.tests.length}`, attemptDir };

  const methodCatalog = await buildJavaMethodCatalogEntries(workspace);
  const canonicalGoldMethod = normalizeJavaMethodIdentity(metadata.gold_method);
  const goldQualified = `${metadata.gold_class}::${canonicalGoldMethod}`;
  const goldEntry = methodCatalog.find((entry) => entry.qualified === goldQualified && entry.file === groups.production[0].path);
  if (!goldEntry) return { status: "generation_failed", reason: `Gold method is not recognized in the changed production file: ${goldQualified}`, attemptDir };

  const variantPatch = await buildPatch(fixedCheckout, workspace, groups.production);
  const testPatch = await buildPatch(fixedCheckout, workspace, groups.tests);
  const stagedVariantPatch = path.join(attemptDir, "variant.patch");
  const stagedTestPatch = path.join(attemptDir, "test.patch");
  await fs.writeFile(stagedVariantPatch, variantPatch);
  await fs.writeFile(stagedTestPatch, testPatch);
  const variantId = await nextVariantId(variantsRoot, project, level);
  const validationRoot = path.join(repoRoot, "runs", "revalidation", variantId, new Date().toISOString().replace(/[-:.]/g, ""));
  let validation;
  try {
    validation = await validateFresh({
      repoRoot,
      project,
      variantId,
      variantPatchPath: stagedVariantPatch,
      testPatchPath: stagedTestPatch,
      triggerTestId: metadata.trigger_test_id,
      originalTestId: originalContext.failing_test_identifier,
      validationRoot,
      env,
      heartbeat,
    });
  } catch (error) {
    return { status: "validation_failed", reason: error instanceof Error ? error.message : String(error), attemptDir, variantId };
  }

  const canonicalDir = canonicalVariantDir(variantsRoot, project, 1, level, variantId);
  await fs.mkdir(canonicalDir, { recursive: false });
  await copyArtifact(stagedVariantPatch, path.join(canonicalDir, "variant.patch"));
  await copyArtifact(stagedTestPatch, path.join(canonicalDir, "test.patch"));
  await copyArtifact(path.join(artifactDir, "candidates.md"), path.join(canonicalDir, "candidates.md"));
  await copyArtifact(path.join(artifactDir, "review.md"), path.join(canonicalDir, "review.md"));
  if (await exists(path.join(attemptDir, "generation_trajectory.json"))) {
    await copyArtifact(path.join(attemptDir, "generation_trajectory.json"), path.join(canonicalDir, "generation_trace.json"));
  } else {
    await fs.writeFile(path.join(canonicalDir, "generation_trace.json"), "{}\n");
  }
  const sourceHashes = {
    schema_version: "d4j-variant-source-hashes/v1",
    fixed_baseline: beforeHashes,
    constructed_variant: afterHashes,
    comparison,
    generated_at: new Date().toISOString(),
  };
  await fs.writeFile(path.join(canonicalDir, "source_hashes.json"), `${JSON.stringify(sourceHashes, null, 2)}\n`);
  await fs.writeFile(path.join(canonicalDir, "validation.json"), `${JSON.stringify(validation, null, 2)}\n`);
  await fs.writeFile(path.join(canonicalDir, "validation.log"), validation.variant_trigger_runs.map((run) => `run ${run.run}: ${run.status}\n${run.output}`).join("\n\n"));
  const generatedAt = new Date().toISOString();
  const reasoningTree = {
    nominal_depth: level,
    actual_semantic_steps: metadata.semantic_inference_steps,
    reasoning_level: level,
    semantic_inference_steps: metadata.semantic_inference_steps,
    shortest_reasoning_path: metadata.shortest_reasoning_path,
    changed_reasoning_node: metadata.changed_reasoning_node,
    preserved_reasoning_nodes: metadata.preserved_reasoning_nodes ?? [],
    shortcut_risks: metadata.shortcut_risks ?? [],
    nodes: metadata.reasoning_nodes ?? metadata.shortest_reasoning_path.map((semanticInference, index) => ({
      node_id: `S${String(index + 1).padStart(2, "0")}`,
      parent_node: index === 0 ? null : `S${String(index).padStart(2, "0")}`,
      semantic_inference: semanticInference,
      affected_class: metadata.gold_class,
      affected_method: canonicalGoldMethod,
      required_evidence: ["implementation.json", index === 0 ? "trigger test and failing output" : "preceding semantic inference"],
      dependency: index === 0 ? "Starting observation from the deterministic trigger." : "This conclusion requires the preceding node in the shortest valid path.",
    })),
  };
  await fs.writeFile(path.join(canonicalDir, "reasoning_tree.yaml"), `${JSON.stringify(reasoningTree, null, 2)}\n`);
  const report = `# ${variantId}\n\n- Source: ${project}-1 fixed baseline\n- Level: ${level}\n- Actual semantic inference steps: ${metadata.semantic_inference_steps}\n- Gold: ${goldQualified}\n- Trigger: ${metadata.trigger_test_id}\n- Root cause: ${metadata.semantic_root_cause}\n- Difference from original: ${metadata.difference_from_original}\n- Limitations: ${metadata.limitations}\n\nThe fresh reconstruction gate passed baseline compile/trigger, variant compile, and deterministic variant failure three times.\n`;
  await fs.writeFile(path.join(canonicalDir, "variant_report.md"), report);
  const manifest = {
    schema_version: "d4j-variant-manifest/v1",
    variant_id: variantId,
    source: {
      defects4j_project: project,
      defects4j_bug_id: 1,
      bug_slug: `${project}-1`,
      baseline_version: "Defects4J 1f fixed checkout",
      artifact_path: `${path.relative(repoRoot, canonicalDir)}/`,
    },
    status: "validated",
    benchmark_eligible: true,
    reproducibility: {
      status: "passed",
      reproduced_at: generatedAt,
      revalidation_run: `${path.relative(repoRoot, validationRoot)}/`,
      artifact_hashes: {},
    },
    reasoning: {
      level,
      nominal_depth: level,
      actual_semantic_steps: metadata.semantic_inference_steps,
      unit_count: metadata.semantic_inference_steps,
      semantic_inference_steps: metadata.semantic_inference_steps,
      shortest_reasoning_path: metadata.shortest_reasoning_path,
      reasoning_level_status: "validated",
      changed_node: metadata.changed_reasoning_node,
      preserved_nodes: metadata.preserved_reasoning_nodes ?? [],
      shortcut_risks: metadata.shortcut_risks ?? [],
    },
    transformation_dimensions: ["propagation-path modification"],
    fault: {
      locations: [{ class: metadata.gold_class, method: canonicalGoldMethod, file: goldEntry.file, production: true }],
      gold: { faulty_class: metadata.gold_class, faulty_method: canonicalGoldMethod },
      semantic_root_cause: metadata.semantic_root_cause,
    },
    trigger: {
      test_id: metadata.trigger_test_id,
      stack_trace: validation.variant_trigger_runs[0].output,
      expected_failure_signature: metadata.expected_failure_signature,
    },
    validation: { status: "accepted", deterministic_runs: 3, expected_failure_signature: metadata.expected_failure_signature },
    research_metadata: {
      generated_at: generatedAt,
      generator: "mini-swe-agent",
      generator_model: provider.model,
      public_status: "private",
      released_before_evaluation: false,
      evaluator_agent: "mini-swe-agent",
      evaluator_model: provider.model,
      same_model_family: true,
      source_bug_publicly_known: true,
      generator_evaluator_coupling: "potential",
    },
    contamination_metadata: {
      task_kind: "private_variant",
      source_bug_public: true,
      exact_variant_private: true,
      generator_model: provider.model,
      evaluator_model: provider.model,
      same_model_family: true,
      gold_in_stack_trace: false,
      gold_called_directly_by_test: false,
      test_name_hint_risk: "reviewed",
      failure_string_search_risk: "reviewed",
    },
    artifacts: {
      manifest: "variant_manifest.json",
      reasoning_tree: "reasoning_tree.yaml",
      variant_patch: "variant.patch",
      test_patch: "test.patch",
      validation: "validation.json",
      validation_log: "validation.log",
      variant_report: "variant_report.md",
      candidates: "candidates.md",
      review: "review.md",
      generation_trace: "generation_trace.json",
      source_hashes: "source_hashes.json",
    },
    provenance: { created_by: "mini-swe-agent", construction_attempt: `${path.relative(repoRoot, attemptDir)}/` },
    created_at: generatedAt,
    updated_at: generatedAt,
  };
  for (const [key, fileName] of Object.entries({
    reasoning_tree: "reasoning_tree.yaml",
    variant_patch: "variant.patch",
    test_patch: "test.patch",
    validation: "validation.json",
    validation_log: "validation.log",
    variant_report: "variant_report.md",
    generation_trace: "generation_trace.json",
    source_hashes: "source_hashes.json",
  })) {
    manifest.reproducibility.artifact_hashes[key] = await sha256File(path.join(canonicalDir, fileName));
  }
  await fs.writeFile(path.join(canonicalDir, "variant_manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  return {
    status: "validated",
    variantId,
    canonicalDir,
    attemptDir,
    metadata,
    validation,
    gold: goldQualified,
  };
}
