"""Token cardinalities on the patched states of both arms (main hits / files / hits inside the gold method; test hits).
Usage: token_surface.py <config.json> <control_state> <treatment_state> <out_json> <out_md> <token> [<token> ...]"""
import json, os, subprocess, sys
cfg = json.load(open(sys.argv[1])); states = {"CONTROL": sys.argv[2], "TREATMENT": sys.argv[3]}; out_json, out_md = sys.argv[4], sys.argv[5]; TOKENS = sys.argv[6:]
SRC, TST = cfg["src_dir"], cfg["test_dir"]
def grep(root, tok, sub):
    p = subprocess.run(["grep", "-rnF", "--include=*.java", tok, os.path.join(root, sub)], capture_output=True, text=True); return [l.replace(root + "/", "") for l in p.stdout.splitlines()]
def span(root, f, decl):
    L = open(os.path.join(root, f), "rb").read().decode("utf-8").replace("\r\n", "\n").split("\n"); s = next((i for i, l in enumerate(L) if decl in l), None)
    if s is None: return None
    d = 0; st = False
    for j in range(s, len(L)):
        d += L[j].count("{") - L[j].count("}"); st = st or "{" in L[j]
        if st and d == 0: return (s + 1, j + 1)
out = {}
for arm, root in states.items():
    A = cfg[arm.lower()]; gf = A["gold_file"]; gs = span(root, gf, A["gold_decl"]); res = {"gold_file": gf, "gold_span": gs, "tokens": {}}
    for tok in TOKENS:
        hm = grep(root, tok, SRC); ht = grep(root, tok, TST); files = sorted({h.split(":")[0].split("/")[-1] for h in hm})
        ing = [h for h in hm if h.startswith(gf + ":") and gs and gs[0] <= int(h.split(":")[1]) <= gs[1]]
        res["tokens"][tok] = {"main_hits": len(hm), "main_files": files, "test_hits": len(ht), "gold_file_hits": sum(1 for h in hm if h.startswith(gf + ":")), "hits_inside_gold_method": len(ing), "scannable(<=40)": len(hm) <= 40}
    out[arm] = res
json.dump(out, open(out_json, "w"), indent=1)
lines = ["| token | CONTROL: main hits / files / in-gold | TREATMENT: main hits / files / in-gold | TREATMENT files (first 6) |", "|---|---|---|---|"]
for tok in TOKENS: lines.append(f"| `{tok}` | " + " | ".join(f"{out[a]['tokens'][tok]['main_hits']} / {len(out[a]['tokens'][tok]['main_files'])} / {out[a]['tokens'][tok]['hits_inside_gold_method']}" for a in states) + f" | {', '.join(out['TREATMENT']['tokens'][tok]['main_files'][:6])} |")
open(out_md, "w").write("\n".join(lines) + "\n"); print("\n".join(lines)); print("gold spans:", {a: out[a]["gold_span"] for a in states})
