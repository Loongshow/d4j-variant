#!/usr/bin/env python
"""analysis/OWNERSHIP_PROOFS.md and analysis/LOCAL_BLINDNESS.md aggregated over all pairs. Usage: build_lb_review.py"""
import json, glob, os
L = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1"; os.makedirs(f"{L}/analysis", exist_ok=True)
OP = ["# Ownership proofs (Level B, all pairs)", "", "Isolated repairs executed by the validator on each buggy arm. Gold repair must pass trigger + pin + external evidence; the compensating repair at the other hop must pass the trigger but break the pin or the external evidence.", "",
      "| Pair | Arm | Gold | External evidence | Pin on buggy (fail) | External on buggy (fail) | Gold repair: trigger/pin/external fail | Compensating repair (target): trigger/pin/external fail | Classification |", "|" + "---|" * 9]
LB = ["# Local blindness (V15) and two-hop ambiguity (V16), all pairs", "", "Two independent blinded graders per packet; packets contain only the method (javadoc, signature, body). V15 passes when no grader confidently identifies the true gold from its own packet; V16 is LOCAL_AMBIGUOUS when no grader confidently names the true gold from the H2+H3 packet.", "",
      "| Pair | V15 | V16 | Confident exposures of the gold (single packet) | Confident but not the gold | H2+H3 exposures | Graders |", "|" + "---|" * 7]
for pj in sorted(glob.glob(f"{L}/projects/*/bug-*/pair.json")):
    s = json.load(open(pj)); vp = f"{s['pair_dir']}/validation/validation.json"; bp = f"{s['pair_dir']}/blindness/verdicts.json"
    if os.path.exists(vp):
        v = json.load(open(vp))
        for arm, A in s["arms"].items():
            a = v["arms"].get(arm, {}); gr = a.get("gold_repair", {}); cr = a.get("compensating_repair", {})
            OP.append(f"| `{s['pair_id']}` | {arm} | `{A['gold']['class'].split('.')[-1]}.{A['gold']['method']}` | {s.get('second_caller','-')} | {a.get('pin_on_buggy',{}).get('n_fail')} | {a.get('external_on_buggy')} | {gr.get('trigger_fail')}/{gr.get('pin_fail')}/{gr.get('external_fail')} | ({cr.get('target_role')}) {cr.get('trigger_fail')}/{cr.get('pin_fail')}/{cr.get('external_fail')} | **{a.get('ownership')}** |")
    if os.path.exists(bp):
        b = json.load(open(bp)); LB.append(f"| `{s['pair_id']}` | **{b['V15']}** | **{b['V16']}** | {b['v15_exposures'] or 'none'} | {len(b['v15_confident_but_not_gold'])} | {b['v16_exposures'] or 'none'} | {b['n_graders']} |")
    else: LB.append(f"| `{s['pair_id']}` | not graded | not graded | - | - | - | 0 |")
open(f"{L}/analysis/OWNERSHIP_PROOFS.md", "w").write("\n".join(OP) + "\n"); open(f"{L}/analysis/LOCAL_BLINDNESS.md", "w").write("\n".join(LB) + "\n"); print("review docs built")
