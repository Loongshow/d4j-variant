"""C10i cell (batch 7, paired bridge): a copy of mr_build_records.py that reads main-run/bridge*_tasks.json (task keys <key>__i, field fixture_key = <key>),
specs/MI-<key>.json, instances/MI-<key>/, audits/MI-<key>.json and analysis/bridge*_dispositions.json, and writes INSTANCE_BUILD_LOG_C10I.csv and
INSTANCE_PROVENANCE_C10I.csv. The C10/C10f files are untouched. Original docstring follows.
Main run: write main-run/INSTANCE_BUILD_LOG.csv and main-run/INSTANCE_PROVENANCE.csv from the construction records.
Reads, per attempted candidate: main-run/batch<N>_tasks.json (pool rank, real-bug modified classes, fixed revision),
main-run/batch<N>_build_audit_results.json (builder status, redesigns, minutes, concerns), construction/mainrun/specs/MR-<key>.json,
construction/mainrun/designs/<key>.py (the lie text), instances/MR-<key>/validation.json, construction/mainrun/audits/MR-<key>.json and
the packaged variant manifest. Status rule: ACCEPTED = validation READY and audit CONFIRMED; FLAGGED = READY and FLAG_AMBIGUOUS (run,
reported separately, never counted); REJECTED = audit REJECTED (one redesign allowed); UNBUILDABLE = builder stopped under BUILD_BRIEF
step 7 or the redesign also failed. Read-only except the two CSVs. Usage: mr_build_records.py"""
import csv, glob, hashlib, json, os, runpy, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); WM = os.path.dirname(HERE); MR = f"{WM}/main-run"
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
rel = lambda p: os.path.relpath(p, WM)

tasks, results = {}, {}
for tf in sorted(glob.glob(f"{MR}/bridge*_tasks.json") + glob.glob(f"{MR}/batch8_tasks.json") + glob.glob(f"{MR}/batch9_tasks.json")):   # W56; batch 9 (W61): batch 8 (C10i on bugs without a static facade) uses the same cell files
    b = os.path.basename(tf).split("_")[0]
    for t in json.load(open(tf)): tasks[t["key"]] = dict(t, batch=b)
    rf = f"{MR}/{b}_build_audit_results.json"
    if os.path.exists(rf):
        for r in json.load(open(rf)):
            if "versions" in r:   # batch-3 format (one entry per version built); the last version is the one dispositioned
                last = r["versions"][-1]; b = dict(last.get("build") or {}); b.setdefault("key", r["key"])
                b["redesigns"] = (b.get("redesigns") or 0) + (1 if r.get("redesigned") else 0)
                b["minutes"] = sum((x.get("build") or {}).get("minutes") or 0 for x in r["versions"]) or None
                if r.get("status_reason"): b["reason"] = r["status_reason"]
                results[r["key"]] = {"build": b, "audit": last.get("audit")}
            else:
                results[r["build"]["key"]] = r

DISP = {}   # batch -> {key: disposition}; batch 3 onward: the pre-registered disposition table is authoritative
for f in glob.glob(f"{MR}/analysis/bridge*_dispositions.json") + glob.glob(f"{MR}/analysis/batch8_dispositions.json") + glob.glob(f"{MR}/analysis/batch9_dispositions.json"):   # W56; W61
    DISP[os.path.basename(f).split("_")[0]] = json.load(open(f))["dispositions"]
build_rows, prov_rows = [], []
for key, t in tasks.items():
    r = results.get(key, {}); bres = r.get("build") or {}; ares = r.get("audit") or {}
    fk = t["fixture_key"]   # C10i: the task key is <key>__i; files are named by the fixture key with the MI- prefix
    sp = f"{WM}/construction/mainrun/specs/MI-{fk}.json"; vp = f"{WM}/instances/MI-{fk}/validation.json"
    ap = f"{WM}/construction/mainrun/audits/MI-{fk}.json"
    s = json.load(open(sp)) if os.path.exists(sp) else {}
    v = json.load(open(vp)) if os.path.exists(vp) else {}
    a = json.load(open(ap)) if os.path.exists(ap) else {}
    gates = v.get("gates", []); npass = sum(1 for g in gates if g["status"] == "pass")
    verdict = a.get("verdict") or ares.get("verdict") or ""
    if v.get("overall") == "READY" and verdict == "CONFIRMED": status = "ACCEPTED"
    elif v.get("overall") == "READY" and verdict == "FLAG_AMBIGUOUS": status = "FLAGGED"
    elif verdict == "REJECTED": status = "REJECTED"
    elif bres.get("status") == "UNBUILDABLE": status = "UNBUILDABLE"
    else: status = "PENDING"
    if True:   # C10i: the pre-registered disposition table is always authoritative   # pre-registered disposition table, applied in main-run/analysis/<batch>_dispositions.json, is authoritative
        status = DISP.get(t["batch"], {}).get(key, {}).get("status", "PENDING")
    alts = a.get("alternative_repairs_tried", [])
    byp = [x for x in alts if x.get("class") == "bypass"]
    build_rows.append({
        "instance": key, "batch": t["batch"], "project": t["project"], "bug_id": t["bug_id"], "pool_rank": t["pool_rank"], "status": status,
        "validation": v.get("overall", ""), "gates_passed": f"{npass}/{len(gates)}" if gates else "", "audit_verdict": verdict,
        "competing_repair_found": a.get("c_competing_repair", ""), "bypasses_recorded": len(byp),
        "alternative_repairs_tried": len(alts), "redesigns_before_ready": bres.get("redesigns", ""),
        "builder_minutes": bres.get("minutes") if bres.get("minutes") is not None else "",
        "variant_id": s.get("variant_id", ""), "reason": (bres.get("reason") or "").replace("\n", " ")[:400],
        "builder_concerns": (bres.get("concerns") or "").replace("\n", " ")[:600]})
    if not s or status not in ("ACCEPTED", "FLAGGED"): continue
    G = s["gold"]; T = s["trigger"]; hops = s["stage_b"]["hops"]
    design = runpy.run_path(f"{WM}/{s['design_file']}")["DESIGN"]
    fx = os.path.realpath(f"{WM}/construction/fresh-mr/{s['fixture_key']}")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=fx, capture_output=True, text=True).stdout.strip()
    harness = os.path.realpath(f"{WM}/models/w55/workspaces/defects4j/{fk}/fixed")
    vdir = f"{WM}/new_bug_variants/{s['project']}/bug-{int(s['bug_id'])}/L20/{s.get('variant_id', '')}"
    man = json.load(open(f"{vdir}/variant_manifest.json")) if s.get("variant_id") else {}
    facade = s["entry_points"][0]; facade_cls = facade.split("::")[0]
    edits = G["edits"]
    prov_rows.append({
        "instance": key, "instance_id": s["iid"], "variant_id": s.get("variant_id", ""), "project": s["project"], "bug_id": s["bug_id"],
        "fixed_revision": t.get("fixed_revision", ""), "harness_checkout": harness, "fixture": rel(fx), "fixture_git_head": head,
        "real_bug_modified_classes": t.get("real_bug_modified_classes", ""),
        "facade": facade, "facade_in_real_bug_class": facade_cls in t.get("real_bug_modified_classes", "").split(";"),
        "trigger": f"{T['test_class']}::{T['test_method']}", "trigger_is_existing_test": T.get("existing", False),
        "failure_signature": (v.get("signature") or "").replace("\n", " ")[:200],
        "gold": f"{G['class']}::{G['method']}", "gold_file": G["file"],
        "fault_removed_text": " | ".join(e["old"].strip() for e in edits).replace("\n", " ")[:400],
        "fault_variant_text": " | ".join(e["new"].strip() for e in edits).replace("\n", " ")[:400],
        "hop_chain": " -> ".join(f"{h['class']}::{h['method']}" for h in hops),
        "hop_anchors": " ; ".join(f"after {h['anchor_after']} (seed {h['anchor_seed']})" for h in hops),
        "host_draw_seed": s["stage_b"]["seed"], "lie": " ".join(str(design["chain"]["lie"]).split()),
        "transformation": "Stage B C10 (facade = guard + 1 call, lie appended; 5 new static hops in 5 seeded hosts; hop 5 = gold with a one-line quiet omission)",
        "spec_sha256": sha(sp), "variant_patch_sha256": man.get("artifact_hashes", {}).get("variant.patch", ""),
        "test_patch_sha256": man.get("artifact_hashes", {}).get("test.patch", ""), "validation_finished_at": v.get("finished_at", "")})

def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("wrote", rel(path), len(rows), "rows")
write(f"{MR}/INSTANCE_BUILD_LOG_C10I.csv", build_rows)
write(f"{MR}/INSTANCE_PROVENANCE_C10I.csv", prov_rows)
