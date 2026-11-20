"""weaker-model-v1: re-host frozen, validated variants from other roots UNCHANGED, under an opaque id, and reproduce them here.
Adapted from mechanism-search-v1/scripts/mx_rehost.py with three generalisations needed for the canonical Closure instances:
  * the Defects4J bug id comes from the source manifest (dst = new_bug_variants/<Project>/bug-<id>/L20/<VID>; the harness maps
    source.defects4j_project-<id>/fixed to its checkout); the pristine base is construction/fresh/<Project>-<id> if present, else
    construction/fresh/<Project>;
  * an empty test.patch (trigger is an existing test) is skipped rather than applied;
  * when the manifest has no failure_signature line, the trigger must still fail as exactly 1 failing test and the assertion line
    observed in failing_tests is recorded as the expected signature.
Usage: wm_rehost.py <rehost_plan.json> [--only IID[,IID]]
Plan entries: {iid, source_variant_dir, project, group, mechanism, tags, gold[], decoys[], entry_points[], fault_lines[], evidence[], notes}"""
import json, os, sys, hashlib, shutil, subprocess, datetime, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
MX = C.V3; plan = json.load(open(sys.argv[1])); only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
keyp = f"{MX}/review/VARIANT_KEY.json"; key = json.load(open(keyp)) if os.path.exists(keyp) else {}
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def sh(cmd, cwd, timeout=3600):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env={**os.environ, "PERL5LIB": os.path.expanduser("~/perl5/lib/perl5")})
    return p.returncode, p.stdout + p.stderr
def vid_of(iid): return "CTV-" + hashlib.sha256(f"weaker-model-v1:{iid}".encode()).hexdigest()[:6].upper()
for e in plan:
    iid = e["iid"]
    if only and iid not in only: continue
    src = e["source_variant_dir"]; man0 = json.load(open(f"{src}/variant_manifest.json")); val0 = json.load(open(f"{src}/validation.json"))
    V = vid_of(iid); assert V not in key or key[V]["instance_id"] == iid, f"id collision {V}"
    trig = man0["trigger"]; bug = int((man0.get("source") or {}).get("defects4j_bug_id") or 1)
    sig0 = trig.get("failure_signature") or ""
    assert0 = next((l.strip() for l in sig0.split("\n") if "Error" in l or "expected" in l), sig0.strip()[:200])
    fresh = f"{MX}/construction/fresh/{e['project']}-{bug}" if os.path.isdir(f"{MX}/construction/fresh/{e['project']}-{bug}") else f"{MX}/construction/fresh/{e['project']}"
    patches = [p for p in ("variant.patch", "test.patch") if os.path.getsize(f"{src}/{p}") > 0]
    tmp = tempfile.mkdtemp(prefix="mxb-", dir="/private/tmp"); shutil.copytree(fresh, f"{tmp}/w", symlinks=True); subprocess.run(["chmod", "-R", "u+w", f"{tmp}/w"]); w = f"{tmp}/w"
    ok_apply = all(sh(["git", "apply", f"{src}/{p}"], w)[0] == 0 for p in patches)
    rc_c, o_c = sh(["defects4j", "compile"], w, 2400) if ok_apply else (1, "apply failed")
    rc_t, o_t = sh(["defects4j", "test", "-t", trig["test_id"]], w, 2400) if rc_c == 0 else (1, "")
    ft = open(f"{w}/failing_tests", errors="replace").read() if os.path.exists(f"{w}/failing_tests") else ""
    one_fail = ok_apply and rc_c == 0 and "Failing tests: 1" in o_t and trig["test_id"] in ft
    if assert0: reproduced = one_fail and assert0 in ft
    else:
        observed = next((l.strip() for l in ft.split("\n") if "Error" in l or "expected" in l or "Exception" in l), "")
        reproduced = one_fail and bool(observed); assert0 = observed
    rep = {"iid": iid, "variant_id": V, "source": src, "bug_id": bug, "fresh": fresh, "patches_applied": patches, "apply_ok": ok_apply, "compile_ok": rc_c == 0,
           "trigger_output_tail": o_t[-400:], "recorded_or_observed_assertion": assert0, "observed_failing_tests_head": ft[:600], "reproduced": bool(reproduced),
           "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(f"{MX}/instances/{iid}", exist_ok=True); json.dump(rep, open(f"{MX}/instances/{iid}/reproduction.json", "w"), indent=1)
    spec = {k: e.get(k) for k in ("iid", "project", "group", "mechanism", "tags", "gold", "decoys", "entry_points", "fault_lines", "evidence", "notes")}
    spec.update({"tier": "REHOSTED_FROZEN", "kind": "rehosted", "bug_id": bug, "source_variant_dir": src, "variant_id": V, "trigger": trig["test_id"], "expected_signature": assert0,
                 "source_validation_overall": val0.get("status") or (val0.get("validation_summary") or {}).get("overall"), "variant_patch_sha256": h(f"{src}/variant.patch")})
    json.dump(spec, open(f"{MX}/instances/{iid}/spec.json", "w"), indent=1)
    if not reproduced: print(f"NOT REPRODUCED {iid}: apply={ok_apply} compile={rc_c == 0} {o_t[-200:]}", flush=True); continue
    dst = f"{MX}/new_bug_variants/{e['project']}/bug-{bug}/L20/{V}"
    if os.path.exists(dst): shutil.rmtree(dst)
    os.makedirs(dst)
    for p in ("variant.patch", "test.patch"): shutil.copyfile(f"{src}/{p}", f"{dst}/{p}")
    man = {k: man0[k] for k in man0 if k in ("schema_version", "source", "trigger", "fault", "semantic_bug", "changed_files", "synthetic_call_hops", "reasoning", "artifacts", "provenance")}
    man["source"] = {k: v for k, v in (man0.get("source") or {}).items() if k in ("defects4j_project", "defects4j_bug_id", "bug_slug", "fixed_revision", "baseline_version")}
    man.update({"variant_id": V, "status": "non_canonical_validated", "benchmark_eligible": True, "non_canonical": True, "label": "NON-CANONICAL RESEARCH BENCHMARK",
                "manifest_extension": "weaker-model-v1/rehosted/v1", "artifact_hashes": {"variant.patch": h(f"{dst}/variant.patch"), "test.patch": h(f"{dst}/test.patch")},
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    man.setdefault("reasoning", {}); man["reasoning"].setdefault("changed_node", f"{e['gold'][0].replace('::', '#')}")
    # the harness drops a record whose reasoning.level differs from its directory namespace; re-hosted copies live under L20
    if man["reasoning"].get("level") != "L20": man["reasoning"]["original_level"] = man["reasoning"].get("level"); man["reasoning"]["level"] = "L20"
    man["artifacts"] = {k: v for k, v in (man.get("artifacts") or {}).items() if os.path.exists(f"{dst}/{v}")}   # only files actually shipped
    vrec = dict(val0); vrec["variant_id"] = V
    json.dump(man, open(f"{dst}/variant_manifest.json", "w"), indent=1); json.dump(vrec, open(f"{dst}/validation.json", "w"), indent=1)
    key = json.load(open(keyp)) if os.path.exists(keyp) else {}
    key[V] = {"instance_id": iid, "group": e.get("group"), "mechanism": e.get("mechanism"), "tags": e.get("tags"), "tier": "REHOSTED_FROZEN", "project": e["project"], "bug_id": bug,
              "gold": e["gold"], "decoys": e.get("decoys", []), "entry_points": e.get("entry_points", []), "fault_lines": e.get("fault_lines", []),
              "evidence": e.get("evidence", []), "expected_signature": assert0, "trigger": trig["test_id"], "fresh": fresh,
              "variant_patch_sha256": man["artifact_hashes"]["variant.patch"], "test_patch_sha256": man["artifact_hashes"]["test.patch"]}
    tmpk = keyp + ".tmp"; json.dump(key, open(tmpk, "w"), indent=1, sort_keys=True); os.replace(tmpk, keyp)
    print(f"re-hosted {iid} -> {V} (bug {bug}; reproduced: {assert0[:80]})", flush=True)
