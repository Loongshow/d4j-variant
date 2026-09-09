import crypto from "node:crypto";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const PROMPT_VERSION = "d4j-localization-only/v2";

export const LOCALIZATION_SYSTEM_PROMPT = `You are performing repository-level method fault localization.

You are given a buggy software repository and a failing test case.

Your goal is NOT to repair the bug.

Your goal is to identify the production methods most likely to require
modification in order to fix the observed failure.

You are initially given:
- failing test identifier;
- failing test source;
- failure stack trace.

You have access to the complete buggy repository.

You may:
- search the repository;
- inspect source and tests;
- follow callers and callees;
- inspect class relationships;
- run the associated failing test case(s).

You must NOT:
- modify production source;
- modify test source;
- access the fixed revision;
- access Git history/fix commits;
- access benchmark gold labels;
- access reasoning trees;
- access variant patches or generation reports.

Investigate before answering.

Return exactly ten UNIQUE production methods ranked from most likely to least
likely responsible for the failure.

After investigation, submit your final ranking using the
submit_fault_localization tool. The tool payload must be:

{
  "predictions": [
    { "class": "fully.qualified.ClassName", "method": "methodName" }
  ]
}

The predictions array must contain exactly ten ranked production methods in
order from most likely to least likely responsible for the failure.

You may also include an optional evidence_chain containing concise statements
of evidence you observed, the inference supported by that evidence, and any
candidate-method update. Keep these summaries brief and auditable. Do not
provide hidden chain-of-thought or private internal reasoning.

Do not propose a patch. Do not finish with a plain-text final answer.`;

const ignoredDirectories = new Set([
  ".git",
  ".svn",
  ".hg",
  ".gradle",
  ".idea",
  ".settings",
  "node_modules",
  "target",
  "build",
  "dist",
  "out",
]);

const privateMetadataNames = new Set([
  ".git",
  ".svn",
  ".hg",
  "variant.patch",
  "test.patch",
  "reasoning_tree.yaml",
  "variant_report.md",
  "validation.json",
  "validation.log",
  "agent1_report.md",
  "candidates.md",
  "review.md",
  "generation_trace.json",
  "variant_manifest.json",
  "gold.json",
  "gold_methods.json",
  "evaluation.json",
  "ranking.json",
  "run_manifest.json",
  "reasoning_workflow.json",
  "pilot_summary.json",
  "pilot_audit.json",
  "original_vs_variant_comparison.json",
]);

const sourceExtensions = new Set([".java", ".xml", ".properties", ".gradle"]);

export class AgentAdapter {
  async prepareRun() {
    throw new Error("prepareRun() is not implemented");
  }

  async execute() {
    throw new Error("execute() is not implemented");
  }

  parseResult() {
    throw new Error("parseResult() is not implemented");
  }

  async collectTrajectory() {
    throw new Error("collectTrajectory() is not implemented");
  }

  async cleanup() {}
}

export function sha256Text(value) {
  return crypto.createHash("sha256").update(String(value)).digest("hex");
}

export function renderLocalizationPrompt(task) {
  const failingTestSource = task.failing_test_source ? String(task.failing_test_source).trim() : "(not provided)";
  const stackTrace = task.stack_trace ? String(task.stack_trace).trim() : "(not provided)";
  const allowedCommand = task.allowed_test_command ? String(task.allowed_test_command).trim() : "(not provided)";
  const repoPath = task.read_only_buggy_repository_path ? String(task.read_only_buggy_repository_path).trim() : "(not provided)";
  return `${LOCALIZATION_SYSTEM_PROMPT}

Task metadata:
- failing test identifier: ${task.failing_test_identifier || "(not provided)"}
- repository path: ${repoPath}
- allowed test command: ${allowedCommand}

Failing test source:
\`\`\`
${failingTestSource}
\`\`\`

Failure stack trace:
\`\`\`
${stackTrace}
\`\`\`

Use the repository path above as your working directory. When you have the
ten-method ranking, call submit_fault_localization with exactly ten production
Class::method predictions.`;
}

export function promptMetadata(renderedPrompt) {
  return {
    version: PROMPT_VERSION,
    base_prompt_sha256: sha256Text(LOCALIZATION_SYSTEM_PROMPT),
    rendered_prompt_sha256: sha256Text(renderedPrompt),
  };
}

export async function writePromptArtifact(runDir, task) {
  const rendered = renderLocalizationPrompt(task);
  const metadata = promptMetadata(rendered);
  await fs.writeFile(path.join(runDir, "prompt.txt"), rendered);
  await fs.writeFile(path.join(runDir, "prompt.json"), `${JSON.stringify(metadata, null, 2)}\n`);
  return { rendered, metadata };
}

export function safeResolveWithin(root, requestedPath = "") {
  const relativePath = String(requestedPath);
  if (!relativePath || path.isAbsolute(relativePath) || relativePath.includes("\0")) {
    throw new Error("Invalid file path");
  }
  const target = path.resolve(root, relativePath);
  const rootWithSep = root.endsWith(path.sep) ? root : `${root}${path.sep}`;
  if (target !== root && !target.startsWith(rootWithSep)) {
    throw new Error("Rejected path traversal attempt");
  }
  return target;
}

function classifyForbiddenEntry(rel, entry, root) {
  const normalized = rel.split(path.sep).join("/");
  const name = path.basename(normalized);
  const result = {
    forbidden: false,
    category: "",
    reason: "",
  };

  if ([".git", ".svn", ".hg"].includes(name)) {
    return { forbidden: true, category: "git_history_leak", reason: "VCS history directory or file" };
  }
  if (name.endsWith(".orig") || name.endsWith(".rej") || name.endsWith(".bak")) {
    return { forbidden: true, category: "patch_backup_leak", reason: "Patch backup or reject artifact" };
  }
  if (name.endsWith(".patch")) {
    return { forbidden: true, category: "unexpected_artifact_leak", reason: "Patch implementation artifact" };
  }
  if (privateMetadataNames.has(name)) {
    return { forbidden: true, category: "private_benchmark_metadata_leak", reason: "Private benchmark metadata" };
  }
  if (/^gold[-_]?.*\.json$/i.test(name) || /^evaluation[-_]?.*\.json$/i.test(name)) {
    return { forbidden: true, category: "private_benchmark_metadata_leak", reason: "Private gold/evaluation metadata" };
  }
  if (entry?.isSymbolicLink?.()) {
    try {
      const target = fsSync.realpathSync(path.join(root, rel));
      const rootReal = fsSync.realpathSync(root);
      const rootWithSep = rootReal.endsWith(path.sep) ? rootReal : `${rootReal}${path.sep}`;
      if (target !== rootReal && !target.startsWith(rootWithSep)) {
        const category = /(?:^|\/)(fixed|new_bug_variants|benchmark_runs|runs)(?:\/|$)/.test(target)
          ? "fixed_revision_leak"
          : "unexpected_artifact_leak";
        return { forbidden: true, category, reason: "Symlink escapes the agent workspace" };
      }
    } catch {
      return { forbidden: true, category: "unexpected_artifact_leak", reason: "Unreadable symlink" };
    }
  }
  return result;
}

function isPrivateMetadataName(name) {
  return Boolean(classifyForbiddenEntry(name, null, process.cwd()).forbidden);
}

function shouldExcludeFromWorkspace(src, sourceRoot) {
  const relative = path.relative(sourceRoot, src);
  if (!relative) return false;
  const parts = relative.split(path.sep);
  return parts.some((part) => ignoredDirectories.has(part) || isPrivateMetadataName(part));
}

export async function copyDirectoryFiltered(sourceRoot, destinationRoot) {
  await fs.cp(sourceRoot, destinationRoot, {
    recursive: true,
    dereference: false,
    errorOnExist: false,
    force: true,
    filter: (src) => !shouldExcludeFromWorkspace(src, sourceRoot),
  });
}

export async function stripHistoryDirs(root) {
  const entries = await fs.readdir(root, { withFileTypes: true }).catch(() => []);
  await Promise.all(
    entries.map(async (entry) => {
      const current = path.join(root, entry.name);
      if (entry.isDirectory() && (entry.name === ".git" || entry.name === ".svn")) {
        await fs.rm(current, { recursive: true, force: true });
        return;
      }
      if (entry.isDirectory() && !ignoredDirectories.has(entry.name)) {
        await stripHistoryDirs(current);
      }
    }),
  );
}

export async function scanPrivateMetadata(root) {
  const hits = [];
  const leaks = [];
  const categories = {
    git_history_leak: false,
    patch_backup_leak: false,
    private_benchmark_metadata_leak: false,
    fixed_revision_leak: false,
    unexpected_artifact_leak: false,
  };
  async function walk(current, relative = "") {
    const entries = await fs.readdir(current, { withFileTypes: true }).catch(() => []);
    for (const entry of entries) {
      const rel = path.join(relative, entry.name).split(path.sep).join("/");
      const abs = path.join(current, entry.name);
      const classification = classifyForbiddenEntry(rel, entry, root);
      if (classification.forbidden) {
        hits.push(rel);
        categories[classification.category] = true;
        leaks.push({
          path: rel,
          category: classification.category,
          reason: classification.reason,
        });
      }
      if (entry.isDirectory() && !ignoredDirectories.has(entry.name)) {
        await walk(abs, rel);
      }
    }
  }
  await walk(root);
  return {
    ok: hits.length === 0,
    ...categories,
    banned_entries: hits.sort(),
    leaks: leaks.sort((a, b) => a.path.localeCompare(b.path)),
    checked_at: new Date().toISOString(),
  };
}

export async function sanitizeAgentWorkspace(root) {
  const removed = [];
  async function walk(current, relative = "") {
    const entries = await fs.readdir(current, { withFileTypes: true }).catch(() => []);
    for (const entry of entries) {
      const rel = path.join(relative, entry.name).split(path.sep).join("/");
      const abs = path.join(current, entry.name);
      const classification = classifyForbiddenEntry(rel, entry, root);
      if (classification.forbidden) {
        await fs.rm(abs, { recursive: true, force: true });
        removed.push({
          path: rel,
          category: classification.category,
          reason: classification.reason,
        });
        continue;
      }
      if (entry.isDirectory() && !ignoredDirectories.has(entry.name)) {
        await walk(abs, rel);
      }
    }
  }
  await walk(root);
  return {
    removed_entries: removed.sort((a, b) => a.path.localeCompare(b.path)),
    removed_count: removed.length,
    sanitized_at: new Date().toISOString(),
  };
}

function isSourceFile(relativePath) {
  const normalized = relativePath.split(path.sep).join("/");
  const ext = path.extname(normalized);
  if (path.basename(normalized) === "pom.xml" || path.basename(normalized) === "build.xml") return false;
  if (!sourceExtensions.has(ext)) return false;
  return /(^|\/)(source|src|tests?|test)\//.test(normalized);
}

export async function walkSourceFiles(root) {
  const files = [];
  async function walk(current, relative = "") {
    const entries = await fs.readdir(current, { withFileTypes: true }).catch(() => []);
    for (const entry of entries) {
      const rel = path.join(relative, entry.name);
      const abs = path.join(current, entry.name);
      if (entry.isDirectory()) {
        if (!ignoredDirectories.has(entry.name)) await walk(abs, rel);
        continue;
      }
      if (entry.isFile() && isSourceFile(rel)) {
        files.push(rel.split(path.sep).join("/"));
      }
    }
  }
  await walk(root);
  return files.sort();
}

export async function hashSourceFiles(root) {
  const files = await walkSourceFiles(root);
  const hashed = [];
  for (const file of files) {
    const abs = safeResolveWithin(root, file);
    const data = await fs.readFile(abs);
    hashed.push({
      path: file,
      sha256: crypto.createHash("sha256").update(data).digest("hex"),
      size: data.length,
    });
  }
  const aggregateInput = hashed.map((file) => `${file.path}:${file.sha256}`).join("\n");
  return {
    schema_version: "d4j-source-hashes/v1",
    file_count: hashed.length,
    aggregate_sha256: sha256Text(aggregateInput),
    files: hashed,
    generated_at: new Date().toISOString(),
  };
}

export function compareSourceHashes(before, after) {
  const beforeMap = new Map((before?.files ?? []).map((file) => [file.path, file]));
  const afterMap = new Map((after?.files ?? []).map((file) => [file.path, file]));
  const paths = Array.from(new Set([...beforeMap.keys(), ...afterMap.keys()])).sort();
  const changed_files = [];
  for (const filePath of paths) {
    const oldFile = beforeMap.get(filePath);
    const newFile = afterMap.get(filePath);
    if (!oldFile && newFile) {
      changed_files.push({ path: filePath, change: "added", before_sha256: null, after_sha256: newFile.sha256 });
    } else if (oldFile && !newFile) {
      changed_files.push({ path: filePath, change: "deleted", before_sha256: oldFile.sha256, after_sha256: null });
    } else if (oldFile && newFile && oldFile.sha256 !== newFile.sha256) {
      changed_files.push({
        path: filePath,
        change: "modified",
        before_sha256: oldFile.sha256,
        after_sha256: newFile.sha256,
      });
    }
  }
  return {
    ok: changed_files.length === 0,
    changed_files,
    before_file_count: before?.file_count ?? 0,
    after_file_count: after?.file_count ?? 0,
    checked_at: new Date().toISOString(),
  };
}

function relativeTarget(root, candidate) {
  if (!candidate) return "";
  const clean = candidate.replace(/^['"]|['"]$/g, "");
  const resolved = path.isAbsolute(clean) ? clean : path.resolve(root, clean);
  const rootWithSep = root.endsWith(path.sep) ? root : `${root}${path.sep}`;
  if (resolved === root || resolved.startsWith(rootWithSep)) {
    return path.relative(root, resolved).split(path.sep).join("/");
  }
  return clean;
}

function extractFileTarget(command, root) {
  const patterns = [
    /\b(?:cat|less|more)\s+([^\s|;&]+)/,
    /\bnl\s+-ba\s+([^\s|;&]+)/,
    /\bsed\s+-n\s+['"]?[^'"\s]+['"]?\s+([^\s|;&]+)/,
    /\b(?:head|tail)(?:\s+-n\s+\d+)?\s+([^\s|;&]+)/,
  ];
  for (const pattern of patterns) {
    const match = command.match(pattern);
    if (match?.[1]) return relativeTarget(root, match[1]);
  }
  return "";
}

function classifyCommand(command, root) {
  const value = String(command ?? "");
  if (/\bdefects4j\s+test\b|\bmvn\s+(?:-q\s+)?test\b|\bgradle\s+test\b/.test(value)) {
    return { type: "test_run", target: value };
  }
  if (/\b(rg|grep|find|fd|ag)\b/.test(value)) {
    return { type: "search", target: value };
  }
  const fileTarget = extractFileTarget(value, root);
  if (fileTarget) {
    return { type: "open_file", target: fileTarget };
  }
  return { type: "command", target: value };
}

function normalizeExistingEvent(event, index) {
  return {
    sequence: Number(event.sequence ?? index + 1),
    timestamp: event.timestamp ?? new Date().toISOString(),
    type: String(event.type ?? "other"),
    target: String(event.target ?? ""),
    metadata: event.metadata && typeof event.metadata === "object" ? event.metadata : {},
  };
}

export function normalizeTrajectoryEvents(raw, workspaceRoot = "") {
  if (!raw) return [];
  if (Array.isArray(raw) && raw.every((event) => event && typeof event === "object" && "type" in event)) {
    return raw.map(normalizeExistingEvent);
  }

  const payload =
    typeof raw === "string"
      ? raw
          .split(/\r?\n/)
          .map((line) => line.trim())
          .filter(Boolean)
          .map((line) => JSON.parse(line))
      : raw;
  const sourceEvents = Array.isArray(payload) ? payload : payload?.messages ?? [];
  const events = [];
  for (const message of sourceEvents) {
    const actions = message?.extra?.actions ?? [];
    for (const action of actions) {
      if (action?.tool === "submit_fault_localization") {
        events.push({
          sequence: events.length + 1,
          timestamp: message.timestamp ?? new Date().toISOString(),
          type: "submission",
          target: "submit_fault_localization",
          metadata: {
            role: message.role ?? "assistant",
            action_type: "submit_fault_localization",
            prediction_count: Array.isArray(action?.predictions) ? action.predictions.length : null,
          },
        });
        continue;
      }
      const command = action?.command ?? "";
      const classified = classifyCommand(command, workspaceRoot);
      events.push({
        sequence: events.length + 1,
        timestamp: message.timestamp ?? new Date().toISOString(),
        ...classified,
        metadata: {
          role: message.role ?? "assistant",
          action_type: action?.type ?? "bash",
        },
      });
    }
  }
  return events;
}

export function trajectoryJsonl(events) {
  return events.map((event) => JSON.stringify(event)).join("\n") + (events.length ? "\n" : "");
}

function productionSourceFile(relativePath) {
  const normalized = relativePath.split(path.sep).join("/");
  return /(^|\/)(source|src\/main|src\/java|src\/com)\//.test(normalized) && normalized.endsWith(".java");
}

async function firstExecutable(candidates) {
  for (const candidate of candidates.filter(Boolean)) {
    try {
      await fs.access(candidate);
      return candidate;
    } catch {
      // Try the next configured JDK.
    }
  }
  return "java";
}

async function buildCatalogWithJdkParser(root) {
  const java = await firstExecutable([
    process.env.D4J_JAVA_HOME && path.join(process.env.D4J_JAVA_HOME, "bin", "java"),
    process.env.JAVA_HOME && path.join(process.env.JAVA_HOME, "bin", "java"),
    "/Users/shawnli/.homebrew/opt/openjdk@11/bin/java",
    "/opt/homebrew/opt/openjdk@11/bin/java",
    "/usr/local/opt/openjdk@11/bin/java",
  ]);
  const helper = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "tools", "JavaMethodCatalog.java");
  return new Promise((resolve, reject) => {
    execFile(
      java,
      [helper, root],
      { timeout: 120000, maxBuffer: 50 * 1024 * 1024, env: process.env },
      (error, stdout = "", stderr = "") => {
        if (error) {
          reject(new Error(`JDK method catalog failed: ${error.message}${stderr ? `: ${stderr.trim()}` : ""}`));
          return;
        }
        try {
          const parsed = JSON.parse(stdout);
          resolve(Array.isArray(parsed.methods) ? parsed.methods : []);
        } catch (parseError) {
          reject(new Error(`JDK method catalog returned invalid JSON: ${parseError.message}`));
        }
      },
    );
  });
}

function stripJavaComments(source) {
  return String(source ?? "")
    .replace(/\/\*[\s\S]*?\*\//g, (match) => match.replace(/[^\n]/g, " "))
    .replace(/\/\/[^\n\r]*/g, "");
}

function classNameForJavaFile(relativePath, content) {
  const source = stripJavaComments(content);
  const packageName = source.match(/\bpackage\s+([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*;/)?.[1] ?? "";
  const fileClassName = path.basename(relativePath, ".java");
  const declarations = Array.from(
    source.matchAll(
      /(?:^|\n)\s*(?:(?:public|protected|private|abstract|final|static)\s+)*(?:class|interface|enum)\s+([A-Za-z_$][\w$]*)\b/g,
    ),
    (match) => match[1],
  );
  const className = declarations.find((name) => name === fileClassName) ?? declarations[0] ?? fileClassName;
  return packageName ? `${packageName}.${className}` : className;
}

function collectJavaMethodNames(source) {
  const names = [];
  const keywords = new Set(["if", "for", "while", "switch", "catch", "return", "new"]);
  const modifiers = new Set([
    "public",
    "protected",
    "private",
    "static",
    "final",
    "synchronized",
    "abstract",
    "native",
    "strictfp",
    "default",
  ]);
  let declaration = "";
  let collecting = false;

  for (const rawLine of String(source ?? "").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("@")) continue;
    if (!collecting && !/^(?:public|protected|private|static|final|synchronized|abstract|native|strictfp|default)\b/.test(line)) {
      continue;
    }

    declaration = collecting ? `${declaration} ${line}` : line;
    collecting = true;

    if (!declaration.includes("{")) {
      if (/[;=]$/.test(line) || declaration.includes(";") || declaration.includes("=")) {
        declaration = "";
        collecting = false;
      }
      continue;
    }

    const beforeBody = declaration.slice(0, declaration.indexOf("{")).replace(/\s+/g, " ").trim();
    declaration = "";
    collecting = false;
    if (!beforeBody.includes("(") || !beforeBody.includes(")")) continue;

    const openParen = beforeBody.indexOf("(");
    const prefix = beforeBody.slice(0, openParen).trim();
    const method = prefix.split(/\s+/).pop() ?? "";
    if (!/^[A-Za-z_$][\w$]*$/.test(method) || keywords.has(method)) continue;

    const tokens = prefix.split(/\s+/).filter(Boolean);
    const nonModifiers = tokens.filter((token) => !modifiers.has(token));
    if (nonModifiers.length < 2) continue;
    names.push(method);
  }

  return names;
}

export async function buildJavaMethodCatalogEntries(root) {
  try {
    const parsed = await buildCatalogWithJdkParser(root);
    if (parsed.length > 0) {
      return parsed;
    }
  } catch {
    // Older or JRE-only environments retain the conservative scanner below.
  }
  const entries = [];
  const files = (await walkSourceFiles(root)).filter(productionSourceFile);
  const seen = new Set();
  for (const file of files) {
    const content = await fs.readFile(safeResolveWithin(root, file), "utf8").catch(() => "");
    const className = classNameForJavaFile(file, content);
    const source = stripJavaComments(content);
    for (const method of collectJavaMethodNames(source)) {
      const qualified = `${className}::${method}`;
      if (!seen.has(qualified)) {
        seen.add(qualified);
        entries.push({
          class: className,
          method,
          qualified,
          file,
          source_type: "production",
        });
      }
    }
  }
  return entries;
}

export async function buildJavaMethodCatalog(root) {
  const entries = await buildJavaMethodCatalogEntries(root);
  const catalog = new Set(entries.map((entry) => entry.qualified));
  return catalog;
}

export function topTenTextToPredictionPayload(text) {
  const predictions = [];
  const lines = String(text ?? "").split(/\r?\n/);
  for (const line of lines) {
    const match = line.trim().match(/^(\d{1,2})[\).\s-]+([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)::([A-Za-z_$][\w$]*)\s*$/);
    if (match) {
      predictions.push({ rank: Number(match[1]), class: match[2], method: match[3] });
    }
  }
  return { predictions };
}
