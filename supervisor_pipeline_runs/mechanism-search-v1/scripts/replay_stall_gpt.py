"""Bounded diagnostic (pilot halt review, slot 8): replay the exact conversation state of a stalled GPT-5.6 run to the same model with
the same tools and model_kwargs, and report latency, finish reason and token use. Never touches run artifacts.
Usage: replay_stall_gpt.py <run_dir> <cap_seconds> <tag>
The OpenAI key is loaded in-process from the authorized env file and never printed; the user's global mini-swe-agent config is not read."""
import json, sys, time, os, re, tempfile
os.environ["MSWEA_GLOBAL_CONFIG_DIR"] = tempfile.mkdtemp()
for l in open("/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/.env"):
    m = re.match(r'^\s*(?:export\s+)?(D4J_OPENAI_API_KEY)\s*=\s*"?(.*?)"?\s*$', l)
    if m: os.environ["OPENAI_API_KEY"] = m.group(2).strip()
for k in [k for k in os.environ if k.startswith(("ANTHROPIC", "CLAUDE", "OPENAI_BASE", "D4J_OPENAI_BASE"))]: del os.environ[k]
import litellm
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/mechanism-search-v1/models/mxF0/variant-lab/server/agents")
from mini_swe_fault_localization import SUBMIT_FAULT_LOCALIZATION_TOOL
from minisweagent.models.utils.actions_toolcall import BASH_TOOL
d, cap, tag = sys.argv[1], float(sys.argv[2]), sys.argv[3]
t = json.load(open(f"{d}/mini-swe-agent.traj.json")); cfg = t["info"]["config"]["model"]
msgs = [{k: v for k, v in m.items() if k != "extra"} for m in t["messages"] if m.get("role") != "exit"]
kw = dict(cfg.get("model_kwargs") or {})
out = {"run_dir": d, "tag": tag, "model": cfg["model_name"], "model_kwargs": kw, "messages": len(msgs), "last_role": msgs[-1]["role"]}
t0 = time.time(); err = None; usage = None; finish = None; ntools = None; rmodel = None
try:
    r = litellm.completion(model=cfg["model_name"], messages=msgs, tools=[BASH_TOOL, SUBMIT_FAULT_LOCALIZATION_TOOL], timeout=cap, num_retries=0, **kw)
    finish = r.choices[0].finish_reason; ntools = len(r.choices[0].message.tool_calls or []); rmodel = r.model
    u = r.usage; usage = {"prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens,
                          "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None)}
except Exception as e:
    err = re.sub(r"sk-[A-Za-z0-9_\-]{6,}", "[redacted]", f"{type(e).__name__}: {str(e)[:300]}")
out.update({"elapsed_s": round(time.time() - t0, 1), "finish_reason": finish, "tool_calls": ntools, "response_model": rmodel, "usage": usage, "error": err})
json.dump(out, open(f"diagnostic/stall_replays/replay_{os.path.basename(os.path.dirname(d))}_{os.path.basename(d)}_{tag}.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ("model_kwargs", "run_dir")}))
