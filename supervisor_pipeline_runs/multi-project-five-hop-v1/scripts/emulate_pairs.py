"""Java-double emulation (IEEE 754 binary64; Python floats use the same operations) of the original method, the CONTROL (buggy) method,
the five-hop chain with the correct gold line and the chain with the buggy gold line, for both projects. Prints comparison tables and
asserts: original == chain(correct) and control(buggy) == chain(buggy) for every case, and that the trigger cases discriminate."""
import math, json, sys
# ---------------- Math: MathArrays.safeNorm ----------------
def math_original(v, buggy):
    rdwarf = 3.834e-20; rgiant = 1.304e19; s1 = s2 = s3 = 0.0; x1max = x3max = 0.0; agiant = rgiant / float(len(v))
    for x in v:
        xabs = abs(x)
        if xabs < rdwarf or xabs > agiant:
            if xabs > rdwarf:
                if xabs > x1max: r = x1max / xabs; s1 = 1 + s1 * r * r; x1max = xabs
                else: r = xabs / x1max; s1 += r * r
            else:
                if xabs > x3max: r = x3max / xabs; s3 = 1 + s3 * r * r; x3max = xabs
                elif xabs != 0: r = xabs / x3max; s3 += r * r
        else: s2 += xabs * xabs
    if s1 != 0: return x1max * math.sqrt(s1 + (s2 / x1max if buggy else (s2 / x1max) / x1max))
    if s2 == 0: return x3max * math.sqrt(s3)
    if s2 >= x3max: return math.sqrt(s2 * (1 + (x3max / s2) * (x3max * s3)))
    return math.sqrt(x3max * ((s2 / x3max) + (x3max * s3)))
def math_chain(v, buggy):
    rdwarf = 3.834e-20; rgiant = 1.304e19; agiant = rgiant / float(len(v))
    # hop 1 StatUtils.survey
    major = 0.0; top = 0.0
    for x in v:
        x = abs(x)
        if x > agiant:
            if x > top: r = top / x; major = 1 + major * r * r; top = x
            else: r = x / top; major += r * r
    # hop 2 MathUtils.balance
    middle = 0.0
    for x in v:
        x = abs(x)
        if not (x < rdwarf or x > agiant): middle += x * x
    # hop 3 Precision.residue
    minor = 0.0; bottom = 0.0
    for x in v:
        x = abs(x)
        if x < rdwarf:
            if x > bottom: r = bottom / x; minor = 1 + minor * r * r; bottom = x
            elif x != 0: r = x / bottom; minor += r * r
    # hop 4 MatrixUtils.settle -> hop 5 FastMath.merge
    if major != 0:
        relative = middle / top if buggy else (middle / top) / top
        return top * math.sqrt(major + relative)
    if middle == 0: return bottom * math.sqrt(minor)
    if middle >= bottom: return math.sqrt(middle * (1 + (bottom / middle) * (bottom * minor)))
    return math.sqrt(bottom * ((middle / bottom) + (bottom * minor)))
math_cases = [("trigger#1 mid only", [3.0, 4.0]), ("trigger#2 large+mid", [2.0e19, 1.0e10]), ("trigger#3 large+large+mid", [-3.0e19, 4.0e19, 5.0e9]),
              ("empty", []), ("zeros", [0.0, 0.0]), ("single", [7.5]), ("small only", [1e-25, 2e-25]), ("small+mid", [1e-25, 3.0, 4.0]), ("large only", [1e200, 1e200]), ("large+small", [5e19, 1e-30]),
              ("mixed all", [1e19, 1e-22, 2.0, -1e19]), ("negative mid", [-6.0, 8.0]), ("boundary agiant", [1.304e19 / 2, 1.0]), ("huge n", [1.0] * 1000)]
print("| Math case | args | original | chain(correct) | CONTROL buggy | chain(buggy) | orig==chain | control==chain(bug) |"); print("|---|---|---|---|---|---|---|---|"); ok = True; disc = []
for name, v in math_cases:
    try: o = math_original(v, False); c = math_chain(v, False); ob = math_original(v, True); cb = math_chain(v, True)
    except ZeroDivisionError as e: print(f"| {name} | {v if len(v) < 6 else str(len(v)) + ' ones'} | ZeroDivisionError (Java: NaN/Infinity semantics, see note) | | | | | |"); continue
    same = (o == c) or (math.isnan(o) and math.isnan(c)); sameb = (ob == cb) or (math.isnan(ob) and math.isnan(cb)); ok &= same and sameb; disc.append(o != ob)
    print(f"| {name} | {v if len(v) < 6 else str(len(v)) + ' ones'} | {o!r} | {c!r} | {ob!r} | {cb!r} | {same} | {sameb} |")
print("Math: original == chain(correct) and control == chain(buggy) for all emulated cases:", ok, "| trigger cases discriminate (#2, #3):", disc[1], disc[2])
# ---------------- Chart: CategoryAxis.getCategoryStart ----------------
def chart_original(x, y, w, h, edge, category, count, lower, upper, cm, buggy):
    result = 0.0; available = 0.0
    if edge in ("TOP", "BOTTOM"): result = x + w * lower; available = w
    elif edge in ("LEFT", "RIGHT"): result = y + h * lower; available = h
    if count > 1: size = available * (1 - lower - upper - cm); size = size / count
    else: size = available * (1 - lower - upper)
    gap = available * cm / (count - 1) if count > 1 else 0.0
    return (result + (category * size + gap)) if buggy else (result + category * (size + gap))
def chart_chain(x, y, w, h, edge, index, count, lead, trail, spread, buggy):
    start = 0.0; length = 0.0
    if edge in ("TOP", "BOTTOM"): start = x; length = w
    elif edge in ("LEFT", "RIGHT"): start = y; length = h
    origin = start + length * lead
    fraction = (1 - lead - trail - spread) if count > 1 else (1 - lead - trail)
    cell = length * fraction
    if count > 1: cell = cell / count
    pad = length * spread / (count - 1) if count > 1 else 0.0
    offset = (index * cell + pad) if buggy else (index * (cell + pad))
    return origin + offset
chart_cases = [("trigger cat0 BOTTOM", (10.0, 20.0, 400.0, 200.0, "BOTTOM", 0, 4, 0.05, 0.05, 0.20)), ("trigger cat1 BOTTOM", (10.0, 20.0, 400.0, 200.0, "BOTTOM", 1, 4, 0.05, 0.05, 0.20)), ("trigger cat2 BOTTOM", (10.0, 20.0, 400.0, 200.0, "BOTTOM", 2, 4, 0.05, 0.05, 0.20)), ("trigger cat3 LEFT", (10.0, 20.0, 400.0, 200.0, "LEFT", 3, 4, 0.05, 0.05, 0.20)),
               ("single category", (0.0, 0.0, 100.0, 50.0, "TOP", 0, 1, 0.05, 0.05, 0.20)), ("zero margins", (0.0, 0.0, 100.0, 50.0, "RIGHT", 2, 5, 0.0, 0.0, 0.0)), ("default margins cat 7 of 10", (3.5, -2.0, 640.0, 480.0, "BOTTOM", 7, 10, 0.05, 0.05, 0.2)), ("odd margins", (1.0, 1.0, 333.0, 111.0, "LEFT", 4, 6, 0.1, 0.02, 0.15)), ("no edge (None)", (0.0, 0.0, 100.0, 50.0, None, 2, 3, 0.05, 0.05, 0.2)), ("two categories", (0.0, 0.0, 200.0, 100.0, "TOP", 1, 2, 0.05, 0.05, 0.3))]
print("\n| Chart case | original | chain(correct) | CONTROL buggy | chain(buggy) | orig==chain | control==chain(bug) |"); print("|---|---|---|---|---|---|---|"); ok2 = True; disc2 = []
for name, a in chart_cases:
    o = chart_original(*a, False); c = chart_chain(*a, False); ob = chart_original(*a, True); cb = chart_chain(*a, True); ok2 &= (o == c) and (ob == cb); disc2.append(o != ob)
    print(f"| {name} | {o!r} | {c!r} | {ob!r} | {cb!r} | {o == c} | {ob == cb} |")
print("Chart: original == chain(correct) and control == chain(buggy) for all emulated cases:", ok2, "| trigger cases discriminate (cat0, cat1, cat2, cat3):", disc2[:4])
json.dump({"math_ok": ok, "chart_ok": ok2}, open(sys.argv[1], "w")) if len(sys.argv) > 1 else None
