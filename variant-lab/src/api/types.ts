export type BugStatus = "not-checked-out" | "checked-out" | "original" | "analyzed" | "variant-created";

export type WorkflowStatus = "pending" | "running" | "complete" | "blocked";

export type VariantLevel = "L10" | "L20" | "L30" | "L50" | "L70" | "L90";

export type VariantDimension =
  | "fault-site relocation"
  | "trigger-condition substitution"
  | "propagation-path modification"
  | "failure-mode modification"
  | "API-path substitution";

export interface SourceFile {
  path: string;
  language: string;
  content?: string;
  size?: number;
}

export interface TestArtifact {
  name: string;
  className: string;
  assertion: string;
  output: string;
}

export interface ReasoningNode {
  code: "R" | "C" | "D" | "S" | "F" | "O" | "P";
  label: string;
  detail: string;
}

export interface BugSummary {
  id: string;
  name: string;
  project: string;
  bugId: number;
  baselineVersion: string;
  status: BugStatus;
  issue: string;
}

export interface BugDetail extends BugSummary {
  bug_id?: number;
  buggyVersion?: string;
  fixedVersion?: string;
  modifiedClass: string;
  modifiedClasses?: string[];
  buggyMethod: string;
  rootCause: string;
  triggeringTests?: string[];
  relevantTests?: string[];
  sourceDirs?: string[];
  checkout?: CheckoutStatus;
  analysis?: AnalysisStatus;
  analysis_status?: "missing" | "analyzed";
  bugType?: string[];
  reasoningType?: string[];
  sourceFiles: SourceFile[];
  tests: TestArtifact[];
  diff: string;
  reasoningTree: ReasoningNode[];
  variants?: VariantRun[];
}

export interface CheckoutStatus {
  buggy: boolean;
  fixed: boolean;
  buggyPath?: string;
  fixedPath?: string;
}

export interface AnalysisStatus {
  exists: boolean;
  path?: string;
  content?: string;
}

export interface WorkflowStep {
  id: string;
  title: string;
  status: WorkflowStatus;
  artifactNames: string[];
}

export interface VariantArtifact {
  name: string;
  kind: "report" | "candidates" | "review" | "patch" | "log";
  status: "queued" | "ready";
  path?: string;
}

export interface ValidationStatus {
  baselinePass: "pending" | "pass" | "fail";
  variantFail: "pending" | "pass" | "fail";
  deterministicRuns: "pending" | "pass" | "fail";
}

export interface VariantRun {
  id: string;
  bugId: string;
  project?: string;
  bugNumber?: number;
  variant_id: string;
  level: VariantLevel;
  dimension: VariantDimension;
  changedReasoningNode: string;
  status: "queued" | "running" | "review" | "validated" | "blocked";
  benchmarkStatus?: BenchmarkVariantStatus;
  outputPath: string;
  candidateCount: number;
  humanCheckpoint: boolean;
  createdAt: string;
  validation: ValidationStatus;
  workflow: WorkflowStep[];
  artifacts: VariantArtifact[];
}

export type BenchmarkVariantStatus =
  | "validated"
  | "generation_incomplete"
  | "generation_failed"
  | "validation_failed"
  | "environment_blocked"
  | "schema_error"
  | "rejected"
  | "skipped_existing_validated";

export interface VariantLibrarySummary {
  projects: number;
  total: number;
  validated: number;
  in_progress: number;
  rejected: number;
  failed: number;
  blocked: number;
  levels: Record<VariantLevel, number>;
}

export interface VariantSummary {
  id: string;
  variant_id: string;
  project: string;
  bug_id: number;
  level: VariantLevel;
  status: BenchmarkVariantStatus;
  transformation_dimensions: string[];
  changed_reasoning_node: string;
  reasoning_unit_count: number | null;
  faulty_class: string;
  faulty_method: string;
  triggering_test: string;
  validation_status: string;
  output_path: string;
  created_at: string;
  updated_at: string;
  schema_ok: boolean;
  schema_errors: string[];
}

export interface VariantLevelGroup {
  level: VariantLevel;
  variants: VariantSummary[];
}

export interface VariantBugGroup {
  bugId: number;
  levels: VariantLevelGroup[];
}

export interface VariantProjectGroup {
  project: string;
  bugs: VariantBugGroup[];
}

export interface VariantDetail extends VariantSummary {
  manifest: Record<string, unknown>;
  validation: Record<string, unknown> | null;
  artifacts: Array<{ name: string; status: "ready" | "missing"; path: string }>;
  schema: { ok: boolean; errors: string[] };
  run?: VariantRun;
}

export interface VariantLibraryResponse {
  summary: VariantLibrarySummary;
  groups: VariantProjectGroup[];
  variants: VariantDetail[];
}

export interface VariantArtifactText {
  variant_id: string;
  artifact: string;
  language: string;
  path: string;
  content: string;
  trigger?: Record<string, unknown>;
}

export interface VariantValidationResponse {
  validation: Record<string, unknown> | null;
  accepted: boolean;
  log: string;
}

export interface FaultLocalizationRun {
  schema_version: string;
  task_id: string;
  variant_id: string;
  model: string | null;
  run_id: string;
  status: "provider_not_configured" | "runner_not_implemented" | string;
  predictions: Array<{ rank: number; class: string; method: string }>;
  gold_rank: number | null;
  accuracy_at_1: boolean | null;
  accuracy_at_3: boolean | null;
  trajectory: {
    tool_calls: number | null;
    searches: number | null;
    files_opened: number | null;
    methods_inspected: number | null;
  };
  raw_output: string | null;
  parse_status: string | null;
  created_at: string;
  provider_configured?: boolean;
  message?: string;
  agent_visible_task?: Record<string, unknown>;
}

export interface BatchGenerateResult {
  project: string;
  bug: number;
  variant_id?: string;
  status: string;
  reason?: string;
}

export interface BatchGenerateResponse {
  batch_id: string;
  path: string;
  manifest_path: string;
  report_path: string;
  results: BatchGenerateResult[];
}

export type AgentProfileStatus = "ready" | "configured" | "not_configured" | "invalid";

export interface BenchmarkBudget {
  max_tool_calls: number;
  max_test_runs: number;
  timeout_seconds: number;
}

export interface AgentProfile {
  schema_version: string;
  agent_id: string;
  framework: string;
  provider: string;
  model: string;
  display_name: string;
  status: AgentProfileStatus;
  runtime?: {
    adapter_available: boolean;
    credential_configured: boolean;
    credential_source: string;
    model_configured: boolean;
    provider_ready: boolean;
  };
  provider_config?: ProviderConfigStatus;
  defaults: BenchmarkBudget;
  created_at: string;
  updated_at: string;
}

export interface BenchmarkProtocol {
  schema_version: string;
  agent_receives: string[];
  agent_may: string[];
  agent_may_not: string[];
  source_immutability: Record<string, string>;
}

export interface AgentsResponse {
  protocol: BenchmarkProtocol;
  agents: AgentProfile[];
  adapters?: {
    mini_swe_agent?: AgentAdapterStatus;
  };
}

export type BenchmarkTaskType = "original" | "variant";
export type BenchmarkRunStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "provider_not_configured"
  | string;

export interface BenchmarkRunSummary {
  id: string;
  run_id: string;
  task_id: string;
  task_type: BenchmarkTaskType;
  agent_id: string;
  agent_display_name: string;
  model: string;
  status: BenchmarkRunStatus;
  gold_rank: number | null;
  hit_at_5: boolean | null;
  hit_at_10: boolean | null;
  tool_call_count: number | null;
  unique_files_read: number | null;
  test_run_count: number | null;
  duration_ms?: number | null;
  artifact_path: string;
  started_at: string;
  completed_at: string;
}

export interface BenchmarkRunGroup {
  agent_id: string;
  display_name: string;
  tasks: Array<{
    task_id: string;
    task_type: BenchmarkTaskType;
    runs: BenchmarkRunSummary[];
  }>;
}

export interface BenchmarkRunsResponse {
  protocol: BenchmarkProtocol;
  summary: { total: number; statuses: Record<string, number> };
  groups: BenchmarkRunGroup[];
  runs: BenchmarkRunSummary[];
}

export interface BenchmarkFileRead {
  file: string;
  type: "production" | "test";
  read_count: number;
  first_read_position: number;
  contains_gold_method?: boolean;
}

export interface BenchmarkTrajectoryEvent {
  sequence: number;
  timestamp?: string;
  type: "search" | "open_file" | "command" | "test_run" | "other" | string;
  target: string;
  metadata?: Record<string, unknown>;
}

export type ReasoningWorkflowSourceType = "observed" | "agent_reported" | "derived";

export interface ReasoningWorkflowReference {
  file: string;
  line_start: number | null;
  line_end: number | null;
  trajectory_event_ids: string[];
}

export interface ReasoningWorkflowNode {
  id: string;
  sequence: number;
  timestamp: string;
  kind:
    | "initial_evidence"
    | "search"
    | "file_read"
    | "test_run"
    | "evidence"
    | "inference"
    | "candidate_update"
    | "final_submission"
    | string;
  event_type: string;
  source_type: ReasoningWorkflowSourceType;
  action: string;
  evidence: string;
  inference_summary: string;
  candidate_methods: string[];
  references: ReasoningWorkflowReference[];
  file: string | null;
  command: string | null;
}

export interface ReasoningWorkflowData {
  schema_version: string;
  run_id: string;
  nodes: ReasoningWorkflowNode[];
  edges: Array<{ from: string; to: string; relation: "next" | "supports" | "causes" | "narrows" | string }>;
  agent_reported_chain_status: string;
  agent_reported_chain_errors: string[];
  generated_at: string;
}

export interface BenchmarkRunDetail {
  id: string;
  artifact_path: string;
  manifest: {
    id: string;
    run_id: string;
    task_id: string;
    task_type: BenchmarkTaskType;
    source: Record<string, unknown>;
    agent: {
      agent_id: string;
      framework: string;
      provider: string;
      model: string;
      display_name: string;
    };
    budget: BenchmarkBudget;
    status: BenchmarkRunStatus;
    status_reason: string;
    prompt?: {
      version: string;
      base_prompt_sha256: string;
      rendered_prompt_sha256: string;
    } | null;
    provider_config?: ProviderConfigStatus | null;
    adapter?: AgentAdapterStatus | null;
    workspace?: Record<string, unknown> | null;
    isolation?: {
      fixed_code_inaccessible: boolean;
      git_history_inaccessible: boolean;
      private_metadata_inaccessible: boolean;
      scan?: { ok: boolean; banned_entries: string[]; checked_at: string } | null;
      agent_task?: { ok: boolean; failures: string[] };
    };
    integrity?: {
      ok: boolean;
      changed_files: Array<{ path: string; change: string; before_sha256: string | null; after_sha256: string | null }>;
      before_file_count: number;
      after_file_count: number;
      checked_at: string;
    };
    metrics: {
      tool_call_count: number;
      search_count: number;
      file_read_count: number;
      unique_files_read: number;
      production_files_read: number;
      test_files_read: number;
      test_run_count: number;
      gold_file_read: boolean;
      first_gold_file_read_position: number | null;
      duration_ms?: number | null;
      files: BenchmarkFileRead[];
    };
    started_at: string;
    completed_at: string;
  };
  task: Record<string, unknown>;
  ranking: {
    predictions: Array<{ rank: number; class: string; method: string }>;
    parse_status: string;
    validation_errors?: string[];
  };
  trajectory: BenchmarkTrajectoryEvent[];
  commands: string;
  test_runs: Array<{ test_id: string; run_number: number; status: string; duration_ms?: number; output?: string }>;
  raw_output: string;
  evaluation: {
    gold_methods: Array<{ class: string; method: string; file?: string }>;
    gold_rank: number | null;
    hit_at_5: boolean | null;
    hit_at_10: boolean | null;
    status: string;
    status_reason?: string;
  };
  reasoning_workflow: ReasoningWorkflowData | null;
  shortcut_audit: ShortcutAudit | null;
  files: BenchmarkFileRead[];
}

export interface ShortcutAudit {
  gold_method_in_test_source?: boolean | null;
  gold_class_in_test_source?: boolean | null;
  gold_method_in_test_name?: boolean | null;
  gold_class_in_stack_trace?: boolean | null;
  gold_method_in_stack_trace?: boolean | null;
  failure_message_names_gold_method?: boolean | null;
  trigger_directly_calls_gold_method?: boolean | null;
  gold_file_obvious_from_stack_trace?: boolean | null;
  searched_exact_test_name?: boolean | null;
  searched_exact_exception_message?: boolean | null;
  searched_gold_method_name?: boolean | null;
  first_gold_file_open_position?: number | null;
  first_gold_method_identified_position?: number | null;
  fault_method_relocated?: boolean | null;
  original_faulty_method_preserved?: boolean | null;
}

export interface CreateBenchmarkRunRequest {
  agent_id: string;
  task_type: BenchmarkTaskType;
  original?: { project: string; bug_id: number };
  variant_id?: string;
  budget: BenchmarkBudget;
  repeats?: number;
}

export interface CreateBenchmarkPairRequest {
  agent_id: string;
  original: { project: string; bug_id: number };
  variant_id: string;
  budget: BenchmarkBudget;
}

export interface BenchmarkRunCreateResponse {
  pair_id?: string;
  runs: BenchmarkRunSummary[];
  details: BenchmarkRunDetail[];
}

export interface PairComparisonResponse {
  mode: string;
  original_run_id?: string;
  variant_run_id?: string;
  rows: Array<{ metric: string; original: unknown; variant: unknown }>;
  file_overlap: null | {
    jaccard: number | null;
    shared_files: string[];
    only_a?: string[];
    only_b?: string[];
    intersection_count: number;
    union_count: number;
  };
  message?: string;
}

export interface AgentComparisonResponse {
  mode: string;
  rows: Array<{
    agent: string;
    run_id: string;
    gold_rank: number | null;
    hit_at_5: boolean | null;
    hit_at_10: boolean | null;
    files_read: number;
    tool_calls: number;
  }>;
  overlaps: Array<{
    pair: string;
    jaccard: number | null;
    shared_files: string[];
    intersection_count: number;
    union_count: number;
  }>;
}

export interface DepthLadderRow {
  label: "Original" | "L10" | "L20" | "L30" | string;
  task: string;
  task_id: string;
  task_type: BenchmarkTaskType;
  variant_id: string | null;
  reasoning_level: string;
  semantic_inference_steps: number;
  reasoning_level_status: string;
  variant_status: string;
  benchmark_eligible: boolean;
  run_id: string | null;
  run_number: string | null;
  status: BenchmarkRunStatus | "not_generated" | "not_run";
  artifact_path: string | null;
  model: string | null;
  gold_method: string;
  gold_rank: number | null;
  hit_at_5: boolean | null;
  hit_at_10: boolean | null;
  tool_calls: number | null;
  searches: number | null;
  files_read: number | null;
  unique_files_read: number | null;
  production_files_read: number | null;
  test_files_read: number | null;
  test_runs: number | null;
  duration_ms: number | null;
  first_gold_file_position: number | null;
  gold_file_read: boolean | null;
}

export interface FileOverlapPair {
  from: string;
  to: string;
  jaccard: number | null;
  shared_files: string[];
  only_a?: string[];
  only_b?: string[];
  intersection_count: number;
  union_count: number;
}

export interface FileOverlapMatrix {
  labels: string[];
  matrix: Array<Array<{ from: string; to: string; jaccard: number | null }>>;
  pairs: FileOverlapPair[];
}

export interface ChartDepthLadderResponse {
  schema_version: string;
  title: string;
  scope: string;
  rows: DepthLadderRow[];
  pilot_baseline: {
    original: DepthLadderRow | null;
    l10: DepthLadderRow | null;
    file_jaccard: number | null;
  };
  file_overlap_matrix: FileOverlapMatrix;
  generated_at: string;
}

export interface MultiFamilyBatchMatrixRow {
  Project: string;
  Bug: number;
  Level: VariantLevel;
  "Actual Semantic Steps": number | null;
  "Variant ID": string | null;
  "Root Cause": string | null;
  "Gold Method": string | null;
  "Generation Status": string;
  "Validation Status": string | null;
  "Reproducibility Status": string | null;
  Consistency: boolean | null;
  "Benchmark Eligible": boolean;
  "Benchmark Status": string;
  "Gold Rank": number | null;
  "Hit@1": boolean | null;
  "Hit@5": boolean | null;
  "Hit@10": boolean | null;
  MRR: number | null;
  "Tool Calls": number | null;
  Searches: number | null;
  "Unique Files": number | null;
  "Production Files": number | null;
  "Test Files": number | null;
  Tests: number | null;
  Duration: number | null;
  "Gold File Read": boolean | null;
  "First Gold File Position": number | null;
  "Reasoning Workflow": string | null;
  "Top-10 Ranking": Array<{ rank?: number; class: string; method: string }>;
  "Failure/Skip Reason": string | null;
}

export interface BatchEvent {
  timestamp: string;
  event: "START" | "DONE" | "FAILED" | "SKIPPED" | "CHECKPOINT" | "HEARTBEAT" | string;
  project: string | null;
  bug: number | null;
  level: string | null;
  stage: string;
  status: string;
  reason: string | null;
  artifact_path: string | null;
}

export interface MultiFamilyBatchResponse {
  manifest: {
    batch_id: string;
    status: string;
    updated_at: string;
    concurrency: number;
    frozen_benchmark_protocol: Record<string, unknown>;
  };
  variant_matrix: MultiFamilyBatchMatrixRow[];
  benchmark_results: Array<Record<string, unknown>>;
  acc1_matrix: {
    model: string;
    agent: string;
    levels: VariantLevel[];
    rows: Array<{
      project: string;
      bug: number;
      cells: Record<VariantLevel, {
        accuracy: number | null;
        numerator: number;
        denominator: number;
        display: string;
        task_key: string;
        variant_id: string | null;
      }>;
    }>;
  };
  events: BatchEvent[];
  artifact_path: string;
}

export type AccuracyMetric = "at1" | "at5" | "at10" | "mrr" | "mean_rank";
export type TaskAvailability = "available" | "generation_failed" | "validation_failed" | "depth_unachievable" | "dependency_skipped" | "not_attempted";

export interface AccuracyMetricValue {
  value: number | null;
  numerator?: number;
  denominator: number;
  display?: string;
}

export interface AccuracySummaryRow {
  model: string;
  agent: string;
  family?: string;
  project?: string;
  bug_id?: number;
  depth: string;
  availability: TaskAvailability;
  n_attempted: number;
  n_completed: number;
  n_eligible: number;
  target_runs: number;
  accuracy_at_1: number | null;
  accuracy_at_5: number | null;
  accuracy_at_10: number | null;
  mean_reciprocal_rank: number | null;
  mean_gold_rank: number | null;
  valid_variant_count: number;
  excluded_variant_count: number;
  exclusion_reasons: string[];
}

export interface AccuracyMatrixCell extends AccuracySummaryRow {
  variant_id: string | null;
  actual_semantic_steps: number | null;
  original_accuracy_at_1: number | null;
  variant_accuracy_at_1: number | null;
  delta_accuracy_at_1: number | null;
  metrics: Record<AccuracyMetric, AccuracyMetricValue>;
  selected: AccuracyMetricValue;
}

export interface AccuracyAnalysisResponse {
  schema_version: string;
  selected_metric: AccuracyMetric;
  experiment_config: {
    agent_id: string;
    agent: string;
    model: string;
    protocol_version: string;
    prompt_hash: string;
    target_runs: number;
    depths: VariantLevel[];
  };
  summary: {
    total_historical_runs: number;
    eligible_completed_runs: number;
    excluded_runs: number;
    missing_repetitions_count_as_failures: false;
  };
  matrix: {
    model: string;
    agent: string;
    metric: AccuracyMetric;
    depths: VariantLevel[];
    rows: Array<{
      family: string;
      project: string;
      bug_id: number;
      cells: Record<VariantLevel, AccuracyMatrixCell>;
    }>;
  };
  depth_summary: AccuracySummaryRow[];
  family_summary: Array<{
    family: string;
    project: string;
    bug_id: number;
    original: AccuracySummaryRow;
    depths: AccuracySummaryRow[];
  }>;
  cohort_summaries: {
    seven_family_pilot: {
      cohort_id: string;
      families: string[];
      original: AccuracySummaryRow;
      depths: AccuracySummaryRow[];
    };
  };
  artifact_path: string;
  generated_at: string;
}

export interface CreateVariantRequest {
  bugId: string | number;
  project?: string;
  level: VariantLevel;
  dimension: VariantDimension;
  candidateCount: number;
  humanCheckpoint: boolean;
}

export interface CommandLogEntry {
  command: string;
  cwd: string;
  exitCode: number;
  durationMs: number;
  stdout: string;
  stderr: string;
  error: string;
  timestamp: string;
}

export interface ToolStatus {
  available: boolean;
  path: string;
  source: string;
  version?: string;
}

export interface AgentAdapterStatus extends ToolStatus {
  framework: string;
  supported_invocation: string;
  trajectory_format: string;
  install_requirement: string;
}

export interface ProviderConfigStatus {
  provider: string;
  model: string;
  status: string;
  configured: boolean;
  supported_by_adapter: boolean;
  required_any: string[];
  required_model?: string;
  optional: string[];
  missing_environment: string[];
  credential_configured?: boolean;
  credential_source?: string;
  model_configured?: boolean;
  provider_ready?: boolean;
  message: string;
}

export interface EnvCheck {
  id: string;
  status: string;
  details: Record<string, boolean | string | number | null>;
}

export interface EnvStatus {
  checks?: EnvCheck[];
  defects4j: ToolStatus;
  java: ToolStatus;
  perl: ToolStatus;
  mini_swe_agent?: AgentAdapterStatus;
  openai_provider?: ProviderConfigStatus;
  repoRoot: string;
  workspaceRoot: string;
  checkoutRoot: string;
  path: string;
  lastCommandError: string;
  recentCommands: CommandLogEntry[];
}

export interface CheckoutResponse {
  project: string;
  bugId: number;
  version: "buggy" | "fixed";
  checkoutPath: string;
  fileTreeRoot: string;
  status: "checked-out" | "exists" | "exists-not-overwritten";
}

export interface FileTreeResponse {
  checkedOut: boolean;
  checkoutPath: string;
  files: SourceFile[];
}

export interface DiffResponse {
  diff: string;
  status: "missing-checkout" | "different" | "same";
}
