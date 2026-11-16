"""Java-semantics emulation (64-bit long, 32-bit int, shift count masked to 6 bits) of: the original loop, the CONTROL (buggy) loop,
the five-hop chain with the correct hop-5 line, and the five-hop chain with the buggy hop-5 line. Prints a comparison table."""
M64 = (1 << 64) - 1
def s64(x): x &= M64; return x - (1 << 64) if x >> 63 else x
def i32(x): x &= 0xffffffff; return x - (1 << 32) if x >> 31 else x
def shl(x, n): return s64((x & M64) << (n & 63))
def band(a, b): return s64((a & M64) & (b & M64))
def bor(a, b): return s64((a & M64) | (b & M64))
def bnot(a): return s64(~a & M64)
def loop(src, srcPos, dstInit, dstPos, nInts, buggy):
    if (len(src) == 0 and srcPos == 0) or nInts == 0: return dstInit
    if (nInts - 1) * 32 + dstPos >= 64: raise ValueError("IAE")
    out = dstInit
    for i in range(nInts):
        shift = (i + dstPos) * 32 if buggy else i * 32 + dstPos
        bits = shl(band(0xffffffff, s64(i32(src[i + srcPos]))), shift); mask = shl(0xffffffff, shift); out = bor(band(out, bnot(mask)), bits)
    return out
def chain(src, srcPos, dstInit, dstPos, nInts, buggy):
    if (len(src) == 0 and srcPos == 0) or nInts == 0: return dstInit               # facade guard 1
    if (nInts - 1) * 32 + dstPos >= 64: raise ValueError("IAE")                      # facade guard 2
    # hop 1 ArrayUtils.gather: bounds-checked copy
    if nInts < 0: raise ValueError("NegativeArraySizeException")
    if srcPos < 0 or srcPos + nInts > len(src): raise IndexError("AIOOBE")
    run = [i32(v) for v in src[srcPos:srcPos + nInts]]
    # hop 2 EnumUtils.compose: width and field
    width = 32; field = s64((1 << width) - 1)
    # hop 3 BitField.widen
    words = [band(s64(v), field) for v in run]
    # hop 4 ObjectUtils.combine + hop 5 NumberUtils.overlay
    total = dstInit
    for index, word in enumerate(words):
        shift = (index + dstPos) * width if buggy else index * width + dstPos
        total = bor(band(total, bnot(shl(field, shift))), shl(word, shift))
    return total
src = [0xCDF1F0C1, 0x0F123456, 0x78000000]
cases = [("trigger#1", (src, 1, 0, 8, 1)), ("trigger#2", (src, 0, 0x123456789ABCDEF0, 16, 1)),
         ("t550", (src, 0, 0, 0, 0)), ("t551", (src, 1, 0, 0, 0)), ("t552", (src, 0, 0, 0, 1)), ("t553", (src, 0, 0, 0, 2)), ("t554", (src, 1, 0, 0, 1)), ("t556", (src, 0, 0x123456789ABCDEF0, 0, 0)), ("t558", (src, 2, 0x123456789ABCDEF0, 0, 1)),
         ("extra dstPos=24 n=1", (src, 2, 0x123456789ABCDEF0, 24, 1)), ("extra dstPos=32 n=1", (src, 0, -1, 32, 1)), ("extra empty", ([], 0, 7, 0, 0))]
print("| case | args | original | 5-hop correct | CONTROL buggy | 5-hop buggy | orig==chain | control==chain(bug) |"); print("|---|---|---|---|---|---|---|---|")
allok = True
for name, a in cases:
    o, c, ob, cb = loop(*a, buggy=False), chain(*a, buggy=False), loop(*a, buggy=True), chain(*a, buggy=True)
    ok1, ok2 = o == c, ob == cb; allok &= ok1 and ok2
    print(f"| {name} | srcPos={a[1]} dstInit={a[2] & M64:#x} dstPos={a[3]} n={a[4]} | {o & M64:#018x} | {c & M64:#018x} | {ob & M64:#018x} | {cb & M64:#018x} | {ok1} | {ok2} |")
print("\nALL CASES: original == five-hop(correct) and CONTROL(buggy) == five-hop(buggy):", allok)
print("trigger#1 decimal: expected", loop(*cases[0][1], buggy=False), "actual(buggy)", loop(*cases[0][1], buggy=True), "-> signature expected:<64729929216> but was:<252851286> ->", loop(*cases[0][1], buggy=False) == 64729929216 and loop(*cases[0][1], buggy=True) == 252851286)
for name, a in [("guard IAE (n=2,dstPos=32)", (src, 0, 0, 32, 2)), ("AIOOBE (srcPos=2,n=2)", (src, 2, 0, 0, 2)), ("negative n", (src, 0, 5, 0, -1))]:
    def tr(f):
        try: return f"{f(*a, buggy=False) & M64:#x}"
        except Exception as e: return type(e).__name__ + ":" + str(e)
    print(f"edge {name}: original -> {tr(loop)} | five-hop -> {tr(chain)}")
