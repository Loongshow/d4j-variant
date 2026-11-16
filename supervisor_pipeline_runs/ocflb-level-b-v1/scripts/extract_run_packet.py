#!/usr/bin/env python
"""Compact grading packet for one run: pair context, submission + evidence chain, and the command/output sequence (outputs truncated).
Usage: extract_run_packet.py <run_metrics_row_index|variant/run> ... writes analysis/mechanism/packets/<model>__<variant>__<run>.md for every answered wrong run (default) or the given ones."""
import json, os, sys, glob, re
L = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1"; OUT = f"{L}/analysis/mechanism/packets"; os.makedirs(OUT, exist_ok=True)
rows = json.load(open(f"{L}/analysis/per_run/run_metrics.json")); pairs = {json.load(open(p))["pair_id"]: json.load(open(p)) for p in glob.glob(f"{L}/projects/*/bug-*/pair.json")}
sel = [r for r in rows if r["status"] == "completed" and r["gold_rank"] != 1] if len(sys.argv) < 2 else [r for r in rows if f"{r['variant_id']}/{r['run']}" in sys.argv[1:]]
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
written = []
for r in sel:
    rd = f"{L}/models/{r['server']}/benchmark_runs/mini-swe-claude/{r['variant_id']}/{r['run']}"; spec = pairs[r["pair_id"]]; CH = spec["chain"]; A = spec["arms"][r["arm"]]
    traj = rj(f"{rd}/mini-swe-agent.traj.json"); rk = rj(f"{rd}/ranking.json"); ss = rk.get("structured_submission") or {}
    cmds, outs = [], []
    for m in traj.get("messages") or []:
        if m.get("role") == "assistant":
            for a in ((m.get("extra") or {}).get("actions") or []): cmds.append(a.get("command") or "TOOL:" + str(a.get("tool")))
        elif m.get("role") == "tool": outs.append(str((m.get("extra") or {}).get("raw_output") or m.get("content") or ""))
    strip = lambda c: re.sub(r"^cd\s+\S+\s*(?:&&|;)\s*", "", c.strip(), flags=re.S)
    P = [f"# Run packet: {r['model']} / {r['variant_id']} / {r['run']}", "", f"Pair {r['pair_id']} ({spec['family']}); arm {r['arm']}; gold = {A['gold']['class']}#{A['gold']['method']} (role {r['gold_role']}).",
         f"Chain: facade {CH['facade']['class'].split('.')[-1]}.{CH['facade']['method']} -> " + " -> ".join(f"{h} {CH[h]['class'].split('.')[-1]}.{CH[h]['method']}" for h in ("H1", "H2", "H3", "H4", "H5")) + ".",
         f"Convention (decided by the repository): {spec.get('convention')}", f"External ownership evidence: production second caller {spec.get('second_caller')}; external tests {spec.get('external_evidence_tests')}; unit pin {spec['pin_test']}.",
         f"Outcome: gold rank {r['gold_rank']}; submitted top-10: {r['submitted_top10']}; automatic class {r['classification']} / {r['evidence_subclass']}; tool calls {r['tool_calls']}; external evidence retrieved (strict) {r['external_evidence_retrieved']}, exposed (loose) {r['external_evidence_exposed']}, pin opened {r['pin_retrieved']}, cited in rationale {r['external_evidence_cited']}.", "",
         "## Submitted evidence chain (the agent's own rationale)", "", "```json", json.dumps(ss.get("evidence_chain") or [], indent=1)[:6000], "```", "", "## Trajectory (command -> output, outputs truncated to 700 chars)", ""]
    for i, c in enumerate(cmds):
        o = outs[i] if i < len(outs) else ""
        P.append(f"### step {i + 1}\n```\n{strip(c)[:600]}\n```\noutput:\n```\n{o[:700]}\n```\n")
    name = f"{r['model']}__{r['variant_id']}__{r['run']}.md"; open(f"{OUT}/{name}", "w").write("\n".join(P)); written.append(name)
print(len(written), "packets:", written)
