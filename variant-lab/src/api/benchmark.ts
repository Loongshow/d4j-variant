import type {
  AgentComparisonResponse,
  AgentProfile,
  AgentsResponse,
  BenchmarkRunCreateResponse,
  BenchmarkRunDetail,
  BenchmarkRunsResponse,
  ChartDepthLadderResponse,
  MultiFamilyBatchResponse,
  AccuracyAnalysisResponse,
  AccuracyMetric,
  CreateBenchmarkPairRequest,
  CreateBenchmarkRunRequest,
  PairComparisonResponse,
} from "./types";

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

export async function getAgents(): Promise<AgentsResponse> {
  return fetchJson<AgentsResponse>("/api/agents");
}

export async function createAgent(profile: {
  framework: string;
  provider: string;
  model: string;
  display_name: string;
  defaults: { max_tool_calls: number; max_test_runs: number; timeout_seconds: number };
}): Promise<AgentProfile> {
  return fetchJson<AgentProfile>("/api/agents", {
    method: "POST",
    body: JSON.stringify(profile),
  });
}

export async function getBenchmarkRuns(): Promise<BenchmarkRunsResponse> {
  return fetchJson<BenchmarkRunsResponse>("/api/benchmark-runs");
}

export async function getBenchmarkRun(runId: string): Promise<BenchmarkRunDetail> {
  return fetchJson<BenchmarkRunDetail>(`/api/benchmark-runs/${encodeURIComponent(runId)}`);
}

export async function createBenchmarkRun(request: CreateBenchmarkRunRequest): Promise<BenchmarkRunCreateResponse> {
  return fetchJson<BenchmarkRunCreateResponse>("/api/benchmark-runs", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function createBenchmarkPair(request: CreateBenchmarkPairRequest): Promise<BenchmarkRunCreateResponse> {
  return fetchJson<BenchmarkRunCreateResponse>("/api/benchmark-runs/pair", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getPairComparison(runId: string): Promise<PairComparisonResponse> {
  return fetchJson<PairComparisonResponse>(`/api/benchmark-comparisons/pair?runId=${encodeURIComponent(runId)}`);
}

export async function getAgentComparison(taskId: string): Promise<AgentComparisonResponse> {
  return fetchJson<AgentComparisonResponse>(`/api/benchmark-comparisons/agents?taskId=${encodeURIComponent(taskId)}`);
}

export async function getChartDepthLadder(): Promise<ChartDepthLadderResponse> {
  return fetchJson<ChartDepthLadderResponse>("/api/benchmark-calibrations/chart-1-depth-ladder");
}

export async function getMultiFamilyBatch(batchId = "seven-family-l10-l90-v1"): Promise<MultiFamilyBatchResponse> {
  return fetchJson<MultiFamilyBatchResponse>(`/api/benchmark-batches/${encodeURIComponent(batchId)}`);
}

export async function getBenchmarkAccuracy(metric: AccuracyMetric = "at1"): Promise<AccuracyAnalysisResponse> {
  return fetchJson<AccuracyAnalysisResponse>(`/api/benchmark/accuracy?metric=${encodeURIComponent(metric)}`);
}
