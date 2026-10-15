"""Hashing helpers shared by freeze_gpt_pilot.py (writes FREEZE_GPT56_PILOT.json) and ct_driver.py (verifies it before any paid
OpenAI launch). guarded(server, plan_path) returns {label: sha256} for every artifact whose change after the freeze must stop a block."""
import hashlib, os, glob, json
import ct_lib as C
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def tree_sha(d):
    h = hashlib.sha256()
    for p in sorted(x for x in glob.glob(f"{d}/**/*", recursive=True) if os.path.isfile(x) and "__pycache__" not in x):
        h.update(os.path.relpath(p, d).encode()); h.update(sha(p).encode())
    return h.hexdigest()
SCRIPTS = ["ct_driver.py", "mx_metrics.py", "ct_status.py", "scan_v3.py", "freeze_lib.py", "ct_plan.py", "ct_lib.py", "start_gpt_server.sh",
           "setup_server.py", "patch_p4.py", "mx_phase1_accept.py"]
def variant_files(vid):
    key = json.load(open(f"{C.V3}/review/VARIANT_KEY.json"))[vid]; d = f"{C.V3}/new_bug_variants/{key['project']}/bug-{key.get('bug_id', 1)}/L20/{vid}"   # W6: bug id from the key
    return {f"variant/{vid}/{f}": sha(f"{d}/{f}") for f in ("variant_manifest.json", "variant.patch", "test.patch", "validation.json")}
def guarded(server, plan_path):
    g = {f"scripts/{s}": sha(f"{C.V3}/scripts/{s}") for s in SCRIPTS}
    key = json.load(open(f"{C.V3}/review/VARIANT_KEY.json")); servers = json.load(open(f"{C.V3}/models/servers.json"))
    g.update({f"serverentry/{server}": hashlib.sha256(json.dumps(servers[server], sort_keys=True).encode()).hexdigest(),
              "prereg/PREREGISTRATION.md": sha(f"{C.V3}/PREREGISTRATION.md"),
              f"models/{server}/variant-lab/server": tree_sha(f"{C.V3}/models/{server}/variant-lab/server"),
              f"models/{server}/benchmark_runs/agents.json": sha(f"{C.V3}/models/{server}/benchmark_runs/agents.json"),
              f"plan/{os.path.relpath(plan_path, C.V3)}": sha(plan_path)})
    insts = set()
    for s in json.load(open(plan_path))["slots"]:
        g.update(variant_files(s["variant_id"])); insts.add(s["instance_id"])
        g[f"keyentry/{s['variant_id']}"] = hashlib.sha256(json.dumps(key[s["variant_id"]], sort_keys=True).encode()).hexdigest()
    for iid in sorted(insts):   # every file of each planned instance folder (spec, build patches, validation)
        d = f"{C.V3}/instances/{iid}"
        for p in sorted(x for x in glob.glob(f"{d}/**/*", recursive=True) if os.path.isfile(x)):
            g[f"instance/{iid}/{os.path.relpath(p, d)}"] = sha(p)
    return g

PLAN_PREFIXES = ("plan/", "variant/", "instance/", "keyentry/", "serverentry/", "prereg/")
def partition(g, server):
    """mechanism-search-v1: common = scripts; by_server = the server tree and profile list; everything else belongs to the plan."""
    common = {k: v for k, v in g.items() if k.startswith("scripts/")}
    by_server = {k: v for k, v in g.items() if k.startswith(f"models/{server}/")}
    plan = {k: v for k, v in g.items() if k.startswith(PLAN_PREFIXES)}
    assert len(common) + len(by_server) + len(plan) == len(g), sorted(set(g) - set(common) - set(by_server) - set(plan))
    return common, by_server, plan
def acceptance_digest(fz):
    """Stable digest of the frozen protocol that Phase 1 acceptance is bound to: common + per-server guards and the pilot and smoke
    plans. Adding a later plan (Phase 3) does not change it; changing any guarded artifact does."""
    core = {"guarded_common": fz["guarded_common"], "guarded_by_server": fz["guarded_by_server"],
            "plans": {k: fz["plans"][k] for k in ("plans/smoke.json",) if k in fz["plans"]}}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()
