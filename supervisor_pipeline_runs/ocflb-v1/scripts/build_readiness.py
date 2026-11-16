#!/usr/bin/env python
"""review/OCFLB_READINESS.md: one row per pair from pair.json + validation.json. Usage: build_readiness.py"""
import json, glob, os
O = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1"
rows = []; ready = []
for pj in sorted(glob.glob(f"{O}/projects/*/bug-*/pair.json")):
    s = json.load(open(pj)); vp = f"{s['pair_dir']}/validation/validation.json"; v = json.load(open(vp)) if os.path.exists(vp) else None
    g = {(x["gate"], x["arm"]): x["status"] for x in (v or {}).get("gates", [])}
    def ok(gate, arm=None): return g.get((gate, arm)) == "pass"
    d_valid = all(ok(x, "DEFINER_FAULT") for x in ("V1c", "V3a", "V3b", "V3c", "V5", "V6", "V7", "V8", "V9c", "V10", "V11a", "V11b", "V12", "V13"))
    a_valid = all(ok(x, "ADAPTER_FAULT") for x in ("V1c", "V3a", "V3b", "V3c", "V5", "V6", "V7", "V8", "V9c", "V10", "V11a", "V11b", "V12", "V13"))
    same_fail = ok("V3d"); same_chain = ok("V10b"); second = s.get("pin_test") is not None and ok("V12", "ADAPTER_FAULT")
    pinned = v and all((v["arms"].get(a) or {}).get("ownership") == "PINNED_UNIQUE" for a in ("DEFINER_FAULT", "ADAPTER_FAULT"))
    fresh = ok("V7", "DEFINER_FAULT") and ok("V7", "ADAPTER_FAULT"); lex = ok("V9a") and ok("V9b") and ok("V9c", "DEFINER_FAULT") and ok("V9c", "ADAPTER_FAULT")
    installed = all(os.path.isdir(f"{O}/new_bug_variants/{s['project']}/bug-1/L20/{s['arms'][a]['variant_id']}") for a in s["arms"])
    R = bool(v and v.get("overall") == "READY" and installed)
    rows.append((s["project"], s["bug"], s["pair_id"], s["family"], d_valid, a_valid, same_fail, same_chain, second, pinned, fresh, lex, installed, R, (v or {}).get("overall", "not validated")))
    if R: ready.append(s["pair_id"])
Y = lambda b: "yes" if b else "NO"
L = ["# OCFLB readiness (NON-CANONICAL RESEARCH BENCHMARK)", "", f"{len(ready)} of {len(rows)} pairs READY: {', '.join(ready)}", "",
     "| Project | Bug | Pair | Fault family | Definer arm valid | Adapter arm valid | Same failure | Same chain | Second caller | Ownership pinned | Fresh repro | Lexgate | Installed | READY |", "|" + "---|" * 14]
for r in rows: L.append(f"| {r[0]} | {r[1]} | `{r[2]}` | {r[3]} | {Y(r[4])} | {Y(r[5])} | {Y(r[6])} | {Y(r[7])} | {Y(r[8])} | {Y(r[9])} | {Y(r[10])} | {Y(r[11])} | {Y(r[12])} | **{'READY' if r[13] else r[14]}** |")
L += ["", "Gate mapping: V1 compile; V2 CORRECT-chain trigger and pin pass; V3 deterministic failure x3 + signature; V5/V13 suite collateral only as declared; V6 dynamic participation of facade+H1..H5 (instrumented run); V7 fresh reproduction on a pristine checkout; V8 packaged patches apply; V9 lexgate; V10 logic-chain edges + real work; V10b matched arms (patches differ only in declared lines); V11 ownership proof by isolated repairs; V12 pin test behaviour; V14 reset cleanliness. Only READY pairs proceed to model runs."]
open(f"{O}/review/OCFLB_READINESS.md", "w").write("\n".join(L) + "\n"); print(f"{len(ready)}/{len(rows)} READY"); json.dump(ready, open(f"{O}/review/ready_pairs.json", "w"))
