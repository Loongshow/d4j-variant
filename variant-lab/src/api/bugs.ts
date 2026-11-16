import { mockBugs, mockBugSummaries } from "./mockData";
import type {
  BugDetail,
  BugSummary,
  CheckoutResponse,
  DiffResponse,
  EnvStatus,
  FileTreeResponse,
  SourceFile,
} from "./types";

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

function bugParts(id: string) {
  const [project, bugId] = id.split("-");
  if (!project || !bugId) {
    throw new Error(`Bug id ${id} is not in PROJECT-BUGID form`);
  }
  return { project, bugId };
}

export async function getEnvStatus(): Promise<EnvStatus> {
  return fetchJson<EnvStatus>("/api/env");
}

export async function getBugs(useMock = false): Promise<BugSummary[]> {
  if (!useMock) {
    return fetchJson<BugSummary[]>("/api/bugs");
  }
  await delay();
  return mockBugSummaries;
}

export async function getBug(id: string, useMock = false): Promise<BugDetail> {
  if (!useMock) {
    const { project, bugId } = bugParts(id);
    return fetchJson<BugDetail>(`/api/bugs/${encodeURIComponent(project)}/${encodeURIComponent(bugId)}`);
  }
  return getMockBug(id);
}

export async function getMockBug(id: string): Promise<BugDetail> {
  await delay();
  const bug = mockBugs.find((item) => item.id === id || item.name.toLowerCase() === id.toLowerCase());
  if (!bug) {
    throw new Error(`Bug ${id} was not found`);
  }
  return bug;
}

export async function checkoutBug(
  bug: Pick<BugDetail, "project" | "bugId" | "id">,
  version: "buggy" | "fixed",
  useMock = false,
): Promise<CheckoutResponse> {
  if (!useMock) {
    return fetchJson<CheckoutResponse>(
      `/api/bugs/${encodeURIComponent(bug.project)}/${encodeURIComponent(String(bug.bugId))}/checkout`,
      {
        method: "POST",
        body: JSON.stringify({ version: version === "buggy" ? "b" : "f", force: false }),
      },
    );
  }
  await delay(180);
  return {
    project: bug.project,
    bugId: bug.bugId,
    version,
    checkoutPath: `variant_work/${bug.project}_${bug.bugId}_base`,
    fileTreeRoot: `variant_work/${bug.project}_${bug.bugId}_base`,
    status: "exists",
  };
}

export async function analyzeBug(bug: Pick<BugDetail, "project" | "bugId" | "id">, useMock = false): Promise<BugDetail> {
  if (!useMock) {
    return fetchJson<BugDetail>(
      `/api/bugs/${encodeURIComponent(bug.project)}/${encodeURIComponent(String(bug.bugId))}/analyze`,
      { method: "POST", body: JSON.stringify({}) },
    );
  }
  const mock = await getMockBug(bug.id);
  return {
    ...mock,
    status: "analyzed",
    analysis: {
      exists: true,
      path: `runs/${mock.project}-${mock.bugId}/analysis/agent1_report.md`,
      content: `# Agent 1 Report: ${mock.name}\n\nMock analysis artifact for frontend fallback mode.`,
    },
    analysis_status: "analyzed",
  };
}

export async function getFileTree(
  bug: Pick<BugDetail, "project" | "bugId" | "sourceFiles">,
  version: "buggy" | "fixed",
  useMock = false,
): Promise<FileTreeResponse> {
  if (!useMock) {
    return fetchJson<FileTreeResponse>(
      `/api/bugs/${encodeURIComponent(bug.project)}/${encodeURIComponent(String(bug.bugId))}/files?version=${version}`,
    );
  }
  await delay(140);
  return {
    checkedOut: true,
    checkoutPath: `mock/${version}`,
    files: bug.sourceFiles.map(({ content: _content, ...file }) => file),
  };
}

export async function getFileContent(
  bug: Pick<BugDetail, "project" | "bugId" | "sourceFiles">,
  version: "buggy" | "fixed",
  filePath: string,
  useMock = false,
): Promise<SourceFile> {
  if (!useMock) {
    return fetchJson<SourceFile>(
      `/api/bugs/${encodeURIComponent(bug.project)}/${encodeURIComponent(String(bug.bugId))}/file?version=${version}&path=${encodeURIComponent(filePath)}`,
    );
  }
  await delay(100);
  const file = bug.sourceFiles.find((item) => item.path === filePath);
  if (!file) {
    throw new Error(`File ${filePath} was not found`);
  }
  return file;
}

export async function getBugDiff(bug: Pick<BugDetail, "project" | "bugId" | "diff">, useMock = false): Promise<DiffResponse> {
  if (!useMock) {
    return fetchJson<DiffResponse>(
      `/api/bugs/${encodeURIComponent(bug.project)}/${encodeURIComponent(String(bug.bugId))}/diff`,
    );
  }
  await delay(120);
  return {
    diff: bug.diff,
    status: "different",
  };
}
