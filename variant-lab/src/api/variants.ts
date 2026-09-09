import { artifactTemplate, mockBugs, nodeForDimension, workflowTemplate } from "./mockData";
import { readVariantRuns, writeVariantRuns } from "./storage";
import type { BugDetail, CreateVariantRequest, VariantRun } from "./types";

const delay = (ms = 260) => new Promise((resolve) => window.setTimeout(resolve, ms));

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(body?.error ?? `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

function runNumberFor(bugId: string, level: VariantRun["level"], runs: VariantRun[]) {
  return runs.filter((run) => run.bugId === bugId && run.level === level).length + 1;
}

function paddedRun(index: number) {
  return `run-${String(index).padStart(3, "0")}`;
}

function slug(project: string, bugId: number) {
  return `${project}-${bugId}`;
}

// POST /api/variants
export async function createVariant(request: CreateVariantRequest, useMock = false): Promise<VariantRun> {
  if (!useMock && request.project) {
    return fetchJson<VariantRun>("/api/variants", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  await delay(320);
  const bug = mockBugs.find((item) => item.id === request.bugId || item.name === `${request.project}-${request.bugId}`);
  if (!bug) {
    throw new Error(`Bug ${request.bugId} was not found`);
  }

  const runs = readVariantRuns();
  const requestBugId = String(request.bugId);
  const runIndex = runNumberFor(requestBugId, request.level, runs);
  const runName = paddedRun(runIndex);
  const bugSlug = slug(bug.project, bug.bugId);
  const workflow = workflowTemplate();
  workflow[0] = { ...workflow[0], status: "running" };

  const variant: VariantRun = {
    id: `${bug.id}-${request.level.toLowerCase()}-${runName}`,
    bugId: bug.id,
    variant_id: `${bugSlug}-${request.level}-${runName}`,
    level: request.level,
    dimension: request.dimension,
    changedReasoningNode: nodeForDimension[request.dimension],
    status: "running",
    outputPath: `new_bug_variants/${bugSlug}/${request.level}/${runName}/`,
    candidateCount: request.candidateCount,
    humanCheckpoint: request.humanCheckpoint,
    createdAt: new Date().toISOString(),
    validation: {
      baselinePass: "pending",
      variantFail: "pending",
      deterministicRuns: "pending",
    },
    workflow,
    artifacts: artifactTemplate(),
  };

  writeVariantRuns([variant, ...runs]);
  return variant;
}

export async function getVariantsForBug(bug: string | Pick<BugDetail, "id" | "project" | "bugId" | "variants">, useMock = false): Promise<VariantRun[]> {
  if (!useMock && typeof bug !== "string") {
    return bug.variants ?? [];
  }

  await delay(180);
  const bugId = typeof bug === "string" ? bug : bug.id;
  return readVariantRuns()
    .filter((run) => run.bugId === bugId)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

// GET /api/variants/:id
export async function getVariant(id: string, useMock = false): Promise<VariantRun> {
  if (!useMock) {
    return fetchJson<VariantRun>(`/api/variants/${encodeURIComponent(id)}`);
  }

  await delay();
  const run = readVariantRuns().find((item) => item.id === id);
  if (!run) {
    throw new Error(`Variant ${id} was not found`);
  }
  return run;
}

// POST /api/workflows/:id/run-agent
export async function runWorkflowAgent(id: string, useMock = false): Promise<VariantRun> {
  if (!useMock) {
    return fetchJson<VariantRun>(`/api/workflows/${encodeURIComponent(id)}/run-agent`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  await delay(300);
  const runs = readVariantRuns();
  const runIndex = runs.findIndex((item) => item.id === id);
  if (runIndex === -1) {
    throw new Error(`Variant ${id} was not found`);
  }

  const run = runs[runIndex];
  const workflow = run.workflow.map((step) => ({ ...step }));
  let activeIndex = workflow.findIndex((step) => step.status === "running");
  if (activeIndex === -1) {
    activeIndex = workflow.findIndex((step) => step.status === "pending");
    if (activeIndex !== -1) {
      workflow[activeIndex].status = "running";
    }
  } else {
    workflow[activeIndex].status = "complete";
    const nextIndex = workflow.findIndex((step, index) => index > activeIndex && step.status === "pending");
    if (nextIndex !== -1) {
      workflow[nextIndex].status = "running";
    }
  }

  const completedArtifactNames = new Set(
    workflow.flatMap((step) => (step.status === "complete" ? step.artifactNames : [])),
  );
  const artifacts = run.artifacts.map((artifact) => ({
    ...artifact,
    status: completedArtifactNames.has(artifact.name) ? "ready" : artifact.status,
  }));
  const complete = workflow.every((step) => step.status === "complete");

  const updated: VariantRun = {
    ...run,
    workflow,
    artifacts,
    status: complete ? "validated" : workflow.some((step) => step.status === "blocked") ? "blocked" : "running",
    validation: complete
      ? {
          baselinePass: "pass",
          variantFail: "fail",
          deterministicRuns: "pass",
        }
      : run.validation,
  };

  runs[runIndex] = updated;
  writeVariantRuns(runs);
  return updated;
}
