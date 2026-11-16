"""ADV-REGISTRY-01: registry dispatch by runtime source type over five real packer implementations that all share the
method name `pack`; the fault is in the implementation the trigger selects (int[] -> Packer32); Packer16 is correct but
written with an odd-looking shift and is registered first. Usage: build_registry.py <work> <pkgdir>"""
import sys, json, os
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1/scripts"); import buildlib as B
W, PKG = sys.argv[1], sys.argv[2]; os.makedirs(PKG, exist_ok=True)
HIST_TEST = B.HIST_LANG_PATCH.replace("variant.patch", "test.patch")
CONV = "src/main/java/org/apache/commons/lang3/Conversion.java"; TEST = "src/test/java/org/apache/commons/lang3/ConversionTest.java"; PK = "src/main/java/org/apache/commons/lang3/"
HDR = """/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.commons.lang3;
"""
B.reset(W)
B.apply_patch(W, HIST_TEST); B.diff_to(W, f"{PKG}/test.patch", [TEST]); B.sh(["git", "checkout", "--", TEST], W)
B.new_file(W, PK + "Packer.java", HDR + """
/**
 * <p>Packs a run of source elements into a {@code long} holder.</p>
 *
 * <p>Implementations are selected by {@link Packers#forSource(Object)} according to the
 * element type of the source.</p>
 *
 * @since 3.2
 */
public interface Packer {

    /**
     * <p>Packs {@code count} elements of {@code source}, starting at {@code sourcePos}, into
     * {@code holder} starting at bit {@code holderPos}.</p>
     *
     * @param source the source to read from
     * @param sourcePos the index of the first element to read
     * @param holder the initial value of the holder
     * @param holderPos the position in the holder of the first element
     * @param count the number of elements to pack
     * @return the holder with the elements packed
     */
    long pack(Object source, int sourcePos, long holder, int holderPos, int count);
}
""")
B.new_file(W, PK + "Packers.java", HDR + """
import java.util.HashMap;
import java.util.Map;

/**
 * <p>Registry of {@link Packer} implementations keyed by the source type they accept.</p>
 *
 * @since 3.2
 */
public final class Packers {

    private static final Map<Class<?>, Packer> REGISTRY = new HashMap<Class<?>, Packer>();

    static {
        REGISTRY.put(short[].class, new Packer16());
        REGISTRY.put(String.class, new Packer4());
        REGISTRY.put(boolean[].class, new Packer1());
        REGISTRY.put(byte[].class, new Packer8());
        REGISTRY.put(int[].class, new Packer32());
    }

    private Packers() {
    }

    /**
     * <p>Returns the packer registered for the runtime type of {@code source}.</p>
     *
     * @param source the source that will be packed
     * @return the packer for its type
     * @throws IllegalArgumentException if no packer is registered for the type
     */
    public static Packer forSource(final Object source) {
        final Packer packer = REGISTRY.get(source.getClass());
        if (packer == null) {
            throw new IllegalArgumentException("no packer for " + source.getClass().getName());
        }
        return packer;
    }
}
""")
def impl(name, elem, width, mask, extract, shift_expr, doc):
    return HDR + f"""
/**
 * <p>{doc}</p>
 *
 * @since 3.2
 */
final class {name} implements Packer {{

    public long pack(final Object source, final int sourcePos, final long holder, final int holderPos, final int count) {{
        final {elem} src = ({elem}) source;
        long out = holder;
        int shift = 0;
        for (int i = 0; i < count; i++) {{
            shift = {shift_expr};
            final long bits = ({mask} & {extract}) << shift;
            final long mask = {mask} << shift;
            out = (out & ~mask) | bits;
        }}
        return out;
    }}
}}
"""
B.new_file(W, PK + "Packer32.java", impl("Packer32", "int[]", 32, "0xffffffffL", "src[i + sourcePos]", "(i + holderPos) * 32", "Packs {@code int} values, 32 bits each."))
B.new_file(W, PK + "Packer16.java", impl("Packer16", "short[]", 16, "0xffffL", "src[i + sourcePos]", "(i << 4) + holderPos", "Packs {@code short} values, 16 bits each."))
B.new_file(W, PK + "Packer8.java", impl("Packer8", "byte[]", 8, "0xffL", "src[i + sourcePos]", "i * 8 + holderPos", "Packs {@code byte} values, 8 bits each."))
B.new_file(W, PK + "Packer4.java", impl("Packer4", "String", 4, "0xfL", "Conversion.hexDigitToInt(src.charAt(i + sourcePos))", "i * 4 + holderPos", "Packs hexadecimal digits, 4 bits each."))
B.new_file(W, PK + "Packer1.java", impl("Packer1", "boolean[]", 1, "0x1L", "(src[i + sourcePos] ? 1 : 0)", "i + holderPos", "Packs {@code boolean} values, one bit each."))
# facades delegate to the registry (guards untouched)
def delegate(sig_start, old_loop_first_line, n):
    t, eol = B.read(W, CONV); k = t.index(sig_start); seg = t[k:k + 1600]
    s = seg.index("        long out = dstInit;"); e = seg.index("        return out;\n    }", s) + len("        return out;")
    seg2 = seg[:s] + f"        return Packers.forSource(src).pack(src, srcPos, dstInit, dstPos, {n});" + seg[e:]
    B.write(W, CONV, t[:k] + seg2 + t[k + 1600:], eol)
delegate("public static long intArrayToLong", None, "nInts"); delegate("public static long shortArrayToLong", None, "nShorts")
delegate("public static long byteArrayToLong", None, "nBytes"); delegate("public static long hexToLong", None, "nHex"); delegate("public static long binaryToLong", None, "nBools")
B.diff_to(W, f"{PKG}/variant.patch"); B.reset(W)
cands = ["org.apache.commons.lang3.Packer32#pack", "org.apache.commons.lang3.Packer16#pack", "org.apache.commons.lang3.Packer8#pack", "org.apache.commons.lang3.Packer4#pack",
         "org.apache.commons.lang3.Packer1#pack", "org.apache.commons.lang3.Packers#forSource", "org.apache.commons.lang3.Conversion#intArrayToLong"]
cfg = {"variant_id": "ADV-REGISTRY-01", "attack_id": "NAV-01", "title": "runtime-type registry over five real `pack` implementations; fault in the selected one, odd-looking correct sibling registered first",
       "project": "Lang", "base_version": "Lang-1f", "trigger": "org.apache.commons.lang3.ConversionTest::testLang1112", "related_tests": [], "test_file": TEST,
       "expected_signature": "expected:<64729929216> but was:<252851286>", "assertion_class_regex": "AssertionFailedError|AssertionError",
       "gold": {"class": "org.apache.commons.lang3.Packer32", "method": "pack", "file": PK + "Packer32.java", "decl": "public long pack(final Object source",
                "bug_line": "            shift = (i + holderPos) * 32;", "orig_line": "            shift = i * 32 + holderPos;"},
       "allowed_collateral": ["org.apache.commons.lang3.ConversionTest::testIntArrayToLong"],
       "mechanism": "the facade reaches the fault through Packers.forSource(src).pack(...): the symbol `pack` names five methods in five classes, the selected one depends on the runtime type of the source array, and the first-registered sibling (Packer16) has a correct but unusual shift expression; grep-the-next-symbol returns five equally named candidates",
       "classification": ["SEARCH_TRAP", "TOOL_BEHAVIOR_TRAP", "CANDIDATE_OVERLOAD", "MODEL_SPECIFIC", "ARTIFACT"], "family": "word-offset convention (historical shift fault) behind registry dispatch",
       "effect": "int words are placed at (i + dstPos) * 32 instead of i * 32 + dstPos; any packing with a non-zero destination offset is wrong",
       "predicted_wrong_top1": "org.apache.commons.lang3.Packer16#pack (read first, odd shift) or Packers#forSource or the facade",
       "roles": {"org.apache.commons.lang3.Packer16#pack": "implementation-sibling", "org.apache.commons.lang3.Packer8#pack": "implementation-sibling", "org.apache.commons.lang3.Packer4#pack": "implementation-sibling",
                 "org.apache.commons.lang3.Packer1#pack": "implementation-sibling", "org.apache.commons.lang3.Packers#forSource": "registry", "org.apache.commons.lang3.Conversion#intArrayToLong": "facade"},
       "candidates": cands, "structure": "facade -> registry lookup by runtime type -> one of five same-named implementations", "hops": 2, "chain": [],
       "changed_files": [{"file": CONV, "role": "facade"}, {"file": PK + "Packers.java", "role": "registry"}] + [{"file": PK + f"Packer{w}.java", "role": ("gold" if w == 32 else "implementation-sibling")} for w in (32, 16, 8, 4, 1)] + [{"file": TEST, "role": "trigger"}],
       "package_dir": PKG}
json.dump(cfg, open(f"{PKG}/attack.json", "w"), indent=1)
print("built ADV-REGISTRY-01:", os.path.getsize(f"{PKG}/variant.patch"), "B variant")
