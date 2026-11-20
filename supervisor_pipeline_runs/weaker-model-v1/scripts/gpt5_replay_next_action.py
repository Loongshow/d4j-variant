"""Study 1 bounded replay diagnostic (brief section 8): replay the exact pre-timeout conversation state of ONE gpt-5 timeout run to the
same model, model_kwargs and tool schema (bash + the submission tool from the w50 server's own agent module), ONE request, capped,
and record what the model does next: the tool it calls (bash command class, or submission with its top-3 and the gold's rank),
latency, finish reason and token counts. Diagnostic only: never scored, never written into any run directory.
The OpenAI key is loaded in-process from the authorized env file (as scripts/replay_stall_gpt.py does) and never printed.
Usage: gpt5_replay_next_action.py <run_dir> <cap_seconds> <tag>"""
import json, sys, time, os, re, tempfile
os.environ["MSWEA_GLOBAL_CONFIG_DIR"] = tempfile.mkdtemp()
for l in open("/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/.env"):
    m = re.match(r'^\s*(?:export\s+)?(D4J_OPENAI_API_KEY)\s*=\s*"?(.*?)"?\s*$', l)
    if m: os.environ["OPENAI_API_KEY"] = m.group(2).strip()
for k in [k for k in os.environ if k.startswith(("ANTHROPIC", "CLAUDE", "OPENAI_BASE", "D4J_OPENAI_BASE"))]: del os.environ[k]
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
import litellm
sys.path.insert(0, f"{ROOT}/models/w50/variant-lab/server/agents")
from mini_swe_fault_localization import SUBMIT_FAULT_LOCALIZATION_TOOL
from minisweagent.models.utils.actions_toolcall import BASH_TOOL
src = open(f"{HERE}/mx_metrics.py").read(); NS = {"__file__": f"{HERE}/mx_metrics.py"}
exec(compile(src[:src.index("rows, diag_rows = [], []")], "mx_metrics_frozen_defs", "exec"), NS)
d, cap, tag = sys.argv[1], float(sys.argv[2]), sys.argv[3]
V = os.path.basename(os.path.dirname(d)); K = NS["KEY"][V]; golds = K["gold"] if isinstance(K["gold"], list) else [K["gold"]]
t = json.load(open(f"{d}/mini-swe-agent.traj.json")); cfg = t["info"]["config"]["model"]
msgs = [{k: v for k, v in m.items() if k != "extra"} for m in t["messages"] if m.get("role") != "exit"]
kw = dict(cfg.get("model_kwargs") or {})
out = {"run": f"{V}/{os.path.basename(d)}", "tag": tag, "model": cfg["model_name"], "messages_replayed": len(msgs), "last_role": msgs[-1]["role"],
       "reasoning_effort_passed": kw.get("reasoning_effort")}
t0 = time.time(); err = None
try:
    r = litellm.completion(model=cfg["model_name"], messages=msgs, tools=[BASH_TOOL, SUBMIT_FAULT_LOCALIZATION_TOOL], timeout=cap, num_retries=0, **kw)
    msg = r.choices[0].message; tcs = msg.tool_calls or []; u = r.usage
    out.update({"finish_reason": r.choices[0].finish_reason, "response_model": r.model, "n_tool_calls": len(tcs),
                "usage": {"prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens,
                          "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None)}})
    acts = []
    for tc in tcs:
        name = tc.function.name
        try: args = json.loads(tc.function.arguments or "{}")
        except Exception: args = {}
        if name == "bash":
            cmd = args.get("command", ""); kinds = sorted({k for k, _ in NS["classify_command"](cmd, K.get("trigger", ""))})
            files = sorted({os.path.basename(x) for x in re.findall(r"[\w./-]+\.(?:java|xml|txt|properties)", cmd)})
            acts.append({"tool": "bash", "kinds": kinds, "files": files, "command_chars": len(cmd)})
        else:
            preds = args.get("predictions") or (args.get("structured_submission") or {}).get("predictions") or []
            keys = [f"{p.get('class')}::{p.get('method')}" for p in preds]
            gr = min([keys.index(g) + 1 for g in golds if g in keys] or [None]) if keys else None
            acts.append({"tool": name, "n_predictions": len(keys), "top3": [k.split(".")[-1] for k in keys[:3]], "gold_rank": gr})
    out["actions"] = acts; out["visible_content_chars"] = len(msg.content or "")
except Exception as e:
    err = f"{type(e).__name__}: {str(e)[:300]}"
out.update({"elapsed_s": round(time.time() - t0, 1), "error": err})
json.dump(out, open(f"{ROOT}/gpt5-timeouts/replays/replay_{V}_{os.path.basename(d)}_{tag}.json", "w"), indent=1)
print(json.dumps(out))
