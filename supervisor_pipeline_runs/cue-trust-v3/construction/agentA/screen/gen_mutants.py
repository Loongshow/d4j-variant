"""Generate one-line value mutants for the body lines of selected methods (no LLM).
Usage: gen_mutants.py <checkout> <file> <out.json> <tests,comma,sep> method[:maxoffset] ...
Each mutant's anchor is (previous line + target line) and must be unique in the file."""
import sys, os, re, json
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/shim")
from callgraph import extract_methods_from_file
co, rel, out, tests = sys.argv[1:5]; specs = sys.argv[5:]
lines = open(os.path.join(co, rel), "rb").read().decode("utf-8").replace("\r\n", "\n").split("\n"); text = "\n".join(lines)
ms = extract_methods_from_file(os.path.join(co, rel))
OPS = [(r"==", "!="), (r"!=", "=="), (r"(?<![<>=!])<=", "<"), (r"(?<![<>=!])>=", ">"), (r"(?<![<>=!-])<(?![=<A-Z?])", "<="), (r"(?<![<>=!-A-Z?])>(?![=>(])", ">="), (r"(?<![<>=!-])<(?![=<A-Z?])", ">"), (r"(?<![<>=!-A-Z?\]])>(?![=>(])", "<"),
       (r"\|\|", "&&"), (r"&&", "||"), (r"\btrue\b", "false"), (r"\bfalse\b", "true"), (r"(?<![+])\+(?![+=])", "-"), (r"(?<![-])-(?![-=>])", "+"),
       (r"\+\+", "--"), (r"\b0\b", "1"), (r"\b1\b", "0"), (r"\b1\b", "2"), (r"-1\b", "0"), (r"\bnull\b(?=\s*,)", '" "')]
BOOLS = ["match", "lastMatch", "preserveAllTokens", "detail", "repeat", "camelCase"]
muts = []
def add(i, new, why, mname, off):
    old_l = lines[i]
    if new == old_l: return
    for k in range(1, 8):
        ctx_old = "\n".join(lines[i - k:i] + [old_l]); ctx_new = "\n".join(lines[i - k:i] + [new])
        if text.count(ctx_old) == 1: break
    else: return
    muts.append({"id": f"{mname}+{off}:{why}:{len(muts)}", "file": rel, "old": ctx_old, "new": ctx_new, "tests": tests.split(","), "line": old_l.strip(), "mut": new.strip(), "offset": off})
for sp in specs:
    name, _, mx = sp.partition(":"); mx = int(mx) if mx else 10**6
    for m in [m for m in ms if m["name"] == name]:
        s, e = m["start_line"] - 1, m["end_line"]
        for i in range(s + 1, e):
            off = i - s; l = lines[i]; st = l.strip()
            if off > mx: break
            if not st or st.startswith(("*", "/", "//")) or st in ("{", "}", "} else {", "try {"): continue
            code = l.split("//")[0] if '"' not in l else l
            for pat, rep in OPS:
                for mm in re.finditer(pat, code):
                    add(i, l[:mm.start()] + rep + l[mm.end():], f"{mm.group(0)}->{rep}", name, off)
            for b in BOOLS:
                for mm in re.finditer(r"(?<![.!\w])%s\b(?!\s*=[^=])" % b, code):
                    add(i, l[:mm.start()] + "!" + b + l[mm.end():], f"{b}->!{b}", name, off)
            for mm in re.finditer(r"!(?=[a-zA-Z(])", code):
                add(i, l[:mm.start()] + l[mm.end():], "drop!", name, off)
json.dump(muts, open(out, "w"), indent=1); print(len(muts), "mutants")
for m in muts: print(m["id"], "|", m["mut"][:100])
