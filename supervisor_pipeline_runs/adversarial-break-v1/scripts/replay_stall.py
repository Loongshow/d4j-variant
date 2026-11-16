#!/usr/bin/env python
"""Bounded diagnostic: replay the exact conversation state of a stalled run to the same model with streaming and report what the
in-flight request would have done (latency, error class, output size). Never touches run artifacts. Usage: replay_stall.py <run_dir> <cap_seconds>"""
import json, sys, time, os
import litellm
from minisweagent.models.litellm_model import BASH_TOOL
from minisweagent.models.utils.cache_control import set_cache_control
d, cap = sys.argv[1], float(sys.argv[2])
t = json.load(open(f"{d}/mini-swe-agent.traj.json")); cfg = t["info"]["config"]["model"]
msgs = [{k: v for k, v in m.items() if k != "extra"} for m in t["messages"]]
msgs = set_cache_control(msgs, mode=cfg.get("set_cache_control"))
kw = dict(cfg.get("model_kwargs") or {})
print("model:", cfg["model_name"], "model_kwargs keys:", sorted(kw), "messages:", len(msgs), "last role:", msgs[-1]["role"], flush=True)
litellm.request_timeout = cap
out = {"run_dir": d, "model": cfg["model_name"], "model_kwargs": kw, "messages": len(msgs)}
t0 = time.time(); first = None; chunks = 0; text = ""; tool_args = ""; finish = None; err = None
try:
    resp = litellm.completion(model=cfg["model_name"], messages=msgs, tools=[BASH_TOOL], stream=True, timeout=cap, **kw)
    for ch in resp:
        chunks += 1
        if first is None: first = time.time() - t0
        c = ch.choices[0] if ch.choices else None
        if c is not None:
            dl = c.delta
            if getattr(dl, "content", None): text += dl.content
            for tc in (getattr(dl, "tool_calls", None) or []):
                if tc.function and tc.function.arguments: tool_args += tc.function.arguments
            if c.finish_reason: finish = c.finish_reason
        if time.time() - t0 > cap: err = f"cap {cap}s reached while streaming"; break
except Exception as e:
    err = f"{type(e).__module__}.{type(e).__name__}: {str(e)[:400]}"
out.update({"elapsed_s": round(time.time() - t0, 1), "first_chunk_s": round(first, 1) if first else None, "chunks": chunks, "finish_reason": finish, "text_chars": len(text), "tool_args_chars": len(tool_args), "error": err, "text_head": text[:300], "tool_args_head": tool_args[:300]})
print(json.dumps({k: v for k, v in out.items() if k not in ("model_kwargs",)}, indent=1))
os.makedirs(f"{os.environ.get('OUT', '.')}", exist_ok=True)
json.dump(out, open(f"{os.environ.get('OUT', '.')}/replay_{os.path.basename(os.path.dirname(d))}_{os.path.basename(d)}.json", "w"), indent=1)
