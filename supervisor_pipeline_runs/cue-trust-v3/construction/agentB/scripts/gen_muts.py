"""Generate one-line value mutations inside named methods (agentB screening; no LLM).
Usage: gen_muts.py <checkout> <out.json> <file>::<method>[::<decl substring>] ..."""
import os, re, sys, json
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/shim")
from callgraph import extract_methods_from_file
co, out = sys.argv[1], sys.argv[2]
SWAPS = [("<=", "<"), (">=", ">"), ("==", "!="), ("!=", "=="), ("&&", "||"), ("||", "&&"),
         ("Math.min", "Math.max"), ("Math.max", "Math.min"), ("getX()", "getY()"), ("getY()", "getX()"),
         ("getWidth()", "getHeight()"), ("getHeight()", "getWidth()"), ("getMinX()", "getMaxX()"), ("getMaxX()", "getMinX()"),
         ("getMinY()", "getMaxY()"), ("getMaxY()", "getMinY()"), ("RectangleEdge.LEFT", "RectangleEdge.RIGHT"),
         ("RectangleEdge.RIGHT", "RectangleEdge.LEFT"), ("RectangleEdge.TOP", "RectangleEdge.BOTTOM"), ("RectangleEdge.BOTTOM", "RectangleEdge.TOP"),
         ("calculateLeftOutset", "calculateRightOutset"), ("calculateRightOutset", "calculateLeftOutset"),
         ("calculateTopOutset", "calculateBottomOutset"), ("calculateBottomOutset", "calculateTopOutset"),
         ("SortOrder.ASCENDING", "SortOrder.DESCENDING"), ("PlotOrientation.VERTICAL", "PlotOrientation.HORIZONTAL"),
         ("PlotOrientation.HORIZONTAL", "PlotOrientation.VERTICAL"), ("true", "false"), ("false", "true"),
         (" + 1", ""), (" - 1", ""), (" + ", " - "), (" - ", " + "), ("getLeft()", "getRight()"), ("getRight()", "getLeft()"),
         ("getTop()", "getBottom()"), ("getBottom()", "getTop()"), (" / 2.0", ""), (" * 2.0", ""), ("0.0", "1.0")]
muts = []
for spec in sys.argv[3:]:
    parts = spec.split("::"); rel, meth = parts[0], parts[1]; decl = parts[2] if len(parts) > 2 else None
    full = os.path.join(co, rel); lines = open(full, "rb").read().decode("utf-8").replace("\r\n", "\n").split("\n"); text = "\n".join(lines)
    ms = [m for m in extract_methods_from_file(full) if m["name"] == meth and (not decl or decl in lines[m["start_line"] - 1])]
    assert len(ms) == 1, (spec, len(ms)); m = ms[0]; cls = os.path.basename(rel)[:-5]; n0 = len(muts)
    for i in range(m["start_line"], m["end_line"]):
        line = lines[i - 1] if False else lines[i]; s = line.strip()
        if not s or s.startswith(("*", "/", "//")): continue
        code = line.split("//")[0]
        for a_, b_ in SWAPS:
            for mm in re.finditer(re.escape(a_), code):
                if a_ in ("<=", ">=") and code[mm.end():mm.end()+1] == "=": continue
                if a_ in ("true", "false") and not re.match(r"\b", code[mm.start()-1:mm.start()] + "x"): pass
                if a_ in ("true", "false", "0.0") and (re.match(r"\w", code[mm.start()-1:mm.start()] or " ") or re.match(r"[\w.]", code[mm.end():mm.end()+1] or " ")): continue
                nl = line[:mm.start()] + b_ + line[mm.end():]
                ctx_old = lines[i - 1] + "\n" + line; ctx_new = lines[i - 1] + "\n" + nl
                if text.count(ctx_old) != 1: continue
                muts.append({"id": f"{cls}.{meth}:L{i+1}:{a_.strip()}->{b_.strip() or 'DEL'}:{len(muts)}", "file": rel, "method": meth,
                             "line_no": i + 1, "offset": i + 1 - m["start_line"], "old": ctx_old, "new": ctx_new, "orig_line": s, "bug_line": nl.strip()})
    print(spec, len(muts) - n0)
json.dump(muts, open(out, "w"), indent=1); print("total", len(muts))
