#!/usr/bin/env python
"""Build the trajectory audit, infrastructure accounting, cost accounting, manifest and README.
Usage: build_pilot_meta.py"""
import json, os, glob, re, datetime, collections, hashlib, statistics as st

SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
R = f"{SP}/anthropic-pilot-v1"; D = f"{R}/diagnostic"; A = f"{R}/analysis"
rows = json.load(open(f"{A}/per_run/pilot_run_metrics.json"))
res = json.load(open(f"{R}/claude_pilot_results.json"))
CLAUDE, GPT = "claude-opus-5-5", "gpt-5.6"
cl = [r for r in rows if r["model"] == CLAUDE]
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def strip_cd(c):
    m = re.match(r"^cd\s+\S+\s*(?:&&|;)\s*(.*)$", c.strip(), re.S)
    return m.group(1).strip() if m else c.strip()


def commands_of(rd):
    try:
        t = json.load(open(f"{rd}/mini-swe-agent.traj.json"))
    except Exception:
        return []
    out = []
    for m in t.get("messages") or []:
        if m.get("role") == "assistant":
            for a in ((m.get("extra") or {}).get("actions") or []):
                if a.get("command"):
                    out.append(strip_cd(a["command"]))
                elif a.get("tool"):
                    out.append("SUBMIT:" + str(a.get("tool")))
    return out


# ---------------------------------------------------------------- CLAUDE_TRAJECTORY_AUDIT.md
def classify(c):
    if c.startswith("SUBMIT:"):
        return "submit"
    if re.search(r"\bdefects4j test\b", c):
        return "run test"
    if re.search(r"\b(grep|rg)\b", c):
        return "search"
    if re.search(r"\b(sed|cat|head|tail|awk|nl)\b", c):
        return "read"
    if re.search(r"\b(find|ls)\b", c):
        return "list"
    return "other"


T = ["# Claude trajectory audit", "",
     "What Claude actually did, read from the recorded commands and tool outputs of every completed pilot run.",
     "Reasoning traces are never read. Command classes: read (sed/cat/head/tail/awk), search (grep/rg),",
     "list (find/ls), run test, submit.", "",
     "## Command mix per arm", "",
     "| Unit | Arm | runs | commands per run | read | search | list | run test | submit | other |",
     "|" + "---|" * 10]
groups = collections.OrderedDict()
for r in cl:
    groups.setdefault((r["unit"], r["arm"]), []).append(r)
for (unit, arm), rs in groups.items():
    counts = collections.Counter()
    per_run = []
    for r in rs:
        rd = f"{R}/benchmark_runs/mini-swe-claude/{r['variant_id']}/{r['run']}"
        cs = commands_of(rd)
        per_run.append(len(cs))
        for c in cs:
            counts[classify(c)] += 1
    n = len(rs)
    T.append(f"| `{unit}` | {arm} | {n} | {round(st.mean(per_run), 1) if per_run else '-'} | " +
             " | ".join(str(counts.get(k, 0)) for k in ("read", "search", "list", "run test", "submit", "other")) + " |")
T += ["", "## Representative trajectory per arm", "",
      "The first completed run of each arm, commands in order, truncated to 110 characters.", ""]
for (unit, arm), rs in groups.items():
    r = next((x for x in rs if x["status"] == "completed"), None)
    if not r:
        continue
    rd = f"{R}/benchmark_runs/mini-swe-claude/{r['variant_id']}/{r['run']}"
    T.append(f"**{unit} / {arm} / {r['run']}** (gold rank {r['gold_rank']}, first gold at step {r['first_gold_step']}, "
             f"{r['tool_calls']} tool calls)")
    T.append("")
    T.append("```")
    for i, c in enumerate(commands_of(rd), 1):
        T.append(f"{i:2d}. {c[:110]}")
    T.append("```")
    T.append("")
T += ["## Chain traversal", "",
      "| Unit | Arm | runs | hops exposed (mean of 5) | traversal order seen | facade seen first | direct gold-name search | lexical shortcut |",
      "|" + "---|" * 8]
for (unit, arm), rs in groups.items():
    comp = [r for r in rs if r["status"] == "completed"]
    if not comp or arm == "CONTROL":
        continue
    orders = collections.Counter(tuple(r["chain_traversal_in_order"]) for r in comp)
    fac_first = sum(1 for r in comp if r["first_facade_step"] and (not r["first_gold_step"] or r["first_facade_step"] <= r["first_gold_step"]))
    T.append(f"| `{unit}` | {arm} | {len(comp)} | {round(st.mean([r['hops_exposed'] for r in comp]), 1)} | "
             f"{'; '.join('>'.join(o) + f' x{c}' for o, c in orders.items())[:90]} | {fac_first}/{len(comp)} | "
             f"{sum(1 for r in comp if r['direct_gold_search_step'])}/{len(comp)} | "
             f"{sum(1 for r in comp if r['lexical_shortcut'])}/{len(comp)} |")
open(f"{R}/CLAUDE_TRAJECTORY_AUDIT.md", "w").write("\n".join(T) + "\n")

# ---------------------------------------------------------------- INFRASTRUCTURE_ACCOUNTING.md
probes = [l.strip() for l in open(f"{D}/health_gate_claude.log")] if os.path.exists(f"{D}/health_gate_claude.log") else []
fast = sum(1 for l in probes if "fast_pass" in l)
slow = sum(1 for l in probes if "slow_or_anomalous" in l)
hung = sum(1 for l in probes if "hang_killed" in l)
block = [json.loads(l) for l in open(f"{D}/block_claude.log")] if os.path.exists(f"{D}/block_claude.log") else []
state = json.load(open(f"{D}/driver_state_claude.json")) if os.path.exists(f"{D}/driver_state_claude.json") else {}
I = ["# Infrastructure accounting", "",
     "| Item | Value |", "|---|---|",
     f"| Claude slots attempted | {len(cl)} |",
     f"| Claude runs completed with a valid ranking | {sum(1 for r in cl if r['status'] == 'completed' and r['gold_rank'] is not None)} |",
     f"| Infrastructure-affected slots (preserved, never replaced) | {sum(1 for r in cl if r['status'] != 'completed')} |",
     f"| Bounded Anthropic probes run | {len(probes)} |",
     f"| Probe verdicts | {fast} fast_pass, {slow} slow_or_anomalous, {hung} hang_killed |",
     f"| Driver halts | {'none' if not state.get('halted') else state['halted'].get('reason')} |",
     f"| Protocol identity asserted per run | {sum(1 for b in block if b.get('protocol_identity_ok'))}/{len(block)} |",
     f"| Source integrity ok per run | {sum(1 for b in block if b.get('source_integrity_ok'))}/{len(block)} |",
     f"| Runs with any contamination | {sum(1 for b in block if b.get('contaminated'))} |",
     f"| Out-of-workspace flagged calls (benign path echoes) | {sum(b.get('oow_flagged_calls') or 0 for b in block)} |",
     "", "## Protected trees, verified after the block", "",
     "| Tree | Files checked | Result |", "|---|---|---|"]
for name, root, manifest in (("frozen GPT-5.6 run artifacts", f"{SP}/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6", f"{D}/frozen_runs_before.txt"),
                             ("frozen GPT-5.6 server code tree", f"{SP}/diagnostic-noncanonical-v3/variant-lab", f"{D}/frozen_server_tree_before.txt"),
                             ("variant packages (read-only via symlink)", f"{SP}/diagnostic-noncanonical-v3/new_bug_variants", f"{D}/variant_packages_before.txt")):
    import subprocess
    p = subprocess.run(["shasum", "-a", "256", "-c", manifest, "--quiet"], cwd=root, capture_output=True, text=True)
    nfiles = sum(1 for _ in open(manifest))
    I.append(f"| {name} | {nfiles} | {'unchanged' if p.returncode == 0 else 'CHANGED: ' + (p.stdout + p.stderr)[-120:]} |")
I += ["", "## Interpretation caveat for any future Anthropic failure", "",
      "A provider failure on the Claude arm can surface as `timeout` rather than `provider_error`: the agent's",
      "litellm wrapper does not abort on BadRequest/RateLimit/InternalServer/APIConnection errors, so it retries",
      "with exponential backoff that can outlast the harness's 300 s SIGTERM, and the harness tests `timed_out`",
      "first. No run in this pilot failed, so the distinction never had to be drawn; a future block should read a",
      "`timeout` run's preserved raw output before classifying it.", "",
      "## Incidents", "",
      "1. **The user's frozen GPT-5.6 server process was stopped by an over-broad process-kill pattern.** Full",
      "   record in `diagnostic/INCIDENT_frozen_server_process.md`. No artifact was affected; all three protected",
      "   trees verify unchanged above. The process must be restarted by the user because its OpenAI credential",
      "   lives only in that process environment. The OpenAI account is out of credits in any case.",
      "2. **12 pre-hardening runs were discarded and preserved.** They were made before the pilot server's",
      "   provider environment was pinned explicitly (endpoint and Claude Code variables). They are kept under",
      "   `pre_hardening/` and excluded from every results table; the whole set was discarded regardless of",
      "   outcome, so no selection was introduced.", "",
      "## Isolation properties of the pilot harness", "",
      "- `repoRoot` resolves to `anthropic-pilot-v1`, so Claude runs write only into this root.",
      "- Variant packages are reached read-only through a symlink to the frozen root, so both models score",
      "  byte-identical artifacts.",
      "- The pilot server holds no OpenAI credential and reports `mini-swe-gpt56` as `not_configured`, so it",
      "  cannot spend OpenAI money even by mistake.",
      "- The patched copy differs from the frozen tree in exactly 2 files and 4 edits; both trees pass the same",
      "  198-test server suite with identical per-test outcomes."]
open(f"{R}/INFRASTRUCTURE_ACCOUNTING.md", "w").write("\n".join(I) + "\n")

# ---------------------------------------------------------------- COST_ACCOUNTING.md
pre = glob.glob(f"{R}/pre_hardening/benchmark_runs_mini-swe-claude/*/run-*/mini-swe-agent.traj.json")
pre_cost = 0.0
for p in pre:
    t = json.load(open(p)); pre_cost += ((t.get("info") or {}).get("model_stats") or {}).get("instance_cost") or 0
probe_costs = []
for p in glob.glob(f"{D}/probe_claude_*.json"):
    try:
        d = json.load(open(p)); c = ((d.get("model_stats") or {}) or {}).get("instance_cost")
        if c:
            probe_costs.append(c)
    except Exception:
        pass
pilot_cost = sum(r["cost_usd"] or 0 for r in cl)
C = ["# Cost accounting", "",
     "Anthropic and OpenAI accounting are kept separate. Every figure below is the provider's own reported",
     f"`instance_cost` from litellm, read out of each run's trajectory. Claude and GPT-5.6 have identical list",
     "prices in litellm's registry (4.00 USD per million input tokens, 20.00 USD per million output), so spend",
     "differences reflect token usage, not price.", "",
     "| Item | Runs | USD |", "|---|---|---|",
     f"| Claude pilot block (counted as experiment data) | {len(cl)} | {pilot_cost:.4f} |",
     f"| Pre-hardening Claude runs (discarded, preserved) | {len(pre)} | {pre_cost:.4f} |",
     f"| Bounded health probes with a reported cost | {len(probe_costs)} | {sum(probe_costs):.4f} |",
     f"| **Total Anthropic spend this session** | {len(cl) + len(pre) + len(probe_costs)} | **{pilot_cost + pre_cost + sum(probe_costs):.4f}** |",
     "| OpenAI spend this session | 0 | 0.0000 (no OpenAI credential on the pilot server; the account is out of credits) |",
     "", "## Per-arm Claude spend", "", "| Unit | Arm | completed | USD | USD per completed run |", "|---|---|---|---|---|"]
for k, v in res["per_arm"].items():
    m, unit, arm = k.split("|")
    if m != CLAUDE or not v["attempted"]:
        continue
    per = (v["cost_usd"] / v["completed"]) if v["completed"] else None
    C.append(f"| `{unit}` | {arm} | {v['completed']} | {v['cost_usd']:.4f} | {('%.4f' % per) if per else '-'} |")
C += ["", "## Caveat on comparing cost with GPT-5.6", "",
      "mini-swe-agent automatically enables Anthropic prompt caching for any model whose name contains",
      "`claude`, `opus`, `sonnet` or `anthropic` (`minisweagent/models/__init__.py:56`). The GPT-5.6 runs had no",
      "equivalent. Claude's reported spend therefore benefits from cache reads that the GPT-5.6 figures never",
      "had, so the two spend columns are not a clean per-task price comparison. Token counts and tool calls are",
      "the comparable quantities."]
open(f"{R}/COST_ACCOUNTING.md", "w").write("\n".join(C) + "\n")
print("wrote CLAUDE_TRAJECTORY_AUDIT.md, INFRASTRUCTURE_ACCOUNTING.md, COST_ACCOUNTING.md")
print(f"  claude pilot cost {pilot_cost:.4f} | pre-hardening {pre_cost:.4f} | probes {sum(probe_costs):.4f}")
