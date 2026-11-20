"""W72 (exploratory, post hoc): draw the stratified annotation sample and write blind per-run views.
Strata (fixed before annotation): D = every run where the frozen text matcher and the location-bound re-check disagree;
A1 = shifted, both exposed (14, one run per instance); A2 = gold first, both exposed (8); A3 = neither exposed (5 shifted + 3 gold first).
Seeded (random.Random(72)); opaque ids R01..R60 in shuffled order; the key (stratum, labels) goes to sample_key.csv, never to annotators.
Views reuse mx_traj_view.py's exclusions: no system prompt, no content part whose type mentions reason/think/encrypt, never
raw_agent_output.txt, probe or credential files. Output: main-run/analysis/exposure_check/annotation/."""
import csv, json, os, random, re, collections
HERE = os.path.dirname(os.path.abspath(__file__)); WM = os.path.dirname(HERE); MR = f"{WM}/main-run"; EC = f"{MR}/analysis/exposure_check"
OUT = f"{EC}/annotation"; os.makedirs(f"{OUT}/views", exist_ok=True)
KEY = json.load(open(f"{WM}/review/VARIANT_KEY.json")); AGENT = "mini-swe-agent-openai-gpt-5-5"
PROV = {}
for f in ("INSTANCE_PROVENANCE.csv", "INSTANCE_PROVENANCE_C10I.csv"):
    for r in csv.DictReader(open(f"{MR}/{f}")): PROV[r["instance_id"]] = r
HIDE = ("reason", "think", "encrypt")
def txt(c):
    if isinstance(c, str): return c
    if isinstance(c, list): return " ".join(x.get("text", "") for x in c if isinstance(x, dict) and not any(h in str(x.get("type", "")).lower() for h in HIDE))
    return ""
rows = list(csv.DictReader(open(f"{EC}/exposure_recheck.csv")))
rng = random.Random(72)
def pick(cands, n):
    by = collections.defaultdict(list)
    for r in cands: by[r["instance_id"]].append(r)
    inst = sorted(by); rng.shuffle(inst); return [rng.choice(by[i]) for i in inst[:n]]
D = [r for r in rows if r["frozen_gold_exposed"] != r["location_bound_exposed"]]
both = lambda r, v: r["frozen_gold_exposed"] == v and r["location_bound_exposed"] == v
A1 = pick([r for r in rows if both(r, "True") and r["shift"] == "True"], 14)
A2 = pick([r for r in rows if both(r, "True") and r["failure_mode"] == "GOLD_FIRST"], 8)
A3 = pick([r for r in rows if both(r, "False") and r["shift"] == "True"], 5) + pick([r for r in rows if both(r, "False") and r["failure_mode"] == "GOLD_FIRST"], 3)
sample = [("D", r) for r in D] + [("A1", r) for r in A1] + [("A2", r) for r in A2] + [("A3", r) for r in A3]
rng.shuffle(sample)
key = []
for n, (stratum, r) in enumerate(sample, 1):
    rid = f"R{n:02d}"; V = r["variant_id"]; rd = f"{WM}/models/w55/benchmark_runs/{AGENT}/{V}/{r['run']}"; K = KEY[V]; P = PROV[r["instance_id"]]
    d = f"{OUT}/views/{rid}"; os.makedirs(d, exist_ok=True)
    sub = json.load(open(f"{rd}/fault-localization-submission.json")); traj = json.load(open(f"{rd}/mini-swe-agent.traj.json"))
    A = [f"# Run {rid}: agent's visible text, commands and final submission", "", "Tool outputs are in tool_outputs.txt, referred to by their number.", ""]
    O = [f"# Run {rid}: tool outputs (complete)", ""]
    step = k = 0
    for m in traj.get("messages", []):
        role = m.get("role")
        if role == "system": continue
        if role == "user" and step == 0: A.append("[task prompt omitted; it gives the failing test, its source and the stack trace]"); step += 1; continue
        body = txt(m.get("content"))
        if role == "assistant":
            step += 1
            if body.strip(): A += [f"## assistant turn {step}", body.strip()]
            for c in m.get("tool_calls") or []:
                try: cmd = json.loads((c.get("function") or {}).get("arguments") or "{}").get("command", "")
                except Exception: cmd = (c.get("function") or {}).get("arguments", "")
                A.append(f"- command: `{str(cmd)[:600]}`")
        elif role in ("tool", "user"):
            k += 1; A.append(f"  - output #{k}: {body.count(chr(10)) + 1} lines (see tool_outputs.txt)")
            O += [f"### output #{k}", body, ""]
    A += ["", "## FINAL SUBMISSION (ranked methods)"] + [f"{p['rank']}. {p['class']}::{p['method']}" for p in sub.get("predictions", [])]
    A += ["", "## FINAL EVIDENCE CHAIN"] + [f"- evidence: {e.get('evidence', '')}\n  inference: {e.get('inference_summary', '')}" for e in sub.get("evidence_chain", [])]
    open(f"{d}/agent_text.md", "w").write("\n".join(A) + "\n"); open(f"{d}/tool_outputs.txt", "w").write("\n".join(O) + "\n")
    cat = json.load(open(f"{rd}/method_catalog.json")).get("methods", [])
    g = K["gold"][0] if isinstance(K["gold"], list) else K["gold"]; cls, meth = g.split("::")
    e = next(x for x in cat if x.get("class") == cls and x.get("method") == meth)
    src = open(f"{rd}/workspace/{V}/{e['file']}", errors="replace").read().split("\n")[e["line_start"] - 1:e["line_end"]]
    fls = [l.strip() for fl in (K["fault_lines"] if isinstance(K["fault_lines"], list) else [K["fault_lines"]]) for l in str(fl).split("\n") if l.strip()]
    marked = [f"{e['line_start'] + i:5d} {'>>' if any(fl and fl in l.strip() for fl in fls) and l.strip() not in ('}', '{') else '  '} {l}" for i, l in enumerate(src)]
    spec = [f"# Run {rid}: the injected fault (answer key for questions Q1–Q3)", "",
            f"- Gold method (contains the injected omission): `{g}`", f"- Gold file in the workspace: `{e['file']}` (lines {e['line_start']}–{e['line_end']})",
            f"- Method the failing test calls (facade): `{K.get('entry_points', [''])[0] if K.get('entry_points') else ''}`",
            f"- Failing test: `{K.get('trigger', '')}`", f"- Text removed from the gold (the omission): `{P['fault_removed_text']}`",
            f"- The same place in the variant now reads: `{P['fault_variant_text']}`", "",
            "Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):", "```java"] + marked + ["```"]
    open(f"{d}/gold_spec.md", "w").write("\n".join(spec) + "\n")
    key.append({"rid": rid, "stratum": stratum, **{k2: r[k2] for k2 in ("cell", "instance_id", "variant_id", "run", "shift", "failure_mode", "rank1_category", "frozen_gold_exposed", "location_bound_exposed")}})
with open(f"{OUT}/sample_key.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(key[0])); w.writeheader(); w.writerows(key)
print(len(key), collections.Counter(k["stratum"] for k in key), collections.Counter((k["stratum"], k["shift"]) for k in key))
