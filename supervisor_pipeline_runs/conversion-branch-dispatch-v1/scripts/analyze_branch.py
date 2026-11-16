"""Observable-only analysis of the BRANCH-DISPATCH GPT-5.6 diagnostic (CONVERSION-BRANCH-CONTROL-01 / CONVERSION-BRANCH-TREATMENT-01).
Adds branch-resolution metrics (selector/condition/both-implementation discovery, wrong-branch inspection, backtracking) and ownership-attribution classification.
Adds dispatch-resolution metrics (route A-H, calls/files/searches spent resolving, detours, backtracking) on top of the five-hop metrics.
Reads bash commands, tool outputs, test executions and submitted rankings from mini-swe-agent.traj.json + run artifacts. Never reads
reasoning_content / reasoning_items. Usage: analyze_long.py <runs_root (…/benchmark_runs/<agent>)> <out_json> [--runs 1-5]"""
import json, os, re, sys, glob, statistics, argparse
ap = argparse.ArgumentParser(); ap.add_argument("runs_root"); ap.add_argument("out"); ap.add_argument("--runs", default="1-5"); ap.add_argument("--label", default="NON-CANONICAL / BRANCH-DISPATCH DIAGNOSTIC / GPT-5.6"); a = ap.parse_args()
LO, HI = (int(x) for x in a.runs.split("-"))
CHAIN = [("facade", "Conversion", "intArrayToLong", "intArrayToLong(final int[] src", "return ArrayUtils.gather(src, srcPos, dstInit, dstPos, nInts);"),
         ("H1", "ArrayUtils", "gather", "gather(final int[] array", "return EnumUtils.compose(run, initial, at);"),
         ("H2", "EnumUtils", "compose", "compose(final int[] run", "return BitField.widen(run, initial, at, width, field);"),
         ("H3", "BitField", "widen", "widen(final int[] run", "return Folding.forWidth(width).fold(words, initial, at, width, field);"),
         ("H4", "ObjectUtils", "combine", "combine(final long[] words", "NumberUtils.overlay(total, words[i], i, at, width, field);"),
         ("H5", "NumberUtils", "overlay", "overlay(final long holder", None)]
ARMS = {"CONVERSION-BRANCH-CONTROL-01": dict(arm="CONTROL", gold_class="org.apache.commons.lang3.Conversion", gold_method="intArrayToLong", gold_decl="intArrayToLong(final int[] src", buggy="shift = (i + dstPos) * 32;"),
        "CONVERSION-BRANCH-TREATMENT-01": dict(arm="TREATMENT", gold_class="org.apache.commons.lang3.math.NumberUtils", gold_method="overlay", gold_decl="overlay(final long holder", buggy="shift = (index + at) * width;")}
CONTRACT = {"H_in_bits": "in bits", "facade_guard": "(nInts - 1) * 32 + dstPos >= 64", "J2_sibling_short": "i * 16 + dstPos", "J3_sibling_byte": "i * 8 + dstPos", "J4_inverse_pattern": "i * 32 + srcPos", "I_longToIntArray": "longToIntArray",
            "M_test_dstPos_24": "0x123456789ABCDEF0L, 24, 1", "M_test_dstPos_16": "0x123456789ABCDEF0L, 16, 2", "M_test_dstPos_8": "0x123456789ABCDEF0L, 8, 2"}
OTHER = {"assertion_msg": "expected:<64729929216> but was:<252851286>", "d4j_modified_class_output": "d4j.classes.modified", "sibling_shift_left": "<< shift", "Integer_SIZE": "Integer.SIZE", "field_derivation": "(1L << width) - 1"}
PAYLOAD_TOKENS = {"testLang1112", "ConversionTest", "Conversion", "intArrayToLong", "src", "assertEquals", "int", "new", "final", "Test"}
NOVEL_WATCH = ["gather", "compose", "widen", "combine", "overlay", "Folding", "StandardFolding", "NarrowFolding", "STANDARD", "NARROW", "forWidth", "fold(", "EnumUtils", "BitField", "ObjectUtils", "NumberUtils", "ArrayUtils", "dstPos", "srcPos", "nInts", "dstInit", "shift", "longToIntArray", "0xffffffffL", "shortArrayToLong", "byteArrayToLong", "intToLong", "binaryToLong", "endian", "Lsb0", "mask", "bits", "field", "holder", "width", "Integer.SIZE", "& ~"]
def rj(p):
    try: return json.load(open(p))
    except Exception: return None
def strip_cd(c):
    c = c.strip()
    for _ in range(2):
        c = re.sub(r"""^cd\s+(?:'[^']*'|"[^"]*"|\S+)\s*(?:&&|;)\s*""", '', c)
        c = re.sub(r"""^ROOT=(?:'[^']*'|"[^"]*"|\S+)\s*;?\s*(?:cd\s+"?\$ROOT"?\s*(?:&&|;)\s*)?""", '', c)
    return c.replace('$ROOT/', '').replace('"$ROOT"/', '')
def is_search(c): return bool(re.search(r'\b(rg|grep|find|fd|ag)\b', c))
def is_repo_wide(c): return bool(re.search(r'\bgrep\b[^|;]*\s-[a-zA-Z]*[rR]', c)) or bool(re.search(r'\brg\b', c))
def is_test(c): return "defects4j test" in c
def opened_files(c): return re.findall(r'(?:cat|less|more|head|tail|nl|sed -n \S+|awk)\b[^|;&]*?([A-Za-z0-9_/.-]+\.java)', c)
def steps_from(traj):
    msgs = traj.get("messages", []); outs = {m.get("tool_call_id"): (m.get("content") or "") for m in msgs if m.get("role") == "tool"}; steps = []; submit = None
    for m in msgs:
        if m.get("role") != "assistant": continue
        for tc in m.get("tool_calls") or []:
            fn = tc.get("function") or {}; name = fn.get("name"); args = fn.get("arguments")
            try: args = json.loads(args) if isinstance(args, str) else (args or {})
            except Exception: args = {}
            if name == "bash": steps.append({"idx": len(steps) + 1, "command": strip_cd(args.get("command", "")), "output": outs.get(tc.get("id"), "")})
            elif name == "submit_fault_localization": submit = {"idx": len(steps) + 1, "predictions": args.get("predictions"), "evidence_chain": args.get("evidence_chain")}
    return steps, submit, msgs
def first_out(steps, needle): return next((s["idx"] for s in steps if needle in s["output"]), None)
def first_cmd(steps, pred): return next((s["idx"] for s in steps if pred(s["command"])), None)
def analyze(rdir, vid, spec):
    man = rj(os.path.join(rdir, "run_manifest.json")) or {}; ev = rj(os.path.join(rdir, "evaluation.json")) or {}; rk = rj(os.path.join(rdir, "ranking.json")) or {}; pr = rj(os.path.join(rdir, "prompt.json")) or {}; si = rj(os.path.join(rdir, "source_integrity.json")) or {}
    traj = rj(os.path.join(rdir, "mini-swe-agent.traj.json")) or {}; steps, submit, msgs = steps_from(traj); ms = (traj.get("info") or {}).get("model_stats") or {}
    preds = (rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or (submit or {}).get("predictions") or []
    top = [f"{p.get('class')}::{p.get('method')}" for p in preds[:10]]; gold_key = f"{spec['gold_class']}::{spec['gold_method']}"; gold_rank = ev.get("gold_rank")
    if gold_rank is None and top: gold_rank = next((i + 1 for i, k in enumerate(top) if k == gold_key), None)
    cl = open(os.path.join(rdir, "commands.log")).read() if os.path.exists(os.path.join(rdir, "commands.log")) else ""; raw = open(os.path.join(rdir, "raw_agent_output.txt"), errors="replace").read() if os.path.exists(os.path.join(rdir, "raw_agent_output.txt")) else ""
    timing = {"execution_timer_started_at": (re.search(r"execution_timer_started_at: (\S+)", cl) or [None, None])[1], "duration_ms": int((re.search(r"duration_ms: (\d+)", cl) or [None, "0"])[1]) or None, "timed_out": "timed_out: true" in cl, "provider_retry_lines": raw.count("Retrying"), "provider_error_excerpt": (re.search(r"raised ([^\n]{0,160})", raw) or [None, None])[1],
              "blocked_on": ("model response" if (steps and msgs and msgs[-1].get("role") == "tool" and man.get("status") == "timeout") else ("n/a" if man.get("status") != "timeout" else "unclear"))}
    # chain node exposure (first OUTPUT showing the node's declaration or its call-to-next line), and the command that did it
    nodes = {}
    for tag, cls, meth, decl, call in CHAIN:
        d = first_out(steps, decl); c = first_out(steps, call) if call else None; body_seen = c
        e = min([x for x in (d, c) if x] or [None]) if (d or c) else None
        cmd = next((s["command"] for s in steps if s["idx"] == e), "") if e else ""
        nodes[tag] = {"class": cls, "method": meth, "decl_first_shown": d, "call_to_next_first_shown": c, "first_exposed": e, "exposing_cmd": cmd[:200], "name_searched_first_at": first_cmd(steps, lambda x, m=meth: m in x and is_search(x)), "class_searched_or_opened_first_at": first_cmd(steps, lambda x, k=cls: k in x)}
    gold_decl = first_out(steps, spec["gold_decl"]); buggy = first_out(steps, spec["buggy"]); gold_step = min([x for x in (gold_decl, buggy) if x] or [None]) if (gold_decl or buggy) else None
    gold_cmd = next((s["command"] for s in steps if s["idx"] == gold_step), "") if gold_step else ""
    contract = {k: first_out(steps, v) for k, v in CONTRACT.items()}; other = {k: first_out(steps, v) for k, v in OTHER.items()}
    first_contract = min([v for v in contract.values() if v] or [None]) if any(contract.values()) else None
    contract_after_gold = sorted(k for k, v in contract.items() if v and gold_step and v > gold_step)
    post = [s for s in steps if gold_step and s["idx"] > gold_step]
    novel = []
    for s in steps:
        if not is_search(s["command"]): continue
        earlier = "\n".join(x["output"] for x in steps if x["idx"] < s["idx"]) + "\n" + "\n".join(x["command"] for x in steps if x["idx"] < s["idx"])
        for w in NOVEL_WATCH:
            if w in s["command"] and w not in earlier and w not in PAYLOAD_TOKENS: novel.append({"step": s["idx"], "token": w, "command": s["command"][:140]})
    # ---- chain completion metrics (TREATMENT) ----
    cc = {}
    if spec["arm"] == "TREATMENT":
        exp = {t: nodes[t]["first_exposed"] for t in ("facade", "H1", "H2", "H3", "H4")}; exp["H5"] = gold_step
        reached = {t: exp[t] is not None for t in ("H1", "H2", "H3", "H4", "H5")}
        order = [exp[t] for t in ("facade", "H1", "H2", "H3", "H4", "H5")]
        sequential = all(order) and all(order[i] < order[i + 1] for i in range(len(order) - 1))
        # was each hop's first exposure produced by a command naming that hop (or its class) AFTER the previous node's call-to-next line was on screen?
        via_chain = {}
        for i, t in enumerate(("H1", "H2", "H3", "H4", "H5")):
            prev = ("facade", "H1", "H2", "H3", "H4")[i]; m = nodes[t]["method"]; k = nodes[t]["class"]; e = exp[t]; pc = nodes[prev]["call_to_next_first_shown"]; cmd = nodes[t]["exposing_cmd"] if t != "H5" else gold_cmd
            via_chain[t] = bool(e and pc and pc <= e and (m in cmd or k in cmd))
        skipped = [t for t in ("H1", "H2", "H3", "H4") if gold_step and (exp[t] is None or exp[t] > gold_step)]
        gold_by_name = bool(gold_step and ("overlay" in gold_cmd or "NumberUtils" in gold_cmd))
        h4_call_seen_before_gold = bool(nodes["H4"]["call_to_next_first_shown"] and gold_step and nodes["H4"]["call_to_next_first_shown"] <= gold_step)
        lexical_bypass = bool(gold_step and is_search(gold_cmd) and not gold_by_name)
        repo_wide_shortcut = bool(gold_step and is_repo_wide(gold_cmd) and not h4_call_seen_before_gold)
        direct_gold_search = bool(gold_step and gold_by_name and not h4_call_seen_before_gold)
        last_reached = max([i + 1 for i, t in enumerate(("H1", "H2", "H3", "H4", "H5")) if reached[t]] or [0])
        abandoned = bool(man.get("status") == "completed" and gold_step is None)
        timeout_before_gold = bool(man.get("status") == "timeout" and gold_step is None)
        path = " → ".join([f"facade({exp['facade']})"] + [f"{t}({exp[t]})" if exp[t] else f"{t}(—)" for t in ("H1", "H2", "H3", "H4", "H5")] + [f"rank {gold_rank}" if gold_rank else ("timeout" if man.get("status") == "timeout" else "no gold in ranking")])
        if gold_step is None: route = "timeout before gold" if man.get("status") == "timeout" else "abandoned chain (submitted without exposing the gold)"
        elif sequential and all(via_chain.values()): route = "A. explicit five-hop traversal (each hop found by name after the previous hop's call was shown)"
        elif not skipped and h4_call_seen_before_gold and gold_by_name: route = "A'. full traversal (all hops shown in order; some hop exposed by a non-name command)"
        elif lexical_bypass or repo_wide_shortcut: route = "B/C. lexical or repository-wide shortcut to the gold (hop(s) skipped: %s)" % (",".join(skipped) or "none")
        elif direct_gold_search: route = "D. direct gold search before hop 4's call was shown"
        else: route = "E. other / unclear (skipped: %s)" % (",".join(skipped) or "none")
        inc = {}; prevstep = 0
        for t in ("H1", "H2", "H3", "H4", "H5"):
            inc[f"calls_to_{t}"] = (exp[t] - 1) if exp[t] else None; inc[f"incremental_to_{t}"] = (exp[t] - prevstep) if exp[t] else None; prevstep = exp[t] or prevstep
        cc = {"exposure_steps": exp, "reached": reached, "followed_all_five_sequentially": sequential and all(via_chain.values()), "sequential_order": sequential, "via_chain_per_hop": via_chain, "skipped_hops": skipped, "lexical_bypass": lexical_bypass, "repository_wide_shortcut": repo_wide_shortcut, "direct_gold_search": direct_gold_search, "abandoned_chain": abandoned, "timeout_before_gold": timeout_before_gold, "last_hop_reached": last_reached, "gold_exposed_by_name": gold_by_name, "chain_path": path, "route": route, "increments": inc}
    else:
        cc = {"chain_path": f"facade/gold({gold_step}) → rank {gold_rank}", "route": "n/a (0-hop)", "exposure_steps": {"facade": gold_step}}
    disp = {}
    if spec["arm"] == "TREATMENT":
        DM = {"abstraction_decl": "public abstract class Folding", "abstract_method": "public abstract long fold(", "binding_line": "STANDARD = new StandardFolding()", "narrow_binding_line": "NARROW = new NarrowFolding()", "selector_decl": "public static Folding forWidth(final int width)", "condition_line": "width < Integer.SIZE ? NARROW : STANDARD", "impl_decl": "class StandardFolding extends Folding", "impl_override": "public long fold(final long[] values", "impl_call": "return ObjectUtils.combine(values, initial, at, width, field);", "alt_decl": "class NarrowFolding extends Folding", "alt_loop": "final int shift = i * width + at;", "h4_decl": "combine(final long[] words", "width_is_integer_size": "final int width = Integer.SIZE;"}
        fo = {k: first_out(steps, v) for k, v in DM.items()}
        h3_body = nodes["H3"]["call_to_next_first_shown"]  # the Folding.STANDARD.fold line on screen = first encounter with the abstraction
        resolved = min([x for x in (fo["impl_call"], fo["h4_decl"]) if x] or [None]) if (fo["impl_call"] or fo["h4_decl"]) else None
        rcmd = next((st["command"] for st in steps if st["idx"] == resolved), "") if resolved else ""
        def fc(pred): return first_cmd(steps, pred)
        cm = {"first_search_interface": fc(lambda c: "Folding" in c and is_search(c)), "first_cmd_mentioning_interface": fc(lambda c: "Folding" in c), "first_search_abstract_method": fc(lambda c: re.search(r"\bfold\b", c) is not None and is_search(c)),
              "first_binding_lookup": fc(lambda c: "STANDARD" in c or "Folding.java" in c), "first_impl_lookup": fc(lambda c: "StandardFolding" in c), "first_extends_implements_search": fc(lambda c: is_search(c) and re.search(r"extends Folding|implements|extends", c) is not None and "Folding" in c),
              "first_combine_cmd": fc(lambda c: "combine" in c), "first_ObjectUtils_cmd": fc(lambda c: "ObjectUtils" in c), "first_javap_jshell": fc(lambda c: re.search(r"\bjshell\b|\bjavap\b", c) is not None), "first_open_Folding_java": fc(lambda c: "Folding.java" in c and not is_search(c)), "first_open_StandardFolding_java": fc(lambda c: "StandardFolding.java" in c)}
        win = [st for st in steps if h3_body and resolved and h3_body < st["idx"] <= resolved] if (h3_body and resolved) else []
        chain_files = {"BitField.java", "Folding.java", "StandardFolding.java", "ObjectUtils.java", "Conversion.java", "ConversionTest.java", "NumberUtils.java", "EnumUtils.java", "ArrayUtils.java"}
        win_files = sorted({os.path.basename(f) for st in win for f in opened_files(st["command"])}); detours = [f for f in win_files if f not in chain_files]
        pre_tokens_shown = lambda step: any(t in "\n".join(x["output"] for x in steps if x["idx"] < step) for t in ("Folding", "STANDARD", "StandardFolding"))
        prior_disp_cmd = any(("Folding" in st["command"] or "STANDARD" in st["command"] or re.search(r"\bfold\b", st["command"])) for st in steps if resolved and st["idx"] < resolved)
        binding_before = bool(fo["binding_line"] and resolved and fo["binding_line"] < resolved)
        if resolved is None: route = "G. failed to resolve dispatch (next stage never exposed)"
        elif re.search(r"\bjshell\b|\bjavap\b", rcmd): route = "H. other: runtime resolution (javap/jshell)"
        elif cc.get("direct_gold_search"): route = "F. direct gold search"
        elif ("combine" in rcmd or "ObjectUtils" in rcmd) and not prior_disp_cmd and not pre_tokens_shown(resolved): route = "E. lexical shortcut (next-stage name used before any dispatch token was displayed)"
        elif ("combine" in rcmd or "ObjectUtils" in rcmd) and not prior_disp_cmd: route = "D. caller/callee heuristic shortcut (next stage reached without searching the abstraction/binding)"
        elif binding_before and ("StandardFolding" in rcmd or "Folding.java" in rcmd or "STANDARD" in rcmd): route = "B. interface -> factory/binding -> implementation"
        elif binding_before: route = "B'. binding displayed first, implementation then reached by a method-name/implementation search"
        elif is_repo_wide(rcmd) and ("Folding" in rcmd or re.search(r"\bfold\b", rcmd)): route = "C. repository-wide implementation search"
        elif ("Folding" in rcmd or re.search(r"\bfold\b", rcmd) or "StandardFolding" in rcmd): route = "A. interface -> implementation search"
        else: route = "H. other: " + rcmd[:60]
        post = [st for st in steps if resolved and st["idx"] > resolved]
        backtrack = [st["idx"] for st in post if re.search(r"Folding|StandardFolding|widen\b", st["command"])]
        top1 = top[0] if top else None; earlier = {"intArrayToLong", "widen", "compose", "gather", "combine", "fold"}
        directed = [st["idx"] for st in win if re.search(r"Folding|StandardFolding|STANDARD|\bfold\b", st["command"])]
        both_in_one = bool(rcmd and "Folding.java" in rcmd and "StandardFolding.java" in rcmd)
        disp = {"dispatch_directed_calls_in_window": len(directed), "dispatch_directed_steps": directed, "binding_and_impl_read_in_same_command": both_in_one, "first_encounter_abstraction_step": h3_body, "first_search_for_interface": cm["first_search_interface"], "first_binding_lookup": cm["first_binding_lookup"], "binding_line_first_shown": fo["binding_line"], "abstraction_decl_first_shown": fo["abstraction_decl"], "abstract_method_first_shown": fo["abstract_method"], "impl_first_shown": min([x for x in (fo["impl_decl"], fo["impl_override"]) if x] or [None]) if (fo["impl_decl"] or fo["impl_override"]) else None, "impl_call_first_shown": fo["impl_call"], "h4_decl_first_shown": fo["h4_decl"],
                "dispatch_resolved": resolved is not None, "resolved_step": resolved, "resolving_cmd": rcmd[:200], "calls_spent_resolving": (resolved - h3_body) if (resolved and h3_body) else None, "files_opened_while_resolving": win_files, "searches_while_resolving": sum(1 for st in win if is_search(st["command"])), "window_commands": [st["command"][:120] for st in win],
                "wrong_implementations_inspected": 0, "detour_files_while_resolving": detours, "backtracked_to_boundary_after_resolution": bool(backtrack), "backtrack_steps": backtrack, "ranked_earlier_hop_instead_of_gold": bool(gold_rank != 1 and top1 and top1.split("::")[-1] in earlier), "top1_when_not_gold": (top1 if gold_rank != 1 else None), "ranked_interface_or_impl_first": bool(top1 and ("Folding" in top1)), "abandoned_chain": cc.get("abandoned_chain"), "route": route, "cmd_markers": cm}
    br = {}
    if spec["arm"] == "TREATMENT":
        sel_shown = fo["selector_decl"]; cond_shown = fo["condition_line"]; std_shown = min([x for x in (fo["impl_decl"], fo["impl_override"]) if x] or [None]) if (fo["impl_decl"] or fo["impl_override"]) else None
        # StandardFolding vs NarrowFolding: which file's CONTENT was displayed first (decl line or loop line)
        nar_shown = min([x for x in (fo["alt_decl"], fo["alt_loop"]) if x] or [None]) if (fo["alt_decl"] or fo["alt_loop"]) else None
        nar_named = first_out(steps, "NarrowFolding"); std_named = first_out(steps, "StandardFolding")
        nar_opened = first_cmd(steps, lambda c: "NarrowFolding.java" in c and not is_search(c)); std_opened = first_cmd(steps, lambda c: "StandardFolding.java" in c and not is_search(c))
        nar_any_cmd = first_cmd(steps, lambda c: "NarrowFolding" in c or "NARROW" in c)
        width_src_shown = fo["width_is_integer_size"]; width_searched = first_cmd(steps, lambda c: "Integer.SIZE" in c or re.search(r"\bwidth\b", c) is not None and is_search(c))
        sel_searched = first_cmd(steps, lambda c: "forWidth" in c); javap_folding = first_cmd(steps, lambda c: re.search(r"javap[^|;]*(Folding|BitField)", c) is not None); jshell_any = first_cmd(steps, lambda c: "jshell" in c)
        # wrong-branch metrics
        both_found = bool(std_named and nar_named); both_opened = bool(std_shown and nar_shown)
        wrong_first = bool(nar_shown and (std_shown is None or nar_shown < std_shown))
        # 'followed' the wrong branch = after NarrowFolding's body was shown, the agent searched for its callers/usages or ran/grepped its internals before showing StandardFolding's call to combine
        nar_follow_cmds = [st["idx"] for st in steps if nar_shown and st["idx"] > nar_shown and ("NarrowFolding" in st["command"] or "NARROW" in st["command"]) and (resolved is None or st["idx"] < resolved)]
        wrong_followed = bool(nar_follow_cmds)
        # runtime branch inference: observable proxies
        runtime_inference = {"width_source_line_shown_before_resolution": bool(width_src_shown and resolved and width_src_shown < resolved), "condition_shown_before_resolution": bool(cond_shown and resolved and cond_shown <= resolved), "selector_searched": sel_searched, "executed_selector_or_widen_in_jshell": bool(first_cmd(steps, lambda c: "jshell" in c and ("forWidth" in c or "widen" in c or "Folding" in c)))}
        # backtracking: after resolution, commands returning to the dispatch layer / alternate
        back = [st["idx"] for st in steps if resolved and st["idx"] > resolved and re.search(r"Folding|NARROW|STANDARD|forWidth|widen\b", st["command"])]
        # attribution classification of the rank-1 choice
        top1 = top[0] if top else None; m1 = (top1 or "").split("::")[-1]; c1 = (top1 or "").split("::")[0].split(".")[-1]
        if top1 is None: cat = "H. other (no submission)"
        elif top1 == gold_key: cat = "A. true gold"
        elif m1 == "intArrayToLong": cat = "B. facade"
        elif m1 == "forWidth": cat = "C. selector/factory"
        elif c1 == "Folding": cat = "D. abstraction/interface"
        elif c1 == "StandardFolding": cat = "E. concrete implementation wrapper"
        elif c1 == "NarrowFolding": cat = "G. alternative branch implementation"
        elif m1 in ("gather", "compose", "widen", "combine"): cat = "F. earlier hop"
        else: cat = "H. other: " + top1
        discovery = gold_step is not None; attribution_failure = bool(discovery and gold_rank != 1)
        br = {"selector_discovered": bool(sel_shown or cond_shown or sel_searched), "selector_first_shown": sel_shown, "condition_first_shown": cond_shown, "both_implementations_discovered": both_found, "both_implementations_opened": both_opened, "standard_first_shown": std_shown, "narrow_first_shown": nar_shown, "narrow_named_first_at": nar_named, "standard_named_first_at": std_named,
              "narrow_opened_at": nar_opened, "standard_opened_at": std_opened, "first_cmd_mentioning_narrow": nar_any_cmd, "wrong_branch_inspected_first": wrong_first, "wrong_branch_followed": wrong_followed, "wrong_branch_follow_cmds": nar_follow_cmds, "ignored_alternate": not bool(nar_shown), "correct_runtime_branch_inferred_observably": runtime_inference, "width_source_line_shown": width_src_shown,
              "backtracking_occurred": bool(back), "backtrack_steps": back, "calls_spent_resolving_branch": disp.get("calls_spent_resolving"), "files_opened_during_branch_resolution": disp.get("files_opened_while_resolving"), "branch_resolution_searches": disp.get("searches_while_resolving"), "first_gold_exposure": gold_step, "final_gold_rank": gold_rank,
              "rank1_category": cat, "discovery_success": discovery, "attribution_failure": attribution_failure, "ranked_selector": any(x.endswith("::forWidth") for x in top), "ranked_abstraction": any(x.endswith("Folding::fold") and "StandardFolding" not in x and "NarrowFolding" not in x for x in top), "ranked_wrong_implementation": any("NarrowFolding" in x for x in top), "ranked_wrapper": any("StandardFolding" in x for x in top), "ranked_facade": any(x.endswith("::intArrayToLong") for x in top), "rank_of_narrow": next((i + 1 for i, x in enumerate(top) if "NarrowFolding" in x), None), "rank_of_facade": next((i + 1 for i, x in enumerate(top) if x.endswith("::intArrayToLong")), None), "rank_of_wrapper": next((i + 1 for i, x in enumerate(top) if "StandardFolding" in x), None)}
    info = {"tool_calls_to_first_gold": (gold_step - 1) if gold_step else None, "calls_after_first_gold": (len(steps) - gold_step) if gold_step else None, "external_contract_retrieval_count": sum(1 for v in contract.values() if v), "contract_markers_after_gold": contract_after_gold,
            "tests_executed": [s["command"][:110] for s in steps if is_test(s["command"])], "tests_executed_count": sum(1 for s in steps if is_test(s["command"])),
            "source_files_opened": sorted({os.path.basename(f) for s in steps for f in opened_files(s["command"])}), "unique_search_queries": len({s["command"] for s in steps if is_search(s["command"])}), "search_count": sum(1 for s in steps if is_search(s["command"])),
            "post_gold_searches": [s["command"][:110] for s in post if is_search(s["command"])], "post_gold_opens": [s["command"][:110] for s in post if opened_files(s["command"])], "javap_jshell_steps": [s["idx"] for s in steps if re.search(r'\bjshell\b|\bjavap\b', s["command"])],
            "build_properties_cmd": first_cmd(steps, lambda c: "defects4j.build.properties" in c or ".defects4j.config" in c or "classes.modified" in c), "first_command": steps[0]["command"][:160] if steps else None, "first_search": next((s["command"][:160] for s in steps if is_search(s["command"])), None), "first_search_idx": first_cmd(steps, is_search), "first_action_is_test_run": bool(steps) and is_test(steps[0]["command"])}
    return {"run_id": "/".join(rdir.split("/")[-2:]), "variant_id": vid, "arm": spec["arm"], "gold": gold_key, "status": man.get("status"), "status_reason": man.get("status_reason"), "timing": timing,
            "gold_rank": gold_rank, "hit_at_1": gold_rank == 1, "hit_at_3": bool(gold_rank and gold_rank <= 3), "hit_at_5": bool(gold_rank and gold_rank <= 5), "hit_at_10": bool(gold_rank and gold_rank <= 10), "reciprocal_rank": (1.0 / gold_rank) if gold_rank else 0.0,
            "top10": top, "tool_call_count": (man.get("metrics") or {}).get("tool_call_count") or len(steps), "api_calls": ms.get("api_calls"), "cost_usd": ms.get("instance_cost"), "source_integrity_ok": si.get("ok"), "prompt_version": pr.get("version"), "base_prompt_sha256": pr.get("base_prompt_sha256"),
            "nodes": nodes, "gold_first_exposed_step": gold_step, "gold_exposing_cmd": gold_cmd[:200], "buggy_line_first_shown": buggy, "gold_decl_first_shown": gold_decl, "contract_first_shown": contract, "first_contract_step": first_contract, "other_markers": other,
            "chain": cc, "dispatch": disp, "branch": br, "info_distance": info, "novel_search_vocabulary": novel, "total_bash_steps": len(steps), "steps": [{"idx": s["idx"], "command": s["command"][:300], "output_head": s["output"][:120].replace("\n", " | ")} for s in steps],
            "agent_reported_evidence_chain_unverified": (submit or {}).get("evidence_chain"), "hidden_reasoning_read": False}
runs = []
for vid, spec in ARMS.items():
    for rdir in sorted(glob.glob(os.path.join(a.runs_root, vid, "run-*"))):
        if LO <= int(os.path.basename(rdir).split("-")[-1]) <= HI: runs.append(analyze(rdir, vid, spec))
def mm(xs): xs = [x for x in xs if x is not None]; return [round(statistics.mean(xs), 2), statistics.median(xs)] if xs else [None, None]
def agg(rs):
    comp = [r for r in rs if r["status"] == "completed"]; T = rs and rs[0]["arm"] == "TREATMENT"
    rate = lambda k: (sum(1 for r in comp if r[k]) / len(comp)) if comp else None; rate_all = lambda k: (sum(1 for r in rs if r[k]) / len(rs)) if rs else None
    out = {"n": len(rs), "completed": len(comp), "timeout": sum(1 for r in rs if r["status"] == "timeout"), "other_status": [(r["run_id"], r["status"]) for r in rs if r["status"] not in ("completed", "timeout")],
           "acc_at_1": rate("hit_at_1"), "acc_at_3": rate("hit_at_3"), "acc_at_5": rate("hit_at_5"), "acc_at_10": rate("hit_at_10"), "mrr": (sum(r["reciprocal_rank"] for r in comp) / len(comp)) if comp else None,
           "acc_at_1_all_runs": rate_all("hit_at_1"), "acc_at_3_all_runs": rate_all("hit_at_3"), "acc_at_5_all_runs": rate_all("hit_at_5"), "acc_at_10_all_runs": rate_all("hit_at_10"), "mrr_all_runs": (sum(r["reciprocal_rank"] for r in rs) / len(rs)) if rs else None,
           "gold_ranks": [r["gold_rank"] for r in rs], "tool_calls": [r["tool_call_count"] for r in rs], "tool_calls_mean_median": mm([r["tool_call_count"] for r in rs]), "api_calls": [r["api_calls"] for r in rs], "api_calls_mean_median": mm([r["api_calls"] for r in rs]),
           "first_gold_step": [r["gold_first_exposed_step"] for r in rs], "first_gold_step_mean_median": mm([r["gold_first_exposed_step"] for r in rs]), "buggy_line_step": [r["buggy_line_first_shown"] for r in rs],
           "calls_to_first_gold": [r["info_distance"]["tool_calls_to_first_gold"] for r in rs], "calls_after_gold": [r["info_distance"]["calls_after_first_gold"] for r in rs], "calls_after_gold_mean_median": mm([r["info_distance"]["calls_after_first_gold"] for r in rs]),
           "costs": [r["cost_usd"] for r in rs], "total_cost_usd": sum(r["cost_usd"] or 0 for r in rs), "contract_retrieval_count": [r["info_distance"]["external_contract_retrieval_count"] for r in rs], "runs_with_contract_evidence_before_rank": sum(1 for r in rs if r["first_contract_step"]),
           "runs_with_new_contract_evidence_after_gold": sum(1 for r in rs if r["info_distance"]["contract_markers_after_gold"]), "tests_executed": [r["info_distance"]["tests_executed_count"] for r in rs], "source_files_opened": [len(r["info_distance"]["source_files_opened"]) for r in rs], "unique_search_queries": [r["info_distance"]["unique_search_queries"] for r in rs],
           "novel_vocab_events": sum(len(r["novel_search_vocabulary"]) for r in rs), "runs_with_novel_vocab": sum(1 for r in rs if r["novel_search_vocabulary"]), "build_properties_observably_used": sum(1 for r in rs if r["info_distance"]["build_properties_cmd"] or r["other_markers"]["d4j_modified_class_output"]), "source_integrity_ok_all": all(r["source_integrity_ok"] for r in rs) if rs else None,
           "provider_retry_lines_total": sum(r["timing"]["provider_retry_lines"] for r in rs), "durations_s": [round((r["timing"]["duration_ms"] or 0) / 1000) for r in rs]}
    if T:
        D = [r["dispatch"] for r in rs]
        out.update({"dispatch_resolution_success_rate": sum(1 for d in D if d["dispatch_resolved"]) / len(D), "dispatch_routes": {t: sum(1 for d in D if d["route"] == t) for t in sorted({d["route"] for d in D})}, "calls_spent_resolving": [d["calls_spent_resolving"] for d in D], "calls_spent_resolving_mean_median": mm([d["calls_spent_resolving"] for d in D]),
                    "dispatch_directed_calls": [d["dispatch_directed_calls_in_window"] for d in D], "dispatch_directed_calls_mean_median": mm([d["dispatch_directed_calls_in_window"] for d in D]), "binding_and_impl_read_together": sum(1 for d in D if d["binding_and_impl_read_in_same_command"]),
                    "files_opened_while_resolving": [len(d["files_opened_while_resolving"]) for d in D], "searches_while_resolving": [d["searches_while_resolving"] for d in D], "detour_files": [d["detour_files_while_resolving"] for d in D], "backtracked": sum(1 for d in D if d["backtracked_to_boundary_after_resolution"]), "ranked_earlier_hop_instead_of_gold": sum(1 for d in D if d["ranked_earlier_hop_instead_of_gold"]), "ranked_interface_or_impl_first": sum(1 for d in D if d["ranked_interface_or_impl_first"]), "abandoned_chain_count": sum(1 for d in D if d["abandoned_chain"]),
                    "binding_line_shown": [d["binding_line_first_shown"] for d in D], "impl_first_shown": [d["impl_first_shown"] for d in D], "first_search_for_interface": [d["first_search_for_interface"] for d in D], "javap_jshell_used": sum(1 for r in rs if r["info_distance"]["javap_jshell_steps"])})
        B = [r["branch"] for r in rs]
        out.update({"branch": {"selector_discovered": sum(1 for b in B if b["selector_discovered"]), "condition_shown": sum(1 for b in B if b["condition_first_shown"]), "both_implementations_discovered": sum(1 for b in B if b["both_implementations_discovered"]), "both_implementations_opened": sum(1 for b in B if b["both_implementations_opened"]), "wrong_branch_inspected_first": sum(1 for b in B if b["wrong_branch_inspected_first"]), "wrong_branch_followed": sum(1 for b in B if b["wrong_branch_followed"]), "ignored_alternate": sum(1 for b in B if b["ignored_alternate"]), "backtracking": sum(1 for b in B if b["backtracking_occurred"]),
                               "width_source_shown_before_resolution": sum(1 for b in B if b["correct_runtime_branch_inferred_observably"]["width_source_line_shown_before_resolution"]), "condition_shown_before_resolution": sum(1 for b in B if b["correct_runtime_branch_inferred_observably"]["condition_shown_before_resolution"]), "jshell_on_dispatch": sum(1 for b in B if b["correct_runtime_branch_inferred_observably"]["executed_selector_or_widen_in_jshell"]),
                               "rank1_categories": {t: sum(1 for b in B if b["rank1_category"] == t) for t in sorted({b["rank1_category"] for b in B})}, "discovery_success": sum(1 for b in B if b["discovery_success"]), "attribution_failures": sum(1 for b in B if b["attribution_failure"]), "ranked_selector": sum(1 for b in B if b["ranked_selector"]), "ranked_abstraction": sum(1 for b in B if b["ranked_abstraction"]), "ranked_wrong_implementation": sum(1 for b in B if b["ranked_wrong_implementation"]), "ranked_wrapper": sum(1 for b in B if b["ranked_wrapper"]), "ranked_facade": sum(1 for b in B if b["ranked_facade"]), "rank_of_narrow": [b["rank_of_narrow"] for b in B], "rank_of_facade": [b["rank_of_facade"] for b in B], "rank_of_wrapper": [b["rank_of_wrapper"] for b in B],
                               "narrow_first_shown": [b["narrow_first_shown"] for b in B], "standard_first_shown": [b["standard_first_shown"] for b in B], "selector_first_shown": [b["selector_first_shown"] for b in B], "condition_first_shown": [b["condition_first_shown"] for b in B]}})
        out.update({"routes": {t: sum(1 for r in rs if r["chain"]["route"] == t) for t in sorted({r["chain"]["route"] for r in rs})}, "full_five_hop_traversal_rate": sum(1 for r in rs if r["chain"].get("followed_all_five_sequentially")) / len(rs), "all_hops_shown_in_order_rate": sum(1 for r in rs if r["chain"].get("sequential_order")) / len(rs),
                    "lexical_bypass_rate": sum(1 for r in rs if r["chain"].get("lexical_bypass")) / len(rs), "repository_wide_shortcut_rate": sum(1 for r in rs if r["chain"].get("repository_wide_shortcut")) / len(rs), "direct_gold_search_rate": sum(1 for r in rs if r["chain"].get("direct_gold_search")) / len(rs),
                    "abandoned_chain": sum(1 for r in rs if r["chain"].get("abandoned_chain")), "timeout_before_gold": sum(1 for r in rs if r["chain"].get("timeout_before_gold")), "reached_per_hop": {t: sum(1 for r in rs if r["chain"]["reached"].get(t)) for t in ("H1", "H2", "H3", "H4", "H5")}, "skipped_hops": [r["chain"]["skipped_hops"] for r in rs],
                    "hop_exposure_steps": {t: [r["chain"]["exposure_steps"].get(t) for r in rs] for t in ("facade", "H1", "H2", "H3", "H4", "H5")}, "hop_exposure_mean": {t: mm([r["chain"]["exposure_steps"].get(t) for r in rs]) for t in ("facade", "H1", "H2", "H3", "H4", "H5")},
                    "increments_mean": {k: mm([r["chain"]["increments"].get(k) for r in rs if r["chain"].get("increments")]) for k in ("incremental_to_H1", "incremental_to_H2", "incremental_to_H3", "incremental_to_H4", "incremental_to_H5")}})
    return out
out = {"schema_version": "branch-dispatch-results/v1", "label": a.label, "run_range": a.runs, "interpretation_rule": "Not an L-level / reasoning-depth estimate and not a causal CONTROL-vs-TREATMENT effect; n=5 per arm; descriptive only; timeouts are reported separately and never treated as localization misses.",
       "per_arm": {"CONTROL": agg([r for r in runs if r["arm"] == "CONTROL"]), "BRANCH_TREATMENT": agg([r for r in runs if r["arm"] == "TREATMENT"])}, "total_recorded_cost_usd": sum(r["cost_usd"] or 0 for r in runs), "runs": runs}
json.dump(out, open(a.out, "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1))
for r in runs:
    print(f"\n### {r['run_id']} [{r['arm']}] status={r['status']} rank={r['gold_rank']} tc={r['tool_call_count']} api={r['api_calls']} cost={r['cost_usd']} dur={r['timing']['duration_ms']} retries={r['timing']['provider_retry_lines']}")
    print("  path:", r["chain"]["chain_path"], "|", r["chain"]["route"]); print("  gold at", r["gold_first_exposed_step"], "via:", r["gold_exposing_cmd"][:120]); print("  dispatch:", {k: v for k, v in r["dispatch"].items() if k not in ("window_commands", "cmd_markers")} if r["dispatch"] else "n/a"); print("  branch:", r["branch"] if r["branch"] else "n/a"); print("  contract:", {k: v for k, v in r["contract_first_shown"].items() if v}, "| after gold:", r["info_distance"]["contract_markers_after_gold"]); print("  novel:", r["novel_search_vocabulary"][:4]); print("  top5:", [x.split(".")[-1] for x in r["top10"][:5]])
    for s in r["steps"]: print(f"   {s['idx']:>2}. {s['command'][:170]}")
