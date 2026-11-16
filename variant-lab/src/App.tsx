import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import Editor from "@monaco-editor/react";
import {
  AlertCircle,
  BarChart3,
  Beaker,
  Boxes,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Circle,
  Clock3,
  Code2,
  FileCode2,
  FileDiff,
  FileText,
  Folder,
  GitBranch,
  Loader2,
  PanelRight,
  Play,
  Plus,
  Search,
  ShieldCheck,
  SquareStack,
  TerminalSquare,
  TestTube2,
  Workflow,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  createAgent,
  createBenchmarkPair,
  createBenchmarkRun,
  getAgentComparison,
  getAgents,
  getBenchmarkRun,
  getBenchmarkRuns,
  getBenchmarkAccuracy,
  getChartDepthLadder,
  getMultiFamilyBatch,
  getPairComparison,
} from "./api/benchmark";
import {
  analyzeBug,
  checkoutBug,
  getBug,
  getBugDiff,
  getBugs,
  getEnvStatus,
  getFileContent,
  getFileTree,
} from "./api/bugs";
import { createVariant, getVariantsForBug, runWorkflowAgent } from "./api/variants";
import {
  generateMissingL10Variants,
  generateProjectL10Variant,
  getFaultLocalizationRuns,
  getVariantDetail,
  getVariantDiff,
  getVariantLibrary,
  getVariantReasoningTree,
  getVariantTest,
  getVariantValidation,
  runFaultLocalization,
} from "./api/variantLibrary";
import type {
  AgentComparisonResponse,
  AccuracyAnalysisResponse,
  AccuracyMatrixCell,
  AccuracyMetric,
  AgentProfile,
  AgentsResponse,
  BatchGenerateResponse,
  BenchmarkBudget,
  BenchmarkProtocol,
  BenchmarkRunCreateResponse,
  BenchmarkRunDetail,
  BenchmarkRunsResponse,
  ChartDepthLadderResponse,
  MultiFamilyBatchResponse,
  DepthLadderRow,
  PairComparisonResponse,
  ReasoningWorkflowNode,
  BugDetail,
  BugStatus,
  BugSummary,
  CreateVariantRequest,
  EnvStatus,
  FaultLocalizationRun,
  SourceFile,
  ValidationStatus,
  VariantArtifactText,
  VariantDetail,
  VariantDimension,
  VariantLibraryResponse,
  VariantLevel,
  VariantRun,
  WorkflowStep,
} from "./api/types";

const tabs = ["Overview", "Source Code", "Tests", "Diff", "Reasoning Tree", "Variants"] as const;
type Tab = (typeof tabs)[number];

const variantDetailTabs = ["Overview", "Reasoning Tree", "Source Diff", "Trigger Test", "Validation", "Fault Localization"] as const;
type VariantDetailTab = (typeof variantDetailTabs)[number];
const benchmarkTabs = ["Summary", "Top Methods", "Reasoning Workflow", "Shortcut Audit", "Session / Trajectory", "Files Read", "Commands", "Test Runs", "Comparison", "Raw Output"] as const;
type BenchmarkTab = (typeof benchmarkTabs)[number];
type SidebarMode = "bugs" | "variants" | "agents";
type BenchmarkTaskMode = "original" | "variant" | "pair";

const levels: VariantLevel[] = ["L10", "L20", "L30", "L50", "L70", "L90"];
const dimensions: VariantDimension[] = [
  "fault-site relocation",
  "trigger-condition substitution",
  "propagation-path modification",
  "failure-mode modification",
  "API-path substitution",
];

const statusLabel: Record<BugStatus, string> = {
  "not-checked-out": "not checked out",
  "checked-out": "checked out",
  original: "original",
  analyzed: "analyzed",
  "variant-created": "variant-created",
};

const workflowStatusIcon = {
  pending: Circle,
  running: Loader2,
  complete: CheckCircle2,
  blocked: AlertCircle,
};

const validationText: Record<ValidationStatus[keyof ValidationStatus], string> = {
  pending: "pending",
  pass: "pass",
  fail: "fail",
};

interface CreateVariantModalState {
  level: VariantLevel;
  dimension: VariantDimension;
  humanCheckpoint: boolean;
  candidateCount: number;
}

interface AgentModalState {
  framework: string;
  provider: string;
  model: string;
  display_name: string;
  defaults: BenchmarkBudget;
}

const defaultModalState: CreateVariantModalState = {
  level: "L10",
  dimension: "trigger-condition substitution",
  humanCheckpoint: true,
  candidateCount: 3,
};

const defaultAgentModalState: AgentModalState = {
  framework: "mini-swe-agent",
  provider: "openai",
  model: "gpt-5.6",
  display_name: "mini-swe / GPT-5.6",
  defaults: {
    max_tool_calls: 50,
    max_test_runs: 5,
    timeout_seconds: 300,
  },
};

function App() {
  const [sidebarMode, setSidebarMode] = useState<SidebarMode>("bugs");
  const [bugs, setBugs] = useState<BugSummary[]>([]);
  const [selectedBugId, setSelectedBugId] = useState("");
  const [selectedBug, setSelectedBug] = useState<BugDetail | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("Overview");
  const [projectFilter, setProjectFilter] = useState("All");

  const [envStatus, setEnvStatus] = useState<EnvStatus | null>(null);
  const [envLoading, setEnvLoading] = useState(true);
  const [useMockFallback, setUseMockFallback] = useState(false);

  const [bugLoading, setBugLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [variantsLoading, setVariantsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [sourceVersion, setSourceVersion] = useState<"fixed" | "buggy">("fixed");
  const [fileTree, setFileTree] = useState<SourceFile[]>([]);
  const [fileTreeLoading, setFileTreeLoading] = useState(false);
  const [selectedSourcePath, setSelectedSourcePath] = useState("");
  const [sourceContent, setSourceContent] = useState<SourceFile | null>(null);
  const [sourceLoading, setSourceLoading] = useState(false);
  const [diffText, setDiffText] = useState("");
  const [diffLoading, setDiffLoading] = useState(false);

  const [variants, setVariants] = useState<VariantRun[]>([]);
  const [selectedVariantId, setSelectedVariantId] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [modalState, setModalState] = useState<CreateVariantModalState>(defaultModalState);
  const [createBusy, setCreateBusy] = useState(false);
  const [workflowBusyId, setWorkflowBusyId] = useState("");

  const [variantLibrary, setVariantLibrary] = useState<VariantLibraryResponse | null>(null);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [selectedLibraryVariantId, setSelectedLibraryVariantId] = useState("");
  const [selectedLibraryVariant, setSelectedLibraryVariant] = useState<VariantDetail | null>(null);
  const [variantDetailTab, setVariantDetailTab] = useState<VariantDetailTab>("Overview");
  const [variantArtifact, setVariantArtifact] = useState<VariantArtifactText | null>(null);
  const [variantArtifactLoading, setVariantArtifactLoading] = useState(false);
  const [flRuns, setFlRuns] = useState<FaultLocalizationRun[]>([]);
  const [flBusy, setFlBusy] = useState(false);
  const [batchBusy, setBatchBusy] = useState(false);
  const [projectGenerateBusy, setProjectGenerateBusy] = useState("");
  const [batchResult, setBatchResult] = useState<BatchGenerateResponse | null>(null);
  const [libraryStatus, setLibraryStatus] = useState("");

  const [agentsResponse, setAgentsResponse] = useState<AgentsResponse | null>(null);
  const [benchmarkRuns, setBenchmarkRuns] = useState<BenchmarkRunsResponse | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [agentModalOpen, setAgentModalOpen] = useState(false);
  const [agentModalState, setAgentModalState] = useState<AgentModalState>(defaultAgentModalState);
  const [agentBusy, setAgentBusy] = useState(false);
  const [benchmarkTaskMode, setBenchmarkTaskMode] = useState<BenchmarkTaskMode>("variant");
  const [benchmarkProject, setBenchmarkProject] = useState("Chart");
  const [benchmarkBugId, setBenchmarkBugId] = useState(1);
  const [benchmarkLevel, setBenchmarkLevel] = useState<VariantLevel>("L10");
  const [benchmarkVariantId, setBenchmarkVariantId] = useState("CHART-1-L10-SECONDARY-02");
  const [benchmarkBudget, setBenchmarkBudget] = useState<BenchmarkBudget>(defaultAgentModalState.defaults);
  const [benchmarkRepeats, setBenchmarkRepeats] = useState(1);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [runBusy, setRunBusy] = useState(false);
  const [benchmarkStatus, setBenchmarkStatus] = useState("");
  const [selectedBenchmarkRunId, setSelectedBenchmarkRunId] = useState("");
  const [selectedBenchmarkRun, setSelectedBenchmarkRun] = useState<BenchmarkRunDetail | null>(null);
  const [benchmarkTab, setBenchmarkTab] = useState<BenchmarkTab>("Summary");
  const [pairComparison, setPairComparison] = useState<PairComparisonResponse | null>(null);
  const [agentComparison, setAgentComparison] = useState<AgentComparisonResponse | null>(null);
  const [depthLadder, setDepthLadder] = useState<ChartDepthLadderResponse | null>(null);
  const [multiFamilyBatch, setMultiFamilyBatch] = useState<MultiFamilyBatchResponse | null>(null);
  const [accuracyAnalysis, setAccuracyAnalysis] = useState<AccuracyAnalysisResponse | null>(null);

  const [operationStatus, setOperationStatus] = useState("");
  const [checkoutBusy, setCheckoutBusy] = useState<"buggy" | "fixed" | "">("");
  const [analyzeBusy, setAnalyzeBusy] = useState(false);
  const bugListRef = useRef<HTMLDivElement | null>(null);
  const [bugScrollState, setBugScrollState] = useState({ canScrollUp: false, canScrollDown: false });

  useEffect(() => {
    let cancelled = false;
    setBugLoading(true);
    setEnvLoading(true);

    getEnvStatus()
      .then((env) => {
        if (cancelled) return Promise.resolve([]);
        setEnvStatus(env);
        setUseMockFallback(false);
        return getBugs(false);
      })
      .catch(() => {
        if (cancelled) return Promise.resolve([]);
        setEnvStatus(null);
        setUseMockFallback(true);
        return getBugs(true);
      })
      .then((items) => {
        if (cancelled) return;
        setBugs(items);
        setSelectedBugId(items.find((item) => item.id.toLowerCase() === "chart-1")?.id ?? items[0]?.id ?? "");
      })
      .catch((caught: Error) => setError(caught.message))
      .finally(() => {
        if (!cancelled) {
          setBugLoading(false);
          setEnvLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedBugId) {
      setSelectedBug(null);
      setVariants([]);
      return;
    }

    let cancelled = false;
    setDetailLoading(true);
    setVariantsLoading(true);
    setFileTree([]);
    setSelectedSourcePath("");
    setSourceContent(null);
    setDiffText("");
    setError(null);

    getBug(selectedBugId, useMockFallback)
      .then(async (bug) => {
        const bugVariants = await getVariantsForBug(bug, useMockFallback);
        return [bug, bugVariants] as const;
      })
      .then(([bug, bugVariants]) => {
        if (cancelled) return;
        setSelectedBug(bug);
        setVariants(bugVariants);
        setSelectedVariantId((current) => {
          if (bugVariants.some((variant) => variant.id === current)) return current;
          return bugVariants[0]?.id ?? "";
        });
      })
      .catch((caught: Error) => setError(caught.message))
      .finally(() => {
        if (!cancelled) {
          setDetailLoading(false);
          setVariantsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedBugId, useMockFallback]);

  useEffect(() => {
    if (!selectedBug || activeTab !== "Source Code") return;
    let cancelled = false;
    setFileTreeLoading(true);

    getFileTree(selectedBug, sourceVersion, useMockFallback)
      .then((tree) => {
        if (cancelled) return;
        setFileTree(tree.files);
        setSelectedSourcePath((current) => {
          if (current && tree.files.some((file) => file.path === current)) return current;
          return tree.files[0]?.path ?? "";
        });
        if (!tree.checkedOut) {
          setOperationStatus(`${sourceVersion} checkout is missing; run checkout first.`);
        }
      })
      .catch((caught: Error) => setError(caught.message))
      .finally(() => {
        if (!cancelled) setFileTreeLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedBug, sourceVersion, activeTab, useMockFallback]);

  useEffect(() => {
    if (!selectedBug || activeTab !== "Source Code" || !selectedSourcePath) {
      setSourceContent(null);
      return;
    }

    let cancelled = false;
    setSourceLoading(true);
    getFileContent(selectedBug, sourceVersion, selectedSourcePath, useMockFallback)
      .then((file) => {
        if (!cancelled) setSourceContent(file);
      })
      .catch((caught: Error) => setError(caught.message))
      .finally(() => {
        if (!cancelled) setSourceLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedBug, sourceVersion, selectedSourcePath, activeTab, useMockFallback]);

  useEffect(() => {
    if (!selectedBug || activeTab !== "Diff") return;
    let cancelled = false;
    setDiffLoading(true);

    getBugDiff(selectedBug, useMockFallback)
      .then((result) => {
        if (!cancelled) setDiffText(result.diff);
      })
      .catch((caught: Error) => setError(caught.message))
      .finally(() => {
        if (!cancelled) setDiffLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedBug, activeTab, useMockFallback]);

  async function refreshVariantLibrary(selectVariantId?: string) {
    if (useMockFallback) return null;
    setLibraryLoading(true);
    setError(null);
    try {
      const library = await getVariantLibrary();
      setVariantLibrary(library);
      const nextSelected =
        selectVariantId ??
        selectedLibraryVariantId ??
        library.variants.find((variant) => variant.variant_id === "CHART-1-L10-SECONDARY-02")?.variant_id ??
        library.variants[0]?.variant_id ??
        "";
      setSelectedLibraryVariantId(nextSelected);
      return library;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load variant library");
      return null;
    } finally {
      setLibraryLoading(false);
    }
  }

  useEffect(() => {
    if ((sidebarMode !== "variants" && sidebarMode !== "agents") || useMockFallback) return;
    void refreshVariantLibrary();
  }, [sidebarMode, useMockFallback]);

  useEffect(() => {
    if (sidebarMode !== "variants" || useMockFallback || !selectedLibraryVariantId) {
      setSelectedLibraryVariant(null);
      return;
    }

    let cancelled = false;
    getVariantDetail(selectedLibraryVariantId)
      .then((detail) => {
        if (!cancelled) {
          setSelectedLibraryVariant(detail);
          setVariantArtifact(null);
        }
      })
      .catch((caught: Error) => setError(caught.message));

    return () => {
      cancelled = true;
    };
  }, [selectedLibraryVariantId, sidebarMode, useMockFallback]);

  useEffect(() => {
    if (sidebarMode !== "variants" || !selectedLibraryVariantId) return;

    let cancelled = false;
    async function loadArtifact() {
      setVariantArtifact(null);
      setVariantArtifactLoading(true);
      try {
        if (variantDetailTab === "Reasoning Tree") {
          const artifact = await getVariantReasoningTree(selectedLibraryVariantId);
          if (!cancelled) setVariantArtifact(artifact);
        } else if (variantDetailTab === "Source Diff") {
          const artifact = await getVariantDiff(selectedLibraryVariantId);
          if (!cancelled) setVariantArtifact(artifact);
        } else if (variantDetailTab === "Trigger Test") {
          const artifact = await getVariantTest(selectedLibraryVariantId);
          if (!cancelled) setVariantArtifact(artifact);
        } else if (variantDetailTab === "Validation") {
          const validation = await getVariantValidation(selectedLibraryVariantId);
          if (!cancelled) {
            setVariantArtifact({
              variant_id: selectedLibraryVariantId,
              artifact: "validation.json + validation.log",
              language: "plaintext",
              path: "validation.json",
              content: `${JSON.stringify(validation.validation, null, 2)}\n\n/* validation.log */\n${validation.log}`,
            });
          }
        } else if (variantDetailTab === "Fault Localization") {
          const runs = await getFaultLocalizationRuns(selectedLibraryVariantId);
          if (!cancelled) setFlRuns(runs);
        }
      } catch (caught) {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Could not load variant artifact");
      } finally {
        if (!cancelled) setVariantArtifactLoading(false);
      }
    }

    if (variantDetailTab !== "Overview") void loadArtifact();

    return () => {
      cancelled = true;
    };
  }, [variantDetailTab, selectedLibraryVariantId, sidebarMode]);

  async function refreshBenchmarkWorkspace(selectRunId?: string) {
    if (useMockFallback) return;
    setBenchmarkLoading(true);
    setError(null);
    try {
      const [agents, runs, ladder, batch, accuracy] = await Promise.all([
        getAgents(),
        getBenchmarkRuns(),
        getChartDepthLadder(),
        getMultiFamilyBatch(),
        getBenchmarkAccuracy(),
      ]);
      setAgentsResponse(agents);
      setBenchmarkRuns(runs);
      setDepthLadder(ladder);
      setMultiFamilyBatch(batch);
      setAccuracyAnalysis(accuracy);
      setSelectedAgentId((current) => current || agents.agents[0]?.agent_id || "");
      const nextRunId = selectRunId ?? selectedBenchmarkRunId ?? runs.runs[0]?.id ?? "";
      setSelectedBenchmarkRunId(nextRunId);
      if (!benchmarkProtocol && agents.protocol) {
        setBenchmarkBudget(agents.agents[0]?.defaults ?? defaultAgentModalState.defaults);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load Agent Benchmark workspace");
    } finally {
      setBenchmarkLoading(false);
    }
  }

  useEffect(() => {
    if (sidebarMode !== "agents" || useMockFallback) return;
    void refreshBenchmarkWorkspace();
  }, [sidebarMode, useMockFallback]);

  const benchmarkProtocol: BenchmarkProtocol | null = agentsResponse?.protocol ?? benchmarkRuns?.protocol ?? null;
  const selectedAgent = agentsResponse?.agents.find((agent) => agent.agent_id === selectedAgentId) ?? agentsResponse?.agents[0] ?? null;

  useEffect(() => {
    if (!selectedAgent) return;
    setBenchmarkBudget(selectedAgent.defaults);
  }, [selectedAgentId]);

  useEffect(() => {
    if (sidebarMode !== "agents" || !selectedBenchmarkRunId) {
      setSelectedBenchmarkRun(null);
      return;
    }
    let cancelled = false;
    getBenchmarkRun(selectedBenchmarkRunId)
      .then((detail) => {
        if (!cancelled) setSelectedBenchmarkRun(detail);
      })
      .catch((caught: Error) => setError(caught.message));
    return () => {
      cancelled = true;
    };
  }, [sidebarMode, selectedBenchmarkRunId]);

  useEffect(() => {
    if (sidebarMode !== "agents" || !selectedBenchmarkRunId) return;
    const status = selectedBenchmarkRun?.manifest.status;
    if (!status || !["queued", "running"].includes(status)) return;
    const interval = window.setInterval(() => {
      getBenchmarkRun(selectedBenchmarkRunId)
        .then(setSelectedBenchmarkRun)
        .catch((caught: Error) => setError(caught.message));
    }, 2500);
    return () => window.clearInterval(interval);
  }, [sidebarMode, selectedBenchmarkRunId, selectedBenchmarkRun?.manifest.status]);

  useEffect(() => {
    if (sidebarMode !== "agents" || benchmarkTab !== "Comparison" || !selectedBenchmarkRun) return;
    let cancelled = false;
    Promise.all([
      getPairComparison(selectedBenchmarkRun.id),
      getAgentComparison(selectedBenchmarkRun.manifest.task_id),
    ])
      .then(([pair, agents]) => {
        if (!cancelled) {
          setPairComparison(pair);
          setAgentComparison(agents);
        }
      })
      .catch((caught: Error) => setError(caught.message));
    return () => {
      cancelled = true;
    };
  }, [sidebarMode, benchmarkTab, selectedBenchmarkRun]);

  useEffect(() => {
    if (!variantLibrary?.variants.length) return;
    const matching =
      benchmarkTaskMode === "pair"
        ? variantLibrary.variants.filter(
            (variant) => variant.project === benchmarkProject && variant.bug_id === benchmarkBugId && variant.level === benchmarkLevel,
          )
        : benchmarkTaskMode === "variant"
          ? variantLibrary.variants.filter((variant) => variant.level === benchmarkLevel)
          : variantLibrary.variants;
    if (matching.length && !matching.some((variant) => variant.variant_id === benchmarkVariantId)) {
      setBenchmarkVariantId(matching[0].variant_id);
    }
  }, [variantLibrary, benchmarkTaskMode, benchmarkProject, benchmarkBugId, benchmarkLevel, benchmarkVariantId]);

  const projects = useMemo(() => ["All", ...Array.from(new Set(bugs.map((bug) => bug.project))).sort()], [bugs]);

  const filteredBugs = useMemo(() => {
    if (projectFilter === "All") return bugs;
    return bugs.filter((bug) => bug.project === projectFilter);
  }, [bugs, projectFilter]);

  function updateBugScrollState() {
    const list = bugListRef.current;
    if (!list) return;
    setBugScrollState({
      canScrollUp: list.scrollTop > 4,
      canScrollDown: list.scrollTop + list.clientHeight < list.scrollHeight - 4,
    });
  }

  useEffect(() => {
    updateBugScrollState();
  }, [filteredBugs.length, bugLoading]);

  useEffect(() => {
    const onResize = () => updateBugScrollState();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  function scrollBugList(direction: "up" | "down") {
    const list = bugListRef.current;
    if (!list) return;
    list.scrollBy({
      top: direction === "down" ? Math.max(180, list.clientHeight * 0.8) : -Math.max(180, list.clientHeight * 0.8),
      behavior: "smooth",
    });
    window.setTimeout(updateBugScrollState, 260);
  }

  const activeVariant = variants.find((variant) => variant.id === selectedVariantId) ?? variants[0] ?? null;
  const selectedSource =
    sourceContent ??
    fileTree.find((file) => file.path === selectedSourcePath) ??
    selectedBug?.sourceFiles.find((file) => file.path === selectedSourcePath) ??
    selectedBug?.sourceFiles[0];

  const nextRunIndex = variants.filter((variant) => variant.level === modalState.level).length + 1;
  const previewPath =
    selectedBug == null
      ? "new_bug_variants/{project}/bug-{bug_id}/{level}/{PROJECT}-{bug_id}-{level}-RUN-001/"
      : `new_bug_variants/${selectedBug.project}/bug-${selectedBug.bugId}/${modalState.level}/${selectedBug.project.toUpperCase()}-${selectedBug.bugId}-${modalState.level}-RUN-${String(nextRunIndex).padStart(3, "0")}/`;

  async function refreshEnv() {
    if (useMockFallback) return;
    try {
      setEnvStatus(await getEnvStatus());
    } catch {
      setUseMockFallback(true);
    }
  }

  async function refreshSelectedBug() {
    if (!selectedBug) return null;
    const refreshed = await getBug(selectedBug.id, useMockFallback);
    const bugVariants = await getVariantsForBug(refreshed, useMockFallback);
    setSelectedBug(refreshed);
    setVariants(bugVariants);
    setBugs((current) => current.map((bug) => (bug.id === refreshed.id ? { ...bug, status: refreshed.status } : bug)));
    return refreshed;
  }

  async function handleCheckout(version: "buggy" | "fixed") {
    if (!selectedBug) return;
    setCheckoutBusy(version);
    setOperationStatus(`Checking out ${version} revision...`);
    setError(null);
    try {
      const result = await checkoutBug(selectedBug, version, useMockFallback);
      setOperationStatus(`${version} checkout ${result.status}: ${result.checkoutPath}`);
      await refreshSelectedBug();
      await refreshEnv();
    } catch (caught) {
      setOperationStatus(caught instanceof Error ? caught.message : "Checkout failed");
    } finally {
      setCheckoutBusy("");
    }
  }

  async function handleAnalyze() {
    if (!selectedBug) return;
    setAnalyzeBusy(true);
    setOperationStatus("Creating agent1_report.md...");
    setError(null);
    try {
      const analyzed = await analyzeBug(selectedBug, useMockFallback);
      setSelectedBug(analyzed);
      setBugs((current) => current.map((bug) => (bug.id === analyzed.id ? { ...bug, status: analyzed.status } : bug)));
      setOperationStatus(`Analysis ready: ${analyzed.analysis?.path ?? "agent1_report.md"}`);
      setActiveTab("Reasoning Tree");
      await refreshEnv();
    } catch (caught) {
      setOperationStatus(caught instanceof Error ? caught.message : "Analyze failed");
    } finally {
      setAnalyzeBusy(false);
    }
  }

  async function handleCreateVariant() {
    if (!selectedBug) return;
    setCreateBusy(true);
    setError(null);
    try {
      const request: CreateVariantRequest = {
        project: selectedBug.project,
        bugId: selectedBug.bugId,
        level: modalState.level,
        dimension: modalState.dimension,
        candidateCount: modalState.candidateCount,
        humanCheckpoint: modalState.humanCheckpoint,
      };
      const created = await createVariant(request, useMockFallback);
      const refreshed = await refreshSelectedBug();
      const bugVariants = await getVariantsForBug(refreshed ?? selectedBug, useMockFallback);
      setVariants(bugVariants);
      setSelectedVariantId(created.id);
      setActiveTab("Variants");
      setModalOpen(false);
      setModalState(defaultModalState);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create variant");
    } finally {
      setCreateBusy(false);
    }
  }

  async function handleContinueWorkflow(variantId: string) {
    setWorkflowBusyId(variantId);
    setError(null);
    try {
      const updated = await runWorkflowAgent(variantId, useMockFallback);
      setVariants((current) => current.map((variant) => (variant.id === updated.id ? updated : variant)));
      setSelectedVariantId(updated.id);
      await refreshSelectedBug();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not continue workflow");
    } finally {
      setWorkflowBusyId("");
    }
  }

  async function handleGenerateMissingL10() {
    if (useMockFallback) return;
    setBatchBusy(true);
    setLibraryStatus("Generating missing L10 attempts sequentially...");
    setError(null);
    try {
      const result = await generateMissingL10Variants();
      setBatchResult(result);
      setLibraryStatus(`Batch report ready: ${result.report_path}`);
      await refreshVariantLibrary();
    } catch (caught) {
      setLibraryStatus(caught instanceof Error ? caught.message : "Batch generation failed");
    } finally {
      setBatchBusy(false);
    }
  }

  async function handleGenerateProjectL10(project: string) {
    if (useMockFallback) return;
    setProjectGenerateBusy(project);
    setLibraryStatus(`Attempting ${project}-1 L10 generation...`);
    setError(null);
    try {
      const result = await generateProjectL10Variant(project);
      setLibraryStatus(`${project}-1: ${result.status}${result.reason ? ` (${result.reason})` : ""}`);
      await refreshVariantLibrary(result.variant_id);
    } catch (caught) {
      setLibraryStatus(caught instanceof Error ? caught.message : `Could not generate ${project}-1`);
    } finally {
      setProjectGenerateBusy("");
    }
  }

  async function handleRunFaultLocalization() {
    if (!selectedLibraryVariantId) return;
    setFlBusy(true);
    setError(null);
    try {
      const result = await runFaultLocalization(selectedLibraryVariantId);
      setLibraryStatus(result.message ?? result.status);
      setFlRuns(await getFaultLocalizationRuns(selectedLibraryVariantId));
    } catch (caught) {
      setLibraryStatus(caught instanceof Error ? caught.message : "Fault-localization run failed");
    } finally {
      setFlBusy(false);
    }
  }

  async function handleAddAgent() {
    setAgentBusy(true);
    setError(null);
    try {
      const created = await createAgent(agentModalState);
      const agents = await getAgents();
      setAgentsResponse(agents);
      setSelectedAgentId(created.agent_id);
      setAgentModalOpen(false);
      setAgentModalState(defaultAgentModalState);
      setBenchmarkStatus(`Agent profile saved: ${created.display_name}`);
    } catch (caught) {
      setBenchmarkStatus(caught instanceof Error ? caught.message : "Could not save agent profile");
    } finally {
      setAgentBusy(false);
    }
  }

  async function handleCreateBenchmarkRun() {
    if (!selectedAgent) return;
    setRunBusy(true);
    setError(null);
    setBenchmarkStatus("Creating benchmark run...");
    try {
      let result: BenchmarkRunCreateResponse;
      if (benchmarkTaskMode === "pair") {
        result = await createBenchmarkPair({
          agent_id: selectedAgent.agent_id,
          original: { project: benchmarkProject, bug_id: benchmarkBugId },
          variant_id: benchmarkVariantId,
          budget: benchmarkBudget,
        });
      } else {
        result = await createBenchmarkRun({
          agent_id: selectedAgent.agent_id,
          task_type: benchmarkTaskMode,
          original:
            benchmarkTaskMode === "original"
              ? { project: benchmarkProject, bug_id: benchmarkBugId }
              : undefined,
          variant_id: benchmarkTaskMode === "variant" ? benchmarkVariantId : undefined,
          budget: benchmarkBudget,
          repeats: benchmarkRepeats,
        });
      }
      const firstRun = result.runs[0];
      setBenchmarkStatus(
        firstRun?.status === "provider_not_configured"
          ? "Provider not configured. Run manifest and isolated task were created without model output."
          : `Benchmark run created: ${firstRun?.id ?? "run"}`,
      );
      await refreshBenchmarkWorkspace(firstRun?.id);
      if (firstRun?.id) setBenchmarkTab("Summary");
    } catch (caught) {
      setBenchmarkStatus(caught instanceof Error ? caught.message : "Could not create benchmark run");
    } finally {
      setRunBusy(false);
    }
  }

  const rightPanelBug = sidebarMode === "bugs" ? selectedBug : null;
  const rightPanelVariant =
    sidebarMode === "variants" ? selectedLibraryVariant?.run ?? null : sidebarMode === "bugs" ? activeVariant : null;
  const handleRightPanelContinue =
    sidebarMode === "bugs"
      ? handleContinueWorkflow
      : () => setLibraryStatus("Canonical workflow artifacts are derived from manifest files; agent runner wiring comes later.");

  return (
    <div className="appShell">
      <aside className="sidebar">
        <div className="activityRail" aria-label="Activity">
          <button
            className={`railButton ${sidebarMode === "bugs" ? "active" : ""}`}
            onClick={() => setSidebarMode("bugs")}
            aria-label="Bug Explorer"
            title="Bug Explorer"
          >
            <Code2 size={20} />
          </button>
          <button
            className={`railButton ${sidebarMode === "variants" ? "active" : ""}`}
            onClick={() => {
              setSidebarMode("variants");
              setVariantDetailTab("Overview");
            }}
            aria-label="Variant Library"
            title="Variant Library"
          >
            <GitBranch size={20} />
          </button>
          <button
            className={`railButton ${sidebarMode === "agents" ? "active" : ""}`}
            onClick={() => {
              setSidebarMode("agents");
              setBenchmarkTab("Summary");
            }}
            aria-label="Agent Benchmark"
            title="Agent Benchmark"
          >
            <Workflow size={20} />
          </button>
          <Beaker className="railIcon" size={20} />
        </div>

        <div className={`explorer ${sidebarMode === "agents" ? "agentExplorer" : ""}`}>
          {sidebarMode !== "agents" && (
            <>
              <div className="appTitle">
                <Boxes size={18} />
                <span>D4J Variant Lab</span>
              </div>
              <div className={`mockBadge ${useMockFallback ? "warning" : "live"}`}>
                <ShieldCheck size={14} />
                {useMockFallback ? "Backend unavailable: using mock data" : "Local Defects4J backend"}
              </div>
            </>
          )}

          {sidebarMode === "bugs" ? (
            <>
              <label className="filterLabel" htmlFor="project-filter">
                Project filter
              </label>
              <select
                id="project-filter"
                className="selectControl"
                value={projectFilter}
                onChange={(event) => setProjectFilter(event.target.value)}
              >
                {projects.map((project) => (
                  <option key={project}>{project}</option>
                ))}
              </select>

              <div className="explorerHeader">
                <span>BUGS</span>
                <span>{filteredBugs.length}</span>
              </div>

              <div className="bugList" ref={bugListRef} onScroll={updateBugScrollState}>
                {bugLoading && <InlineState icon={Loader2} text="Loading bug index..." spinning />}
                {!bugLoading && filteredBugs.length === 0 && <InlineState icon={Search} text="No bugs match this filter." />}
                {filteredBugs.map((bug) => {
                  const hasRuns = selectedBugId === bug.id && variants.length > 0;
                  const displayStatus: BugStatus = hasRuns ? "variant-created" : bug.status;
                  return (
                    <button
                      key={bug.id}
                      className={`bugItem ${selectedBugId === bug.id ? "selected" : ""}`}
                      onClick={() => {
                        setSelectedBugId(bug.id);
                        setActiveTab("Overview");
                        setOperationStatus("");
                      }}
                    >
                      <span className="bugName">
                        <FileCode2 size={15} />
                        {bug.name}
                      </span>
                      <span className={`statusBadge ${displayStatus}`}>{statusLabel[displayStatus]}</span>
                    </button>
                  );
                })}
              </div>
              <div className="bugScrollControls" aria-label="Bug list scrolling">
                <button
                  className="scrollButton"
                  onClick={() => scrollBugList("up")}
                  disabled={!bugScrollState.canScrollUp}
                  aria-label="Scroll bugs up"
                  title="Scroll bugs up"
                >
                  <ChevronUp size={16} />
                </button>
                <button
                  className="scrollButton"
                  onClick={() => scrollBugList("down")}
                  disabled={!bugScrollState.canScrollDown}
                  aria-label="Scroll bugs down"
                  title="Scroll bugs down"
                >
                  <ChevronDown size={16} />
                </button>
              </div>
            </>
          ) : sidebarMode === "variants" ? (
            <VariantLibrarySidebar
              library={variantLibrary}
              loading={libraryLoading}
              useMockFallback={useMockFallback}
              projects={projects.filter((project) => project !== "All")}
              selectedVariantId={selectedLibraryVariantId}
              batchBusy={batchBusy}
              projectBusy={projectGenerateBusy}
              status={libraryStatus}
              onRefresh={() => void refreshVariantLibrary()}
              onGenerateMissing={handleGenerateMissingL10}
              onGenerateProject={handleGenerateProjectL10}
              onSelect={(variantId) => {
                setSelectedLibraryVariantId(variantId);
                setVariantDetailTab("Overview");
              }}
            />
          ) : (
            <AgentBenchmarkSidebar
              agents={agentsResponse?.agents ?? []}
              adapters={agentsResponse?.adapters}
              loading={benchmarkLoading}
              useMockFallback={useMockFallback}
              selectedAgentId={selectedAgentId}
              runBusy={runBusy}
              onRefresh={() => void refreshBenchmarkWorkspace()}
              onSelectAgent={setSelectedAgentId}
              onOpenAddAgent={() => setAgentModalOpen(true)}
            />
          )}
        </div>
      </aside>

      <main className="mainPanel">
        {error && (
          <div className="errorBar">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {sidebarMode === "agents" ? (
          <AgentBenchmarkMain
            agents={agentsResponse?.agents ?? []}
            runs={benchmarkRuns}
            selectedRun={selectedBenchmarkRun}
            loading={benchmarkLoading}
            activeTab={benchmarkTab}
            pairComparison={pairComparison}
            agentComparison={agentComparison}
            depthLadder={depthLadder}
            multiFamilyBatch={multiFamilyBatch}
            accuracyAnalysis={accuracyAnalysis}
            status={benchmarkStatus}
            useMockFallback={useMockFallback}
            onTabChange={setBenchmarkTab}
          />
        ) : sidebarMode === "variants" ? (
          <VariantLibraryMain
            library={variantLibrary}
            loading={libraryLoading}
            detail={selectedLibraryVariant}
            activeTab={variantDetailTab}
            artifact={variantArtifact}
            artifactLoading={variantArtifactLoading}
            flRuns={flRuns}
            flBusy={flBusy}
            batchResult={batchResult}
            status={libraryStatus}
            useMockFallback={useMockFallback}
            onTabChange={setVariantDetailTab}
            onRunFaultLocalization={handleRunFaultLocalization}
            onGenerateMissing={handleGenerateMissingL10}
          />
        ) : (
          <>
            {!selectedBug && !detailLoading && (
              <EmptyPanel
                icon={Folder}
                title="No bug selected"
                detail="Choose a Defects4J bug from the explorer to inspect its code, tests, diff, and variant runs."
              />
            )}

            {detailLoading && <EmptyPanel icon={Loader2} title="Loading bug details" detail="Fetching Defects4J metadata..." spinning />}

            {selectedBug && !detailLoading && (
              <>
            <header className="bugHeader">
              <div className="bugHeaderMain">
                <div className="eyebrow">SELECTED BUG</div>
                <h1>{selectedBug.name}</h1>
                <div className="metadataRow">
                  <span>{selectedBug.project}</span>
                  <span>Bug ID {selectedBug.bugId}</span>
                  <span>buggy {selectedBug.buggyVersion ?? `${selectedBug.bugId}b`}</span>
                  <span>fixed {selectedBug.fixedVersion ?? `${selectedBug.bugId}f`}</span>
                  <span>{selectedBug.modifiedClasses?.length ?? (selectedBug.modifiedClass ? 1 : 0)} classes</span>
                  <span>{selectedBug.tests.length} triggers</span>
                </div>
              </div>
              <div className="headerActions">
                <button className="secondaryButton" onClick={() => handleCheckout("buggy")} disabled={checkoutBusy !== ""}>
                  {checkoutBusy === "buggy" ? <Loader2 className="spin" size={15} /> : <GitBranch size={15} />}
                  Checkout Buggy
                </button>
                <button className="secondaryButton" onClick={() => handleCheckout("fixed")} disabled={checkoutBusy !== ""}>
                  {checkoutBusy === "fixed" ? <Loader2 className="spin" size={15} /> : <GitBranch size={15} />}
                  Checkout Fixed
                </button>
                {selectedBug.analysis?.exists ? (
                  <span className="analyzedLink">Analyzed: {selectedBug.analysis.path ?? "agent1_report.md"}</span>
                ) : (
                  <button className="secondaryButton" onClick={handleAnalyze} disabled={analyzeBusy}>
                    {analyzeBusy ? <Loader2 className="spin" size={15} /> : <Workflow size={15} />}
                    Analyze
                  </button>
                )}
                <button className="primaryButton" onClick={() => setModalOpen(true)}>
                  <Plus size={16} />
                  Create Variant
                </button>
              </div>
            </header>

            <nav className="tabBar" aria-label="Bug detail tabs">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  className={`tabButton ${activeTab === tab ? "active" : ""}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {iconForTab(tab)}
                  <span>{tab}</span>
                </button>
              ))}
            </nav>

            <section className="tabContent">
              {activeTab === "Overview" && (
                <OverviewTab
                  bug={selectedBug}
                  env={envStatus}
                  envLoading={envLoading}
                  useMockFallback={useMockFallback}
                  operationStatus={operationStatus}
                  analyzeBusy={analyzeBusy}
                  onAnalyze={handleAnalyze}
                />
              )}
              {activeTab === "Source Code" && (
                <SourceTab
                  files={fileTree.length ? fileTree : selectedBug.sourceFiles}
                  selectedPath={selectedSource?.path ?? ""}
                  selectedSource={selectedSource}
                  version={sourceVersion}
                  loading={fileTreeLoading || sourceLoading}
                  checkedOut={selectedBug.checkout?.[sourceVersion] ?? useMockFallback}
                  onVersionChange={setSourceVersion}
                  onSelect={setSelectedSourcePath}
                />
              )}
              {activeTab === "Tests" && <TestsTab bug={selectedBug} />}
              {activeTab === "Diff" &&
                (diffLoading ? (
                  <EmptyPanel icon={Loader2} title="Loading diff" detail="Comparing buggy and fixed checkouts..." spinning />
                ) : (
                  <EditorPane
                    language="diff"
                    value={diffText || selectedBug.diff || "Checkout buggy and fixed versions to view a local diff."}
                  />
                ))}
              {activeTab === "Reasoning Tree" && (
                <ReasoningTreeTab bug={selectedBug} analyzeBusy={analyzeBusy} onAnalyze={handleAnalyze} />
              )}
              {activeTab === "Variants" && (
                <VariantsTab
                  loading={variantsLoading}
                  variants={variants}
                  activeVariantId={activeVariant?.id ?? ""}
                  busyId={workflowBusyId}
                  onSelect={setSelectedVariantId}
                  onContinue={handleContinueWorkflow}
                />
              )}
            </section>
              </>
            )}
          </>
        )}
      </main>

      {sidebarMode === "agents" ? (
        <BenchmarkControlsPanel
          agents={agentsResponse?.agents ?? []}
          protocol={benchmarkProtocol}
          loading={benchmarkLoading}
          selectedAgent={selectedAgent}
          taskMode={benchmarkTaskMode}
          bugs={bugs}
          variants={variantLibrary?.variants ?? []}
          runs={benchmarkRuns}
          selectedRun={selectedBenchmarkRun}
          selectedRunId={selectedBenchmarkRunId}
          project={benchmarkProject}
          bugId={benchmarkBugId}
          level={benchmarkLevel}
          variantId={benchmarkVariantId}
          budget={benchmarkBudget}
          repeats={benchmarkRepeats}
          status={benchmarkStatus}
          runBusy={runBusy}
          onRefresh={() => void refreshBenchmarkWorkspace()}
          onTaskModeChange={setBenchmarkTaskMode}
          onProjectChange={setBenchmarkProject}
          onBugIdChange={setBenchmarkBugId}
          onLevelChange={setBenchmarkLevel}
          onVariantChange={setBenchmarkVariantId}
          onBudgetChange={setBenchmarkBudget}
          onRepeatsChange={setBenchmarkRepeats}
          onRun={handleCreateBenchmarkRun}
          onSelectRun={(runId) => {
            setSelectedBenchmarkRunId(runId);
            setBenchmarkTab("Summary");
          }}
        />
      ) : (
        <WorkflowPanel bug={rightPanelBug} variant={rightPanelVariant} busyId={workflowBusyId} onContinue={handleRightPanelContinue} />
      )}

      {modalOpen && selectedBug && (
        <CreateVariantModal
          state={modalState}
          previewPath={previewPath}
          busy={createBusy}
          useMockFallback={useMockFallback}
          onChange={setModalState}
          onClose={() => setModalOpen(false)}
          onCreate={handleCreateVariant}
        />
      )}

      {agentModalOpen && (
        <AgentProfileModal
          state={agentModalState}
          busy={agentBusy}
          onChange={setAgentModalState}
          onClose={() => setAgentModalOpen(false)}
          onCreate={handleAddAgent}
        />
      )}
    </div>
  );
}

function iconForTab(tab: Tab) {
  const icons: Record<Tab, JSX.Element> = {
    Overview: <FileText size={15} />,
    "Source Code": <FileCode2 size={15} />,
    Tests: <TestTube2 size={15} />,
    Diff: <FileDiff size={15} />,
    "Reasoning Tree": <Workflow size={15} />,
    Variants: <SquareStack size={15} />,
  };
  return icons[tab];
}

function OverviewTab({
  bug,
  env,
  envLoading,
  useMockFallback,
  operationStatus,
  analyzeBusy,
  onAnalyze,
}: {
  bug: BugDetail;
  env: EnvStatus | null;
  envLoading: boolean;
  useMockFallback: boolean;
  operationStatus: string;
  analyzeBusy: boolean;
  onAnalyze: () => void;
}) {
  return (
    <div className="overviewGrid wide">
      <section className="overviewSection">
        <div className="sectionTitle">Bug Summary</div>
        <dl className="detailList">
          <dt>Project</dt>
          <dd>{bug.project}</dd>
          <dt>Bug ID</dt>
          <dd>{bug.bugId}</dd>
          <dt>Buggy version</dt>
          <dd>{bug.buggyVersion ?? `${bug.bugId}b`}</dd>
          <dt>Fixed version</dt>
          <dd>{bug.fixedVersion ?? `${bug.bugId}f`}</dd>
          <dt>Modified classes</dt>
          <dd>{(bug.modifiedClasses ?? [bug.modifiedClass].filter(Boolean)).join(", ") || "unknown"}</dd>
          <dt>Triggering tests</dt>
          <dd>{bug.triggeringTests?.join(", ") || bug.tests.map((test) => `${test.className}::${test.name}`).join(", ") || "unknown"}</dd>
          <dt>Analysis</dt>
          <dd>
            {bug.analysis?.exists ? (
              <span className="inlineGood">{bug.analysis.path ?? "agent1_report.md"}</span>
            ) : (
              <button className="tableButton accent wider" onClick={onAnalyze} disabled={analyzeBusy}>
                {analyzeBusy ? "Analyzing..." : "Analyze"}
              </button>
            )}
          </dd>
        </dl>

        <div className="sectionTitle spacingTop">Bug Type / Reasoning Type</div>
        <div className="chipRow">
          {(bug.bugType?.length ? bug.bugType : ["unknown"]).map((tag) => (
            <span className="typeChip" key={tag}>
              {tag}
            </span>
          ))}
          {!bug.analysis?.exists && <span className="typeChip muted">needs analysis</span>}
        </div>
      </section>

      <section className="overviewSection">
        <div className="sectionTitle">Environment Status</div>
        {envLoading && <InlineState icon={Loader2} text="Checking local toolchain..." spinning />}
        {useMockFallback && (
          <div className="inlineWarning">
            Backend unavailable: using mock data. Start `pnpm run dev:full` to enable `/api/env`, checkout, and artifacts.
          </div>
        )}
        {!useMockFallback && env && (
          <div className="envGrid">
            <EnvRow label="Defects4J" ok={env.defects4j.available} value={env.defects4j.path || "missing"} />
            <EnvRow label="Java" ok={env.java.available} value={env.java.version || env.java.path || "missing"} />
            <EnvRow label="Perl" ok={env.perl.available} value={env.perl.version || env.perl.path || "missing"} />
            <EnvRow
              label="mini-swe-agent"
              ok={Boolean(env.mini_swe_agent?.available)}
              value={env.mini_swe_agent?.version || env.mini_swe_agent?.path || "missing"}
            />
            <EnvRow
              label="OpenAI credential"
              ok={Boolean(env.openai_provider?.credential_configured)}
              value={env.openai_provider?.credential_source || "missing"}
            />
            <EnvRow
              label="OpenAI model"
              ok={Boolean(env.openai_provider?.model_configured)}
              value={env.openai_provider?.model || "missing"}
            />
            <EnvRow label="Repo root" ok value={env.repoRoot} />
            <EnvRow label="Workspace root" ok value={env.workspaceRoot} />
            <EnvRow label="Last command error" ok={!env.lastCommandError} value={env.lastCommandError || "none"} />
          </div>
        )}

        <div className="sectionTitle spacingTop">Checkout Status</div>
        <div className="checkoutRows">
          <span className={`statusBadge ${bug.checkout?.buggy ? "checked-out" : "not-checked-out"}`}>
            buggy {bug.checkout?.buggy ? "checked out" : "not checked out"}
          </span>
          <span className={`statusBadge ${bug.checkout?.fixed ? "checked-out" : "not-checked-out"}`}>
            fixed {bug.checkout?.fixed ? "checked out" : "not checked out"}
          </span>
        </div>
        {operationStatus && <div className="inlineNotice">{operationStatus}</div>}

        <div className="sectionTitle spacingTop">
          <TerminalSquare size={14} />
          Command Log
        </div>
        <div className="commandLog">
          {env?.recentCommands?.length ? (
            env.recentCommands.slice(0, 5).map((entry) => (
              <div className="commandRow" key={`${entry.timestamp}-${entry.command}`}>
                <span className={entry.exitCode === 0 ? "inlineGood" : "inlineBad"}>{entry.exitCode}</span>
                <span>{entry.command}</span>
              </div>
            ))
          ) : (
            <span className="mutedText">No commands recorded yet.</span>
          )}
        </div>
      </section>
    </div>
  );
}

function EnvRow({ label, ok, value }: { label: string; ok: boolean; value: string }) {
  return (
    <div className="envRow">
      <span className={ok ? "envDot ok" : "envDot fail"} />
      <span className="envLabel">{label}</span>
      <span className="envValue">{value}</span>
    </div>
  );
}

function SourceTab({
  files,
  selectedPath,
  selectedSource,
  version,
  loading,
  checkedOut,
  onVersionChange,
  onSelect,
}: {
  files: SourceFile[];
  selectedPath: string;
  selectedSource?: SourceFile;
  version: "fixed" | "buggy";
  loading: boolean;
  checkedOut: boolean;
  onVersionChange: (version: "fixed" | "buggy") => void;
  onSelect: (path: string) => void;
}) {
  return (
    <div className="splitPane">
      <aside className="fileTree">
        <div className="paneTitle">
          <Folder size={14} />
          Files
        </div>
        <div className="segmentGroup compactSegments">
          <button className={`segmentButton ${version === "fixed" ? "active" : ""}`} onClick={() => onVersionChange("fixed")}>
            fixed
          </button>
          <button className={`segmentButton ${version === "buggy" ? "active" : ""}`} onClick={() => onVersionChange("buggy")}>
            buggy
          </button>
        </div>
        {loading && <InlineState icon={Loader2} text="Loading files..." spinning />}
        {!loading && !checkedOut && <InlineState icon={AlertCircle} text="Checkout required for this version." />}
        {!loading &&
          files.map((file) => (
            <button
              key={file.path}
              className={`fileTreeItem ${file.path === selectedPath ? "selected" : ""}`}
              onClick={() => onSelect(file.path)}
            >
              <FileCode2 size={14} />
              <span>{file.path}</span>
            </button>
          ))}
      </aside>
      <div className="editorColumn">
        <div className="editorTab">{selectedSource?.path ?? "No file selected"}</div>
        {loading ? (
          <EmptyPanel icon={Loader2} title="Loading file" detail="Reading local checkout content..." spinning />
        ) : selectedSource?.content ? (
          <EditorPane language={selectedSource.language ?? "java"} value={selectedSource.content} />
        ) : (
          <EmptyPanel icon={FileCode2} title="No source content" detail="Select a checked-out source or test file to open it here." />
        )}
      </div>
    </div>
  );
}

function TestsTab({ bug }: { bug: BugDetail }) {
  const tests = bug.tests.length ? bug.tests : (bug.triggeringTests ?? []).map((testName) => {
    const [className, name] = testName.split("::");
    return { className, name: name ?? testName, assertion: "Defects4J triggering test", output: "" };
  });

  return (
    <div className="testGrid">
      {tests.length === 0 && <EmptyPanel icon={TestTube2} title="No triggering tests" detail="Defects4J did not report triggering tests for this bug." />}
      {tests.map((test) => (
        <section className="testRow" key={`${test.className}-${test.name}`}>
          <div className="testName">
            <TestTube2 size={15} />
            <span>{test.className}::{test.name}</span>
          </div>
          <div className="monoBlock">{test.assertion}</div>
          {test.output && <div className="outputBlock">{test.output}</div>}
        </section>
      ))}
      {bug.relevantTests?.length ? (
        <section className="testRow">
          <div className="sectionTitle">Relevant Tests</div>
          <div className="monoBlock">{bug.relevantTests.join("\n")}</div>
        </section>
      ) : null}
    </div>
  );
}

function ReasoningTreeTab({
  bug,
  analyzeBusy,
  onAnalyze,
}: {
  bug: BugDetail;
  analyzeBusy: boolean;
  onAnalyze: () => void;
}) {
  if (bug.analysis?.exists && bug.analysis.content) {
    return <EditorPane language="markdown" value={bug.analysis.content} />;
  }

  if (!bug.analysis?.exists && bug.reasoningTree.length === 0) {
    return (
      <EmptyPanel
        icon={Workflow}
        title="No analysis artifact"
        detail={`Run Analyze to create runs/${bug.project}-${bug.bugId}/analysis/agent1_report.md from real Defects4J metadata.`}
      >
        <button className="primaryButton emptyAction" onClick={onAnalyze} disabled={analyzeBusy}>
          {analyzeBusy ? <Loader2 className="spin" size={16} /> : <Workflow size={16} />}
          Analyze
        </button>
      </EmptyPanel>
    );
  }

  return (
    <div className="reasoningList">
      {bug.reasoningTree.map((node, index) => (
        <div className="reasoningNode" key={`${node.code}-${index}`}>
          <span className="nodeCode">{node.code}</span>
          <div className="nodeBody">
            <div className="nodeTitle">{node.label}</div>
            <div className="nodeDetail">{node.detail}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function VariantsTab({
  loading,
  variants,
  activeVariantId,
  busyId,
  onSelect,
  onContinue,
}: {
  loading: boolean;
  variants: VariantRun[];
  activeVariantId: string;
  busyId: string;
  onSelect: (id: string) => void;
  onContinue: (id: string) => void;
}) {
  if (loading) {
    return <EmptyPanel icon={Loader2} title="Loading variant runs" detail="Reading variant run folders..." spinning />;
  }

  if (variants.length === 0) {
    return (
      <EmptyPanel
        icon={SquareStack}
        title="No variant runs yet"
        detail="Use Create Variant to start L10 or L30 run history for this bug."
      />
    );
  }

  return (
    <div className="tableWrap">
      <table className="variantTable">
        <thead>
          <tr>
            <th>variant_id</th>
            <th>level</th>
            <th>changed reasoning node</th>
            <th>status</th>
            <th>output path</th>
            <th>validation result</th>
            <th>actions</th>
          </tr>
        </thead>
        <tbody>
          {variants.map((variant) => (
            <tr key={variant.id} className={variant.id === activeVariantId ? "selectedRow" : ""} onClick={() => onSelect(variant.id)}>
              <td>{variant.variant_id}</td>
              <td>
                <span className="levelBadge">{variant.level}</span>
              </td>
              <td>{variant.changedReasoningNode}</td>
              <td>
                <span className={`runStatus ${variant.status}`}>{variant.status}</span>
              </td>
              <td className="pathCell">{variant.outputPath}</td>
              <td>
                <ValidationPills validation={variant.validation} />
              </td>
              <td>
                <div className="actionRow">
                  <button className="tableButton" type="button">
                    Open report
                  </button>
                  <button className="tableButton" type="button">
                    View patch
                  </button>
                  <button
                    className="tableButton accent"
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onContinue(variant.id);
                    }}
                    disabled={busyId === variant.id || variant.status === "validated"}
                  >
                    {busyId === variant.id ? "Running..." : "Continue"}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function VariantLibrarySidebar({
  library,
  loading,
  useMockFallback,
  projects,
  selectedVariantId,
  batchBusy,
  projectBusy,
  status,
  onRefresh,
  onGenerateMissing,
  onGenerateProject,
  onSelect,
}: {
  library: VariantLibraryResponse | null;
  loading: boolean;
  useMockFallback: boolean;
  projects: string[];
  selectedVariantId: string;
  batchBusy: boolean;
  projectBusy: string;
  status: string;
  onRefresh: () => void;
  onGenerateMissing: () => void;
  onGenerateProject: (project: string) => void;
  onSelect: (variantId: string) => void;
}) {
  const summary = library?.summary;
  const projectsWithManifests = new Set(library?.groups.map((group) => group.project) ?? []);

  if (useMockFallback) {
    return (
      <EmptyPanel
        icon={GitBranch}
        title="Variant Library unavailable"
        detail="Start the local backend to read canonical variant manifests from new_bug_variants."
        compact
      />
    );
  }

  return (
    <>
      <div className="libraryActions">
        <button className="secondaryButton" onClick={onRefresh} disabled={loading || batchBusy}>
          {loading ? <Loader2 className="spin" size={14} /> : <Search size={14} />}
          Refresh
        </button>
        <button className="primaryButton compactPrimary" onClick={onGenerateMissing} disabled={loading || batchBusy}>
          {batchBusy ? <Loader2 className="spin" size={14} /> : <Play size={14} />}
          Generate Missing
        </button>
      </div>

      <div className="summaryGrid">
        <Metric label="Projects" value={summary?.projects ?? 0} />
        <Metric label="Validated" value={summary?.validated ?? 0} />
        <Metric label="Failed" value={(summary?.failed ?? 0) + (summary?.rejected ?? 0)} />
        <Metric label="Blocked" value={summary?.blocked ?? 0} />
        <Metric label="L10" value={summary?.levels.L10 ?? 0} />
      </div>

      {status && <div className="inlineNotice compactNotice">{status}</div>}

      <div className="explorerHeader">
        <span>VARIANTS</span>
        <span>{library?.summary.total ?? 0}</span>
      </div>
      <div className="variantTree">
        {loading && <InlineState icon={Loader2} text="Reading manifests..." spinning />}
        {!loading && !library?.groups.length && (
          <InlineState icon={GitBranch} text="No canonical variants found. Generate missing L10 attempts to populate history." />
        )}
        {library?.groups.map((projectGroup) => (
          <div className="treeProject" key={projectGroup.project}>
            <div className="treeHeading">
              <ChevronDown size={13} />
              {projectGroup.project}
            </div>
            {projectGroup.bugs.map((bugGroup) => (
              <div className="treeBug" key={`${projectGroup.project}-${bugGroup.bugId}`}>
                <div className="treeHeading small">
                  <ChevronDown size={13} />
                  Bug {bugGroup.bugId}
                </div>
                {bugGroup.levels.map((levelGroup) => (
                  <div className="treeLevel" key={`${projectGroup.project}-${bugGroup.bugId}-${levelGroup.level}`}>
                    <div className="treeHeading smaller">{levelGroup.level}</div>
                    {levelGroup.variants.map((variant) => (
                      <button
                        key={variant.variant_id}
                        className={`variantTreeItem ${variant.variant_id === selectedVariantId ? "selected" : ""}`}
                        onClick={() => onSelect(variant.variant_id)}
                      >
                        <span className={`treeDot ${variant.status}`} />
                        <span>{variant.variant_id}</span>
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
        ))}
      </div>

      <div className="explorerHeader controlsHeader">
        <span>BUG-1 L10 CONTROLS</span>
        <span>{projects.length}</span>
      </div>
      <div className="projectGenerateList">
        {projects.map((project) => (
          <button
            key={project}
            className="projectGenerateItem"
            onClick={() => onGenerateProject(project)}
            disabled={projectBusy !== "" || batchBusy}
            title={projectsWithManifests.has(project) ? "Attempt already recorded" : "Generate one L10 attempt"}
          >
            <span>{project}-1</span>
            <span>{projectBusy === project ? "running" : projectsWithManifests.has(project) ? "recorded" : "generate"}</span>
          </button>
        ))}
      </div>
    </>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function VariantLibraryMain({
  library,
  loading,
  detail,
  activeTab,
  artifact,
  artifactLoading,
  flRuns,
  flBusy,
  batchResult,
  status,
  useMockFallback,
  onTabChange,
  onRunFaultLocalization,
  onGenerateMissing,
}: {
  library: VariantLibraryResponse | null;
  loading: boolean;
  detail: VariantDetail | null;
  activeTab: VariantDetailTab;
  artifact: VariantArtifactText | null;
  artifactLoading: boolean;
  flRuns: FaultLocalizationRun[];
  flBusy: boolean;
  batchResult: BatchGenerateResponse | null;
  status: string;
  useMockFallback: boolean;
  onTabChange: (tab: VariantDetailTab) => void;
  onRunFaultLocalization: () => void;
  onGenerateMissing: () => void;
}) {
  if (useMockFallback) {
    return (
      <EmptyPanel
        icon={GitBranch}
        title="Mock fallback mode"
        detail="Variant Library reads real local manifests through the backend. Start pnpm run dev:full to use this view."
      />
    );
  }

  if (loading && !detail) {
    return <EmptyPanel icon={Loader2} title="Loading Variant Library" detail="Scanning canonical manifest folders..." spinning />;
  }

  if (!detail) {
    return (
      <div className="libraryEmpty">
        <EmptyPanel
          icon={GitBranch}
          title="No variant selected"
          detail={
            library?.summary.total
              ? "Select a variant from the library tree."
              : "No canonical manifests are visible yet. Generate missing L10 attempts to migrate Chart and record project status."
          }
        >
          {!library?.summary.total && (
            <button className="primaryButton emptyAction" onClick={onGenerateMissing}>
              <Play size={16} />
              Generate Missing L10
            </button>
          )}
        </EmptyPanel>
        {batchResult && <BatchResultPanel batchResult={batchResult} />}
      </div>
    );
  }

  return (
    <>
      <header className="bugHeader">
        <div className="bugHeaderMain">
          <div className="eyebrow">VARIANT LIBRARY</div>
          <h1>{detail.variant_id}</h1>
          <div className="metadataRow">
            <span>{detail.project}-1</span>
            <span>{detail.level}</span>
            <span>{detail.reasoning_unit_count ?? "unknown"} units</span>
            <span>{detail.transformation_dimensions.join(", ") || "pending dimension"}</span>
          </div>
        </div>
        <div className="headerActions">
          <span className={`benchmarkStatus ${detail.status}`}>{benchmarkStatusText(detail.status)}</span>
          <button className="secondaryButton" onClick={onRunFaultLocalization} disabled={flBusy}>
            {flBusy ? <Loader2 className="spin" size={15} /> : <Beaker size={15} />}
            Run FL
          </button>
        </div>
      </header>

      {status && <div className="libraryStatusBar">{status}</div>}
      {batchResult && <BatchResultPanel batchResult={batchResult} compact />}

      <nav className="tabBar" aria-label="Variant detail tabs">
        {variantDetailTabs.map((tab) => (
          <button key={tab} className={`tabButton ${activeTab === tab ? "active" : ""}`} onClick={() => onTabChange(tab)}>
            {iconForVariantTab(tab)}
            <span>{tab}</span>
          </button>
        ))}
      </nav>

      <section className="tabContent">
        {activeTab === "Overview" && <VariantOverview detail={detail} />}
        {activeTab !== "Overview" && activeTab !== "Fault Localization" && (
          artifactLoading ? (
            <EmptyPanel icon={Loader2} title="Loading artifact" detail="Reading local canonical artifact..." spinning />
          ) : (
            <div className="editorColumn">
              <div className="editorTab">{artifact?.path ?? "Artifact"}</div>
              <EditorPane language={artifact?.language ?? "plaintext"} value={artifact?.content ?? "Artifact not available."} />
            </div>
          )
        )}
        {activeTab === "Fault Localization" && (
          <FaultLocalizationPanel runs={flRuns} busy={flBusy} onRun={onRunFaultLocalization} />
        )}
      </section>
    </>
  );
}

function iconForVariantTab(tab: VariantDetailTab) {
  const icons: Record<VariantDetailTab, JSX.Element> = {
    Overview: <FileText size={15} />,
    "Reasoning Tree": <Workflow size={15} />,
    "Source Diff": <FileDiff size={15} />,
    "Trigger Test": <TestTube2 size={15} />,
    Validation: <ShieldCheck size={15} />,
    "Fault Localization": <Beaker size={15} />,
  };
  return icons[tab];
}

function VariantOverview({ detail }: { detail: VariantDetail }) {
  const manifest = detail.manifest as {
    source?: Record<string, unknown>;
    reasoning?: Record<string, unknown>;
    trigger?: Record<string, unknown>;
    fault?: { semantic_root_cause?: string; locations?: Array<Record<string, unknown>> };
  };
  const location = manifest.fault?.locations?.[0];
  return (
    <div className="overviewGrid wide">
      <section className="overviewSection">
        <div className="sectionTitle">Benchmark Summary</div>
        <dl className="detailList">
          <dt>variant ID</dt>
          <dd>{detail.variant_id}</dd>
          <dt>source bug</dt>
          <dd>{detail.project}-{detail.bug_id}</dd>
          <dt>status</dt>
          <dd>
            <span className={`benchmarkStatus ${detail.status}`}>{benchmarkStatusText(detail.status)}</span>
          </dd>
          <dt>level</dt>
          <dd>{detail.level}</dd>
          <dt>reasoning units</dt>
          <dd>{detail.reasoning_unit_count ?? "not counted"}</dd>
          <dt>dimensions</dt>
          <dd>{detail.transformation_dimensions.join(", ") || "pending"}</dd>
          <dt>artifact path</dt>
          <dd>{detail.output_path}</dd>
        </dl>
      </section>

      <section className="overviewSection">
        <div className="sectionTitle">Fault And Trigger</div>
        <dl className="detailList">
          <dt>faulty class</dt>
          <dd>{String((location?.class ?? detail.faulty_class) || "unknown")}</dd>
          <dt>faulty method</dt>
          <dd>{String((location?.method ?? detail.faulty_method) || "unknown")}</dd>
          <dt>triggering test</dt>
          <dd>{detail.triggering_test || "pending"}</dd>
          <dt>failure type</dt>
          <dd>{String(manifest.trigger?.failure_type ?? "pending")}</dd>
          <dt>expected</dt>
          <dd>{String(manifest.trigger?.expected ?? "pending")}</dd>
          <dt>actual</dt>
          <dd>{String(manifest.trigger?.actual ?? "pending")}</dd>
          <dt>semantic root cause</dt>
          <dd>{manifest.fault?.semantic_root_cause ?? "pending accepted evidence"}</dd>
        </dl>

        {!detail.schema.ok && (
          <div className="inlineWarning spacingTop">
            Schema issues: {detail.schema.errors.join("; ")}
          </div>
        )}
      </section>
    </div>
  );
}

function FaultLocalizationPanel({
  runs,
  busy,
  onRun,
}: {
  runs: FaultLocalizationRun[];
  busy: boolean;
  onRun: () => void;
}) {
  return (
    <div className="testGrid">
      <div className="flHeader">
        <div>
          <div className="sectionTitle">Fault Localization</div>
          <div className="mutedText">The agent task uses a strict whitelist: failing test id, stack trace, failing test source, and read-only buggy repo path.</div>
        </div>
        <button className="primaryButton" onClick={onRun} disabled={busy}>
          {busy ? <Loader2 className="spin" size={16} /> : <Beaker size={16} />}
          Run LLM Fault Localizer
        </button>
      </div>
      {runs.length === 0 && (
        <EmptyPanel icon={Beaker} title="No localization runs yet" detail="Run the localizer to create a provider status record. No predictions are fabricated." />
      )}
      {runs.map((run) => (
        <section className="testRow" key={run.run_id}>
          <div className="testName">
            <Beaker size={15} />
            <span>{run.run_id}</span>
          </div>
          <div className={`benchmarkStatus ${run.status}`}>{run.status}</div>
          {run.message && <div className="inlineNotice">{run.message}</div>}
          <div className="monoBlock">
            {run.predictions.length
              ? JSON.stringify(run.predictions, null, 2)
              : "Fault-localization runner is ready, but no LLM provider is currently configured."}
          </div>
        </section>
      ))}
    </div>
  );
}

function BatchResultPanel({ batchResult, compact = false }: { batchResult: BatchGenerateResponse; compact?: boolean }) {
  return (
    <div className={`batchPanel ${compact ? "compact" : ""}`}>
      <div className="batchHeader">
        <span>{batchResult.batch_id}</span>
        <span>{batchResult.report_path}</span>
      </div>
      <div className="batchRows">
        {batchResult.results.map((result) => (
          <div className="batchRow" key={`${result.project}-${result.bug}`}>
            <span>{result.project}-{result.bug}</span>
            <span>{result.variant_id ?? "-"}</span>
            <span className={`benchmarkStatus ${result.status}`}>{result.status}</span>
            <span>{result.reason ?? ""}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function benchmarkStatusText(status: string) {
  return status.split("_").join(" ");
}

function AgentBenchmarkSidebar({
  agents,
  adapters,
  loading,
  useMockFallback,
  selectedAgentId,
  runBusy,
  onRefresh,
  onSelectAgent,
  onOpenAddAgent,
}: {
  agents: AgentProfile[];
  adapters: AgentsResponse["adapters"];
  loading: boolean;
  useMockFallback: boolean;
  selectedAgentId: string;
  runBusy: boolean;
  onRefresh: () => void;
  onSelectAgent: (agentId: string) => void;
  onOpenAddAgent: () => void;
}) {
  const miniSweAdapter = adapters?.mini_swe_agent;

  if (useMockFallback) {
    return (
      <EmptyPanel
        icon={Workflow}
        title="Agent Benchmark unavailable"
        detail="Start the local backend to configure agents and persist benchmark runs."
        compact
      />
    );
  }

  const agentsByFramework = agents.reduce<Record<string, AgentProfile[]>>((groups, agent) => {
    const key = agent.framework || "agent";
    groups[key] = [...(groups[key] ?? []), agent];
    return groups;
  }, {});

  return (
    <div className="agentSelectorPane">
      <div className="agentSelectorHeader">
        <div>
          <div className="eyebrow">AGENT BENCHMARK</div>
          <h2>Agents</h2>
        </div>
        <button className="secondaryButton" onClick={onRefresh} disabled={loading || runBusy}>
          {loading ? <Loader2 className="spin" size={14} /> : <Search size={14} />}
          Refresh
        </button>
      </div>

      <div className="explorerHeader">
        <span>AGENTS / MODELS</span>
        <span>{agents.length}</span>
      </div>

      <div className="agentList agentListScrollable">
        {Object.entries(agentsByFramework).map(([framework, frameworkAgents]) => (
          <div className="agentFrameworkGroup" key={framework}>
            <div className="agentFrameworkTitle">{framework}</div>
            {frameworkAgents.map((agent) => (
              <button
                key={agent.agent_id}
                className={`agentItem ${agent.agent_id === selectedAgentId ? "selected" : ""}`}
                onClick={() => onSelectAgent(agent.agent_id)}
              >
                <span className={`agentDot ${agent.status}`} />
                <span>
                  <strong>{agent.display_name}</strong>
                  <small>{agent.provider} · {agent.model}</small>
                </span>
                <em>{agent.status === "ready" ? "READY" : benchmarkStatusText(agent.status).toUpperCase()}</em>
              </button>
            ))}
          </div>
        ))}
        {!agents.length && <InlineState icon={Clock3} text="No agent profiles yet." />}
      </div>

      <div className="adapterStatusBox">
        <div className="sectionTitle">mini-swe-agent Adapter</div>
        {miniSweAdapter ? (
          <>
            <div className={`protocolLine ${miniSweAdapter.available ? "allow" : "block"}`}>
              <span>{miniSweAdapter.available ? "READY" : "MISSING"}</span>
              {miniSweAdapter.available ? miniSweAdapter.path : miniSweAdapter.install_requirement}
            </div>
            <div className="mutedText">{miniSweAdapter.trajectory_format}</div>
          </>
        ) : (
          <div className="mutedText">Adapter diagnostics unavailable.</div>
        )}
      </div>
      <button className="secondaryButton fullWidth" onClick={onOpenAddAgent}>
        <Plus size={14} />
        Add Agent
      </button>
    </div>
  );
}

function NumberInput({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="numberField compactNumber">
      <span>{label}</span>
      <input type="number" min={1} value={value} onChange={(event) => onChange(Math.max(1, Number(event.target.value) || 1))} />
    </label>
  );
}

function BenchmarkControlsPanel({
  protocol,
  loading,
  selectedAgent,
  taskMode,
  bugs,
  variants,
  runs,
  selectedRun,
  selectedRunId,
  project,
  bugId,
  level,
  variantId,
  budget,
  repeats,
  status,
  runBusy,
  onRefresh,
  onTaskModeChange,
  onProjectChange,
  onBugIdChange,
  onLevelChange,
  onVariantChange,
  onBudgetChange,
  onRepeatsChange,
  onRun,
  onSelectRun,
}: {
  agents: AgentProfile[];
  protocol: BenchmarkProtocol | null;
  loading: boolean;
  selectedAgent: AgentProfile | null;
  taskMode: BenchmarkTaskMode;
  bugs: BugSummary[];
  variants: VariantDetail[];
  runs: BenchmarkRunsResponse | null;
  selectedRun: BenchmarkRunDetail | null;
  selectedRunId: string;
  project: string;
  bugId: number;
  level: VariantLevel;
  variantId: string;
  budget: BenchmarkBudget;
  repeats: number;
  status: string;
  runBusy: boolean;
  onRefresh: () => void;
  onTaskModeChange: (mode: BenchmarkTaskMode) => void;
  onProjectChange: (project: string) => void;
  onBugIdChange: (bugId: number) => void;
  onLevelChange: (level: VariantLevel) => void;
  onVariantChange: (variantId: string) => void;
  onBudgetChange: (budget: BenchmarkBudget) => void;
  onRepeatsChange: (repeats: number) => void;
  onRun: () => void;
  onSelectRun: (runId: string) => void;
}) {
  const projectOptions = Array.from(new Set(bugs.map((bug) => bug.project))).sort();
  const bugOptions = bugs.filter((bug) => bug.project === project).map((bug) => bug.bugId).sort((a, b) => a - b);
  const variantProjectOptions = Array.from(new Set(variants.map((variant) => variant.project))).sort();
  const selectedProject = taskMode === "original" || taskMode === "pair" ? project : project || variantProjectOptions[0] || "Chart";
  const variantBugOptions = Array.from(
    new Set(variants.filter((variant) => variant.project === selectedProject).map((variant) => variant.bug_id)),
  ).sort((a, b) => a - b);
  const variantLevelOptions = Array.from(
    new Set(
      variants
        .filter((variant) => variant.project === selectedProject && variant.bug_id === bugId)
        .map((variant) => variant.level),
    ),
  ) as VariantLevel[];
  const variantOptions = variants.filter((variant) => {
    if (taskMode === "pair" || taskMode === "variant") {
      return variant.project === selectedProject && variant.bug_id === bugId && variant.level === level;
    }
    return true;
  });
  const usedToolCalls = selectedRun?.manifest.metrics.tool_call_count ?? 0;
  const usedTestRuns = selectedRun?.manifest.metrics.test_run_count ?? 0;

  return (
    <aside className="rightPanel benchmarkControlsPanel">
      <div className="rightPanelHeader">
        <Workflow size={16} />
        <span>Benchmark Controls</span>
      </div>

      <div className="benchmarkControlsScroll">
        <section className="controlSection">
          <div className="sectionTitle">Benchmark Task</div>
          <div className="segmentGroup taskSegments">
            {(["original", "variant", "pair"] as BenchmarkTaskMode[]).map((mode) => (
              <button
                key={mode}
                className={`segmentButton ${taskMode === mode ? "active" : ""}`}
                onClick={() => onTaskModeChange(mode)}
              >
                {mode === "original" ? "Original" : mode === "variant" ? "Variant" : "Pair"}
              </button>
            ))}
          </div>

          {(taskMode === "original" || taskMode === "pair") && (
            <div className="compactFields">
              <label>
                <span>Project</span>
                <select className="selectControl" value={project} onChange={(event) => onProjectChange(event.target.value)}>
                  {projectOptions.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Bug ID</span>
                <select className="selectControl" value={bugId} onChange={(event) => onBugIdChange(Number(event.target.value))}>
                  {(bugOptions.length ? bugOptions : [bugId]).map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}

          {(taskMode === "variant" || taskMode === "pair") && (
            <div className="compactFields variantTaskFields">
              {taskMode === "variant" && (
                <>
                  <label>
                    <span>Project</span>
                    <select className="selectControl" value={selectedProject} onChange={(event) => onProjectChange(event.target.value)}>
                      {(variantProjectOptions.length ? variantProjectOptions : [selectedProject]).map((item) => (
                        <option key={item}>{item}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Bug</span>
                    <select className="selectControl" value={bugId} onChange={(event) => onBugIdChange(Number(event.target.value))}>
                      {(variantBugOptions.length ? variantBugOptions : [bugId]).map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </label>
                </>
              )}
              <label>
                <span>Level</span>
                <select className="selectControl" value={level} onChange={(event) => onLevelChange(event.target.value as VariantLevel)}>
                  {(variantLevelOptions.length ? variantLevelOptions : levels).map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label className="wideField">
                <span>{taskMode === "pair" ? "Matching Variant" : "Variant"}</span>
                <select className="selectControl" value={variantId} onChange={(event) => onVariantChange(event.target.value)}>
                  {variantOptions.map((variant) => (
                    <option key={variant.variant_id} value={variant.variant_id}>
                      {variant.variant_id}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}
        </section>

        <details className="controlSection protocolDetails" open>
          <summary>
            <span className="sectionTitle">Protocol</span>
          </summary>
          <div className="protocolBox benchmarkProtocolBox">
            {(protocol?.agent_receives ?? []).map((item) => (
              <div className="protocolLine allow" key={`controls-receives-${item}`}>
                <span>ALLOW</span>
                {item}
              </div>
            ))}
            {(protocol?.agent_may ?? []).map((item) => (
              <div className="protocolLine allow" key={`controls-may-${item}`}>
                <span>ALLOW</span>
                {item}
              </div>
            ))}
            {(protocol?.agent_may_not ?? []).map((item) => (
              <div className="protocolLine block" key={`controls-block-${item}`}>
                <span>BLOCK</span>
                {item}
              </div>
            ))}
          </div>
        </details>

        <section className="controlSection">
          <div className="sectionTitle">Budget</div>
          <div className="budgetGrid">
            <NumberInput label="Max Tool Calls" value={budget.max_tool_calls} onChange={(value) => onBudgetChange({ ...budget, max_tool_calls: value })} />
            <NumberInput label="Max Test Runs" value={budget.max_test_runs} onChange={(value) => onBudgetChange({ ...budget, max_test_runs: value })} />
            <NumberInput label="Timeout" value={budget.timeout_seconds} onChange={(value) => onBudgetChange({ ...budget, timeout_seconds: value })} />
            <NumberInput label="Repeats" value={repeats} onChange={onRepeatsChange} />
          </div>
        </section>

        <section className="controlSection">
          <div className="sectionTitle">Run Status</div>
          <dl className="compactDetailList">
            <dt>Status</dt>
            <dd>{selectedRun ? <span className={`benchmarkStatus ${selectedRun.manifest.status}`}>{benchmarkStatusText(selectedRun.manifest.status)}</span> : "no run selected"}</dd>
            <dt>Elapsed</dt>
            <dd>{selectedRun ? benchmarkDurationText(selectedRun) : "n/a"}</dd>
            <dt>Tool Calls</dt>
            <dd>{usedToolCalls} / {budget.max_tool_calls}</dd>
            <dt>Test Runs</dt>
            <dd>{usedTestRuns} / {budget.max_test_runs}</dd>
          </dl>
          <button className="primaryButton fullWidth runBenchmarkButton" onClick={onRun} disabled={!selectedAgent || runBusy}>
            {runBusy ? <Loader2 className="spin" size={15} /> : <Play size={15} />}
            {taskMode === "pair" ? "Run Original + Variant" : "Run Fault Localization"}
          </button>
          {status && <div className="inlineNotice compactNotice">{status}</div>}
        </section>

        <section className="controlSection">
          <div className="sectionTitle">
            <span>Run History</span>
            <button className="iconButton inlineIconButton" onClick={onRefresh} disabled={loading || runBusy} aria-label="Refresh run history">
              {loading ? <Loader2 className="spin" size={14} /> : <Search size={14} />}
            </button>
          </div>
          <div className="runQueue compactRunHistory">
            {loading && <InlineState icon={Loader2} text="Loading runs..." spinning />}
            {!loading && !runs?.runs.length && <InlineState icon={Clock3} text="No benchmark runs yet." />}
            {runs?.runs.slice(0, 12).map((run) => (
              <button
                key={run.id}
                className={`queueItem ${run.id === selectedRunId ? "selected" : ""}`}
                onClick={() => onSelectRun(run.id)}
              >
                <span className={`treeDot ${run.status}`} />
                <span>
                  <strong>{run.task_id}</strong>
                  <small>{run.agent_display_name} · {run.run_id}</small>
                </span>
                <em>{benchmarkStatusText(run.status)}</em>
              </button>
            ))}
          </div>
        </section>
      </div>
    </aside>
  );
}

function AgentBenchmarkMain({
  agents,
  runs,
  selectedRun,
  loading,
  activeTab,
  pairComparison,
  agentComparison,
  depthLadder,
  multiFamilyBatch,
  accuracyAnalysis,
  status,
  useMockFallback,
  onTabChange,
}: {
  agents: AgentProfile[];
  runs: BenchmarkRunsResponse | null;
  selectedRun: BenchmarkRunDetail | null;
  loading: boolean;
  activeTab: BenchmarkTab;
  pairComparison: PairComparisonResponse | null;
  agentComparison: AgentComparisonResponse | null;
  depthLadder: ChartDepthLadderResponse | null;
  multiFamilyBatch: MultiFamilyBatchResponse | null;
  accuracyAnalysis: AccuracyAnalysisResponse | null;
  status: string;
  useMockFallback: boolean;
  onTabChange: (tab: BenchmarkTab) => void;
}) {
  if (useMockFallback) {
    return (
      <EmptyPanel
        icon={Workflow}
        title="Mock fallback mode"
        detail="Agent Benchmark requires the local backend because runs are persisted as canonical files."
      />
    );
  }

  if (loading && !selectedRun) {
    return <EmptyPanel icon={Loader2} title="Loading Agent Benchmark" detail="Reading agent profiles and run manifests..." spinning />;
  }

  if (!selectedRun) {
    return (
      <div className="agentEmptyWorkspace">
        <EmptyPanel
          icon={Workflow}
          title="Agent Benchmark"
          detail="Select an agent on the left, configure a benchmark task on the right, then run fault localization."
        />
      </div>
    );
  }

  return (
    <>
      <header className="bugHeader">
        <div className="bugHeaderMain">
          <div className="eyebrow">AGENT BENCHMARK</div>
          <h1>{selectedRun.manifest.task_id}</h1>
          <div className="metadataRow">
            <span>{selectedRun.manifest.task_type}</span>
            <span>{selectedRun.manifest.agent.display_name}</span>
            <span>{selectedRun.manifest.agent.model}</span>
            <span>{selectedRun.manifest.run_id}</span>
          </div>
        </div>
        <div className="headerActions">
          <span className={`benchmarkStatus ${selectedRun.manifest.status}`}>{benchmarkStatusText(selectedRun.manifest.status)}</span>
          <span className="analyzedLink">{selectedRun.artifact_path}</span>
        </div>
      </header>

      {status && <div className="libraryStatusBar">{status}</div>}

      <nav className="tabBar" aria-label="Agent benchmark result tabs">
        {benchmarkTabs.map((tab) => (
          <button key={tab} className={`tabButton ${activeTab === tab ? "active" : ""}`} onClick={() => onTabChange(tab)}>
            {iconForBenchmarkTab(tab)}
            <span>{tab}</span>
          </button>
        ))}
      </nav>

      <section className="tabContent">
        {activeTab === "Summary" && (
          <BenchmarkSummaryTab run={selectedRun} agents={agents} runs={runs} depthLadder={depthLadder} multiFamilyBatch={multiFamilyBatch} accuracyAnalysis={accuracyAnalysis} />
        )}
        {activeTab === "Top Methods" && <TopMethodsTab run={selectedRun} />}
        {activeTab === "Reasoning Workflow" && <ReasoningWorkflowTab run={selectedRun} />}
        {activeTab === "Shortcut Audit" && <ShortcutAuditTab run={selectedRun} />}
        {activeTab === "Session / Trajectory" && <SessionTab run={selectedRun} />}
        {activeTab === "Files Read" && <FilesReadTab run={selectedRun} />}
        {activeTab === "Commands" && <CommandsTab run={selectedRun} />}
        {activeTab === "Test Runs" && <TestRunsTab run={selectedRun} />}
        {activeTab === "Comparison" && <ComparisonTab pair={pairComparison} agents={agentComparison} depthLadder={depthLadder} />}
        {activeTab === "Raw Output" && <RawOutputTab run={selectedRun} />}
      </section>
    </>
  );
}

function iconForBenchmarkTab(tab: BenchmarkTab) {
  const icons: Record<BenchmarkTab, JSX.Element> = {
    Summary: <BarChart3 size={15} />,
    "Top Methods": <Search size={15} />,
    "Reasoning Workflow": <GitBranch size={15} />,
    "Shortcut Audit": <ShieldCheck size={15} />,
    "Session / Trajectory": <Workflow size={15} />,
    "Files Read": <FileCode2 size={15} />,
    Commands: <TerminalSquare size={15} />,
    "Test Runs": <TestTube2 size={15} />,
    Comparison: <GitBranch size={15} />,
    "Raw Output": <FileText size={15} />,
  };
  return icons[tab];
}

function BenchmarkProtocolPanel({ protocol, compact = false }: { protocol: BenchmarkProtocol | null; compact?: boolean }) {
  return (
    <div className={`protocolPanel ${compact ? "compact" : ""}`}>
      <div className="sectionTitle">Frozen Benchmark Protocol</div>
      <div className="protocolColumns">
        <ProtocolColumn title="Agent receives" items={protocol?.agent_receives ?? []} tone="allow" />
        <ProtocolColumn title="Agent may" items={protocol?.agent_may ?? []} tone="allow" />
        <ProtocolColumn title="Agent may not" items={protocol?.agent_may_not ?? []} tone="block" />
      </div>
    </div>
  );
}

function ProtocolColumn({ title, items, tone }: { title: string; items: string[]; tone: "allow" | "block" }) {
  return (
    <div>
      <div className="paneTitle">{title}</div>
      {items.map((item) => (
        <div className={`protocolLine ${tone}`} key={`${title}-${item}`}>
          <span>{tone === "allow" ? "ALLOW" : "BLOCK"}</span>
          {item}
        </div>
      ))}
    </div>
  );
}

function BenchmarkSummaryTab({
  run,
  agents: _agents,
  runs: _runs,
  depthLadder,
  multiFamilyBatch,
  accuracyAnalysis,
}: {
  run: BenchmarkRunDetail;
  agents: AgentProfile[];
  runs: BenchmarkRunsResponse | null;
  depthLadder: ChartDepthLadderResponse | null;
  multiFamilyBatch: MultiFamilyBatchResponse | null;
  accuracyAnalysis: AccuracyAnalysisResponse | null;
}) {
  const provider = run.manifest.provider_config;
  const adapter = run.manifest.adapter;
  const workspace = run.manifest.workspace ?? {};
  const workspaceLabel = typeof workspace.workspace_label === "string" ? workspace.workspace_label : "n/a";
  const changedFiles = run.manifest.integrity?.changed_files ?? [];
  return (
    <div className="summaryWorkspace">
      <AccuracyExperimentSection analysis={accuracyAnalysis} />
      <MultiFamilyBatchSection batch={multiFamilyBatch} />
      <PilotSummarySection ladder={depthLadder} />
      <DepthLadderSection ladder={depthLadder} />

      <div className="overviewGrid wide">
        <section className="overviewSection">
          <div className="sectionTitle">Run Summary</div>
          <dl className="detailList">
            <dt>Task</dt>
            <dd>{run.manifest.task_id}</dd>
            <dt>Agent</dt>
            <dd>{run.manifest.agent.display_name}</dd>
            <dt>Model</dt>
            <dd>{run.manifest.agent.model}</dd>
            <dt>Run ID</dt>
            <dd>{run.manifest.id}</dd>
            <dt>Status</dt>
            <dd>
              <span className={`benchmarkStatus ${run.manifest.status}`}>{benchmarkStatusText(run.manifest.status)}</span>
            </dd>
            <dt>Status reason</dt>
            <dd>{run.manifest.status_reason}</dd>
          </dl>

          <div className="sectionTitle spacingTop">Researcher Evaluation</div>
          <dl className="detailList">
            <dt>Gold Rank</dt>
            <dd>{formatNullable(run.evaluation.gold_rank)}</dd>
            <dt>Hit@5</dt>
            <dd>{formatPass(run.evaluation.hit_at_5)}</dd>
            <dt>Hit@10</dt>
            <dd>{formatPass(run.evaluation.hit_at_10)}</dd>
            <dt>Gold methods</dt>
            <dd>{run.evaluation.gold_methods.map((item) => `${item.class}::${item.method}`).join(", ") || "not available"}</dd>
          </dl>

          <div className="sectionTitle spacingTop">Adapter & Prompt</div>
          <dl className="detailList">
            <dt>Provider</dt>
            <dd>{provider ? `${provider.provider} / ${provider.status}` : "n/a"}</dd>
            <dt>Missing Env</dt>
            <dd>{provider?.missing_environment?.join(" or ") || "none"}</dd>
            <dt>Runner</dt>
            <dd>{adapter ? `${adapter.framework} (${adapter.available ? "available" : "missing"})` : "n/a"}</dd>
            <dt>Prompt</dt>
            <dd>{run.manifest.prompt?.version ?? "n/a"}</dd>
            <dt>Prompt Hash</dt>
            <dd>{run.manifest.prompt?.rendered_prompt_sha256?.slice(0, 16) ?? "n/a"}</dd>
          </dl>
        </section>

        <section className="overviewSection">
          <div className="sectionTitle">Behavior Metrics</div>
          <dl className="detailList">
            <dt>Tool Calls</dt>
            <dd>{run.manifest.metrics.tool_call_count}</dd>
            <dt>Searches</dt>
            <dd>{run.manifest.metrics.search_count}</dd>
            <dt>Unique Files Read</dt>
            <dd>{run.manifest.metrics.unique_files_read}</dd>
            <dt>Production Files Read</dt>
            <dd>{run.manifest.metrics.production_files_read}</dd>
            <dt>Test Files Read</dt>
            <dd>{run.manifest.metrics.test_files_read}</dd>
            <dt>Test Runs</dt>
            <dd>{run.manifest.metrics.test_run_count}</dd>
            <dt>Duration</dt>
            <dd>{benchmarkDurationText(run)}</dd>
            <dt>First Gold File Position</dt>
            <dd>{formatNullable(run.manifest.metrics.first_gold_file_read_position)}</dd>
            <dt>Gold File Read</dt>
            <dd>{run.manifest.metrics.gold_file_read ? "yes" : "no"}</dd>
          </dl>

          <div className="sectionTitle spacingTop">Isolation & Integrity</div>
          <dl className="detailList">
            <dt>Workspace</dt>
            <dd>{workspaceLabel}</dd>
            <dt>Fixed Code Hidden</dt>
            <dd>{formatUnknown(run.manifest.isolation?.fixed_code_inaccessible)}</dd>
            <dt>Git History Hidden</dt>
            <dd>{formatUnknown(run.manifest.isolation?.git_history_inaccessible)}</dd>
            <dt>Private Metadata Hidden</dt>
            <dd>{formatUnknown(run.manifest.isolation?.private_metadata_inaccessible)}</dd>
            <dt>Source Unmodified</dt>
            <dd>{formatUnknown(run.manifest.integrity?.ok)}</dd>
            <dt>Changed Files</dt>
            <dd>{changedFiles.length ? changedFiles.map((file) => `${file.change}:${file.path}`).join(", ") : "none"}</dd>
          </dl>
        </section>
      </div>
    </div>
  );
}

const accuracyMetricLabels: Record<AccuracyMetric, string> = {
  at1: "Accuracy@1",
  at5: "Accuracy@5",
  at10: "Accuracy@10",
  mrr: "MRR",
  mean_rank: "Mean Gold Rank",
};

function AccuracyExperimentSection({ analysis }: { analysis: AccuracyAnalysisResponse | null }) {
  const [metric, setMetric] = useState<AccuracyMetric>("at1");
  const [selected, setSelected] = useState<{ family: string; depth: VariantLevel } | null>(null);
  if (!analysis) {
    return (
      <section className="batchResultsSection">
        <InlineState icon={Loader2} text="Building canonical accuracy aggregates..." spinning />
      </section>
    );
  }
  const selectedRow = selected ? analysis.matrix.rows.find((row) => row.family === selected.family) : null;
  const selectedCell = selected ? selectedRow?.cells[selected.depth] ?? null : null;
  return (
    <section className="batchResultsSection accuracyFirstSection">
      <div className="calibrationHeader">
        <div>
          <div className="eyebrow">PRIMARY EXPERIMENTAL RESULT</div>
          <div className="sectionTitle">{accuracyMetricLabels[metric]} - GPT-5.6 / mini-swe-agent</div>
        </div>
        <span className="typeChip observed">{analysis.summary.eligible_completed_runs} eligible runs</span>
      </div>
      <div className="batchArtifactPath" title={analysis.artifact_path}>
        target n={analysis.experiment_config.target_runs} per task · {analysis.artifact_path}
      </div>
      <div className="metricSelector" role="tablist" aria-label="Accuracy metric">
        {(Object.keys(accuracyMetricLabels) as AccuracyMetric[]).map((item) => (
          <button key={item} role="tab" aria-selected={metric === item} className={metric === item ? "active" : ""} onClick={() => setMetric(item)}>
            {accuracyMetricLabels[item]}
          </button>
        ))}
      </div>
      <div className="tableWrap batchMatrixWrap accuracyMatrixWrap">
        <table className="variantTable benchmarkTable accuracyMatrix">
          <thead>
            <tr><th>Task</th>{analysis.matrix.depths.map((depth) => <th key={depth}>{depth}</th>)}</tr>
          </thead>
          <tbody>
            {analysis.matrix.rows.map((row) => (
              <tr key={row.family}>
                <td><strong>{row.family}</strong></td>
                {analysis.matrix.depths.map((depth) => {
                  const cell = row.cells[depth];
                  const value = cell.metrics[metric];
                  return (
                    <td key={depth}>
                      <button
                        className={`matrixCellButton accuracyCellButton ${selected?.family === row.family && selected.depth === depth ? "selected" : ""}`}
                        onClick={() => setSelected({ family: row.family, depth })}
                        title={`Open ${row.family} ${depth} accuracy details`}
                      >
                        <strong>{value.value == null ? "N/A" : metric === "mrr" ? value.value.toFixed(3) : value.value.toFixed(2)}</strong>
                        <small>{value.value == null ? accuracyUnavailableLabel(cell) : metric.startsWith("at") ? `(${value.numerator}/${value.denominator})` : `(n=${value.denominator})`}</small>
                        {cell.availability === "available" && <em>{cell.n_eligible} / {cell.target_runs} completed</em>}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selected && selectedCell && (
        <div className="matrixCellDetail">
          <div className="paneTitle">{selected.family} {selected.depth}</div>
          <dl className="detailList matrixDetailList">
            <dt>Family</dt><dd>{selected.family}</dd>
            <dt>Project</dt><dd>{selectedRow?.project ?? "N/A"}</dd>
            <dt>Bug</dt><dd>{selectedRow?.bug_id ?? "N/A"}</dd>
            <dt>Depth</dt><dd>{selected.depth}</dd>
            <dt>Model</dt><dd>{selectedCell.model}</dd>
            <dt>Agent</dt><dd>{selectedCell.agent}</dd>
            <dt>Variant IDs</dt><dd>{selectedCell.variant_id ?? "None"}</dd>
            <dt>Availability</dt><dd><BatchState value={selectedCell.availability} /></dd>
            <dt>Runs attempted</dt><dd>{selectedCell.n_attempted}</dd>
            <dt>Runs completed</dt><dd>{selectedCell.n_completed}</dd>
            <dt>Eligible denominator</dt><dd>{selectedCell.n_eligible}</dd>
            <dt>Planned repetitions</dt><dd>{selectedCell.n_eligible} / {selectedCell.target_runs}</dd>
            <dt>Accuracy@1</dt><dd>{formatAggregateMetric(selectedCell.accuracy_at_1, selectedCell.n_eligible)}</dd>
            <dt>Accuracy@5</dt><dd>{formatAggregateMetric(selectedCell.accuracy_at_5, selectedCell.n_eligible)}</dd>
            <dt>Accuracy@10</dt><dd>{formatAggregateMetric(selectedCell.accuracy_at_10, selectedCell.n_eligible)}</dd>
            <dt>MRR</dt><dd>{formatAggregateMetric(selectedCell.mean_reciprocal_rank, selectedCell.n_eligible, 3)}</dd>
            <dt>Mean gold rank</dt><dd>{formatAggregateMetric(selectedCell.mean_gold_rank, selectedCell.n_eligible)}</dd>
            <dt>Valid variants</dt><dd>{selectedCell.valid_variant_count}</dd>
            <dt>Excluded variants</dt><dd>{selectedCell.excluded_variant_count}</dd>
            <dt>Original Acc@1</dt><dd>{formatNullable(selectedCell.original_accuracy_at_1)}</dd>
            <dt>Variant Acc@1</dt><dd>{formatNullable(selectedCell.variant_accuracy_at_1)}</dd>
            <dt>Delta Acc@1</dt><dd>{selectedCell.delta_accuracy_at_1 == null ? "N/A" : `${selectedCell.delta_accuracy_at_1 >= 0 ? "+" : ""}${selectedCell.delta_accuracy_at_1.toFixed(2)}`}</dd>
            <dt>Exclusion reasons</dt><dd>{selectedCell.exclusion_reasons.join("; ") || "None"}</dd>
          </dl>
        </div>
      )}
      <DepthAccuracySummary analysis={analysis} />
      <OriginalVariantAccuracy analysis={analysis} />
      <AccuracyDepthChart analysis={analysis} />
    </section>
  );
}

function availabilityLabel(value: string) {
  return value.replace(/_/g, " ");
}

function accuracyUnavailableLabel(cell: AccuracyMatrixCell) {
  if (cell.availability !== "available") return availabilityLabel(cell.availability);
  return cell.n_attempted === 0 ? "not attempted" : "no eligible runs";
}

function formatAggregateMetric(value: number | null, n: number, digits = 2) {
  return value == null ? "N/A" : `${value.toFixed(digits)} (n=${n})`;
}

function DepthAccuracySummary({ analysis }: { analysis: AccuracyAnalysisResponse }) {
  return (
    <div className="accuracySubsection">
      <div className="sectionTitle">Depth-Level Summary</div>
      <div className="tableWrap compactTableWrap">
        <table className="variantTable benchmarkTable depthAccuracyTable">
          <thead><tr><th>Depth</th><th>Eligible Runs</th><th>Acc@1</th><th>Acc@5</th><th>Acc@10</th><th>MRR</th><th>Mean Rank</th></tr></thead>
          <tbody>{analysis.depth_summary.map((row) => (
            <tr key={row.depth}>
              <td><strong>{row.depth}</strong></td><td>{row.n_eligible}</td>
              <td>{formatAggregateMetric(row.accuracy_at_1, row.n_eligible)}</td>
              <td>{formatAggregateMetric(row.accuracy_at_5, row.n_eligible)}</td>
              <td>{formatAggregateMetric(row.accuracy_at_10, row.n_eligible)}</td>
              <td>{formatAggregateMetric(row.mean_reciprocal_rank, row.n_eligible, 3)}</td>
              <td>{formatAggregateMetric(row.mean_gold_rank, row.n_eligible)}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  );
}

function OriginalVariantAccuracy({ analysis }: { analysis: AccuracyAnalysisResponse }) {
  const [family, setFamily] = useState(analysis.matrix.rows[0]?.family ?? "Chart-1");
  const row = analysis.matrix.rows.find((item) => item.family === family);
  const familySummary = analysis.family_summary.find((item) => item.family === family);
  return (
    <div className="accuracySubsection originalVariantSection">
      <div className="calibrationHeader">
        <div className="sectionTitle">Original vs Variant Accuracy@1</div>
        <select aria-label="Original versus variant family" value={family} onChange={(event) => setFamily(event.target.value)}>
          {analysis.matrix.rows.map((item) => <option key={item.family}>{item.family}</option>)}
        </select>
      </div>
      <div className="tableWrap compactTableWrap">
        <table className="variantTable benchmarkTable originalVariantTable">
          <thead><tr><th>Baseline</th>{analysis.matrix.depths.map((depth) => <th key={depth}>{depth}</th>)}</tr></thead>
          <tbody><tr>
            <td><strong>{formatAggregateMetric(familySummary?.original.accuracy_at_1 ?? null, familySummary?.original.n_eligible ?? 0)}</strong></td>
            {analysis.matrix.depths.map((depth) => {
              const cell = row?.cells[depth];
              if (!cell || cell.variant_accuracy_at_1 == null) return <td key={depth}><strong>N/A</strong><small>{cell ? accuracyUnavailableLabel(cell) : "not attempted"}</small></td>;
              return <td key={depth}><strong>{cell.variant_accuracy_at_1.toFixed(2)}</strong><small>{cell.delta_accuracy_at_1 == null ? "delta N/A" : `delta ${cell.delta_accuracy_at_1 >= 0 ? "+" : ""}${cell.delta_accuracy_at_1.toFixed(2)}`}</small></td>;
            })}
          </tr></tbody>
        </table>
      </div>
    </div>
  );
}

function AccuracyDepthChart({ analysis }: { analysis: AccuracyAnalysisResponse }) {
  const [mode, setMode] = useState<"aggregate" | "family">("aggregate");
  const [family, setFamily] = useState(analysis.matrix.rows[0]?.family ?? "Chart-1");
  const familyRow = analysis.matrix.rows.find((row) => row.family === family);
  const values = analysis.matrix.depths.map((depth) => ({
    depth,
    value: mode === "aggregate"
      ? analysis.depth_summary.find((row) => row.depth === depth)?.accuracy_at_1 ?? null
      : familyRow?.cells[depth].accuracy_at_1 ?? null,
  }));
  const points = values.map((item, index) => ({ ...item, x: 56 + index * 112, y: item.value == null ? null : 20 + (1 - item.value) * 112 }));
  const segments: string[][] = [];
  let segment: string[] = [];
  for (const point of points) {
    if (point.y == null) {
      if (segment.length) segments.push(segment);
      segment = [];
    } else segment.push(`${point.x},${point.y}`);
  }
  if (segment.length) segments.push(segment);
  return (
    <div className="accuracySubsection accuracyChartSection">
      <div className="calibrationHeader">
        <div className="sectionTitle">Reasoning Depth vs Accuracy@1</div>
        <div className="chartControls">
          <div className="metricSelector compact" role="group" aria-label="Chart scope">
            <button className={mode === "aggregate" ? "active" : ""} onClick={() => setMode("aggregate")}>Aggregate</button>
            <button className={mode === "family" ? "active" : ""} onClick={() => setMode("family")}>Per family</button>
          </div>
          {mode === "family" && <select aria-label="Chart family" value={family} onChange={(event) => setFamily(event.target.value)}>{analysis.matrix.rows.map((row) => <option key={row.family}>{row.family}</option>)}</select>}
        </div>
      </div>
      <svg className="accuracyDepthChart" viewBox="0 0 560 170" role="img" aria-label={`Reasoning depth versus Accuracy at 1 for ${mode === "aggregate" ? "all families" : family}`}>
        {[0, 0.5, 1].map((tick) => <g key={tick}><line x1="56" x2="520" y1={20 + (1 - tick) * 112} y2={20 + (1 - tick) * 112} /><text x="46" y={24 + (1 - tick) * 112} textAnchor="end">{tick.toFixed(1)}</text></g>)}
        {segments.map((item, index) => <polyline key={index} points={item.join(" ")} />)}
        {points.map((point) => <g key={point.depth}><text x={point.x} y="154" textAnchor="middle">{point.depth}</text>{point.y != null && <><circle cx={point.x} cy={point.y} r="4" /><text className="chartValue" x={point.x} y={point.y - 9} textAnchor="middle">{point.value?.toFixed(2)}</text></>}</g>)}
      </svg>
      <div className="chartFootnote">Missing depths are left blank and are not interpolated.</div>
    </div>
  );
}

function MultiFamilyBatchSection({ batch }: { batch: MultiFamilyBatchResponse | null }) {
  if (!batch) {
    return (
      <section className="batchResultsSection">
        <InlineState icon={Loader2} text="Loading multi-family batch artifacts..." spinning />
      </section>
    );
  }

  const projects = Array.from(new Set(batch.variant_matrix.map((row) => row.Project)));
  const displayRows = projects.flatMap((project) => {
    const original = batch.benchmark_results.find(
      (row) => row.Project === project && row.Level === "Original",
    );
    const originalRow = {
      project,
      level: "Original",
      steps: original?.["Actual Semantic Steps"] ?? null,
      generation: "verified",
      validation: "verified",
      reproducibility: "source verified",
      localization: original?.Status ?? "not_run",
      goldRank: original?.["Gold Rank"] ?? null,
      hit5: original?.["Hit@5"] ?? null,
      hit10: original?.["Hit@10"] ?? null,
      toolCalls: original?.["Tool Calls"] ?? null,
      searches: original?.Searches ?? null,
      files: original?.["Unique Files"] ?? null,
      tests: original?.Tests ?? null,
      duration: original?.Duration ?? null,
      goldPosition: original?.["First Gold File Position"] ?? null,
      workflow: original?.["Reasoning Workflow"] ?? null,
      reason: original?.["Failure/Skip Reason"] ?? null,
    };
    const variants = batch.variant_matrix
      .filter((row) => row.Project === project)
      .map((row) => ({
        project,
        level: row.Level,
        steps: row["Actual Semantic Steps"],
        generation: row["Generation Status"],
        validation: row["Validation Status"],
        reproducibility: row["Reproducibility Status"],
        localization: row["Benchmark Status"],
        goldRank: row["Gold Rank"],
        hit5: row["Hit@5"],
        hit10: row["Hit@10"],
        toolCalls: row["Tool Calls"],
        searches: row.Searches,
        files: row["Unique Files"],
        tests: row.Tests,
        duration: row.Duration,
        goldPosition: row["First Gold File Position"],
        workflow: row["Reasoning Workflow"],
        reason: row["Failure/Skip Reason"],
      }));
    return [originalRow, ...variants];
  });
  const terminalEvents = batch.events.filter((event) => event.event !== "HEARTBEAT").slice(-6).reverse();
  return (
    <section className="batchResultsSection">
      <div className="calibrationHeader">
        <div>
          <div className="eyebrow">PERSISTED BATCH · CONCURRENCY {batch.manifest.concurrency}</div>
          <div className="sectionTitle">Task Availability and Run Artifacts</div>
        </div>
        <span className={`benchmarkStatus ${batch.manifest.status}`}>{benchmarkStatusText(batch.manifest.status)}</span>
      </div>
      <div className="batchArtifactPath" title={batch.artifact_path}>{batch.manifest.batch_id} · {batch.artifact_path}</div>
      <div className="tableWrap batchMatrixWrap">
        <table className="variantTable benchmarkTable multiFamilyMatrix">
          <thead>
            <tr>
              <th>Task</th><th>Steps</th><th>Generation</th><th>Validation</th><th>Repro</th><th>Localization</th>
              <th>Rank</th><th>@5</th><th>@10</th><th>Tools</th><th>Search</th><th>Files</th><th>Tests</th><th>Duration</th><th>Gold Pos</th><th>Workflow</th><th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row) => (
              <tr key={`${row.project}-${row.level}`}>
                <td><strong>{row.project}-1 {row.level}</strong></td>
                <td>{formatNullable(row.steps)}</td>
                <td><BatchState value={row.generation} /></td>
                <td><BatchState value={row.validation} /></td>
                <td><BatchState value={row.reproducibility} /></td>
                <td><BatchState value={row.localization} /></td>
                <td>{formatNullable(row.goldRank)}</td>
                <td>{formatPass(row.hit5 as boolean | null)}</td>
                <td>{formatPass(row.hit10 as boolean | null)}</td>
                <td>{formatNullable(row.toolCalls)}</td>
                <td>{formatNullable(row.searches)}</td>
                <td>{formatNullable(row.files)}</td>
                <td>{formatNullable(row.tests)}</td>
                <td>{formatDurationMs(typeof row.duration === "number" ? row.duration : null)}</td>
                <td>{formatNullable(row.goldPosition)}</td>
                <td>{row.workflow ? <span className="typeChip observed">READY</span> : "null"}</td>
                <td className="batchReasonCell" title={String(row.reason ?? "")}>{row.reason ? String(row.reason) : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="batchEventStrip">
        {terminalEvents.map((event) => (
          <div className="batchEventLine" key={`${event.timestamp}-${event.event}-${event.project}-${event.level}`}>
            <span className={`eventKind ${event.event.toLowerCase()}`}>{event.event}</span>
            <time>{new Date(event.timestamp).toLocaleTimeString()}</time>
            <strong>{event.project ? `${event.project}-1 ${event.level ?? ""}` : batch.manifest.batch_id}</strong>
            <span>{event.stage} · {benchmarkStatusText(event.status)}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function BatchState({ value }: { value: unknown }) {
  if (value == null || value === "") return <>null</>;
  const text = String(value);
  const className = text.toLowerCase().split(" ").join("_");
  return <span className={`benchmarkStatus ${className}`}>{benchmarkStatusText(text)}</span>;
}

function PilotSummarySection({ ladder }: { ladder: ChartDepthLadderResponse | null }) {
  const original = ladder?.pilot_baseline.original ?? null;
  const l10 = ladder?.pilot_baseline.l10 ?? null;
  const rows: Array<[string, keyof DepthLadderRow, (value: unknown) => string]> = [
    ["Gold Rank", "gold_rank", formatNullable],
    ["Hit@5", "hit_at_5", (value) => formatPass(value as boolean | null)],
    ["Hit@10", "hit_at_10", (value) => formatPass(value as boolean | null)],
    ["Tool Calls", "tool_calls", formatNullable],
    ["Searches", "searches", formatNullable],
    ["Unique Files", "unique_files_read", formatNullable],
    ["Gold File Pos", "first_gold_file_position", formatNullable],
    ["Duration", "duration_ms", (value) => formatDurationMs(value as number | null)],
  ];

  return (
    <section className="pilotSummarySection">
      <div className="calibrationHeader">
        <div>
          <div className="eyebrow">PILOT · n=1 original · n=1 variant</div>
          <div className="sectionTitle">Chart-1 GPT-5.6 Pilot</div>
        </div>
        <span className="typeChip muted">not final benchmark accuracy</span>
      </div>
      {!ladder && <InlineState icon={Loader2} text="Loading pilot summary..." spinning />}
      {ladder && (
        <div className="tableWrap compactTableWrap depthTableWrap">
          <table className="variantTable benchmarkTable depthTable">
            <thead>
              <tr>
                <th>Metric</th>
                <th>Original</th>
                <th>L10</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(([label, key, formatter]) => (
                <tr key={label}>
                  <td>{label}</td>
                  <td>{original ? formatter(original[key]) : "not run"}</td>
                  <td>{l10 ? formatter(l10[key]) : "not generated"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function DepthLadderSection({ ladder }: { ladder: ChartDepthLadderResponse | null }) {
  const rows = ladder?.rows ?? [];
  const metrics: Array<[string, keyof DepthLadderRow, (value: unknown, row?: DepthLadderRow) => string]> = [
    ["Reasoning steps", "semantic_inference_steps", formatNullable],
    ["Gold Rank", "gold_rank", formatDepthValue],
    ["Hit@5", "hit_at_5", (value, row) => formatDepthPass(value as boolean | null, row)],
    ["Hit@10", "hit_at_10", (value, row) => formatDepthPass(value as boolean | null, row)],
    ["Tool Calls", "tool_calls", formatDepthValue],
    ["Searches", "searches", formatDepthValue],
    ["Unique Files", "unique_files_read", formatDepthValue],
    ["Test Runs", "test_runs", formatDepthValue],
    ["Duration", "duration_ms", (value, row) => (row?.status === "completed" ? formatDurationMs(value as number | null) : missingDepthText(row))],
    ["First Gold File Position", "first_gold_file_position", formatDepthValue],
  ];

  return (
    <section className="depthLadderSection">
      <div className="calibrationHeader">
        <div>
          <div className="eyebrow">Chart-1 GPT-5.6 Calibration Pilot</div>
          <div className="sectionTitle">Reasoning Depth Ladder</div>
        </div>
        <span className="typeChip muted">{ladder?.scope ?? "loading persisted runs"}</span>
      </div>
      {!ladder && <InlineState icon={Loader2} text="Loading depth ladder..." spinning />}
      {ladder && (
        <>
          <div className="tableWrap depthTableWrap">
            <table className="variantTable benchmarkTable depthTable">
              <thead>
                <tr>
                  <th>Metric</th>
                  {rows.map((row) => (
                    <th key={row.label}>{row.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metrics.map(([label, key, formatter]) => (
                  <tr key={label}>
                    <td>{label}</td>
                    {rows.map((row) => (
                      <td key={`${label}-${row.label}`}>{formatter(row[key], row)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="miniChartsGrid">
            <MiniDepthChart title="Gold Rank vs Reasoning Depth" rows={rows} valueKey="gold_rank" invert />
            <MiniDepthChart title="Tool Calls vs Reasoning Depth" rows={rows} valueKey="tool_calls" />
            <MiniDepthChart title="Unique Files Read vs Reasoning Depth" rows={rows} valueKey="unique_files_read" />
            <MiniDepthChart title="Duration vs Reasoning Depth" rows={rows} valueKey="duration_ms" duration />
          </div>
        </>
      )}
    </section>
  );
}

function MiniDepthChart({
  title,
  rows,
  valueKey,
  duration = false,
  invert = false,
}: {
  title: string;
  rows: DepthLadderRow[];
  valueKey: keyof DepthLadderRow;
  duration?: boolean;
  invert?: boolean;
}) {
  const values = rows.map((row) => (typeof row[valueKey] === "number" ? (row[valueKey] as number) : null));
  const max = Math.max(1, ...values.filter((value): value is number => value != null));
  return (
    <section className="miniChart">
      <div className="paneTitle">{title}</div>
      {rows.map((row, index) => {
        const value = values[index];
        const width = value == null ? 0 : Math.max(8, Math.round((value / max) * 100));
        return (
          <div className="chartRow" key={`${title}-${row.label}`}>
            <span className="chartAxisLabel">{row.label}</span>
            <div className="chartBarTrack">
              <span className={`chartBar ${invert ? "rankBar" : ""}`} style={{ width: `${width}%` }} />
            </div>
            <span className="chartValue">{value == null ? missingDepthText(row) : duration ? formatDurationMs(value) : formatNullable(value)}</span>
          </div>
        );
      })}
    </section>
  );
}

function TopMethodsTab({ run }: { run: BenchmarkRunDetail }) {
  const goldKeys = new Set(run.evaluation.gold_methods.map((item) => `${item.class}::${item.method}`));
  return (
    <div className="tableWrap">
      <table className="variantTable benchmarkTable">
        <thead>
          <tr>
            <th>rank</th>
            <th>class</th>
            <th>method</th>
            <th>gold</th>
          </tr>
        </thead>
        <tbody>
          {run.ranking.predictions.length === 0 && (
            <tr>
              <td colSpan={4}>No ranked methods recorded. {run.manifest.status_reason}</td>
            </tr>
          )}
          {run.ranking.predictions.map((prediction) => {
            const isGold = goldKeys.has(`${prediction.class}::${prediction.method}`);
            return (
              <tr key={`${prediction.rank}-${prediction.class}-${prediction.method}`} className={isGold ? "selectedRow" : ""}>
                <td>{prediction.rank}</td>
                <td>{prediction.class}</td>
                <td>{prediction.method}</td>
                <td>{isGold ? <span className="benchmarkStatus validated">GOLD</span> : ""}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="inlineNotice">
        Gold Rank: {formatNullable(run.evaluation.gold_rank)} · Hit@5: {formatPass(run.evaluation.hit_at_5)} · Hit@10:{" "}
        {formatPass(run.evaluation.hit_at_10)}
      </div>
    </div>
  );
}

function ReasoningWorkflowTab({ run }: { run: BenchmarkRunDetail }) {
  const workflow = run.reasoning_workflow;
  if (!workflow?.nodes.length) {
    return (
      <EmptyPanel
        icon={GitBranch}
        title="No reasoning workflow"
        detail="This run has no observable trajectory or agent-reported evidence chain."
      />
    );
  }

  return (
    <div className="reasoningWorkflowView">
      <div className="reasoningWorkflowHeader">
        <div>
          <div className="eyebrow">AUDITABLE INVESTIGATION</div>
          <div className="sectionTitle">Reasoning Workflow</div>
        </div>
        <span className="typeChip muted">observable and labelled summaries only</span>
      </div>
      <div className="reasoningWorkflowChain">
        {workflow.nodes.map((node, index) => (
          <ReasoningWorkflowNodeView key={node.id} node={node} last={index === workflow.nodes.length - 1} />
        ))}
      </div>
    </div>
  );
}

function ReasoningWorkflowNodeView({ node, last }: { node: ReasoningWorkflowNode; last: boolean }) {
  const details = [node.event_type, node.file, node.command, node.evidence, node.inference_summary, ...node.candidate_methods, ...node.references.map((item) => item.file)].filter(Boolean);
  return (
    <div className="reasoningWorkflowItem">
      <details className="reasoningWorkflowNode" open={node.kind === "initial_evidence" || node.kind === "final_submission"}>
        <summary>
          <span className="workflowSequence">{String(node.sequence).padStart(2, "0")}</span>
          <span className="workflowNodeTitle">
            <strong>{reasoningWorkflowKind(node.kind)}</strong>
            <small>{node.action}</small>
          </span>
          <span className={`workflowSourceBadge ${node.source_type}`}>{reasoningWorkflowSource(node.source_type)}</span>
          <time>{formatWorkflowTime(node.timestamp)}</time>
        </summary>
        {details.length > 0 && (
          <div className="reasoningWorkflowDetails">
            <WorkflowDetail label="Event type" value={node.event_type} code />
            {node.file && <WorkflowDetail label="File" value={node.file} code />}
            {node.command && <WorkflowDetail label="Command" value={node.command} code />}
            {node.evidence && <WorkflowDetail label="Evidence" value={node.evidence} />}
            {node.inference_summary && <WorkflowDetail label="Concise inference" value={node.inference_summary} />}
            {node.candidate_methods.length > 0 && <WorkflowDetail label="Candidate methods" value={node.candidate_methods.join("\n")} code />}
            {node.references.length > 0 && (
              <WorkflowDetail
                label="References"
                value={node.references
                  .map((reference) => {
                    const lines = reference.line_start == null ? "" : `:${reference.line_start}${reference.line_end ? `-${reference.line_end}` : ""}`;
                    return `${reference.file}${lines}`;
                  })
                  .join("\n")}
                code
              />
            )}
          </div>
        )}
      </details>
      {!last && <div className="reasoningWorkflowArrow">↓</div>}
    </div>
  );
}

function ShortcutAuditTab({ run }: { run: BenchmarkRunDetail }) {
  const audit = run.shortcut_audit;
  if (!audit) {
    return <EmptyPanel icon={ShieldCheck} title="No shortcut audit" detail="No structured shortcut covariates were recorded for this historical run." />;
  }
  const rows: Array<[string, boolean | null | undefined]> = [
    ["Gold method in test source", audit.gold_method_in_test_source],
    ["Gold class in stack trace", audit.gold_class_in_stack_trace],
    ["Trigger directly calls gold", audit.trigger_directly_calls_gold_method],
    ["Gold method name searched", audit.searched_gold_method_name],
    ["Gold method file read", run.manifest.metrics.gold_file_read],
    ["Fault method relocated", audit.fault_method_relocated],
    ["Original faulty method preserved", audit.original_faulty_method_preserved],
  ];
  return (
    <div className="shortcutAuditView">
      <div className="reasoningWorkflowHeader">
        <div><div className="eyebrow">LOCALIZATION COVARIATES</div><div className="sectionTitle">Shortcut Audit</div></div>
        <span className="typeChip muted">descriptive evidence, not proof of memorization</span>
      </div>
      <div className="shortcutAuditGrid">
        {rows.map(([label, value]) => <div className="shortcutAuditRow" key={label}><span>{label}</span><strong className={value === true ? "yes" : value === false ? "no" : "unknown"}>{value == null ? "N/A" : value ? "YES" : "NO"}</strong></div>)}
      </div>
      <dl className="detailList shortcutAuditDetails">
        <dt>First gold file position</dt><dd>{formatNullable(audit.first_gold_file_open_position ?? run.manifest.metrics.first_gold_file_read_position)}</dd>
        <dt>First gold method identified</dt><dd>{formatNullable(audit.first_gold_method_identified_position ?? null)}</dd>
        <dt>Exact test-name search</dt><dd>{audit.searched_exact_test_name == null ? "N/A" : audit.searched_exact_test_name ? "YES" : "NO"}</dd>
        <dt>Exact exception search</dt><dd>{audit.searched_exact_exception_message == null ? "N/A" : audit.searched_exact_exception_message ? "YES" : "NO"}</dd>
      </dl>
    </div>
  );
}

function WorkflowDetail({ label, value, code = false }: { label: string; value: string; code?: boolean }) {
  return (
    <div className="workflowDetailRow">
      <span>{label}</span>
      {code ? <pre>{value}</pre> : <p>{value}</p>}
    </div>
  );
}

function reasoningWorkflowKind(kind: string) {
  const labels: Record<string, string> = {
    initial_evidence: "Initial Failure",
    test_run: "Test Reproduction",
    search: "Search",
    file_read: "File Inspection",
    evidence: "Evidence",
    inference: "Inference",
    candidate_update: "Candidate Update",
    final_submission: "Final Top-10",
  };
  return labels[kind] ?? kind.replace(/_/g, " ");
}

function reasoningWorkflowSource(source: string) {
  if (source === "agent_reported") return "AGENT-REPORTED";
  return source.toUpperCase();
}

function formatWorkflowTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function SessionTab({ run }: { run: BenchmarkRunDetail }) {
  const isActive = ["queued", "running"].includes(run.manifest.status);
  const hasExecuted = run.trajectory.length > 0 || run.ranking.predictions.length > 0 || run.manifest.status === "completed";
  const completionTitle = run.manifest.status === "completed" ? "LOCALIZATION COMPLETE" : "RUN ENDED";
  return (
    <div className="sessionView">
      <section className="sessionHeader">
        <div>
          <div className="eyebrow">OBSERVABLE AGENT SESSION</div>
          <h2>{run.manifest.agent.display_name}</h2>
          <div className="metadataRow">
            <span>{run.manifest.task_id}</span>
            <span>{run.manifest.agent.model}</span>
            <span>{run.manifest.run_id}</span>
          </div>
        </div>
        <span className={`benchmarkStatus ${run.manifest.status}`}>{benchmarkStatusText(run.manifest.status).toUpperCase()}</span>
      </section>

      {run.trajectory.length === 0 && (
        <EmptyPanel
          icon={Workflow}
          title="No observable trajectory"
          detail="No search, file-open, command, or test-run events have been recorded for this run."
          compact
        />
      )}
      {run.trajectory.map((event) => (
        <section className="sessionEvent" key={`${event.sequence}-${event.type}-${event.target}`}>
          <div className="sessionEventNumber">{String(event.sequence).padStart(2, "0")}</div>
          <div className="sessionEventBody">
            <div className="sessionEventType">
              {iconForSessionEvent(event.type)}
              <span>{sessionEventLabel(event.type)}</span>
            </div>
            <div className="sessionTarget">{event.target || "no target recorded"}</div>
            {event.metadata && Object.keys(event.metadata).length > 0 && (
              <pre className="sessionMetadata">{JSON.stringify(event.metadata, null, 2)}</pre>
            )}
          </div>
        </section>
      ))}

      {!isActive && hasExecuted && (
        <section className="sessionCompletion">
          <div className="sectionTitle">{completionTitle}</div>
          <div className="sessionMetricGrid">
            <MetricPill label="Gold Rank" value={formatNullable(run.evaluation.gold_rank)} />
            <MetricPill label="Hit@5" value={formatPass(run.evaluation.hit_at_5)} />
            <MetricPill label="Hit@10" value={formatPass(run.evaluation.hit_at_10)} />
            <MetricPill label="Tool Calls" value={run.manifest.metrics.tool_call_count} />
            <MetricPill label="Files Read" value={run.manifest.metrics.file_read_count} />
            <MetricPill label="Tests Run" value={run.manifest.metrics.test_run_count} />
          </div>
          <div className="sectionTitle spacingTop">Final Ranked Output</div>
          {run.ranking.predictions.length ? (
            <ol className="rankedOutput">
              {run.ranking.predictions.map((prediction) => (
                <li key={`${prediction.rank}-${prediction.class}-${prediction.method}`}>
                  {prediction.class}::{prediction.method}
                </li>
              ))}
            </ol>
          ) : (
            <div className="mutedText">No Top-10 ranked output was produced.</div>
          )}
        </section>
      )}
    </div>
  );
}

function MetricPill({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="metric sessionMetric">
      <span>{label}</span>
      <strong>{formatUnknown(value)}</strong>
    </div>
  );
}

function sessionEventLabel(type: string) {
  if (type === "submission") return "FINAL SUBMISSION";
  if (type === "tool_result") return "TOOL RESULT";
  if (type === "open_file") return "OPEN FILE";
  if (type === "test_run") return "TEST RUN";
  return benchmarkStatusText(type).toUpperCase();
}

function iconForSessionEvent(type: string) {
  if (type === "search") return <Search size={14} />;
  if (type === "open_file") return <FileCode2 size={14} />;
  if (type === "test_run") return <TestTube2 size={14} />;
  if (type === "command") return <TerminalSquare size={14} />;
  if (type === "tool_result") return <CheckCircle2 size={14} />;
  if (type === "submission") return <CheckCircle2 size={14} />;
  return <Workflow size={14} />;
}

function FilesReadTab({ run }: { run: BenchmarkRunDetail }) {
  return (
    <div className="resultsPane">
      <div className="sessionMetricGrid metricsStrip">
        <MetricPill label="Unique Files" value={run.manifest.metrics.unique_files_read} />
        <MetricPill label="Production Files" value={run.manifest.metrics.production_files_read} />
        <MetricPill label="Test Files" value={run.manifest.metrics.test_files_read} />
        <MetricPill label="First Gold File" value={formatNullable(run.manifest.metrics.first_gold_file_read_position)} />
      </div>
      <div className="tableWrap resultsTableWrap">
      <table className="variantTable benchmarkTable">
        <thead>
          <tr>
            <th>Order</th>
            <th>File</th>
            <th>Type</th>
            <th>Read Count</th>
            <th>Gold File</th>
          </tr>
        </thead>
        <tbody>
          {run.files.length === 0 && (
            <tr>
              <td colSpan={5}>No file reads recorded.</td>
            </tr>
          )}
          {run.files.map((file) => (
            <tr key={file.file}>
              <td>{file.first_read_position}</td>
              <td>{file.file}</td>
              <td>{fileReadTypeLabel(file.file, file.type)}</td>
              <td>{file.read_count}</td>
              <td>{file.contains_gold_method ? <span className="benchmarkStatus validated">GOLD FILE</span> : ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}

function fileReadTypeLabel(filePath: string, type: string) {
  if (type === "production") return "Production";
  if (type === "test") return "Test";
  if (/\b(pom\.xml|build\.xml|build\.gradle|\.properties|\.yaml|\.yml|\.json)$/i.test(filePath)) return "Build/Config";
  return "Other";
}

function TestRunsTab({ run }: { run: BenchmarkRunDetail }) {
  return (
    <div className="resultsPane">
      {run.test_runs.length === 0 && (
        <EmptyPanel icon={TestTube2} title="No test runs" detail="Only actual observed test executions are shown here." />
      )}
      {run.test_runs.length > 0 && (
        <div className="tableWrap resultsTableWrap">
          <table className="variantTable benchmarkTable">
            <thead>
              <tr>
                <th>Run</th>
                <th>Test</th>
                <th>Status</th>
                <th>Duration</th>
              </tr>
            </thead>
            <tbody>
              {run.test_runs.map((testRun) => (
                <tr key={`${testRun.test_id}-${testRun.run_number}`}>
                  <td>{testRun.run_number}</td>
                  <td>{testRun.test_id}</td>
                  <td><span className={`benchmarkStatus ${testRun.status}`}>{testRun.status}</span></td>
                  <td>{testRun.duration_ms ? `${testRun.duration_ms} ms` : "n/a"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {run.test_runs.map((testRun) => (
        testRun.output ? (
          <details className="testOutputDetails" key={`${testRun.test_id}-${testRun.run_number}-output`}>
            <summary>{testRun.test_id} stdout/stderr</summary>
            <div className="outputBlock">{testRun.output}</div>
          </details>
        ) : null
      ))}
    </div>
  );
}

function CommandsTab({ run }: { run: BenchmarkRunDetail }) {
  const blocks = parseCommandBlocks(run.commands);
  return (
    <div className="terminalPane">
      {!run.commands.trim() && <EmptyPanel icon={TerminalSquare} title="No commands recorded" detail="Command activity appears only when the runner emits observable command events." />}
      {blocks.map((block, index) => (
        <section className="terminalCommand" key={`${index}-${block.command}`}>
          <div className="terminalPrompt">$ {block.command || "command not recorded"}</div>
          {block.cwd && <div className="terminalMeta">cwd: {block.cwd}</div>}
          {block.exitCode && <div className="terminalMeta">exit code: {block.exitCode}</div>}
          {block.output && (
            <details>
              <summary>output</summary>
              <pre>{block.output}</pre>
            </details>
          )}
        </section>
      ))}
    </div>
  );
}

function parseCommandBlocks(commands: string) {
  const lines = commands.split(/\r?\n/);
  const blocks: Array<{ command: string; cwd: string; exitCode: string; output: string }> = [];
  let current: { command: string; cwd: string; exitCode: string; output: string } | null = null;
  for (const line of lines) {
    if (line.startsWith("$ ")) {
      if (current) blocks.push(current);
      current = { command: line.slice(2), cwd: "", exitCode: "", output: "" };
    } else if (current && line.startsWith("cwd:")) {
      current.cwd = line.slice(4).trim();
    } else if (current && line.startsWith("exit_code:")) {
      current.exitCode = line.slice("exit_code:".length).trim();
    } else if (current && line.trim()) {
      current.output += `${line}\n`;
    }
  }
  if (current) blocks.push(current);
  return blocks.length ? blocks : commands.trim() ? [{ command: "recorded command log", cwd: "", exitCode: "", output: commands }] : [];
}

function RawOutputTab({ run }: { run: BenchmarkRunDetail }) {
  const debugPayload = {
    ranking_parse_status: run.ranking.parse_status,
    validation_errors: run.ranking.validation_errors ?? [],
    normalized_trajectory: run.trajectory,
  };
  return (
    <div className="rawOutputGrid">
      <section className="rawOutputSection">
        <div className="sectionTitle">Raw mini-swe-agent Output</div>
        <EditorPane language="plaintext" value={run.raw_output || "No raw mini-swe-agent output recorded."} />
      </section>
      <section className="rawOutputSection">
        <div className="sectionTitle">Normalized Trajectory & Parse State</div>
        <EditorPane language="json" value={JSON.stringify(debugPayload, null, 2)} />
      </section>
    </div>
  );
}

function ComparisonTab({
  pair,
  agents,
  depthLadder,
}: {
  pair: PairComparisonResponse | null;
  agents: AgentComparisonResponse | null;
  depthLadder: ChartDepthLadderResponse | null;
}) {
  const variantHeader = pair?.variant_run_id?.includes("L10") ? "L10" : "Variant";
  return (
    <div className="testGrid">
      <section className="testRow">
        <div className="sectionTitle">Original vs Variant</div>
        {pair?.rows.length ? (
          <ComparisonTable
            rows={pair.rows.map((row) => [
              row.metric,
              row.metric === "Duration" ? formatDurationMs(row.original as number | null) : row.original,
              row.metric === "Duration" ? formatDurationMs(row.variant as number | null) : row.variant,
            ])}
            headers={["Metric", "Original", variantHeader]}
          />
        ) : (
          <div className="mutedText">{pair?.message ?? "No matching original/variant pair selected yet."}</div>
        )}
        {pair?.file_overlap && (
          <div className="inlineNotice comparisonFiles">
            <div>File overlap Jaccard: {formatNullable(pair.file_overlap.jaccard)}</div>
            <div>Shared: {pair.file_overlap.shared_files.join(", ") || "none"}</div>
            <div>Original only: {pair.file_overlap.only_a?.join(", ") || "none"}</div>
            <div>Variant only: {pair.file_overlap.only_b?.join(", ") || "none"}</div>
          </div>
        )}
      </section>

      <section className="testRow">
        <div className="sectionTitle">Agent vs Agent</div>
        {agents?.rows.length ? (
          <ComparisonTable
            rows={agents.rows.map((row) => [row.agent, row.gold_rank, row.hit_at_5, row.hit_at_10, row.files_read, row.tool_calls])}
            headers={["Agent", "Gold Rank", "Hit@5", "Hit@10", "Files", "Tool Calls"]}
          />
        ) : (
          <div className="mutedText">No multi-agent comparison for this task yet.</div>
        )}
        {agents?.overlaps.map((overlap) => (
          <div className="inlineNotice" key={overlap.pair}>
            {overlap.pair}: {formatNullable(overlap.jaccard)} · {overlap.shared_files.join(", ") || "no shared files"}
          </div>
        ))}
      </section>

      <section className="testRow">
        <div className="sectionTitle">Chart-1 Reasoning Depth Ladder</div>
        {depthLadder ? <DepthLadderSection ladder={depthLadder} /> : <div className="mutedText">Depth ladder is loading.</div>}
      </section>
    </div>
  );
}

function ComparisonTable({ headers, rows }: { headers: string[]; rows: unknown[][] }) {
  return (
    <div className="tableWrap compactTableWrap">
      <table className="variantTable benchmarkTable">
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, index) => (
                <td key={`${rowIndex}-${index}`}>{formatUnknown(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AgentProfileModal({
  state,
  busy,
  onChange,
  onClose,
  onCreate,
}: {
  state: AgentModalState;
  busy: boolean;
  onChange: (state: AgentModalState) => void;
  onClose: () => void;
  onCreate: () => void;
}) {
  return (
    <div className="modalBackdrop" role="presentation">
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="add-agent-title">
        <div className="modalHeader">
          <div>
            <div className="eyebrow">BACKEND PROFILE</div>
            <h2 id="add-agent-title">Add Agent</h2>
          </div>
          <button className="iconButton" onClick={onClose} aria-label="Close">
            <X size={17} />
          </button>
        </div>

        <div className="fieldGroup">
          <label htmlFor="agent-framework">Framework</label>
          <select
            id="agent-framework"
            className="selectControl"
            value={state.framework}
            onChange={(event) => onChange({ ...state, framework: event.target.value })}
          >
            <option>mini-swe-agent</option>
          </select>
        </div>
        <div className="fieldGroup">
          <label htmlFor="agent-provider">Provider</label>
          <select
            id="agent-provider"
            className="selectControl"
            value={state.provider}
            onChange={(event) => onChange({ ...state, provider: event.target.value })}
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Claude</option>
            <option value="moonshot">Kimi</option>
          </select>
        </div>
        <div className="fieldGroup">
          <label htmlFor="agent-model">Model ID</label>
          <input
            id="agent-model"
            className="textInput"
            value={state.model}
            onChange={(event) => onChange({ ...state, model: event.target.value })}
          />
        </div>
        <div className="fieldGroup">
          <label htmlFor="agent-display">Display Name</label>
          <input
            id="agent-display"
            className="textInput"
            value={state.display_name}
            onChange={(event) => onChange({ ...state, display_name: event.target.value })}
          />
        </div>
        <div className="fieldRow">
          <NumberInput label="Max Tool Calls" value={state.defaults.max_tool_calls} onChange={(value) => onChange({ ...state, defaults: { ...state.defaults, max_tool_calls: value } })} />
          <NumberInput label="Max Test Runs" value={state.defaults.max_test_runs} onChange={(value) => onChange({ ...state, defaults: { ...state.defaults, max_test_runs: value } })} />
        </div>
        <div className="fieldGroup">
          <NumberInput label="Timeout" value={state.defaults.timeout_seconds} onChange={(value) => onChange({ ...state, defaults: { ...state.defaults, timeout_seconds: value } })} />
        </div>

        <div className="modalFooter">
          <button className="secondaryButton" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button className="primaryButton" onClick={onCreate} disabled={busy}>
            {busy ? <Loader2 className="spin" size={16} /> : <Plus size={16} />}
            Save Agent
          </button>
        </div>
      </div>
    </div>
  );
}

function formatNullable(value: unknown) {
  if (value == null) return "n/a";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(2);
  return String(value);
}

function formatPass(value: boolean | null) {
  if (value == null) return "n/a";
  return value ? "PASS" : "FAIL";
}

function formatUnknown(value: unknown) {
  if (typeof value === "boolean") return value ? "PASS" : "FAIL";
  return formatNullable(value);
}

function formatDepthValue(value: unknown, row?: DepthLadderRow) {
  if (row?.status !== "completed") return missingDepthText(row);
  return formatNullable(value);
}

function formatDepthPass(value: boolean | null, row?: DepthLadderRow) {
  if (row?.status !== "completed") return missingDepthText(row);
  return formatPass(value);
}

function missingDepthText(row?: DepthLadderRow) {
  if (!row) return "n/a";
  if (row.status === "not_generated") return "Not generated";
  if (row.status === "not_run") return "Not run";
  if (row.status === "timeout") return "Timeout";
  if (row.status && row.status !== "completed") return benchmarkStatusText(row.status);
  return "n/a";
}

function formatDurationMs(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) return "n/a";
  return `${(value / 1000).toFixed(1)}s`;
}

function commandDurationMs(commands: string) {
  const matches = Array.from(commands.matchAll(/^duration_ms:\s*(\d+)\s*$/gm));
  const last = matches[matches.length - 1];
  const value = Number(last?.[1]);
  return Number.isFinite(value) ? value : null;
}

function benchmarkDurationText(run: BenchmarkRunDetail) {
  return formatDurationMs(run.manifest.metrics.duration_ms ?? commandDurationMs(run.commands));
}

function WorkflowPanel({
  bug,
  variant,
  busyId,
  onContinue,
}: {
  bug: BugDetail | null;
  variant: VariantRun | null;
  busyId: string;
  onContinue: (id: string) => void;
}) {
  const syntheticAnalysisStep: WorkflowStep | null =
    bug && !variant
      ? {
          id: "agent-1",
          title: "Agent 1: Original Bug Analyst",
          status: bug.analysis?.exists ? "complete" : "pending",
          artifactNames: ["agent1_report.md"],
        }
      : null;
  const workflow = variant?.workflow ?? (syntheticAnalysisStep ? [syntheticAnalysisStep] : []);
  const currentStep = workflow.find((step) => step.status === "running") ?? workflow.find((step) => step.status === "pending") ?? null;
  const artifacts =
    variant?.artifacts ??
    (bug
      ? [
          {
            name: "agent1_report.md",
            kind: "report" as const,
            status: bug.analysis?.exists ? ("ready" as const) : ("queued" as const),
            path: bug.analysis?.path,
          },
        ]
      : []);

  return (
    <aside className="rightPanel">
      <div className="rightPanelHeader">
        <PanelRight size={16} />
        <span>Workflow Panel</span>
      </div>
      {!bug && !variant && (
        <EmptyPanel
          icon={Workflow}
          title="No workflow run"
          detail="Create or select a variant run to see Agent 1-5 progress outside the chat log."
          compact
        />
      )}
      {(bug || variant) && (
        <>
          <div className="runHeader">
            <div className="runId">{variant?.variant_id ?? `${bug?.name ?? "Bug"} analysis`}</div>
            <div className="runMeta">{variant ? `${variant.level} · ${variant.dimension}` : "Agent 1 artifact status"}</div>
            {variant && (
              <button
                className="secondaryButton fullWidth"
                onClick={() => onContinue(variant.id)}
                disabled={busyId === variant.id || variant.status === "validated"}
              >
                <Play size={14} />
                {variant.status === "validated" ? "Workflow complete" : busyId === variant.id ? "Running agent..." : "Run next agent"}
              </button>
            )}
          </div>

          <div className="currentStep">
            <Clock3 size={14} />
            <span>{currentStep ? `Current: ${currentStep.title}` : "Current: artifacts complete"}</span>
          </div>

          <div className="stepper">
            {workflow.map((step) => {
              const Icon = workflowStatusIcon[step.status];
              return (
                <div className={`step ${step.status}`} key={step.id}>
                  <Icon size={16} className={step.status === "running" ? "spin" : ""} />
                  <div>
                    <div className="stepTitle">{step.title}</div>
                    <div className="stepMeta">{step.status}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      <div className="rightPanelHeader artifactsTitle">
        <FileText size={16} />
        <span>Artifacts Panel</span>
      </div>
      {artifacts.length === 0 ? (
        <EmptyPanel
          icon={FileText}
          title="No artifacts yet"
          detail="Agent reports, candidate notes, patches, and validation logs will appear here."
          compact
        />
      ) : (
        <div className="artifactList">
          {artifacts.map((artifact) => (
            <button className="artifactItem" key={artifact.name}>
              <span className="artifactName">
                {artifact.kind === "patch" ? <FileDiff size={14} /> : <FileText size={14} />}
                {artifact.name}
              </span>
              <span className={`artifactStatus ${artifact.status}`}>{artifact.status}</span>
            </button>
          ))}
        </div>
      )}
    </aside>
  );
}

function ValidationPills({ validation }: { validation: ValidationStatus }) {
  return (
    <div className="validationPills" aria-label="Validation status">
      <span className={`validationPill ${validation.baselinePass}`}>baseline {validationText[validation.baselinePass]}</span>
      <span className={`validationPill ${validation.variantFail}`}>variant {validationText[validation.variantFail]}</span>
      <span className={`validationPill ${validation.deterministicRuns}`}>3 runs {validationText[validation.deterministicRuns]}</span>
    </div>
  );
}

function EditorPane({ language, value }: { language: string; value: string }) {
  return (
    <div className="editorShell">
      <Editor
        height="100%"
        defaultLanguage={language}
        language={language}
        value={value}
        theme="vs-dark"
        loading={<InlineState icon={Loader2} text="Loading editor..." spinning />}
        options={{
          readOnly: true,
          minimap: { enabled: false },
          fontSize: 12,
          lineHeight: 19,
          scrollBeyondLastLine: false,
          wordWrap: "off",
          automaticLayout: true,
          renderLineHighlight: "all",
          padding: { top: 10, bottom: 10 },
        }}
      />
    </div>
  );
}

function CreateVariantModal({
  state,
  previewPath,
  busy,
  useMockFallback,
  onChange,
  onClose,
  onCreate,
}: {
  state: CreateVariantModalState;
  previewPath: string;
  busy: boolean;
  useMockFallback: boolean;
  onChange: (state: CreateVariantModalState) => void;
  onClose: () => void;
  onCreate: () => void;
}) {
  return (
    <div className="modalBackdrop" role="presentation">
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="create-variant-title">
        <div className="modalHeader">
          <div>
            <div className="eyebrow">{useMockFallback ? "MOCK FALLBACK RUN" : "LOCAL ARTIFACT RUN"}</div>
            <h2 id="create-variant-title">Create Variant</h2>
          </div>
          <button className="iconButton" onClick={onClose} aria-label="Close">
            <X size={17} />
          </button>
        </div>

        <div className="fieldGroup">
          <label>Target level</label>
          <div className="segmentGroup">
            {levels.map((level) => (
              <button
                key={level}
                className={`segmentButton ${state.level === level ? "active" : ""}`}
                onClick={() => onChange({ ...state, level })}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        <div className="fieldGroup">
          <label htmlFor="dimension">Variant dimension</label>
          <select
            id="dimension"
            className="selectControl"
            value={state.dimension}
            onChange={(event) => onChange({ ...state, dimension: event.target.value as VariantDimension })}
          >
            {dimensions.map((dimension) => (
              <option key={dimension}>{dimension}</option>
            ))}
          </select>
        </div>

        <div className="fieldGroup">
          <label>Output folder preview</label>
          <div className="pathPreview">{previewPath}</div>
        </div>

        <div className="fieldRow">
          <label className="toggleRow">
            <input
              type="checkbox"
              checked={state.humanCheckpoint}
              onChange={(event) => onChange({ ...state, humanCheckpoint: event.target.checked })}
            />
            <span>Human checkpoint</span>
          </label>
          <label className="numberField">
            <span>Candidate count</span>
            <input
              type="number"
              min={1}
              max={8}
              value={state.candidateCount}
              onChange={(event) =>
                onChange({
                  ...state,
                  candidateCount: Math.max(1, Math.min(8, Number(event.target.value) || 1)),
                })
              }
            />
          </label>
        </div>

        <div className="modalFooter">
          <button className="secondaryButton" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button className="primaryButton" onClick={onCreate} disabled={busy}>
            {busy ? <Loader2 className="spin" size={16} /> : <Plus size={16} />}
            Create Variant
          </button>
        </div>
      </div>
    </div>
  );
}

function EmptyPanel({
  icon: Icon,
  title,
  detail,
  spinning = false,
  compact = false,
  children,
}: {
  icon: LucideIcon;
  title: string;
  detail: string;
  spinning?: boolean;
  compact?: boolean;
  children?: ReactNode;
}) {
  return (
    <div className={`emptyPanel ${compact ? "compact" : ""}`}>
      <Icon size={compact ? 22 : 30} className={spinning ? "spin" : ""} />
      <div className="emptyTitle">{title}</div>
      <div className="emptyDetail">{detail}</div>
      {children}
    </div>
  );
}

function InlineState({
  icon: Icon,
  text,
  spinning = false,
}: {
  icon: LucideIcon;
  text: string;
  spinning?: boolean;
}) {
  return (
    <div className="inlineState">
      <Icon size={15} className={spinning ? "spin" : ""} />
      <span>{text}</span>
    </div>
  );
}

export default App;
