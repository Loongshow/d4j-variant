"""Freeze plans in mechanism-search-v1 before any paid call. Usage:
  mx_freeze.py --init                     -> FREEZE.json with the guarded scripts, the paid servers and plans/smoke.json (bound to mxDiag)
  mx_freeze.py --add-plan P --server S    -> appends plan P bound to server S, with its own variant, instance, key-entry, server-entry and
                                             pre-registration hashes (nothing else changes; Phase 1 acceptance stays valid)"""
import json, os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C, freeze_lib as FZ
OUT = f"{C.V3}/FREEZE.json"; now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def entry(p, server):
    _, _, plan = FZ.partition(FZ.guarded(server, p), server); return {"server": server, "frozen_at": now, "sha256": FZ.sha(p), "hashes": plan}
if "--add-plan" in sys.argv:
    p = os.path.abspath(sys.argv[sys.argv.index("--add-plan") + 1]); server = sys.argv[sys.argv.index("--server") + 1]
    fz = json.load(open(OUT)); rel = os.path.relpath(p, C.V3); assert rel not in fz["plans"], f"{rel} already frozen"
    fz["plans"][rel] = entry(p, server); json.dump(fz, open(OUT, "w"), indent=1)
    print("added", rel, "->", server, "| variants", sum(1 for k in fz["plans"][rel]["hashes"] if k.startswith("keyentry/")), "| freeze sha256", FZ.sha(OUT)[:16]); sys.exit(0)
assert "--init" in sys.argv and not os.path.exists(OUT), "use --init once (FREEZE.json exists?)"
servers = json.load(open(f"{C.V3}/models/servers.json")); paid = [n for n, c in servers.items() if c.get("provider") == "openai" and not c.get("stub")]
smoke = f"{C.V3}/plans/smoke.json"
common, _, _ = FZ.partition(FZ.guarded("mxDiag", smoke), "mxDiag")
by_server = {n: FZ.partition(FZ.guarded(n, smoke), n)[1] for n in paid}
fz = {"frozen_at": now, "root": "mechanism-search-v1", "protocol": "see PREREGISTRATION.md (identical to the GPT-5.6 cue pilot; only instances change)",
      "model": {"agent_id": "mini-swe-agent-openai-gpt-5-6", "model": "gpt-5.6", "reasoning_effort": "medium", "server_tree_sha_prefix": "1e1b6fa9"},
      "guarded_common": common, "guarded_by_server": by_server, "plans": {"plans/smoke.json": entry(smoke, "mxDiag")}}
fz["acceptance_digest"] = FZ.acceptance_digest(fz); json.dump(fz, open(OUT, "w"), indent=1)
print("wrote FREEZE.json sha256", FZ.sha(OUT)[:16], "| digest", fz["acceptance_digest"][:16], "| common", len(common), "| servers", list(by_server))
