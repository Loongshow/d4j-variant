"""Local OpenAI-compatible stand-in for the FREE harness proof (Phase 1 items 2-10). It never contacts OpenAI and needs no credential.
Usage: stub_openai.py <port> <scenario.json>
POST /v1/responses (what litellm 1.98 uses for gpt-5.4+ with function tools and reasoning, i.e. the real pilot path) and
POST /v1/chat/completions -> a scripted response with one tool call per step. The step index is the number of earlier tool calls
(function_call items / assistant messages) in the request. Scenario: {"<variant id>": [{"bash": "..."} | {"submit": [ten Class::method keys]}, ...]};
{TRIGGER} in a command is replaced by the prompt's failing test identifier; {"error429": true} answers with OpenAI's
insufficient_quota error (credit-path proof). The harness smoke prompt is answered by submitting
org.example.Smoke::m0..m9. Every request's parameters (never message text) are appended to diagnostic/stub/requests.jsonl together
with prompt facts: the inspection-sentence count, the variant id seen in the prompt, and the request's reasoning_effort/model/tools."""
import json, sys, re, time, hashlib, http.server
PORT = int(sys.argv[1]); SCEN = sys.argv[2]
LOG = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/mechanism-search-v1/diagnostic/stub/requests.jsonl"
SENT = "Before you submit, display the complete source body of every method you rank in your top three."
def tc(name, args, i):
    return {"id": f"call_stub_{i}_{int(time.time()*1000)}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", "0"))) or b"{}")
        responses_api = self.path.rstrip("/").endswith("/responses")
        if responses_api:
            items = body.get("input") or []; items = [{"role": "user", "content": items}] if isinstance(items, str) else items
            msgs = [i for i in items if isinstance(i, dict)]
            first_user = next((m.get("content") for m in msgs if m.get("role") == "user"), "") or ""
            step = sum(1 for m in msgs if m.get("type") == "function_call")
        else:
            msgs = body.get("messages") or []; first_user = next((m.get("content") for m in msgs if m.get("role") == "user"), "") or ""
            step = sum(1 for m in msgs if m.get("role") == "assistant")
        if isinstance(first_user, list): first_user = " ".join(p.get("text", "") for p in first_user if isinstance(p, dict))
        vid = (re.search(r"repository path: \S*/(CTV-[0-9A-F]{6})\b", first_user) or [None, None])[1]
        trig = (re.search(r"failing test identifier: (\S+)", first_user) or [None, None])[1]
        smoke = "non-interactive smoke test" in first_user
        scen = json.load(open(SCEN)); steps = scen.get(vid or "", [])
        if smoke: action = {"submit": [f"org.example.Smoke::m{i}" for i in range(10)]}
        elif step < len(steps): action = steps[step]
        else: action = steps[-1] if steps else {"submit": []}
        if action.get("error429"):
            rec = {"t": time.time(), "path": self.path, "variant": vid, "smoke": smoke, "step": step, "action": "error429",
                   "reasoning_effort": body.get("reasoning_effort") or (body.get("reasoning") or {}).get("effort")}
            open(LOG, "a").write(json.dumps(rec) + "\n")
            err = json.dumps({"error": {"message": "You exceeded your current quota, please check your plan and billing details.", "type": "insufficient_quota",
                                        "param": None, "code": "insufficient_quota"}}).encode()
            self.send_response(429); self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(err)))
            self.end_headers(); self.wfile.write(err); return
        if "bash" in action: call = tc("bash", {"command": action["bash"].replace("{TRIGGER}", trig or "")}, step)
        else: call = tc("submit_fault_localization", {"predictions": [{"class": k.split("::")[0], "method": k.split("::")[1]} for k in action["submit"]]}, step)
        rec = {"t": time.time(), "path": self.path, "variant": vid, "smoke": smoke, "step": step, "action": "bash" if "bash" in action else f"submit[{len(action.get('submit', []))}]",
               "model": body.get("model"), "reasoning_effort": body.get("reasoning_effort") or (body.get("reasoning") or {}).get("effort"),
               "reasoning_param": body.get("reasoning"), "include": body.get("include"), "store": body.get("store"),
               "tools": [t.get("name") or (t.get("function") or {}).get("name") for t in body.get("tools") or []],
               "params": sorted(k for k in body if k not in ("messages", "tools")), "n_messages": len(msgs),
               "prompt_sha256": hashlib.sha256(first_user.encode()).hexdigest(), "inspection_sentence_count": first_user.count(SENT)}
        open(LOG, "a").write(json.dumps(rec) + "\n")
        if responses_api:
            fn = call["function"]
            resp = {"id": f"resp_stub_{step}_{int(time.time()*1000)}", "object": "response", "created_at": int(time.time()), "status": "completed",
                    "model": "gpt-5.6", "error": None, "incomplete_details": None, "instructions": None, "metadata": {}, "parallel_tool_calls": True,
                    "temperature": 1.0, "top_p": 1.0, "tool_choice": "auto", "tools": [], "store": False, "truncation": "disabled",
                    "text": {"format": {"type": "text"}}, "reasoning": {"effort": (body.get("reasoning") or {}).get("effort"), "summary": None},
                    "output": [{"type": "reasoning", "id": f"rs_stub_{step}", "summary": [], "encrypted_content": "stub-encrypted-reasoning"},
                               {"type": "function_call", "id": f"fc_stub_{step}", "call_id": call["id"], "name": fn["name"], "arguments": fn["arguments"], "status": "completed"}],
                    "usage": {"input_tokens": 1000 + 100 * step, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 50,
                              "output_tokens_details": {"reasoning_tokens": 20}, "total_tokens": 1050 + 100 * step}}
            out = json.dumps(resp).encode(); self.send_response(200); self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(out))); self.end_headers(); self.wfile.write(out); return
        resp = {"id": f"chatcmpl-stub-{step}", "object": "chat.completion", "created": int(time.time()), "model": "gpt-5.6",
                "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {"role": "assistant", "content": None, "tool_calls": [call]}}],
                "usage": {"prompt_tokens": 1000 + 100 * step, "completion_tokens": 50, "total_tokens": 1050 + 100 * step,
                          "completion_tokens_details": {"reasoning_tokens": 20}, "prompt_tokens_details": {"cached_tokens": 0}}}
        out = json.dumps(resp).encode(); self.send_response(200); self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(out))); self.end_headers(); self.wfile.write(out)
http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
