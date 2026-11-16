#!/usr/bin/env python
"""OCFLB per-run metrics + failure classification. Reads pair.json (chain roles, golds, pin) and run artifacts only.
Usage: ocflb_metrics.py [out.json]   -> analysis/per_run/run_metrics.json (one row per run, all servers)"""
import glob, json, os, re, sys, itertools, datetime
O = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1"
SERVERS = {"sonnetA": "claude-sonnet-4-6", "sonnetB": "claude-sonnet-4-6", "opusA": "claude-opus-5-5"}
MODEL_OF = {"sonnetA": "sonnet", "sonnetB": "sonnet", "opusA": "opus"}
out_path = sys.argv[1] if len(sys.argv) > 1 else f"{O}/analysis/per_run/run_metrics.json"; os.makedirs(os.path.dirname(out_path), exist_ok=True)
SEARCH = re.compile(r"\b(grep|rg|ack|ag|find)\b"); READ = re.compile(r"\b(?:cat|sed|head|tail|awk|nl|less|more)\b[^|;]*\.java")
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
def strip_cd(c):
    m = re.match(r"^cd\s+\S+\s*(?:&&|;)\s*(.*)$", c.strip(), re.S); return m.group(1).strip() if m else c.strip()
def steps_of(traj):
    cmds, outs = [], []
    for m in traj.get("messages") or []:
        if m.get("role") == "assistant":
            for a in ((m.get("extra") or {}).get("actions") or []): cmds.append(a["command"] if a.get("command") else "TOOL:" + str(a.get("tool")))
        elif m.get("role") == "tool": outs.append(str((m.get("extra") or {}).get("raw_output") or m.get("content") or ""))
    return [(i + 1, cmds[i], outs[i]) for i in range(min(len(cmds), len(outs)))]
def tau(a, b):
    if len(a) < 3: return None
    c = d = 0
    for i, j in itertools.combinations(range(len(a)), 2):
        s = (a[i] - a[j]) * (b[i] - b[j]); c += s > 0; d += s < 0
    return (c - d) / (len(a) * (len(a) - 1) / 2)
def decl_regex(method): return re.compile(r"\b" + re.escape(method) + r"\s*\(")
rows = []
for pj in sorted(glob.glob(f"{O}/projects/*/bug-*/pair.json")):
    spec = rj(pj); CH = spec["chain"]; ROLES = ["H1", "H2", "H3", "H4", "H5"]
    key = lambda r: f"{CH[r]['class'].split('.')[-1]}::{CH[r]['method']}"
    labels = {key(r): r for r in ROLES}; labels[f"{CH['facade']['class'].split('.')[-1]}::{CH['facade']['method']}"] = "facade"
    depth_order = ["H5", "H4", "H3", "H2", "H1", "facade"]
    pin_cls, pin_m = spec["pin_test"].split("::"); pin_simple = pin_cls.split(".")[-1]
    for arm, A in spec["arms"].items():
        V = A["variant_id"]; G = A["gold"]; gold_key = f"{G['class'].split('.')[-1]}::{G['method']}"; gold_role = A["gold_role"]
        if not os.path.exists(f"{O}/new_bug_variants/{spec['project']}/bug-1/L20/{V}"): continue
        for srv, mid in SERVERS.items():
            for rd in sorted(glob.glob(f"{O}/models/{srv}/benchmark_runs/mini-swe-claude/{V}/run-*")):
                man = rj(f"{rd}/run_manifest.json"); traj = rj(f"{rd}/mini-swe-agent.traj.json"); ev = rj(f"{rd}/evaluation.json"); rk = rj(f"{rd}/ranking.json")
                if not man: continue
                steps = steps_of(traj); ms = (traj.get("info") or {}).get("model_stats") or {}
                preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or [])
                top = [f"{(p.get('class') or '').split('.')[-1]}::{p.get('method')}" for p in preds[:10]]
                gold_rank = ev.get("gold_rank")
                # exposure steps: first step whose OUTPUT shows the method declaration/body of each role
                def first_exposure(role):
                    m = CH[role]["method"]; cls_ = CH[role]["class"].split(".")[-1]; rx = re.compile(r"(static|public|protected|private)[^\n;{]*\b" + re.escape(m) + r"\s*\(")
                    return next((i for i, c, o in steps if rx.search(o) and (cls_ in c or cls_ in o)), None)   # declaration in view AND the declaring class named in the command or the output
                exp = {r: first_exposure(r) for r in ["facade"] + ROLES}
                gold_step = exp[gold_role]
                first_hop = min([x for r, x in exp.items() if r != "facade" and x], default=None)
                # contract evidence: H2's javadoc text visible in some output (the convention sentence)
                conv_words = [w for w in re.findall(r"[a-z]{6,}", (spec.get("convention") or "").lower())][:6]
                jd_rx = re.compile(r"/\*\*(?:(?!\*/).){0,2500}\*/\s*(?:@\w+\s*)*(?:public|protected|private|static|final|synchronized|\s)*[\w<>\[\], .]+\s+" + re.escape(CH["H2"]["method"]) + r"\s*\(", re.S)
                h2_text_seen = any(jd_rx.search(o) for i, c, o in steps)
                # second-caller (pin) evidence: pin test file or method name appears in any command or output
                pin_seen_step = next((i for i, c, o in steps if pin_simple in c or pin_m in c or pin_simple in o or pin_m in o), None)
                # external ownership evidence (Level B): production second caller method name, or external test class/method names
                ext_names = set()
                sc = spec.get("second_caller") or ""
                m_sc = re.search(r"#(\w+)", sc)
                if m_sc: ext_names.add(m_sc.group(1))
                trig_cls = spec["trigger"].split("::")[0].split(".")[-1]
                for t in (spec.get("external_evidence_tests") or []):
                    tc, tm = t.split("::")[0].split(".")[-1], t.split("::")[1]; ext_names.add(tm)
                    if tc not in (trig_cls, pin_simple): ext_names.add(tc)     # a test class shared with the trigger is read by every run and is not evidence
                ext_exposed_step = next((i for i, c, o in steps if any(n in c or n in o for n in ext_names)), None) if ext_names else None     # loose: name visible anywhere (incidental exposure through a chain-file read counts)
                ext_body_seen = next((i for i, c, o in steps if m_sc and re.search(r"\b" + re.escape(m_sc.group(1)) + r"\s*\(", o)), None) if m_sc else None
                sc_cls = (sc.split("#")[0].split(".")[-1].strip() if "#" in sc else "")
                caller_search = lambda c: SEARCH.search(strip_cd(c)) is not None and (CH["H2"]["method"] in c or CH["H3"]["method"] in c) and ("-r" in c or "--include" in c or "src" in c or "source" in c or "*" in c)
                chain_classes = {CH[r]["class"].split(".")[-1] for r in ["facade"] + ROLES}
                sc_off_chain = bool(sc_cls) and sc_cls not in chain_classes      # a caller search can only count as retrieval when the second caller lives outside every chain file (otherwise H1's or the facade's own call site produces the same hit)
                sought = [i for i, c, o in steps if any(n in c for n in ext_names)] + [i for i, c, o in steps if caller_search(c) and sc_off_chain and sc_cls in o]   # strict: the agent typed the evidence name, or searched for callers and an off-chain second caller came back
                ext_seen_step = min(sought) if sought else None
                ec = (rk.get("structured_submission") or {}).get("evidence_chain") or []
                ec_text = " ".join(str(v) for e in ec if isinstance(e, dict) for v in e.values() if isinstance(v, (str, int, float)))
                cited_names = set(ext_names) | {pin_simple, pin_m}
                ext_cited = any(n in ec_text for n in cited_names) if ec_text else False
                # post-gold verification: a defects4j test after the gold was exposed
                tests_steps = [i for i, c, o in steps if "defects4j test" in strip_cd(c)]
                post_gold_test = bool(gold_step and any(t > gold_step for t in tests_steps))
                reads = sum(1 for i, c, o in steps if READ.search(strip_cd(c))); searches = sum(1 for i, c, o in steps if SEARCH.search(strip_cd(c)))
                ranks = {labels.get(t): k + 1 for k, t in enumerate(top) if t in labels}
                order = [t for t in top if t in labels and labels[t] in ROLES]; pos = {labels[t]: k for k, t in enumerate(order)}
                common = [t for t in ["H5", "H4", "H3", "H2", "H1"] if t in pos]; t_ = tau([pos[x] for x in common], [["H5", "H4", "H3", "H2", "H1"].index(x) for x in common]) if len(common) >= 3 else None
                deepest_rank = ranks.get("H5")
                # status rules (uniform with adversarial-break-v1): stall rule 1 & 2, context overflow rule 3
                st_ = man.get("status"); final_gap = last_role = None
                stall = st_ == "timeout" and (ms.get("api_calls") or 0) <= 2 and len(steps) <= 2
                if st_ == "timeout":
                    try:
                        cl = open(f"{rd}/commands.log").read(); t0 = datetime.datetime.fromisoformat(re.search(r"execution_timer_started_at: (\S+)", cl).group(1).replace("Z", "+00:00")).timestamp()
                        evs = [(m["role"], float(m["extra"]["timestamp"])) for m in (traj.get("messages") or []) if m.get("role") in ("assistant", "tool") and (m.get("extra") or {}).get("timestamp") is not None]
                        if evs: last_role = evs[-1][0]; final_gap = round(t0 + 300 - evs[-1][1], 1)
                    except Exception: pass
                    if last_role == "tool" and final_gap is not None and final_gap > 60: stall = True
                if stall: st_ = "provider_stall"
                if st_ == "provider_error":
                    try: raw = open(f"{rd}/raw_agent_output.txt", errors="replace").read()
                    except Exception: raw = ""
                    if "prompt is too long" in raw or "ContextWindowExceededError" in raw: st_ = "context_overflow"
                rank1 = top[0] if top else None; r1 = labels.get(rank1, "off-chain" if rank1 else None)
                if st_ == "provider_stall": cls = "PROVIDER_STALL"
                elif st_ == "provider_error": cls = "INFRASTRUCTURE"
                elif st_ in ("timeout", "invalid_ranking", "context_overflow"): cls = "NO_ANSWER"
                elif st_ != "completed": cls = "INFRASTRUCTURE"
                elif gold_rank == 1: cls = "CORRECT"
                elif gold_step is None: cls = "DISCOVERY_FAILURE"
                elif gold_role == "H3" and ranks.get("H2") and (gold_rank is None or ranks["H2"] < gold_rank): cls = "DEFINER_ATTRIBUTION"
                elif gold_role == "H2" and ranks.get("H3") and (gold_rank is None or ranks["H3"] < gold_rank): cls = "ADAPTER_ATTRIBUTION"
                elif r1 in ROLES and depth_order.index(r1) < depth_order.index(gold_role): cls = "DEPTH_PRIOR"
                elif r1 == "facade": cls = "FACADE_ATTRIBUTION"
                elif r1 in ROLES: cls = "OTHER_CHAIN_ATTRIBUTION"
                else: cls = "OFF_CHAIN_ERROR"
                # Level-B sub-classification of misattributions by evidence use
                if cls in ("DEFINER_ATTRIBUTION", "ADAPTER_ATTRIBUTION"):
                    ext_sub = "EXTERNAL_EVIDENCE_MISREAD" if (ext_seen_step is not None or ext_cited or pin_seen_step is not None) else "EXTERNAL_EVIDENCE_NOT_RETRIEVED"
                else: ext_sub = None
                no_answer_sub = (("BUDGET_EXHAUSTION" if len(steps) >= 50 else "INVALID_SUBMISSION") if st_ == "invalid_ranking" else "TIMEOUT_EXHAUSTION" if st_ == "timeout" else "CONTEXT_OVERFLOW" if st_ == "context_overflow" else None)
                sc_name_seen = next((i for i, c, o in steps if m_sc and (m_sc.group(1) in c or m_sc.group(1) in o)), None) if m_sc else None
                ts = [float((m_.get("extra") or {}).get("timestamp")) for m_ in (traj.get("messages") or []) if (m_.get("extra") or {}).get("timestamp") is not None]
                wall_s = round(max(ts) - min(ts), 1) if len(ts) >= 2 else None
                try:
                    md = re.search(r"^duration_ms: (\d+)", open(f"{rd}/commands.log").read(), re.M)
                    if md: wall_s = round(int(md.group(1)) / 1000.0, 1)
                except Exception: pass
                valid = st_ in ("completed", "timeout", "invalid_ranking", "context_overflow")
                ext_test_names = set(); [ext_test_names.update({t.split("::")[0].split(".")[-1], t.split("::")[1]}) for t in (spec.get("external_evidence_tests") or [])]
                ext_test_seen = next((i for i, c, o in steps if any(n in c or n in o for n in ext_test_names)), None) if ext_test_names else None
                rows.append({"pair_id": spec["pair_id"], "project": spec["project"], "bug": spec["bug"], "family": spec["family"], "arm": arm, "variant_id": V, "server": srv, "model": MODEL_OF[srv], "model_id": mid,
                             "h2_discovered": exp["H2"] is not None, "h3_discovered": exp["H3"] is not None, "wall_s": wall_s, "valid": valid, "external_evidence_cited": ext_cited, "evidence_chain_text": ec_text[:1500],
                             "production_second_caller_exposed": sc_name_seen is not None, "production_second_caller_step": sc_name_seen, "production_second_caller_body_seen": ext_body_seen is not None,
                             "production_second_caller_retrieved": (any(m_sc.group(1) in c for i, c, o in steps) or any(caller_search(c) and sc_off_chain and sc_cls in o for i, c, o in steps)) if m_sc else False, "second_caller_off_chain": sc_off_chain,
                             "external_test_retrieved": any(n in c for i, c, o in steps for n in ext_test_names) if ext_test_names else False, "external_test_exposed": ext_test_seen is not None, "external_test_step": ext_test_seen, "pin_retrieved": pin_seen_step is not None,
                             "external_evidence_exposed": ext_exposed_step is not None, "external_evidence_exposed_step": ext_exposed_step,
                             "any_external_evidence_retrieved": (ext_seen_step is not None) or ext_cited or (pin_seen_step is not None), "sibling_inverse_evidence_retrieved": None,
                             "run": os.path.basename(rd), "status": st_, "harness_status": man.get("status"), "final_gap_s": final_gap, "answered": st_ == "completed", "no_answer": st_ in ("timeout", "invalid_ranking", "context_overflow"),
                             "gold": f"{G['class']}::{G['method']}", "gold_role": gold_role, "gold_rank": gold_rank, "acc_at_1": gold_rank == 1, "acc_at_3": bool(gold_rank and gold_rank <= 3), "acc_at_5": bool(gold_rank and gold_rank <= 5), "acc_at_10": bool(gold_rank and gold_rank <= 10),
                             "mrr": round(1.0 / gold_rank, 4) if gold_rank else 0.0, "submitted_top10": top, "n_predictions": len(preds), "rank1": rank1, "rank1_role": r1, "role_ranks": ranks,
                             "first_facade_exposure": exp["facade"], "first_hop_exposure": first_hop, "first_gold_exposure": gold_step, "h2_exposure": exp["H2"], "h3_exposure": exp["H3"], "gold_discovered": gold_step is not None,
                             "contract_evidence_retrieved": bool(h2_text_seen), "second_caller_evidence_retrieved": pin_seen_step is not None, "pin_seen_step": pin_seen_step, "external_evidence_retrieved": (ext_seen_step is not None) or ext_cited, "external_evidence_step": ext_seen_step, "external_caller_body_seen": ext_body_seen is not None, "post_gold_verification": post_gold_test,
                             "tool_calls": len(steps), "api_calls": ms.get("api_calls"), "test_executions": len(tests_steps), "file_reads": reads, "repository_searches": searches,
                             "deepest_stage_rank": deepest_rank, "reverse_depth_tau": round(t_, 3) if t_ is not None else None, "classification": cls, "evidence_subclass": ext_sub, "no_answer_subclass": no_answer_sub, "cost_usd": ms.get("instance_cost"), "wall_ms": man.get("duration_ms")})
json.dump(rows, open(out_path, "w"), indent=1); print(len(rows), "runs ->", out_path)
