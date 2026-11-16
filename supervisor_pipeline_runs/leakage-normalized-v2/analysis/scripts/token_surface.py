"""Observable search-surface measurement over the four states (grep counts per token, files, gold exposure)."""
import json, os, re, subprocess, sys
V2 = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/leakage-normalized-v2"
STATES = {"CONTROL-01": ("c01", "NumberUtils.java", "createBigInteger"), "TREATMENT-01": ("t01", "CompareToBuilder.java", "decodeMagnitude"),
          "CONTROL-02": ("c02", "NumberUtils.java", "createBigInteger"), "TREATMENT-02": ("t02", "CompareToBuilder.java", "decodeMagnitude")}
TOKENS = ["testCreateBigIntegerPositiveSigned", "testLang1106", "NumberUtilsTest", "+1234", "+7\"", "createBigInteger", "NumberUtils", "BigInteger", "java.math.BigInteger", "new BigInteger",
          "resolveWholeValue", "decodeMagnitude", "ObjectUtils", "CompareToBuilder", "positive", "signed", "plus", "sign", "magnitude", "decode", "resolve", "radix", "negate",
          'startsWith("+")', '"+"', 'startsWith("-")', "math", "import java.math.BigInteger", "scanned once", "explicit positive"]
def grep(root, tok, sub):
    p = subprocess.run(["grep", "-rnF", "--include=*.java", tok, os.path.join(root, sub)], capture_output=True, text=True); return [l.replace(root + "/", "") for l in p.stdout.splitlines()]
def gold_span(root, file_rel, decl):
    L = open(os.path.join(root, file_rel)).read().split("\n"); s = next((i for i, l in enumerate(L) if decl in l), None)
    if s is None: return None
    d = 0; st = False
    for j in range(s, len(L)):
        d += L[j].count("{") - L[j].count("}"); st = st or "{" in L[j]
        if st and d == 0: return (s + 1, j + 1)
out = {}
for name, (sd, gfile, gmeth) in STATES.items():
    root = os.path.join(V2, "analysis/states", sd)
    gfile_rel = "src/main/java/org/apache/commons/lang3/" + ("math/NumberUtils.java" if gmeth == "createBigInteger" else "builder/CompareToBuilder.java")
    decl = "createBigInteger(final String str)" if gmeth == "createBigInteger" else "decodeMagnitude(final String str)"
    gs = gold_span(root, gfile_rel, decl); res = {"gold_file": gfile_rel, "gold_span": gs, "tokens": {}}
    for tok in TOKENS:
        hm = grep(root, tok, "src/main/java"); ht = grep(root, tok, "src/test/java")
        files = sorted({h.split(":")[0].split("/")[-1] for h in hm}); gold_hits = [h for h in hm if h.startswith(gfile_rel + ":") and gs and gs[0] <= int(h.split(":")[1]) <= gs[1]]
        res["tokens"][tok] = {"main_hits": len(hm), "main_files": files, "test_hits": len(ht), "gold_file_hits": sum(1 for h in hm if h.startswith(gfile_rel + ":")), "hits_inside_gold_method": len(gold_hits), "scannable(<=40)": len(hm) <= 40}
    out[name] = res
json.dump(out, open(os.path.join(V2, "analysis/data/token_surface.json"), "w"), indent=1)
hdr = "| token | " + " | ".join(f"{n}: main hits / files / in-gold" for n in STATES) + " |"; print(hdr); print("|---" * (len(STATES) + 1) + "|")
for tok in TOKENS:
    row = f"| `{tok}` | " + " | ".join(f"{out[n]['tokens'][tok]['main_hits']} / {len(out[n]['tokens'][tok]['main_files'])} / {out[n]['tokens'][tok]['hits_inside_gold_method']}" for n in STATES) + " |"; print(row)
print("\ngold spans:", {n: out[n]["gold_span"] for n in STATES})
for n in STATES:
    print(n, "BigInteger files:", out[n]["tokens"]["BigInteger"]["main_files"], "| math files:", out[n]["tokens"]["math"]["main_files"], "| new BigInteger files:", out[n]["tokens"]["new BigInteger"]["main_files"], "| CompareToBuilder files:", out[n]["tokens"]["CompareToBuilder"]["main_files"])
