"""weaker-model-v1: add ONE agent profile for the server's model to its agents.json, cloned from the canonical
mini-swe-agent-openai-gpt-5-6 profile. Only agent_id, model and display_name change; defaults (max_tool_calls 50, max_test_runs 5,
timeout_seconds 300) and every other field are copied unchanged. Usage: wm_add_profile.py <server>"""
import json, sys, copy, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
name = sys.argv[1]; cfg = json.load(open(f"{C.V3}/models/servers.json"))[name]
p = f"{C.V3}/models/{name}/benchmark_runs/agents.json"; d = json.load(open(p))
ags = d["agents"] if isinstance(d, dict) and "agents" in d else d
src = [a for a in ags if a.get("agent_id") == "mini-swe-agent-openai-gpt-5-6"]; assert len(src) == 1
assert not any(a.get("agent_id") == cfg["agent_id"] for a in ags), "profile exists"
new = copy.deepcopy(src[0]); new.update({"agent_id": cfg["agent_id"], "model": cfg["model"], "display_name": f"mini-swe / {cfg['model']}"})
assert {k: v for k, v in new.items() if k not in ("agent_id", "model", "display_name")} == {k: v for k, v in src[0].items() if k not in ("agent_id", "model", "display_name")}
ags.append(new); json.dump(d, open(p, "w"), indent=2)
print(name, "profile", cfg["agent_id"], "model", cfg["model"], "defaults", new.get("defaults"))
