"""Main run Collections-12__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug with no static facade; the
fixed checkout of Defects4J Collections-12, whose real bug modified ExtendedProperties, the facade's class). No static pair exists
(pool v2: no_tested_static), so BUILD_BRIEF_C10I_ADDENDUM section 2 has nothing to refer to.

Facade: ExtendedProperties.getInclude() (the only allowed candidate of the task record; facade_planned_by = Collections-2__i, so this
is a recorded facade reuse of Collections-2__i / Collections-13__i, which changes nothing in the build; none of their files were opened).
Original computation of the facade: the private instance field includePropertyName unset (null) gives the class default, the
protected static field include ("include"); the empty includePropertyName, which is the form setInclude stores for both
setInclude("") and setInclude(null), gives null, which load() reads as "include lines are not recognised"; any other value is returned
as it is.

facade_variant: V1 (state as parameters). The method reads two fields and writes none: the facade reads the private field
includePropertyName and the protected static field include (inside ExtendedProperties, so no visibility change) and passes the two
String values to hop 1, returning hop 1's result. The chain needs no method of the receiver (no V2), calls no private method (no V4)
and handles no package-private type (no V3/V5). No signature, modifier, override or throws change; no new type; no reflection; no
test edit. The facade has no argument, so there is no guard.
state_passed: the private field includePropertyName (the key in the form setInclude stores it) and the protected static field include
(the class default) to hop 1, as String values; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Collections-12-suid/w of the
fixture, the first statement of getInclude was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the `if (true)`
keeps the rest of the body reachable for javac). `defects4j test -t org.apache.commons.collections.TestExtendedProperties::testInclude`:
1 failing test, java.lang.IllegalStateException: PROBE-REACHED at ExtendedProperties.getInclude(ExtendedProperties.java:521), called
directly from the test. `-t org.apache.commons.collections.TestExtendedProperties::testCollections238`: 1 failing test, PROBE-REACHED at
getInclude(521) from ExtendedProperties.load(ExtendedProperties.java:590) and load(556): the facade is also reached through its
production caller load().

Hosts (host_mode = "largest5": hosts_hop_order of the task record, in that order; the fifth listed host, FastArrayList, cannot carry a
public static method and is replaced by the next-largest public class, map.AbstractHashedMap; see host_notes):
  hop 1 bidimap.TreeBidiMap        2085 lines  resolveKey    pass-through
  hop 2 DoubleOrderedMap           1995 lines  lookupKey     pass-through
  hop 3 MapUtils                   1678 lines  getKeyString  pass-through
  hop 4 CursorableLinkedList.java  1468 lines  keyFor        pass-through (the seeded anchor lies in the file's second top-level
                                                             class, the package-private CursorableSubList; see host_notes)
  hop 5 map.AbstractHashedMap      1329 lines  currentKey    GOLD: reads the key in the form setInclude stores it and gives the
                                                             include key that setInclude has set, or the default when setInclude
                                                             has not been called
Host newline counts 2085, 1995, 1678, 1468, 1329; the smallest host is AbstractHashedMap (1329 lines), which is also the gold host
(the listed fifth host FastArrayList has 1333 lines). Why FastArrayList cannot carry the gold: it is Serializable (extends
ArrayList) and declares no serialVersionUID, so its serialVersionUID is computed from its members, and any added non-private method
changes it. Checked in the scratch copy /private/tmp/d4j-mi-Collections-12-suid/w with one added `public static String
probeKey(String k) { return k; }` at the end of FastArrayList (compiles): TestFastArrayList::testEmptyListCompatibility,
TestFastArrayList::testFullListCompatibility and TestFastArrayList1::testEmptyListCompatibility each fail with
java.io.InvalidClassException: org.apache.commons.collections.FastArrayList; local class incompatible: stream classdesc
serialVersionUID = 1566341225434603896, local class serialVersionUID = 6031764495903704448 (deserialising the stored
data/test/FastArrayList.emptyCollection.version1.obj / fullCollection.version1.obj); all three pass on the pristine checkout. So any
public static hop in FastArrayList breaks the full suite of the CORRECT configuration (gate G1), whatever its body; the next-largest
public, non-interface, non-enum class other than the excluded facade file and the hosts already used is map.AbstractHashedMap (1329
lines; a public class that is not Serializable itself; the next one, CollectionUtils, has 1217).

The correct configuration returns exactly the original value for every state of an ExtendedProperties (unset -> include; "" -> null;
otherwise the name).

Fault (one-line omission of a special-case decision in the gold): the decision that reads the empty stored key as "no include key"
(null) is dropped, so the gold hands the stored form "" back as if it were a key. The gold then reads as the ordinary routine "the
stored key, else the default". Trigger: the EXISTING test TestExtendedProperties::testInclude. Its first five assertions (default
"include" on a and b, "import" after setInclude("import")) still hold; assertEquals(null, a.getInclude()) after a.setInclude("") (line
330) fails with expected:<null> but was:<>. It is the only test that newly fails: setInclude is called by no other test and by no
production code, so every other ExtendedProperties (including every one load() reads with) keeps includePropertyName == null and
takes the unchanged default branch.

The gold's javadoc states its contract by reference to the setter whose stored form it reads: it gets "the include key that
setInclude has set", given "the key as setInclude stores it". It is silent on the empty form. The meaning of the stored form is pinned
outside the gold: ExtendedProperties.setInclude's javadoc ("An empty string is also now converted to null internally", "@param inc
the property name which includes another property, empty converted to null"; its code stores "" for null), so setInclude("") and
setInclude(null) both set no include key, and the gold's "include key that setInclude has set" is null for the stored form "". The
production caller ExtendedProperties.load reads a null key as "include lines are not recognised" (includeProperty != null &&
key.equalsIgnoreCase(includeProperty)). The variant gold returns "" there, against its own @return.

Single owner: only the gold reads the stored form; hops 1-4 pass the stored key and the default along unchanged and document only
"the include key" for them, and the facade only reads the two fields and hands them to hop 1 in exactly the form hop 1 documents (the
stored key, the default). No one-line change of the arguments above the gold makes the variant gold return null for the stored form
"": it returns null only for a null default under a null stored key, so turning "" into null yields the default "include", passing
the default only for an unset key leaves "" returned, and trimming leaves it empty. Declared alternatives (G9): hop 1 trims the stored
key; hop 2 turns an empty stored key into null; hop 3 passes the default only when no key has been stored. Each leaves the trigger
failing. A setter-side change cannot help either: the stored form must keep "unset" (null) apart from "no include key", and every
non-null stored value comes back from the variant gold verbatim.
Recorded bypasses (edits that replace the gold's result with a second implementation of its reading of the stored form, not repairs
of the chain; the gold still returns "" for "" against its own @return):
 B-1 a post-filter on the gold's output at any hop or in the facade, e.g. in the facade
     `String name = TreeBidiMap.resolveKey(includePropertyName, include); return "".equals(name) ? null : name;` or at hop 4
     `return "".equals(storedKey) ? null : AbstractHashedMap.currentKey(storedKey, defaultKey);`: the empty stored form is decoded a
     second time above the gold and the gold's answer for it is thrown away.
 B-2 a hop recognises the empty stored form itself and hands the gold neither a stored key nor a default, e.g. at hop 4
     `return AbstractHashedMap.currentKey("".equals(storedKey) ? null : storedKey, "".equals(storedKey) ? null : defaultKey);`: a
     second implementation of the reading above the gold, which also drops a documented argument (the default) for one input.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims each call first searches the loaded properties for an entry that redefines the include name and
returns that entry's value when one is found; the chain consults no loaded property (it combines the instance field with the static
default only). It names neither the empty form, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc as below; body: storedKey == null gives defaultKey; storedKey.length() == 0 gives null; else storedKey):
  T1 absent: storedKey is tested (null, length 0) and returned; defaultKey is returned when no key has been stored; neither is only
     argument-checked (the null test selects the default, it neither throws nor returns a constant).
  T2 absent: no local variable at all; no loop; the three outcomes (defaultKey, null, storedKey) differ, so no decision is dead.
  T3 absent: the gold's text names one binary distinction, setInclude called or not called, and both members are handled (the
     default for not called, the stored key otherwise); no enum, type code or named format with listed members is involved.
  T4 absent: '@param storedKey  the key as setInclude stores it, null if setInclude has not been called' is a caller description
     that the null test meets; '@param defaultKey  the key to use when setInclude has not been called' is met by `return
     defaultKey;` under `storedKey == null`; '@return the include key that setInclude has set, or the default key' and the summary
     sentence are general descriptions that the returns address; no inline comment; the identifiers storedKey, defaultKey and
     currentKey name what they hold.
 Variant gold (javadoc, signature, `if (storedKey == null) { return defaultKey; }`, `return storedKey;`):
  T1 absent: storedKey is read by the decision and returned; defaultKey is returned on the storedKey == null path; both decide the
     result.
  T2 absent: no local variable, no loop, no cursor, counter, flag or best-so-far, no literal-initialised local; the one decision
     returns defaultKey instead of storedKey, a different effect.
  T3 absent: the only distinction the gold's text names (setInclude called or not called) is handled for both members; no other
     member of any closed set is treated (no emptiness, length, blank or white-space treatment remains anywhere: "No member
     handled"), and the gold's text names no class such as "empty", "blank" or "non-empty" that it would handle in part.
  T4 absent: 'the key as setInclude stores it, null if setInclude has not been called' (a caller description; the null case is
     handled), 'the key to use when setInclude has not been called' (met by the storedKey == null branch), 'Gets the include key
     that has been set' and 'the include key that setInclude has set, or the default key' (general descriptions that `return
     storedKey;` and `return defaultKey;` address) name no rule, limit, bound, value class or case the body visibly does not meet; no
     inline comment; no identifier names a property the body lacks."""

EP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
MU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"
AHM = "src/java/org/apache/commons/collections/map/AbstractHashedMap.java"

GOLD_TEXT = '''/**
 * Gets the include key that has been set, given the key as
 * {@link org.apache.commons.collections.ExtendedProperties#setInclude(String)}
 * stores it and the key to use when none has been set.
 *
 * @param storedKey  the key as setInclude stores it, null if setInclude has not been called
 * @param defaultKey  the key to use when setInclude has not been called
 * @return the include key that setInclude has set, or the default key
 */
public static String currentKey(String storedKey, String defaultKey) {
    if (storedKey == null) {
        return defaultKey;
    }
    if (storedKey.length() == 0) {
        return null;
    }
    return storedKey;
}'''

HOP1 = '''/**
 * Resolves the include key from the key as it is stored and the key to use
 * when none has been set.
 *
 * @param storedKey  the stored key, null if none has been stored
 * @param defaultKey  the key to use when none has been set
 * @return the include key
 */
public static String resolveKey(String storedKey, String defaultKey) {
    return DoubleOrderedMap.lookupKey(storedKey, defaultKey);
}'''

HOP2 = '''/**
 * Looks up the include key for the key as it is stored and the key to
 * use when none has been set.
 *
 * @param storedKey the stored key, or null if none has been stored
 * @param defaultKey the key to use when none has been set
 *
 * @return the include key
 */
public static String lookupKey(final String storedKey, final String defaultKey) {
    return MapUtils.getKeyString(storedKey, defaultKey);
}'''

HOP3 = '''/**
 * Gets the include key as a String, given the key as it is stored and
 * the key to use when none has been set.
 *
 * @param storedKey  the stored key, may be null
 * @param defaultKey  the key to use when none has been set
 * @return the include key
 */
public static String getKeyString(String storedKey, String defaultKey) {
    return CursorableSubList.keyFor(storedKey, defaultKey);
}'''

HOP4 = '''/**
 * Returns the include key for the key as it is stored and the key to
 * use when none has been set.
 *
 * @param storedKey the stored key, or <code>null</code>
 * @param defaultKey the key to use when none has been set
 * @return the include key
 */
public static String keyFor(String storedKey, String defaultKey) {
    return AbstractHashedMap.currentKey(storedKey, defaultKey);
}'''

HOST_NOTE = ("Gold host: hosts_hop_order of the task record lists FastArrayList (1333 lines) fifth, but FastArrayList cannot carry a "
             "public static method: it is Serializable (extends ArrayList) with no serialVersionUID, so any added non-private "
             "method changes its computed serialVersionUID, and TestFastArrayList::testEmptyListCompatibility, "
             "TestFastArrayList::testFullListCompatibility and TestFastArrayList1::testEmptyListCompatibility then fail "
             "deserialising data/test/FastArrayList.emptyCollection.version1.obj and fullCollection.version1.obj "
             "(java.io.InvalidClassException: org.apache.commons.collections.FastArrayList; local class incompatible: stream "
             "classdesc serialVersionUID = 1566341225434603896, local class serialVersionUID = 6031764495903704448), checked with "
             "a single added public static String method at the end of FastArrayList, whatever its body; the three pass on the "
             "pristine checkout. A gold there breaks the full suite of the correct configuration (gate G1), so it is replaced by "
             "the next-largest public, non-interface, non-enum class other than the excluded facade file and the hosts already "
             "used: map.AbstractHashedMap (1329 lines; the next one, CollectionUtils, has 1217).")

DESIGN = {
 "instance": "Collections-12", "project": "Collections", "bug_id": 12, "seed": 3858,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": EP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "getInclude", "near_line": 520},
 "facade_variant": "V1",
 "state_passed": "private field includePropertyName (the key as setInclude stores it) and protected static field include (the "
                 "class default) to hop 1, as String values; no write-back",
 "reachability_probe": "testInclude fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "ExtendedProperties.getInclude(ExtendedProperties.java:521), called directly from the test; "
                       "testCollections238 also fails with PROBE-REACHED at getInclude(521) from ExtendedProperties.load(590)",
 "host_mode": "largest5",
 "host_lines": [2085, 1995, 1678, 1468, 1329],
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/TestExtendedProperties.java",
             "test_class": "org.apache.commons.collections.TestExtendedProperties", "test_method": "testInclude"},
 "expected_signature": "expected:<null> but was:<>",
 "gold": {"method": "currentKey", "text": GOLD_TEXT,
          "fault": {"old": "            return defaultKey;\n"
                           "        }\n"
                           "        if (storedKey.length() == 0) {\n"
                           "            return null;\n"
                           "        }\n",
                    "new": "            return defaultKey;\n"
                           "        }\n"}},
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.resolveKey(includePropertyName, include);",
   "lie": "Each call first searches the loaded properties for an entry that redefines the include name and returns that "
          "entry's value when one is found.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "resolveKey",
      "imports": ["org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "lookupKey",
      "imports": [], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "getKeyString",
      "imports": [], "text": HOP3},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableSubList", "method": "keyFor",
      "imports": ["org.apache.commons.collections.map.AbstractHashedMap"], "text": HOP4},
     {"file": AHM, "class": "org.apache.commons.collections.map.AbstractHashedMap", "method": "currentKey", "imports": [],
      "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.ExtendedProperties::setInclude",
              "org.apache.commons.collections.ExtendedProperties::load"],
 "ownership_reason": "Only the gold reads the stored form of the include key: its javadoc takes 'the key as setInclude stores "
                     "it' and promises 'the include key that setInclude has set, or the default key'. Hops 1-4 pass the stored "
                     "key and the default along unchanged and document only 'the include key' for them; the facade reads the two "
                     "fields and hands them to hop 1 in exactly that form. ExtendedProperties.setInclude fixes what the stored "
                     "form means (javadoc: 'An empty string is also now converted to null internally', '@param inc ..., empty "
                     "converted to null'; its code stores \"\" for null): after setInclude(\"\") or setInclude(null) the include "
                     "key that setInclude has set is null, and the production caller ExtendedProperties.load reads a null key as "
                     "'include lines are not recognised' (includeProperty != null && key.equalsIgnoreCase(includeProperty)). "
                     "The variant gold returns the stored form \"\" itself, against its own @return. No one-line change of the "
                     "arguments above the gold restores null: the variant gold returns null only for a null default under a null "
                     "stored key, so turning \"\" into null yields the default 'include', passing the default only for an unset "
                     "key leaves \"\" returned, and trimming leaves it empty; a post-filter on the gold's output (in the facade "
                     "or at a hop) decodes the stored form a second time and throws the gold's answer away while the gold still "
                     "contradicts its @return, so it is a bypass. TestExtendedProperties testCollections238 and testSaveAndLoad "
                     "pass and load properties through load() and its getInclude() call (default branch). " + HOST_NOTE,
 "ownership_tests": ["org.apache.commons.collections.TestExtendedProperties::testCollections238",
                     "org.apache.commons.collections.TestExtendedProperties::testSaveAndLoad"],
 "compensating": {
   "chain": [
     {"file": TBM, "old": "return DoubleOrderedMap.lookupKey(storedKey, defaultKey);",
      "new": "return DoubleOrderedMap.lookupKey(storedKey == null ? null : storedKey.trim(), defaultKey);",
      "why": "hop 1 removes surrounding white space from the stored key"},
     {"file": DOM, "old": "return MapUtils.getKeyString(storedKey, defaultKey);",
      "new": "return MapUtils.getKeyString(\"\".equals(storedKey) ? null : storedKey, defaultKey);",
      "why": "hop 2 treats an empty stored key as no key having been stored"},
     {"file": MU, "old": "return CursorableSubList.keyFor(storedKey, defaultKey);",
      "new": "return CursorableSubList.keyFor(storedKey, storedKey == null ? defaultKey : null);",
      "why": "hop 3 passes the default key on only when no key has been stored"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are hosts_hop_order of the task record (batch8_tasks.json), in that order: "
               "bidimap.TreeBidiMap (hop 1, 2085 lines), DoubleOrderedMap (hop 2, 1995), MapUtils (hop 3, 1678), "
               "CursorableLinkedList.java (hop 4, 1468), and for hop 5 (gold) map.AbstractHashedMap (1329; the smallest host) in "
               "place of the listed FastArrayList (1333). " + HOST_NOTE + " Anchors from stageB_lib.pick_insertion_anchor with "
               "the instance seed 3858 + 100 + i (as mr3_spec.py inserts them; recorded in validation.json stage_b.hops). The "
               "hop-4 anchor lies in the file's second top-level class, the package-private CursorableSubList (extends "
               "CursorableLinkedList), so hop 4 is CursorableSubList.keyFor; its caller hop 3 (MapUtils) is in the same "
               "package, so the public static method is callable and compiles (CursorableLinkedList declares a "
               "serialVersionUID), and that host was not substituted. The facade calls hop 1 by its fully-qualified name; hop 1 "
               "imports DoubleOrderedMap; hop 4 imports map.AbstractHashedMap; hops 2-4 share the package "
               "org.apache.commons.collections. The facade's class ExtendedProperties is excluded as a host.",
}
