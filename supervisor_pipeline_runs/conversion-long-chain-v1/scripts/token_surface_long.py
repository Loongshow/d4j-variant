import json, os, subprocess, sys
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/conversion-long-chain-v1"
STATES = {"LONG-CONTROL-01": ("c", "src/main/java/org/apache/commons/lang3/Conversion.java", "public static long intArrayToLong(final int[] src"),
          "LONG-TREATMENT-01": ("t", "src/main/java/org/apache/commons/lang3/math/NumberUtils.java", "public static long overlay(final long holder")}
TOKENS = ["testLang1112", "ConversionTest", "intArrayToLong", "Conversion", "gather", "compose", "widen", "combine", "overlay", "ArrayUtils", "EnumUtils", "BitField", "ObjectUtils", "NumberUtils",
          "dstPos", "nInts", "srcPos", "dstInit", "0xffffffffL", "<< shift", "shift = ", "* 32", "* width", "Integer.SIZE", "int[]", "long[]", "long out", "mask", "bits", "field", "holder", "width", "words", "run[", "greather", "endian", "offset",
          "0xCDF1F0C1", "0x0F123456", "0x0000000F12345600", "0x1234CDF1F0C1DEF0", "position in the result", "position in the holder", "(index + at)", "(i + dstPos)", "index * width", "System.arraycopy",
          "import org.apache.commons.lang3.math.NumberUtils", "ArrayUtils.gather", "EnumUtils.compose", "BitField.widen", "ObjectUtils.combine", "NumberUtils.overlay", "1L <<", "<<", "& ~("]
def grep(root, tok, sub):
    p = subprocess.run(["grep", "-rnF", "--include=*.java", tok, os.path.join(root, sub)], capture_output=True, text=True); return [l.replace(root + "/", "") for l in p.stdout.splitlines()]
def span(root, f, decl):
    L = open(os.path.join(root, f)).read().split("\n"); s = next((i for i, l in enumerate(L) if decl in l), None)
    if s is None: return None
    d = 0; st = False
    for j in range(s, len(L)):
        d += L[j].count("{") - L[j].count("}"); st = st or "{" in L[j]
        if st and d == 0: return (s + 1, j + 1)
out = {}
for name, (sd, gf, decl) in STATES.items():
    root = os.path.join(R, "analysis/states", sd); gs = span(root, gf, decl); res = {"gold_file": gf, "gold_span": gs, "tokens": {}}
    for tok in TOKENS:
        hm = grep(root, tok, "src/main/java"); ht = grep(root, tok, "src/test/java"); files = sorted({h.split(":")[0].split("/")[-1] for h in hm})
        ing = [h for h in hm if h.startswith(gf + ":") and gs and gs[0] <= int(h.split(":")[1]) <= gs[1]]
        res["tokens"][tok] = {"main_hits": len(hm), "main_files": files, "test_hits": len(ht), "gold_file_hits": sum(1 for h in hm if h.startswith(gf + ":")), "hits_inside_gold_method": len(ing), "scannable(<=40)": len(hm) <= 40}
    out[name] = res
json.dump(out, open(os.path.join(R, "analysis/data/token_surface_long.json"), "w"), indent=1)
lines = ["| token | LONG-CONTROL-01: main hits / files / in-gold | LONG-TREATMENT-01: main hits / files / in-gold | TREATMENT files |", "|---|---|---|---|"]
for tok in TOKENS: lines.append(f"| `{tok}` | " + " | ".join(f"{out[n]['tokens'][tok]['main_hits']} / {len(out[n]['tokens'][tok]['main_files'])} / {out[n]['tokens'][tok]['hits_inside_gold_method']}" for n in STATES) + f" | {', '.join(out['LONG-TREATMENT-01']['tokens'][tok]['main_files'][:6])} |")
open(os.path.join(R, "analysis/data/token_surface_long_table.md"), "w").write("\n".join(lines) + "\n"); print("\n".join(lines)); print("\ngold spans:", {n: out[n]["gold_span"] for n in STATES})
