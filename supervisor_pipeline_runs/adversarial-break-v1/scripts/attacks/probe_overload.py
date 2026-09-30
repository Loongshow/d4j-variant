"""Empirical probe for the overload attack: add the round-trip boolean test, try candidate one-line bugs, report trigger + collateral."""
import sys, json, re, os
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1/scripts"); import buildlib as B
W = sys.argv[1]; which = sys.argv[2] if len(sys.argv) > 2 else "none"
CONV = "src/main/java/org/apache/commons/lang3/Conversion.java"; TEST = "src/test/java/org/apache/commons/lang3/ConversionTest.java"
B.reset(W)
B.add_import(W, TEST, "import static org.junit.Assert.assertTrue;")
B.add_test_method(W, TEST, '''    @Test
    public void testLang1180() {
        final long seed = 0x9ABCDEF012345678L;
        long acc = 0L;
        acc ^= Conversion.intArrayToLong(Conversion.longToIntArray(seed, 0, new int[2], 0, 2), 0, 0L, 0, 2);
        acc ^= Conversion.shortArrayToLong(Conversion.longToShortArray(seed, 0, new short[4], 0, 4), 0, 0L, 0, 4);
        acc ^= Conversion.byteArrayToLong(Conversion.longToByteArray(seed, 0, new byte[8], 0, 8), 0, 0L, 0, 8);
        acc ^= Conversion.hexToLong(Conversion.longToHex(seed, 0, "", 0, 16), 0, 0L, 0, 16);
        acc ^= Conversion.binaryToLong(Conversion.longToBinary(seed, 0, new boolean[64], 0, 64), 0, 0L, 0, 64);
        final int seed32 = (int) seed;
        int acc32 = 0;
        acc32 ^= Conversion.shortArrayToInt(Conversion.intToShortArray(seed32, 0, new short[2], 0, 2), 0, 0, 0, 2);
        acc32 ^= Conversion.byteArrayToInt(Conversion.intToByteArray(seed32, 0, new byte[4], 0, 4), 0, 0, 0, 4);
        acc32 ^= Conversion.hexToInt(Conversion.intToHex(seed32, 0, "", 0, 8), 0, 0, 0, 8);
        acc32 ^= Conversion.binaryToInt(Conversion.intToBinary(seed32, 0, new boolean[32], 0, 32), 0, 0, 0, 32);
        assertTrue(acc == seed && acc32 == 0);
    }''')
BUGS = {
 "B1": (CONV, "            final long bits = (0xffL & src[i + srcPos]) << shift;\n            final long mask = 0xffL << shift;\n            out = (out & ~mask) | bits;\n        }\n        return out;\n    }\n\n    /**\n     * <p>Converts an array of byte into an int",
        None),
}
# simpler: apply by unique context lines
if which == "B1":   # byteArrayToLong: drop the unsigned mask
    t, eol = B.read(W, CONV); k = t.index("public static long byteArrayToLong"); seg = t[k:k+1200]
    old = "            final long bits = (0xffL & src[i + srcPos]) << shift;"; assert seg.count(old) == 1
    t = t[:k] + seg.replace(old, "            final long bits = ((long) src[i + srcPos]) << shift;", 1) + t[k+1200:]; B.write(W, CONV, t, eol)
elif which == "B2":  # longToShortArray: drop the top bit of every short (scoped to that method)
    t, eol = B.read(W, CONV); k = t.index("public static short[] longToShortArray"); seg = t[k:k+900]
    old = "            dst[dstPos + i] = (short)(0xffff & (src >> shift));"; assert seg.count(old) == 1, seg.count(old)
    t = t[:k] + seg.replace(old, "            dst[dstPos + i] = (short)(0x7fff & (src >> shift));", 1) + t[k+900:]; B.write(W, CONV, t, eol)
elif which == "B3":  # binaryToLong: use the wrong bit weight order for the last... simpler: shift off by one in hexToLong
    t, eol = B.read(W, CONV); k = t.index("public static long hexToLong"); seg = t[k:k+1100]
    old = "            shift = i * 4 + dstPos;"; assert seg.count(old) == 1, seg.count(old)
    t = t[:k] + seg.replace(old, "            shift = i * 4 + dstPos + (i >> 3);", 1) + t[k+1100:]; B.write(W, CONV, t, eol)
elif which == "B4":  # intToBinary: reversed bit order within each nibble? -> plausible: wrong mask width
    B.replace_once(W, CONV, "            dst[dstPos + i] = ((0x1 & (src >> shift)) != 0);\n        }\n        return dst;\n    }\n\n    /**\n     * <p>Converts a short into an array of boolean",
                   "            dst[dstPos + i] = ((0x1 & (src >> (shift ^ 1))) != 0);\n        }\n        return dst;\n    }\n\n    /**\n     * <p>Converts a short into an array of boolean")
ok, o = B.compile_(W); print("compile:", ok)
n, ft = B.trigger(W, "org.apache.commons.lang3.ConversionTest::testLang1180"); print("trigger fails:", n, ft[:2])
o = B.sh(["defects4j", "test"], W, check=False); m = re.search(r"Failing tests:\s*(\d+)", o); print("full suite failing:", m.group(1) if m else "?", re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M)[:6])
B.reset(W)
