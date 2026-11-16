"""IEEE/Java-semantics emulation of the original intArrayToLong, the LOW and HIGH chains (correct lane = floor; buggy lane = ceiling) over an input grid.
Verifies: correct LOW == correct HIGH == original (bitwise), buggy LOW == buggy HIGH, and the trigger values. Java long shifts mask the count to 6 bits."""
import json, itertools, sys
M64 = (1 << 64) - 1
def s64(x): x &= M64; return x - (1 << 64) if x >> 63 else x
def shl(x, n): return s64((x & M64) << (n & 63))
def original(src, srcPos, dstInit, dstPos, n):
    out = dstInit
    for i in range(n):
        shift = i * 32 + dstPos; bits = shl(0xffffffff & src[i + srcPos], shift); mask = shl(0xffffffff, shift); out = s64((out & ~mask) | bits)
    return out
def lane(at, buggy): return (at + 31) // 32 if buggy else at // 32
def high(src, srcPos, dstInit, dstPos, n, buggy):
    L = lane(dstPos, buggy); off = dstPos % 32; out = dstInit
    for index in range(n):
        ln = L + index; shift = ln * 32 + off; field = shl(0xffffffff, shift); out = s64((out & ~field) | shl(0xffffffff & src[srcPos + index], shift))
    return out
def low(src, srcPos, dstInit, dstPos, n, buggy):
    run = src[srcPos:srcPos + n]; L = lane(dstPos, buggy); off = dstPos % 32; out = dstInit
    for index in range(n):
        shift = (L + index) * 32 + off; value = 0xffffffff & run[index]; field = shl(0xffffffff, shift); out = s64((out & ~field) | shl(value, shift))
    return out
src = [0x1CDF1F0C, 0x00123456, 0x78000000, -1, 0x7fffffff]
cases = []
for srcPos, n in ((0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (3, 2), (0, 0)):
    for dstPos in range(0, 64):
        if n and (n - 1) * 32 + dstPos >= 64: continue
        for dstInit in (0, 0x123456789ABCDEF0, -1):
            cases.append((srcPos, dstInit, dstPos, n))
ok_correct = ok_buggy = 0; diff_correct = []; buggy_differs_from_correct = 0
for (srcPos, dstInit, dstPos, n) in cases:
    o = original(src, srcPos, dstInit, dstPos, n); lc = low(src, srcPos, dstInit, dstPos, n, False); hc = high(src, srcPos, dstInit, dstPos, n, False)
    lb = low(src, srcPos, dstInit, dstPos, n, True); hb = high(src, srcPos, dstInit, dstPos, n, True)
    if o == lc == hc: ok_correct += 1
    else: diff_correct.append((srcPos, dstInit, dstPos, n, o, lc, hc))
    if lb == hb: ok_buggy += 1
    if lb != o: buggy_differs_from_correct += 1
trig = dict(src=src, srcPos=1, dstInit=0, dstPos=8, n=1)
res = {"cases": len(cases), "correct_chains_equal_original": ok_correct, "buggy_chains_equal_each_other": ok_buggy, "buggy_differs_from_correct_cases": buggy_differs_from_correct,
       "buggy_visible_only_when_dstPos_mod_32_nonzero": all((low(src, s, d, p, n, True) == original(src, s, d, p, n)) == (p % 32 == 0 or n == 0) for (s, d, p, n) in cases),
       "trigger": {"expected": hex(original(src, 1, 0, 8, 1)), "expected_dec": original(src, 1, 0, 8, 1), "buggy_low": hex(low(src, 1, 0, 8, 1, True)), "buggy_high": hex(high(src, 1, 0, 8, 1, True)), "buggy_dec": low(src, 1, 0, 8, 1, True),
                   "assertion2_dstPos32_expected": hex(original(src, 1, 0, 32, 1)), "assertion2_buggy": hex(low(src, 1, 0, 32, 1, True))},
       "existing_tests_dstPos0_unaffected": all(low(src, s, d, 0, n, True) == original(src, s, d, 0, n) for (s, d, p, n) in cases if p == 0), "first_differences": diff_correct[:5]}
print(json.dumps(res, indent=1)); json.dump(res, open(sys.argv[1], "w"), indent=1) if len(sys.argv) > 1 else None
